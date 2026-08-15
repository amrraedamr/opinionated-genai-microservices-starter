from typing import Any

from base.clients.nosql.mongodb import MongoDBClient
from base.models.view_models.vector_search import VectorRecord
from base.services.configuration.local_config import LocalConfig
from base.services.vector_search import AbstractVectorSearchService


class MongoDBVectorSearchService(AbstractVectorSearchService):
    def __init__(self):
        self._client = MongoDBClient()
        self._database_name = LocalConfig.get("mongodb_database")
        self._async_database = self._client.aget_database(self._database_name)
        self._database = self._client.get_database(self._database_name)

    def create_collection(
        self, collection: str, vector_size: int, distance: str = "cosine", **kwargs: Any
    ):
        self._database.create_collection(collection, vector_size, distance, **kwargs)

    async def acreate_collection(
        self, collection: str, vector_size: int, distance: str = "cosine", **kwargs: Any
    ):
        await self._async_database.create_collection(
            collection, vector_size, distance, **kwargs
        )

    def delete_collection(self, collection: str):
        self._database.drop_collection(collection)

    async def adelete_collection(self, collection: str):
        await self._async_database.drop_collection(collection)

    def upsert(self, collection: str, records: list[VectorRecord]) -> None:
        self._database.get_collection(collection).insert_many(records)

    async def aupsert(self, collection: str, records: list[VectorRecord]) -> None:
        await self._async_database.get_collection(collection).insert_many(records)

    def collection_exists(self, collection: str) -> bool:
        return self._database.get_collection(collection).count_documents({}) > 0

    async def acollection_exists(self, collection: str) -> bool:
        return (
            await self._async_database.get_collection(collection).count_documents({})
            > 0
        )

    def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[VectorRecord]:
        return (
            self._database.get_collection(collection)
            .aggregate(
                [
                    {
                        "$vectorSearch": {
                            "index": collection,
                            "path": "embedding",
                            "queryVector": vector,
                            "numCandidates": limit * 20,  # or a fixed value like 100
                            "limit": limit,
                        }
                    }
                ]
            )
            .to_list(length=limit)
        )

    async def asearch(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        pipeline: list[dict[str, Any]] = [
            {
                "$vectorSearch": {
                    "index": f"{collection}_vector_index",
                    "path": "embedding",
                    "queryVector": vector,
                    "numCandidates": max(limit * 20, 100),
                    "limit": limit,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        if filters:
            pipeline[0]["$vectorSearch"]["filter"] = filters
        cursor = await self._async_database.get_collection(collection).aggregate(
            pipeline
        )
        return [dict(record) async for record in cursor]

    def get(
        self, collection: str, ids: list[str], with_vectors: bool = False
    ) -> list[VectorRecord]:
        return self._database.get_collection(collection).find({"_id": {"$in": ids}})

    async def aget(
        self, collection: str, ids: list[str], with_vectors: bool = False
    ) -> list[VectorRecord]:
        return await self._async_database.get_collection(collection).find(
            {"_id": {"$in": ids}}
        )

    def delete(self, collection: str, ids: list[str]) -> None:
        self._database.get_collection(collection).delete_many({"_id": {"$in": ids}})

    async def adelete(self, collection: str, ids: list[str]) -> None:
        await self._async_database.get_collection(collection).delete_many(
            {"_id": {"$in": ids}}
        )

    def count(self, collection: str) -> int:
        return self._database.get_collection(collection).count_documents({})

    async def acount(self, collection: str) -> int:
        return await self._async_database.get_collection(collection).count_documents({})

    def scroll(
        self,
        collection: str,
        limit: int = 100,
        offset: str | None = None,
        filters: dict[str, Any] | None = None,
        with_vectors: bool = False,
    ) -> tuple[list[VectorRecord], str | None]:
        return (
            self._database.get_collection(collection)
            .find(filters)
            .skip(offset)
            .limit(limit)
        )

    async def ascroll(
        self,
        collection: str,
        limit: int = 100,
        offset: str | None = None,
        filters: dict[str, Any] | None = None,
        with_vectors: bool = False,
    ) -> tuple[list[VectorRecord], str | None]:
        return (
            await self._async_database.get_collection(collection)
            .find(filters)
            .skip(offset)
            .limit(limit)
        )

    def health_check(self) -> bool:
        return self._client.admin.command("ping") == 0

    async def ahealth_check(self) -> bool:
        return await self._async_client.admin.command("ping") == 0

    def get_service_name(self) -> str:
        return "MongoDBVectorSearchService"

    def dispose(self) -> None:
        self._client.close()

    async def adispose(self) -> None:
        await self._async_client.close()
