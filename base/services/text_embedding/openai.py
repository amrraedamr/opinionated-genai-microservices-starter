from openai import (
    AsyncAzureOpenAI,
    AsyncOpenAI,
    AzureOpenAI,
    DefaultAsyncHttpxClient,
    DefaultHttpxClient,
    OpenAI,
)
from openai.types import CreateEmbeddingResponse

from base.models.definitions.model import ProviderType
from base.models.view_models.model import EmbeddingConfigurations
from base.services.common.meta import KeyedSingletonABC
from base.services.text_embedding import AbstractTextEmbeddingService


class OpenAITextEmbeddingService(
    AbstractTextEmbeddingService, metaclass=KeyedSingletonABC
):
    """
    OpenAI-compatible text embedding service.
    Works with any provider following the OpenAI API spec:
    OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, Together, Groq, etc.
    """

    def __init__(self, config: EmbeddingConfigurations) -> None:
        super().__init__()
        assert config.model_name is not None, "model_name is required"
        self._config: EmbeddingConfigurations = config
        self._model: str = config.model_name
        self._batch_size: int = config.batch_size
        self._dimensions: int | None = config.dimensions
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

    # ── Internals ────────────────────────────────────────────────────────

    def _create(self, input: str | list[str]) -> CreateEmbeddingResponse:
        if self._dimensions is not None:
            return self._client.embeddings.create(
                input=input, model=self._model, dimensions=self._dimensions
            )
        return self._client.embeddings.create(input=input, model=self._model)

    async def _acreate(self, input: str | list[str]) -> CreateEmbeddingResponse:
        if self._dimensions is not None:
            return await self._async_client.embeddings.create(
                input=input, model=self._model, dimensions=self._dimensions
            )
        return await self._async_client.embeddings.create(
            input=input, model=self._model
        )

    # ── Sync ─────────────────────────────────────────────────────────────

    def embed_query(self, text: str) -> list[float]:
        return self._create(text).data[0].embedding

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        results: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch: list[str] = texts[i : i + self._batch_size]
            response = self._create(batch)
            results.extend(
                item.embedding for item in sorted(response.data, key=lambda x: x.index)
            )
        return results

    # ── Async ────────────────────────────────────────────────────────────

    async def aembed_query(self, text: str) -> list[float]:
        return (await self._acreate(text)).data[0].embedding

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        results: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch: list[str] = texts[i : i + self._batch_size]
            response = await self._acreate(batch)
            results.extend(
                item.embedding for item in sorted(response.data, key=lambda x: x.index)
            )
        return results
