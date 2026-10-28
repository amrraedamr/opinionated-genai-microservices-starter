from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from base.models.view_models.database import FilteredPaginationParams, PaginatedResult
from base.services.common.meta import SingletonABC
from base.services.sql.service import SQLService
from base.services.store import AbstractStore
from base.tools.database import SQLResultFormats
from identity.models.orm.user import UserDTO


class UserStore(AbstractStore[UserDTO], metaclass=SingletonABC):
    def __init__(self) -> None:
        self._sql_service: SQLService = SQLService()
        self._base_select_query: Select[tuple[UserDTO]] = select(UserDTO)

    def _duplicate_error_types(self) -> tuple[type[BaseException], ...]:
        return (IntegrityError,)

    @staticmethod
    def _sanitize_update_data(data: dict[str, Any]) -> dict[str, Any]:
        protected_fields = {"id", "email", "created_at", "updated_at", "deleted_at"}
        return {k: v for k, v in data.items() if k not in protected_fields}

    # Get single

    def _get(self, value: Any, column_name: str = "id") -> UserDTO | None:
        query = self._base_select_query.where(
            getattr(UserDTO, column_name) == value,
            UserDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.one_or_none_scalar)

    async def _aget(self, value: Any, column_name: str = "id") -> UserDTO | None:
        query = self._base_select_query.where(
            getattr(UserDTO, column_name) == value,
            UserDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(
            query, SQLResultFormats.one_or_none_scalar
        )

    # Get many

    def _get_many(self, keys: list[Any], column_name: str = "id") -> list[UserDTO]:
        query = self._base_select_query.where(
            getattr(UserDTO, column_name).in_(keys),
            UserDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def _aget_many(
        self, keys: list[Any], column_name: str = "id"
    ) -> list[UserDTO]:
        query = self._base_select_query.where(
            getattr(UserDTO, column_name).in_(keys),
            UserDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    # Add single

    def _add(self, entity: UserDTO) -> UserDTO:
        return self._sql_service.upsert_row(entity)

    async def _aadd(self, entity: UserDTO) -> UserDTO:
        return await self._sql_service.aupsert_row(entity)

    # Add many

    def _add_many(self, entities: list[UserDTO]) -> list[UserDTO]:
        return self._sql_service.upsert_rows(entities)

    async def _aadd_many(self, entities: list[UserDTO]) -> list[UserDTO]:
        return await self._sql_service.aupsert_rows(entities)

    # Edit

    def _edit(
        self,
        value: Any,
        entity: UserDTO,
        column_name: str = "id",
    ) -> UserDTO | None:
        existing = self._get(value, column_name)
        if existing is None:
            return None

        update_data = self._sanitize_update_data(entity.to_dict())
        existing.update_from_dict(update_data)
        return self._sql_service.upsert_row(existing)

    async def _aedit(
        self,
        value: Any,
        entity: UserDTO,
        column_name: str = "id",
    ) -> UserDTO | None:
        existing = await self._aget(value, column_name)
        if existing is None:
            return None

        update_data = self._sanitize_update_data(entity.to_dict())
        existing.update_from_dict(update_data)
        return await self._sql_service.aupsert_row(existing)

    # Delete

    def _delete(self, value: Any, column_name: str = "id") -> bool:
        entity = self._get(value, column_name)
        if entity is None:
            return False

        entity.soft_delete()
        self._sql_service.upsert_row(entity)
        return True

    async def _adelete(self, value: Any, column_name: str = "id") -> bool:
        entity = await self._aget(value, column_name)
        if entity is None:
            return False

        entity.soft_delete()
        await self._sql_service.aupsert_row(entity)
        return True

    # Get all

    def _get_all(self, **kwargs: Any) -> list[UserDTO]:
        query = self._base_select_query.where(UserDTO.deleted_at.is_(None))
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def _aget_all(self, **kwargs: Any) -> list[UserDTO]:
        query = self._base_select_query.where(UserDTO.deleted_at.is_(None))
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    # Get all paged

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
