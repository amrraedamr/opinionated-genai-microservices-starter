from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from base.clients.sql.sqlite import SQLiteClient
from base.services.common.meta import SingletonABC
from base.services.sql import AbstractSQLService


class SQLiteService(AbstractSQLService, metaclass=SingletonABC):
    """SQLite service with both sync and async support."""

    def __init__(self) -> None:
        super().__init__()
        self._client: SQLiteClient = SQLiteClient()

    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        with self._client.session() as session:
            yield session

    @asynccontextmanager
    async def _aget_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._client.asession() as session:
            yield session

    def get_service_name(self) -> str:
        return "SQLite"

    def dispose(self) -> None:
        self._client.close()

    async def adispose(self) -> None:
        await self._client.aclose()
