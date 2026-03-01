import asyncio
import time

from openai import (
    APITimeoutError,
    AsyncAzureOpenAI,
    AsyncOpenAI,
    AsyncStream,
    AzureOpenAI,
    DefaultAsyncHttpxClient,
    DefaultHttpxClient,
    OpenAI,
    RateLimitError,
    Stream,
)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionStreamOptionsParam,
)
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.completion_usage import CompletionUsage

from base.models.definitions.model import ProviderType
from base.models.view_models.model import ModelConfigurations
from base.models.view_models.streams import (
    StreamEnd,
    StreamError,
    StreamMessage,
    StreamStart,
)
from base.services.common.meta import KeyedSingletonABC
from base.services.llm import AbstractLLMService
from base.tools.stream import StreamIterator


class OpenAIService(AbstractLLMService, metaclass=KeyedSingletonABC):
    """
    OpenAI-compatible LLM service.
    Works with any provider following the OpenAI API spec:
    OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, Together, Groq, etc.
    """

    def __init__(self, config: ModelConfigurations) -> None:
        super().__init__()
        assert config.model_name is not None, "model_name is required"
        self._config: ModelConfigurations = config
        self._model: str = config.model_name
        self._retries: int = config.api_retries or 3
        self._wait_time: float = config.wait_time or 5
        self._client: AzureOpenAI | OpenAI = self._create_sync_client()
        self._async_client: AsyncAzureOpenAI | AsyncOpenAI = self._create_async_client()

    # ── Client construction ──────────────────────────────────────────────

    def _create_sync_client(self) -> AzureOpenAI | OpenAI:
        if self._config.api_type == ProviderType.AZURE_OPENAI:
            return AzureOpenAI(
                api_key=self._config.api_key,
                azure_deployment=self._config.deployment_name,
                azure_endpoint=self._config.api_host or "",
                api_version=self._config.api_version,
                http_client=DefaultHttpxClient(http2=True),
            )
        return OpenAI(
            api_key=self._config.api_key,
            base_url=self._config.api_host or None,
            http_client=DefaultHttpxClient(http2=True),
        )

    def _create_async_client(self) -> AsyncAzureOpenAI | AsyncOpenAI:
        if self._config.api_type == ProviderType.AZURE_OPENAI:
            return AsyncAzureOpenAI(
                api_key=self._config.api_key,
                azure_deployment=self._config.deployment_name,
                azure_endpoint=self._config.api_host or "",
                api_version=self._config.api_version,
                http_client=DefaultAsyncHttpxClient(http2=True),
            )
        return AsyncOpenAI(
            api_key=self._config.api_key,
            base_url=self._config.api_host or None,
            http_client=DefaultAsyncHttpxClient(http2=True),
        )

    # ── Sync ─────────────────────────────────────────────────────────────

    def generate(
        self,
        messages: list[ChatCompletionMessageParam],
        stream_iterator: StreamIterator | None = None,
    ) -> tuple[ChatCompletionMessage, CompletionUsage | None]:
        for attempt in range(self._retries + 1):
            try:
                return self._completions(messages, stream_iterator)
            except (RateLimitError, APITimeoutError):
                if attempt < self._retries:
                    time.sleep(self._wait_time * (attempt + 1))
                    continue
                raise

        raise RuntimeError("Exhausted all retries without returning or raising")

    def _completions(
        self,
        messages: list[ChatCompletionMessageParam],
        stream_iterator: StreamIterator | None = None,
    ) -> tuple[ChatCompletionMessage, CompletionUsage | None]:
        streaming: bool = bool(stream_iterator)

        response: ChatCompletion | Stream[ChatCompletionChunk] = (
            self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=streaming,
                stream_options=ChatCompletionStreamOptionsParam(include_usage=True)
                if streaming
                else None,
            )
        )

        if streaming and isinstance(response, Stream):
            assert stream_iterator is not None
            return self._stream_completions(response, stream_iterator)

        assert isinstance(response, ChatCompletion)
        return response.choices[0].message, response.usage

    def _stream_completions(
        self,
        response: Stream[ChatCompletionChunk],
        stream_iterator: StreamIterator,
    ) -> tuple[ChatCompletionMessage, CompletionUsage | None]:
        parts: list[str] = []
        started: bool = False
        usage: CompletionUsage | None = None

        try:
            for chunk in response:
                if not started:
                    started = True
                    stream_iterator.send(StreamStart())

                for choice in chunk.choices:
                    if choice.finish_reason:
                        break
                    if choice.delta and choice.delta.content:
                        parts.append(choice.delta.content)
                        stream_iterator.send(StreamMessage(data=choice.delta.content))

                if chunk.usage:
                    usage = chunk.usage

            stream_iterator.send(StreamEnd())

        except Exception:
            stream_iterator.send(StreamError())
            raise

        return ChatCompletionMessage(content="".join(parts), role="assistant"), usage

    # ── Async ────────────────────────────────────────────────────────────

    async def agenerate(
        self,
        messages: list[ChatCompletionMessageParam],
        stream_iterator: StreamIterator | None = None,
    ) -> tuple[ChatCompletionMessage, CompletionUsage | None]:
        for attempt in range(self._retries + 1):
            try:
                return await self._acompletions(messages, stream_iterator)
            except (RateLimitError, APITimeoutError):
                if attempt < self._retries:
                    await asyncio.sleep(self._wait_time * (attempt + 1))
                    continue
                raise

        raise RuntimeError("Exhausted all retries without returning or raising")

    async def _acompletions(
        self,
        messages: list[ChatCompletionMessageParam],
        stream_iterator: StreamIterator | None = None,
    ) -> tuple[ChatCompletionMessage, CompletionUsage | None]:
        streaming: bool = bool(stream_iterator)

        response: (
            ChatCompletion | AsyncStream[ChatCompletionChunk]
        ) = await self._async_client.chat.completions.create(
            model=self._model,
            messages=messages,
            stream=streaming,
            stream_options=ChatCompletionStreamOptionsParam(include_usage=True)
            if streaming
            else None,
        )

        if streaming and isinstance(response, AsyncStream):
            assert stream_iterator is not None
            return await self._astream_completions(response, stream_iterator)

        assert isinstance(response, ChatCompletion)
        return response.choices[0].message, response.usage

    async def _astream_completions(
        self,
        response: AsyncStream[ChatCompletionChunk],
        stream_iterator: StreamIterator,
    ) -> tuple[ChatCompletionMessage, CompletionUsage | None]:
        parts: list[str] = []
        started: bool = False
        usage: CompletionUsage | None = None

        try:
            async for chunk in response:
                if not started:
                    started = True
                    await stream_iterator.asend(StreamStart())

                for choice in chunk.choices:
                    if choice.finish_reason:
                        break
                    if choice.delta and choice.delta.content:
                        parts.append(choice.delta.content)
                        await stream_iterator.asend(
                            StreamMessage(data=choice.delta.content)
                        )

                if chunk.usage:
                    usage = chunk.usage

            await stream_iterator.asend(StreamEnd())

        except Exception:
            await stream_iterator.asend(StreamError())
            raise

        return ChatCompletionMessage(content="".join(parts), role="assistant"), usage
