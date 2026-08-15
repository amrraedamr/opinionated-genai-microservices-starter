from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from base.clients.sql.client import SQLClient
from base.models.definitions.database import SQLBackend
from base.services.common.meta import SingletonABC
from base.services.configuration.local_config import LocalConfig
from base.services.sql import AbstractSQLService


class SQLService(AbstractSQLService, metaclass=SingletonABC):
    def __init__(self) -> None:
        self._backend: SQLBackend = SQLBackend(
            LocalConfig.get("sql_backend") or "sqlite"
        )
        self._client: SQLClient = SQLClient(self._backend)

    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        with self._client.session() as session:
            yield session

    @asynccontextmanager
    async def _aget_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._client.asession() as session:
            yield session

    def get_service_name(self) -> str:
        return self._backend.value.capitalize()

    def dispose(self) -> None:
        self._client.close()

    async def adispose(self) -> None:
        await self._client.aclose()
