import urllib.parse
from typing import Any

from pymongo import AsyncMongoClient, MongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.database import Database

from base.services.common.meta import Singleton
from base.services.configuration.local_config import LocalConfig


class MongoDBClient(metaclass=Singleton):
    """
    MongoDB client with both sync and async (pymongo) support.
    Designed to be instantiated once and reused across the application.
    """

    def __init__(self) -> None:
        self._connection_string: str = self._build_connection_string()

        self._min_pool_size: int = LocalConfig.get_int("mongodb_min_pool_size", 5)
        self._max_pool_size: int = LocalConfig.get_int("mongodb_max_pool_size", 50)
        self._connect_timeout_ms: int = LocalConfig.get_int(
            "mongodb_connect_timeout_ms", 10_000
        )
        self._socket_timeout_ms: int = LocalConfig.get_int(
            "mongodb_socket_timeout_ms", 30_000
        )
        self._server_selection_timeout_ms: int = LocalConfig.get_int(
            "mongodb_server_selection_timeout_ms", 30_000
        )

        self._sync_client: MongoClient[dict[str, Any]] | None = None
        self._async_client: AsyncMongoClient[dict[str, Any]] | None = None

    @staticmethod
    def _build_connection_string() -> str:
        base_path: str = LocalConfig.get("mongodb_base_path") or "mongodb"
        username: str = LocalConfig.get("mongodb_username") or ""
        password: str = LocalConfig.get("mongodb_password") or ""
        host: str = LocalConfig.get("mongodb_host") or "localhost"
        params: str = LocalConfig.get("mongodb_params") or ""

        return (
            f"{base_path}://"
            f"{urllib.parse.quote_plus(username)}:{urllib.parse.quote_plus(password)}"
            f"@{host}/{params}"
        )

    def _get_common_kwargs(self) -> dict[str, Any]:
        return {
            "minPoolSize": self._min_pool_size,
            "maxPoolSize": self._max_pool_size,
            "connectTimeoutMS": self._connect_timeout_ms,
            "socketTimeoutMS": self._socket_timeout_ms,
            "serverSelectionTimeoutMS": self._server_selection_timeout_ms,
        }

    # Sync

    def _ensure_sync_initialized(self) -> None:
        if self._sync_client is not None:
            return
        self._sync_client = MongoClient(
            self._connection_string, **self._get_common_kwargs()
        )

    @property
    def sync_client(self) -> MongoClient[dict[str, Any]]:
        """Sync pymongo client backed by the connection pool."""
        self._ensure_sync_initialized()
        assert self._sync_client is not None
        return self._sync_client

    def get_database(self, database: str) -> Database[dict[str, Any]]:
        """Get a sync database handle."""
        return self.sync_client.get_database(database)

    # Async

    def _ensure_async_initialized(self) -> None:
        if self._async_client is not None:
            return
        self._async_client = AsyncMongoClient(
            self._connection_string, **self._get_common_kwargs()
        )

    @property
    def async_client(self) -> AsyncMongoClient[dict[str, Any]]:
        """Async pymongo client backed by the connection pool."""
        self._ensure_async_initialized()
        assert self._async_client is not None
        return self._async_client

    def aget_database(self, database: str) -> AsyncDatabase[dict[str, Any]]:
        """Get an async database handle."""
        return self.async_client.get_database(database)

    # Health & Lifecycle

    def ping(self) -> bool:
        """Sync health check."""
        try:
            self.sync_client.admin.command("ping")
            return True
        except Exception:
            return False

    async def aping(self) -> bool:
        """Async health check."""
        try:
            await self.async_client.admin.command("ping")
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close sync client and connections."""
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        """Close async client and connections."""
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None

    async def close_all(self) -> None:
        """Close both sync and async resources."""
        self.close()
        await self.aclose()
