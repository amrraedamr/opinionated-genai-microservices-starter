from abc import abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

from base.services import AbstractService


class AbstractKeyVaultService(AbstractService):
    """Abstract base class for key vault service implementations."""

    @abstractmethod
    def get_secret(self, secret_name: str) -> str | None:
        """Fetch a secret from the key vault."""
        ...

    @abstractmethod
    async def aget_secret(self, secret_name: str) -> str | None:
        """Fetch a secret from the key vault asynchronously."""
        ...

    @abstractmethod
    def get_secrets(self, secret_names: list[str]) -> dict[str, str | None]:
        """Fetch multiple secrets from the key vault."""
        ...

    @abstractmethod
    async def aget_secrets(self, secret_names: list[str]) -> dict[str, str | None]:
        """Fetch multiple secrets from the key vault asynchronously."""
        ...

    @abstractmethod
    def upsert_secret(self, secret_key: str, secret_value: str) -> str:
        """Create or update a secret. Returns the secret version."""
        ...

    @abstractmethod
    async def aupsert_secret(self, secret_key: str, secret_value: str) -> str:
        """Create or update a secret asynchronously. Returns the secret version."""
        ...

    @abstractmethod
    def remove_secret(self, secret_name: str) -> None:
        """Remove a secret from the key vault."""
        ...

    @abstractmethod
    async def aremove_secret(self, secret_name: str) -> None:
        """Remove a secret from the key vault asynchronously."""
        ...

    @abstractmethod
    def list_secrets(self) -> Iterator[Any]:
        """List all secrets in the key vault."""
        ...

    @abstractmethod
    def alist_secrets(self) -> AsyncIterator[Any]:
        """List all secrets in the key vault asynchronously."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close sync client resources."""
        ...

    @abstractmethod
    async def aclose(self) -> None:
        """Close async client resources."""
        ...

    @abstractmethod
    def get_service_name(self) -> str:
        """Returns the name of the key vault service."""
        ...
