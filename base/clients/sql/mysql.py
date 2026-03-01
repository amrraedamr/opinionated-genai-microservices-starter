import ssl
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator
from urllib.parse import quote_plus

from sqlalchemy import QueuePool, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from base.models.orm import _import_all_tables
from base.services.common.meta import Singleton
from base.services.configuration.local_config import LocalConfig


class MySQLClient(metaclass=Singleton):
    """
    MySQL client with connection pooling for both sync and async operations.
    Designed to be instantiated once and reused across the application.
    """

    SYNC_DRIVER: str = "pymysql"
    ASYNC_DRIVER: str = "aiomysql"

    def __init__(self) -> None:
        self._pool_size: int = LocalConfig.get_int("db_pool_size", 10)
        self._max_overflow: int = LocalConfig.get_int("db_max_overflow", 20)
        self._pool_timeout: int = LocalConfig.get_int("db_pool_timeout", 30)
        self._pool_recycle: int = LocalConfig.get_int("db_pool_recycle", 3600)
        self._ssl_enabled: bool = LocalConfig.get_bool("db_ssl_enabled", True)

        self._username: str = quote_plus(LocalConfig.get("mysql_username") or "")
        self._password: str = quote_plus(LocalConfig.get("mysql_password") or "")
        self._host: str = LocalConfig.get("mysql_host") or ""
        self._database: str = LocalConfig.get("mysql_database") or ""

        self._sync_engine: Engine | None = None
        self._async_engine: AsyncEngine | None = None
        self._sync_session_maker: sessionmaker[Session] | None = None
        self._async_session_maker: async_sessionmaker[AsyncSession] | None = None

    def _get_database_url(self, driver: str) -> str:
        return (
            f"mysql+{driver}://{self._username}:{self._password}"
            f"@{self._host}/{self._database}"
        )

    def _get_pool_kwargs(self) -> dict[str, Any]:
        return {
            "pool_size": self._pool_size,
            "max_overflow": self._max_overflow,
            "pool_timeout": self._pool_timeout,
            "pool_recycle": self._pool_recycle,
            "pool_pre_ping": True,
            "pool_use_lifo": True,
            "echo": False,
            "echo_pool": False,
        }

    # -------------------------------------------------------------------------
    # Sync
    # -------------------------------------------------------------------------

    def _ensure_sync_initialized(self) -> None:
        if self._sync_engine is not None:
            return

        connect_args: dict[str, Any] = {
            "connect_timeout": 10,
            "read_timeout": 300,
            "write_timeout": 300,
        }
        if self._ssl_enabled:
            connect_args["ssl"] = ssl.create_default_context()

        self._sync_engine = create_engine(
            url=self._get_database_url(self.SYNC_DRIVER),
            poolclass=QueuePool,
            connect_args=connect_args,
            **self._get_pool_kwargs(),
        )
        self._sync_session_maker = sessionmaker(
            bind=self._sync_engine,
            autoflush=False,
            expire_on_commit=False,
        )
        _import_all_tables()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Sync session backed by the connection pool."""
        self._ensure_sync_initialized()
        assert self._sync_session_maker is not None
        with self._sync_session_maker.begin() as session:
            yield session

    # -------------------------------------------------------------------------
    # Async
    # -------------------------------------------------------------------------

    def _ensure_async_initialized(self) -> None:
        if self._async_engine is not None:
            return

        connect_args: dict[str, Any] = {"connect_timeout": 10}
        if self._ssl_enabled:
            connect_args["ssl"] = ssl.create_default_context()

        self._async_engine = create_async_engine(
            url=self._get_database_url(self.ASYNC_DRIVER),
            poolclass=AsyncAdaptedQueuePool,
            connect_args=connect_args,
            **self._get_pool_kwargs(),
        )
        self._async_session_maker = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )
        _import_all_tables()

    @asynccontextmanager
    async def asession(self) -> AsyncGenerator[AsyncSession, None]:
        """Async session backed by the connection pool."""
        self._ensure_async_initialized()
        assert self._async_session_maker is not None
        async with self._async_session_maker.begin() as session:
            yield session

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def close(self) -> None:
        """Close sync engine and pool."""
        if self._sync_engine is not None:
            self._sync_engine.dispose()
            self._sync_engine = None
            self._sync_session_maker = None

    async def aclose(self) -> None:
        """Close async engine and pool."""
        if self._async_engine is not None:
            await self._async_engine.dispose()
            self._async_engine = None
            self._async_session_maker = None

    async def close_all(self) -> None:
        """Close both sync and async resources."""
        self.close()
        await self.aclose()
