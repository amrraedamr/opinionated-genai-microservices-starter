from abc import ABC, abstractmethod

from base.services import AbstractService


class AbstractTextEmbeddingService(AbstractService, ABC):
    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...

    @abstractmethod
    async def aembed_query(self, text: str) -> list[float]: ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def aembed_documents(self, texts: list[str]) -> list[list[float]]: ...
