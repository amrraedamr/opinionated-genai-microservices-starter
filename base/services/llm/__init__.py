from abc import abstractmethod

from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam
from openai.types.completion_usage import CompletionUsage

from base.services import AbstractService
from base.tools.stream import StreamIterator


class AbstractLLMService(AbstractService):
    """Base contract for LLM services. Concrete classes own their config and initialization."""

    @abstractmethod
    def generate(
        self,
        messages: list[ChatCompletionMessageParam],
        stream_iterator: StreamIterator | None = None,
    ) -> tuple[ChatCompletionMessage, CompletionUsage | None]: ...

    @abstractmethod
    async def agenerate(
        self,
        messages: list[ChatCompletionMessageParam],
        stream_iterator: StreamIterator | None = None,
    ) -> tuple[ChatCompletionMessage, CompletionUsage | None]: ...
