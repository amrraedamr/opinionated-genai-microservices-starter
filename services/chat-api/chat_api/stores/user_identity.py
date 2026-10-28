from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from base.models.view_models.database import FilteredPaginationParams, PaginatedResult
from base.services.common.meta import SingletonABC
from base.services.sql.service import SQLService
from base.services.store import AbstractStore
from base.tools.database import SQLResultFormats
from chat_api.models.orm.user_identity import UserIdentityDTO


class UserIdentityStore(AbstractStore[UserIdentityDTO], metaclass=SingletonABC):
    def __init__(self) -> None:
        self._sql_service: SQLService = SQLService()
        self._base_select_query: Select[tuple[UserIdentityDTO]] = select(
            UserIdentityDTO
        )

    def _duplicate_error_types(self) -> tuple[type[BaseException], ...]:
        return (IntegrityError,)

    @staticmethod
    def _sanitize_update_data(data: dict[str, Any]) -> dict[str, Any]:
        protected_fields = {
            "id",
            "provider",
            "subject",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        return {k: v for k, v in data.items() if k not in protected_fields}

    def get_by_provider_subject(
        self, provider: str, subject: str
    ) -> UserIdentityDTO | None:
        query = self._base_select_query.where(
            UserIdentityDTO.provider == provider,
            UserIdentityDTO.subject == subject,
            UserIdentityDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.one_or_none_scalar)

    async def aget_by_provider_subject(
        self, provider: str, subject: str
    ) -> UserIdentityDTO | None:
        query = self._base_select_query.where(
            UserIdentityDTO.provider == provider,
            UserIdentityDTO.subject == subject,
            UserIdentityDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(
            query, SQLResultFormats.one_or_none_scalar
        )

    def _get(self, value: Any, column_name: str = "id") -> UserIdentityDTO | None:
        query = self._base_select_query.where(
            getattr(UserIdentityDTO, column_name) == value,
            UserIdentityDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.one_or_none_scalar)

    async def _aget(
        self, value: Any, column_name: str = "id"
    ) -> UserIdentityDTO | None:
        query = self._base_select_query.where(
            getattr(UserIdentityDTO, column_name) == value,
            UserIdentityDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(
            query, SQLResultFormats.one_or_none_scalar
        )

    def _get_many(
        self, keys: list[Any], column_name: str = "id"
    ) -> list[UserIdentityDTO]:
        query = self._base_select_query.where(
            getattr(UserIdentityDTO, column_name).in_(keys),
            UserIdentityDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def _aget_many(
        self, keys: list[Any], column_name: str = "id"
    ) -> list[UserIdentityDTO]:
        query = self._base_select_query.where(
            getattr(UserIdentityDTO, column_name).in_(keys),
            UserIdentityDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    def _add(self, entity: UserIdentityDTO) -> UserIdentityDTO:
        return self._sql_service.upsert_row(entity)

    async def _aadd(self, entity: UserIdentityDTO) -> UserIdentityDTO:
        return await self._sql_service.aupsert_row(entity)

    def _add_many(self, entities: list[UserIdentityDTO]) -> list[UserIdentityDTO]:
        return self._sql_service.upsert_rows(entities)

    async def _aadd_many(
        self, entities: list[UserIdentityDTO]
    ) -> list[UserIdentityDTO]:
        return await self._sql_service.aupsert_rows(entities)

    def _edit(
        self,
        value: Any,
        entity: UserIdentityDTO,
        column_name: str = "id",
    ) -> UserIdentityDTO | None:
        existing = self._get(value, column_name)
        if existing is None:
            return None
        update_data = self._sanitize_update_data(entity.to_dict())
        existing.update_from_dict(update_data)
        return self._sql_service.upsert_row(existing)

    async def _aedit(
        self,
        value: Any,
        entity: UserIdentityDTO,
        column_name: str = "id",
    ) -> UserIdentityDTO | None:
        existing = await self._aget(value, column_name)
        if existing is None:
            return None
        update_data = self._sanitize_update_data(entity.to_dict())
        existing.update_from_dict(update_data)
        return await self._sql_service.aupsert_row(existing)

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

    def _get_all(self, **kwargs: Any) -> list[UserIdentityDTO]:
        query = self._base_select_query.where(UserIdentityDTO.deleted_at.is_(None))
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def _aget_all(self, **kwargs: Any) -> list[UserIdentityDTO]:
        query = self._base_select_query.where(UserIdentityDTO.deleted_at.is_(None))
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    def _get_all_paged(
        self, filter_page_params: FilteredPaginationParams, **kwargs: Any
    ) -> PaginatedResult[UserIdentityDTO]:
        query = self._base_select_query.where(UserIdentityDTO.deleted_at.is_(None))
        return self._sql_service.paginate(query, filter_page_params)

    async def _aget_all_paged(
        self, filter_page_params: FilteredPaginationParams, **kwargs: Any
    ) -> PaginatedResult[UserIdentityDTO]:
        query = self._base_select_query.where(UserIdentityDTO.deleted_at.is_(None))
        return await self._sql_service.apaginate(query, filter_page_params)
