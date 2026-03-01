from typing import Any

from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.connection import ConnectionPool as AsyncConnectionPool
from redis.connection import ConnectionPool

from base.services.common.meta import Singleton
from base.services.configuration.local_config import LocalConfig


class RedisClient(metaclass=Singleton):
    """
    Redis client with connection pooling for both sync and async operations.
    Designed to be instantiated once and reused across the application.
    """

    def __init__(self) -> None:
        self._url = LocalConfig.get("redis_url")
        if not self._url:
            raise ValueError("redis_url must be configured in LocalConfig")

        self._ssl_cert_reqs = LocalConfig.get("redis_ssl_cert_reqs")
        self._max_connections = LocalConfig.get_int("redis_max_connections", 50)
        self._socket_timeout = LocalConfig.get_float("redis_socket_timeout", 5.0)
        self._socket_connect_timeout = LocalConfig.get_float(
            "redis_socket_connect_timeout", 5.0
        )
        self._retry_on_timeout = LocalConfig.get_bool("redis_retry_on_timeout", True)
        self._health_check_interval = LocalConfig.get_int(
            "redis_health_check_interval", 30
        )
        self._decode_responses = LocalConfig.get_bool("redis_decode_responses", True)

        self._sync_pool: ConnectionPool | None = None
        self._async_pool: AsyncConnectionPool | None = None
        self._sync_client: Redis | None = None
        self._async_client: AsyncRedis | None = None

    def _get_common_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "socket_timeout": self._socket_timeout,
            "socket_connect_timeout": self._socket_connect_timeout,
            "retry_on_timeout": self._retry_on_timeout,
            "health_check_interval": self._health_check_interval,
            "decode_responses": self._decode_responses,
        }
        if self._ssl_cert_reqs:
            kwargs["ssl_cert_reqs"] = self._ssl_cert_reqs
        return kwargs

    # -------------------------------------------------------------------------
    # Sync
    # -------------------------------------------------------------------------

    def _get_sync_pool(self) -> ConnectionPool:
        if self._sync_pool is None:
            self._sync_pool = ConnectionPool.from_url(
                self._url,
                max_connections=self._max_connections,
                **self._get_common_kwargs(),
            )
        return self._sync_pool

    @property
    def sync_client(self) -> Redis:
        """Sync Redis client backed by the connection pool."""
        if self._sync_client is None:
            self._sync_client = Redis(connection_pool=self._get_sync_pool())
        return self._sync_client

    # -------------------------------------------------------------------------
    # Async
    # -------------------------------------------------------------------------

    def _get_async_pool(self) -> AsyncConnectionPool:
        if self._async_pool is None:
            self._async_pool = AsyncConnectionPool.from_url(
                self._url,
                max_connections=self._max_connections,
                **self._get_common_kwargs(),
            )
        return self._async_pool

    @property
    def async_client(self) -> AsyncRedis:
        """Async Redis client backed by the connection pool."""
        if self._async_client is None:
            self._async_client = AsyncRedis(connection_pool=self._get_async_pool())
        return self._async_client

    # -------------------------------------------------------------------------
    # Health & Lifecycle
    # -------------------------------------------------------------------------

    def ping(self) -> bool:
        """Sync health check."""
        try:
            return self.sync_client.ping()  # type: ignore
        except Exception:
            return False

    async def aping(self) -> bool:
        """Async health check."""
        try:
            return await self.async_client.ping()  # type: ignore
        except Exception:
            return False

    def close(self) -> None:
        """Close sync connections and pool."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        if self._sync_pool:
            self._sync_pool.disconnect()
            self._sync_pool = None

    async def aclose(self) -> None:
        """Close async connections and pool."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
        if self._async_pool:
            await self._async_pool.disconnect()
            self._async_pool = None

    async def close_all(self) -> None:
        """Close both sync and async resources."""
        self.close()
        await self.aclose()
