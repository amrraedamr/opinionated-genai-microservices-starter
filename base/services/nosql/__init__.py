import math
from abc import ABC, abstractmethod
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database
from pymongo.results import (
    DeleteResult,
    InsertManyResult,
    InsertOneResult,
    UpdateResult,
)

from base.models.view_models.database import PaginatedResult, PaginationParams
from base.services import AbstractService


class AbstractNoSQLService(AbstractService, ABC):
    """
    Abstract base class for NoSQL (document-oriented) services with both
    sync and async support.

    Subclasses only need to implement database access and metadata.
    All CRUD, aggregation, pagination, and health check logic is handled here.
    """

    def __init__(self) -> None:
        super().__init__()

    # -------------------------------------------------------------------------
    # Abstract — subclasses must implement
    # -------------------------------------------------------------------------

    @abstractmethod
    def _get_database(self) -> Database[dict[str, Any]]: ...

    @abstractmethod
    def _aget_database(self) -> AsyncIOMotorDatabase[dict[str, Any]]: ...

    @abstractmethod
    def get_service_name(self) -> str: ...

    @abstractmethod
    def dispose(self) -> None: ...

    @abstractmethod
    def adispose(self) -> None: ...

    # -------------------------------------------------------------------------
    # Find
    # -------------------------------------------------------------------------

    def find_one(
        self,
        collection: str,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Find a single document matching the filter."""
        return self._get_database()[collection].find_one(filter, projection=projection)

    async def afind_one(
        self,
        collection: str,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Find a single document matching the filter asynchronously."""
        return await self._aget_database()[collection].find_one(
            filter, projection=projection
        )

    def find_many(
        self,
        collection: str,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Find multiple documents matching the filter."""
        cursor = self._get_database()[collection].find(filter, projection=projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    async def afind_many(
        self,
        collection: str,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Find multiple documents matching the filter asynchronously."""
        cursor = self._aget_database()[collection].find(filter, projection=projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=None)

    # -------------------------------------------------------------------------
    # Insert
    # -------------------------------------------------------------------------

    def insert_one(
        self,
        collection: str,
        document: dict[str, Any],
    ) -> InsertOneResult:
        """Insert a single document."""
        return self._get_database()[collection].insert_one(document)

    async def ainsert_one(
        self,
        collection: str,
        document: dict[str, Any],
    ) -> InsertOneResult:
        """Insert a single document asynchronously."""
        return await self._aget_database()[collection].insert_one(document)

    def insert_many(
        self,
        collection: str,
        documents: list[dict[str, Any]],
        ordered: bool = True,
    ) -> InsertManyResult:
        """Insert multiple documents."""
        return self._get_database()[collection].insert_many(documents, ordered=ordered)

    async def ainsert_many(
        self,
        collection: str,
        documents: list[dict[str, Any]],
        ordered: bool = True,
    ) -> InsertManyResult:
        """Insert multiple documents asynchronously."""
        return await self._aget_database()[collection].insert_many(
            documents, ordered=ordered
        )

    # -------------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------------

    def update_one(
        self,
        collection: str,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Update a single document matching the filter."""
        return self._get_database()[collection].update_one(
            filter, update, upsert=upsert
        )

    async def aupdate_one(
        self,
        collection: str,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Update a single document matching the filter asynchronously."""
        return await self._aget_database()[collection].update_one(
            filter, update, upsert=upsert
        )

    def update_many(
        self,
        collection: str,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Update multiple documents matching the filter."""
        return self._get_database()[collection].update_many(
            filter, update, upsert=upsert
        )

    async def aupdate_many(
        self,
        collection: str,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Update multiple documents matching the filter asynchronously."""
        return await self._aget_database()[collection].update_many(
            filter, update, upsert=upsert
        )

    # -------------------------------------------------------------------------
    # Replace
    # -------------------------------------------------------------------------

    def replace_one(
        self,
        collection: str,
        filter: dict[str, Any],
        replacement: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Replace a single document matching the filter."""
        return self._get_database()[collection].replace_one(
            filter, replacement, upsert=upsert
        )

    async def areplace_one(
        self,
        collection: str,
        filter: dict[str, Any],
        replacement: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        """Replace a single document matching the filter asynchronously."""
        return await self._aget_database()[collection].replace_one(
            filter, replacement, upsert=upsert
        )

    # -------------------------------------------------------------------------
    # Delete
    # -------------------------------------------------------------------------

    def delete_one(
        self,
        collection: str,
        filter: dict[str, Any],
    ) -> DeleteResult:
        """Delete a single document matching the filter."""
        return self._get_database()[collection].delete_one(filter)

    async def adelete_one(
        self,
        collection: str,
        filter: dict[str, Any],
    ) -> DeleteResult:
        """Delete a single document matching the filter asynchronously."""
        return await self._aget_database()[collection].delete_one(filter)

    def delete_many(
        self,
        collection: str,
        filter: dict[str, Any],
    ) -> DeleteResult:
        """Delete multiple documents matching the filter."""
        return self._get_database()[collection].delete_many(filter)

    async def adelete_many(
        self,
        collection: str,
        filter: dict[str, Any],
    ) -> DeleteResult:
        """Delete multiple documents matching the filter asynchronously."""
        return await self._aget_database()[collection].delete_many(filter)

    # -------------------------------------------------------------------------
    # Count & Distinct
    # -------------------------------------------------------------------------

    def count(
        self,
        collection: str,
        filter: dict[str, Any] | None = None,
    ) -> int:
        """Count documents matching the filter."""
        return self._get_database()[collection].count_documents(filter or {})

    async def acount(
        self,
        collection: str,
        filter: dict[str, Any] | None = None,
    ) -> int:
        """Count documents matching the filter asynchronously."""
        return await self._aget_database()[collection].count_documents(filter or {})

    def distinct(
        self,
        collection: str,
        key: str,
        filter: dict[str, Any] | None = None,
    ) -> list[Any]:
        """Get distinct values for a key across documents."""
        return self._get_database()[collection].distinct(key, filter=filter or {})

    async def adistinct(
        self,
        collection: str,
        key: str,
        filter: dict[str, Any] | None = None,
    ) -> list[Any]:
        """Get distinct values for a key across documents asynchronously."""
        return await self._aget_database()[collection].distinct(
            key, filter=filter or {}
        )

    # -------------------------------------------------------------------------
    # Aggregation
    # -------------------------------------------------------------------------

    def aggregate(
        self,
        collection: str,
        pipeline: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Run an aggregation pipeline."""
        return list(self._get_database()[collection].aggregate(pipeline))

    async def aaggregate(
        self,
        collection: str,
        pipeline: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Run an aggregation pipeline asynchronously."""
        cursor = self._aget_database()[collection].aggregate(pipeline)
        return await cursor.to_list(length=None)

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def paginate(
        self,
        collection: str,
        filter: dict[str, Any],
        page_params: PaginationParams,
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """Find documents with pagination."""
        total: int = self.count(collection, filter)
        total_pages: int = (
            math.ceil(total / page_params.size) if page_params.size > 0 else 0
        )

        if total == 0 or page_params.page > total_pages:
            return PaginatedResult(
                data=[],
                page=page_params.page,
                size=page_params.size,
                total=total,
                total_pages=total_pages,
            )

        offset: int = (page_params.page - 1) * page_params.size
        data: list[dict[str, Any]] = self.find_many(
            collection,
            filter,
            projection=projection,
            sort=sort,
            skip=offset,
            limit=page_params.size,
        )

        return PaginatedResult(
            data=data,
            page=page_params.page,
            size=page_params.size,
            total=total,
            total_pages=total_pages,
        )

    async def apaginate(
        self,
        collection: str,
        filter: dict[str, Any],
        page_params: PaginationParams,
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
    ) -> PaginatedResult[dict[str, Any]]:
        """Find documents with pagination asynchronously."""
        total: int = await self.acount(collection, filter)
        total_pages: int = (
            math.ceil(total / page_params.size) if page_params.size > 0 else 0
        )

        if total == 0 or page_params.page > total_pages:
            return PaginatedResult(
                data=[],
                page=page_params.page,
                size=page_params.size,
                total=total,
                total_pages=total_pages,
            )

        offset: int = (page_params.page - 1) * page_params.size
        data: list[dict[str, Any]] = await self.afind_many(
            collection,
            filter,
            projection=projection,
            sort=sort,
            skip=offset,
            limit=page_params.size,
        )

        return PaginatedResult(
            data=data,
            page=page_params.page,
            size=page_params.size,
            total=total,
            total_pages=total_pages,
        )

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify database accessibility with a ping command."""
        try:
            self._get_database().command("ping")
            return True
        except Exception as e:
            raise Exception(
                f"{self.get_service_name()} health check failed: {e}"
            ) from e

    async def ahealth_check(self) -> bool:
        """Verify database accessibility with a ping command asynchronously."""
        try:
            await self._aget_database().command("ping")
            return True
        except Exception as e:
            raise Exception(
                f"{self.get_service_name()} health check failed: {e}"
            ) from e
