from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from base.clients.nosql.mongodb import MongoDBClient
from base.services.common.meta import SingletonABC
from base.services.configuration.local_config import LocalConfig
from base.services.nosql import AbstractNoSQLService


class MongoDBService(AbstractNoSQLService, metaclass=SingletonABC):
    """MongoDB service with both sync and async support."""

    def __init__(self) -> None:
        super().__init__()
        self._client: MongoDBClient = MongoDBClient()
        self._database_name: str = LocalConfig.get("mongodb_database") or ""

    def _get_database(self) -> Database[dict[str, Any]]:
        return self._client.get_database(self._database_name)

    def _aget_database(self) -> AsyncIOMotorDatabase[dict[str, Any]]:
        return self._client.aget_database(self._database_name)

    def get_service_name(self) -> str:
        return "MongoDB"

    def dispose(self) -> None:
        self._client.close()

    def adispose(self) -> None:
        self._client.aclose()
