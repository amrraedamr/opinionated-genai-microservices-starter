from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from base.models.orm.user import UserDTO
from base.models.view_models.database import FilteredPaginationParams, PaginatedResult
from base.services.common.meta import SingletonABC
from base.services.sql.sqlite import SQLiteService
from base.services.store import AbstractStore
from base.tools.database import SQLResultFormats


class UserStore(AbstractStore[UserDTO], metaclass=SingletonABC):
    def __init__(self) -> None:
        super().__init__()
        self._sql_service: SQLiteService = SQLiteService()
        self._base_select_query: Select[tuple[UserDTO]] = select(UserDTO)

    def _is_duplicate_error(self, error: Exception) -> bool:
        return isinstance(error, IntegrityError)

    # -------------------------
    # Get single
    # -------------------------

    def _get(self, value: Any, column_name: str = "id") -> UserDTO | None:
        query = self._base_select_query.where(
            getattr(UserDTO, column_name) == value, UserDTO.deleted_at.is_(None)
        )
        return self._sql_service.query(query, SQLResultFormats.one_or_none_scalar)

    async def _aget(self, value: Any, column_name: str = "id") -> UserDTO | None:
        query = self._base_select_query.where(
            getattr(UserDTO, column_name) == value, UserDTO.deleted_at.is_(None)
        )
        return await self._sql_service.aquery(
            query, SQLResultFormats.one_or_none_scalar
        )

    # -------------------------
    # Get many
    # -------------------------

    def _get_many(self, keys: list[Any], column_name: str = "id") -> list[UserDTO]:
        query = self._base_select_query.where(
            getattr(UserDTO, column_name).in_(keys), UserDTO.deleted_at.is_(None)
        )
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def _aget_many(
        self, keys: list[Any], column_name: str = "id"
    ) -> list[UserDTO]:
        query = self._base_select_query.where(
            getattr(UserDTO, column_name).in_(keys), UserDTO.deleted_at.is_(None)
        )
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    # -------------------------
    # Add single
    # -------------------------

    def _add(self, entity: UserDTO) -> UserDTO:
        return self._sql_service.upsert_row(entity)

    async def _aadd(self, entity: UserDTO) -> UserDTO:
        return await self._sql_service.aupsert_row(entity)

    # -------------------------
    # Add many
    # -------------------------

    def _add_many(self, entities: list[UserDTO]) -> list[UserDTO]:
        return self._sql_service.upsert_rows(entities)

    async def _aadd_many(self, entities: list[UserDTO]) -> list[UserDTO]:
        return await self._sql_service.aupsert_rows(entities)

    # -------------------------
    # Edit
    # -------------------------

    def _edit(self, value: Any, entity: UserDTO, column_name: str = "id") -> UserDTO:
        existing = self.get(value, column_name)
        existing.update_from_dict(
            entity.to_dict(exclude={"id", "created_at", "updated_at", "deleted_at"})
        )
        return self._sql_service.upsert_row(existing)

    async def _aedit(
        self, value: Any, entity: UserDTO, column_name: str = "id"
    ) -> UserDTO:
        existing = await self.aget(value, column_name)
        existing.update_from_dict(
            entity.to_dict(exclude={"id", "created_at", "updated_at", "deleted_at"})
        )
        return await self._sql_service.aupsert_row(existing)

    # -------------------------
    # Delete
    # -------------------------

    def _delete(self, value: Any, column_name: str = "id") -> None:
        entity = self.get(value, column_name)
        entity.soft_delete()
        self._sql_service.upsert_row(entity)

    async def _adelete(self, value: Any, column_name: str = "id") -> None:
        entity = await self.aget(value, column_name)
        entity.soft_delete()
        await self._sql_service.aupsert_row(entity)

    # -------------------------
    # Get all
    # -------------------------

    def _get_all(self, **kwargs: Any) -> list[UserDTO]:
        query = self._base_select_query.where(UserDTO.deleted_at.is_(None))
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def _aget_all(self, **kwargs: Any) -> list[UserDTO]:
        query = self._base_select_query.where(UserDTO.deleted_at.is_(None))
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    # -------------------------
    # Get all paged
    # -------------------------

    def _get_all_paged(
        self, filter_page_params: FilteredPaginationParams, **kwargs: Any
    ) -> PaginatedResult[UserDTO]:
        query = (
            self._base_select_query.where(UserDTO.deleted_at.is_(None))
            .where(UserDTO.created_at >= filter_page_params.from_date)
            .where(UserDTO.created_at <= filter_page_params.to_date)
        )
        if filter_page_params.search:
            query = query.where(UserDTO.email.ilike(f"%{filter_page_params.search}%"))
        return self._sql_service.paginate(query, filter_page_params)

    async def _aget_all_paged(
        self, filter_page_params: FilteredPaginationParams, **kwargs: Any
    ) -> PaginatedResult[UserDTO]:
        query = (
            self._base_select_query.where(UserDTO.deleted_at.is_(None))
            .where(UserDTO.created_at >= filter_page_params.from_date)
            .where(UserDTO.created_at <= filter_page_params.to_date)
        )
        if filter_page_params.search:
            query = query.where(UserDTO.email.ilike(f"%{filter_page_params.search}%"))
        return await self._sql_service.apaginate(query, filter_page_params)
