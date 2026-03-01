from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import QueuePool, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from base.models.orm import Base, _import_all_tables
from base.services.common.meta import Singleton
from base.services.configuration.local_config import LocalConfig


class SQLiteClient(metaclass=Singleton):
    """
    SQLite client with connection support for both sync and async operations.
    Designed to be instantiated once and reused across the application.
    """

    def __init__(self) -> None:
        self._db_path: str = LocalConfig.get("sqlite_db_path") or "database/local.db"

        self._sync_engine: Engine | None = None
        self._async_engine: AsyncEngine | None = None
        self._sync_session_maker: sessionmaker[Session] | None = None
        self._async_session_maker: async_sessionmaker[AsyncSession] | None = None
        self._async_initialized: bool = False

    # -------------------------------------------------------------------------
    # Sync
    # -------------------------------------------------------------------------

    def _ensure_sync_initialized(self) -> None:
        if self._sync_engine is not None:
            return

        self._sync_engine = create_engine(
            url=f"sqlite:///{self._db_path}",
            poolclass=QueuePool,
            connect_args={"check_same_thread": False},
            echo=False,
            echo_pool=False,
        )
        self._sync_session_maker = sessionmaker(
            bind=self._sync_engine,
            autoflush=False,
            expire_on_commit=False,
        )
        _import_all_tables()
        Base.metadata.create_all(self._sync_engine)

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

    async def _ensure_async_initialized(self) -> None:
        if self._async_initialized:
            return

        self._async_engine = create_async_engine(
            url=f"sqlite+aiosqlite:///{self._db_path}",
            connect_args={"check_same_thread": False},
            echo=False,
            echo_pool=False,
        )
        self._async_session_maker = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )
        _import_all_tables()
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._async_initialized = True

    @asynccontextmanager
    async def asession(self) -> AsyncGenerator[AsyncSession, None]:
        """Async session backed by the connection pool."""
        await self._ensure_async_initialized()
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
            self._async_initialized = False

    async def close_all(self) -> None:
        """Close both sync and async resources."""
        self.close()
        await self.aclose()
