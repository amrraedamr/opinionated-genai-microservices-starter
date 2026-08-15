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

from base.models.definitions.database import SQLBackend
from base.models.orm import _import_all_tables
from base.services.common.meta import KeyedSingleton
from base.services.configuration.local_config import LocalConfig


class SQLClient(metaclass=KeyedSingleton):
    def __init__(self, backend: SQLBackend) -> None:
        self._backend: SQLBackend = backend

        self._sync_engine: Engine | None = None
        self._async_engine: AsyncEngine | None = None
        self._sync_session_maker: sessionmaker[Session] | None = None
        self._async_session_maker: async_sessionmaker[AsyncSession] | None = None

    def _get_database_url(self, driver: str) -> str:
        match self._backend:
            case SQLBackend.SQLITE:
                db_path: str = LocalConfig.get("sqlite_db_path") or "database/local.db"
                return f"sqlite+{driver}:///{db_path}"
            case SQLBackend.MYSQL:
                username: str = quote_plus(LocalConfig.get("mysql_username") or "")
                password: str = quote_plus(LocalConfig.get("mysql_password") or "")
                host: str = LocalConfig.get("mysql_host") or ""
                database: str = LocalConfig.get("mysql_database") or ""
                return f"mysql+{driver}://{username}:{password}@{host}/{database}"
            case SQLBackend.POSTGRESQL:
                username = quote_plus(LocalConfig.get("pg_username") or "")
                password = quote_plus(LocalConfig.get("pg_password") or "")
                host = LocalConfig.get("pg_host") or ""
                port: str = LocalConfig.get("pg_port") or "5432"
                database = LocalConfig.get("pg_database") or ""
                return f"postgresql+{driver}://{username}:{password}@{host}:{port}/{database}"
            case _:
                raise ValueError(f"Unsupported SQL backend: {self._backend!r}")

    def _get_pool_kwargs(self) -> dict[str, Any]:
        match self._backend:
            case SQLBackend.SQLITE:
                return {"echo": False, "echo_pool": False}
            case SQLBackend.MYSQL | SQLBackend.POSTGRESQL:
                return {
                    "pool_size": LocalConfig.get_int("db_pool_size", 10),
                    "max_overflow": LocalConfig.get_int("db_max_overflow", 20),
                    "pool_timeout": LocalConfig.get_int("db_pool_timeout", 30),
                    "pool_recycle": LocalConfig.get_int("db_pool_recycle", 3600),
                    "pool_pre_ping": True,
                    "pool_use_lifo": True,
                    "echo": False,
                    "echo_pool": False,
                }
            case _:
                raise ValueError(f"Unsupported SQL backend: {self._backend!r}")

    def _get_sync_connect_args(self) -> dict[str, Any]:
        match self._backend:
            case SQLBackend.SQLITE:
                return {"check_same_thread": False}
            case SQLBackend.MYSQL:
                args: dict[str, Any] = {
                    "connect_timeout": 10,
                    "read_timeout": 300,
                    "write_timeout": 300,
                }
                if LocalConfig.get_bool("db_ssl_enabled", True):
                    args["ssl"] = ssl.create_default_context()
                return args
            case SQLBackend.POSTGRESQL:
                args = {
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=300000",
                }
                if LocalConfig.get_bool("db_ssl_enabled", True):
                    args["sslmode"] = "require"
                    args["sslrootcert"] = LocalConfig.get("pg_ssl_root_cert") or ""
                return args
            case _:
                raise ValueError(f"Unsupported SQL backend: {self._backend!r}")

    def _get_async_connect_args(self) -> dict[str, Any]:
        match self._backend:
            case SQLBackend.SQLITE:
                return {"check_same_thread": False}
            case SQLBackend.MYSQL:
                args: dict[str, Any] = {"connect_timeout": 10}
                if LocalConfig.get_bool("db_ssl_enabled", True):
                    args["ssl"] = ssl.create_default_context()
                return args
            case SQLBackend.POSTGRESQL:
                args = {"timeout": 10}
                if LocalConfig.get_bool("db_ssl_enabled", True):
                    args["ssl"] = ssl.create_default_context()
                return args
            case _:
                raise ValueError(f"Unsupported SQL backend: {self._backend!r}")

    def _ensure_sync_initialized(self) -> None:
        if self._sync_engine is not None:
            return

        self._sync_engine = create_engine(
            url=self._get_database_url(self._backend.sync_driver),
            poolclass=QueuePool,
            connect_args=self._get_sync_connect_args(),
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
        self._ensure_sync_initialized()
        assert self._sync_session_maker is not None
        with self._sync_session_maker.begin() as session:
            yield session

    def _ensure_async_initialized(self) -> None:
        if self._async_engine is not None:
            return

        async_pool_class = (
            None if self._backend == SQLBackend.SQLITE else AsyncAdaptedQueuePool
        )
        self._async_engine = create_async_engine(
            url=self._get_database_url(self._backend.async_driver),
            poolclass=async_pool_class,
            connect_args=self._get_async_connect_args(),
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
        self._ensure_async_initialized()
        assert self._async_session_maker is not None
        async with self._async_session_maker.begin() as session:
            yield session

    def close(self) -> None:
        if self._sync_engine is not None:
            self._sync_engine.dispose()
            self._sync_engine = None
            self._sync_session_maker = None

    async def aclose(self) -> None:
        if self._async_engine is not None:
            await self._async_engine.dispose()
            self._async_engine = None
            self._async_session_maker = None

    async def close_all(self) -> None:
        self.close()
        await self.aclose()
