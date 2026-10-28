from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from base.models.view_models.database import FilteredPaginationParams, PaginatedResult
from base.services.common.meta import SingletonABC
from base.services.sql.service import SQLService
from base.services.store import AbstractStore
from base.tools.database import SQLResultFormats
from chat_api.models.orm.chat_history_message import ChatHistoryMessageDTO
from chat_api.models.orm.conversation import ConversationDTO
from chat_api.models.view_models.conversation import (
    CreateConversationRequest,
    EditConversationRequest,
)


class ConversationStore(AbstractStore[ConversationDTO], metaclass=SingletonABC):
    def __init__(self) -> None:
        self._sql_service: SQLService = SQLService()
        self._base_select_query: Select[tuple[ConversationDTO]] = select(
            ConversationDTO
        )

    def _duplicate_error_types(self) -> tuple[type[BaseException], ...]:
        return (IntegrityError,)

    # Helpers

    @staticmethod
    def _sanitize_update_data(data: dict[str, Any]) -> dict[str, Any]:
        protected_fields = {"id", "user_id", "created_at", "updated_at", "deleted_at"}
        return {k: v for k, v in data.items() if k not in protected_fields}

    @staticmethod
    def _apply_edit_request(
        existing: ConversationDTO, request: EditConversationRequest
    ) -> ConversationDTO:
        update_data = request.serialize(
            exclude_unset=True, exclude_none=True, by_alias=False
        )

        if "metadata" in update_data:
            update_data["meta"] = update_data.pop("metadata")

        existing.update_from_dict(ConversationStore._sanitize_update_data(update_data))
        return existing

    @staticmethod
    def _build_conversation_entity(
        user_id: UUID, request: CreateConversationRequest
    ) -> ConversationDTO:
        return ConversationDTO(
            user_id=user_id,
            title=request.title,
            meta=request.metadata,
        )

    # Get single

    def _get(self, value: Any, column_name: str = "id") -> ConversationDTO | None:
        query = self._base_select_query.where(
            getattr(ConversationDTO, column_name) == value,
            ConversationDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.one_or_none_scalar)

    async def _aget(
        self, value: Any, column_name: str = "id"
    ) -> ConversationDTO | None:
        query = self._base_select_query.where(
            getattr(ConversationDTO, column_name) == value,
            ConversationDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(
            query, SQLResultFormats.one_or_none_scalar
        )

    def get_for_user(
        self, user_id: UUID, conversation_id: UUID
    ) -> ConversationDTO | None:
        query = self._base_select_query.where(
            ConversationDTO.user_id == user_id,
            ConversationDTO.id == conversation_id,
            ConversationDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.one_or_none_scalar)

    async def aget_for_user(
        self, user_id: UUID, conversation_id: UUID
    ) -> ConversationDTO | None:
        query = self._base_select_query.where(
            ConversationDTO.user_id == user_id,
            ConversationDTO.id == conversation_id,
            ConversationDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(
            query, SQLResultFormats.one_or_none_scalar
        )

    # Get many

    def _get_many(
        self, keys: list[Any], column_name: str = "id"
    ) -> list[ConversationDTO]:
        query = self._base_select_query.where(
            getattr(ConversationDTO, column_name).in_(keys),
            ConversationDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def _aget_many(
        self, keys: list[Any], column_name: str = "id"
    ) -> list[ConversationDTO]:
        query = self._base_select_query.where(
            getattr(ConversationDTO, column_name).in_(keys),
            ConversationDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    def get_many_for_user(
        self, user_id: UUID, conversation_ids: list[UUID]
    ) -> list[ConversationDTO]:
        query = self._base_select_query.where(
            ConversationDTO.user_id == user_id,
            ConversationDTO.id.in_(conversation_ids),
            ConversationDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def aget_many_for_user(
        self, user_id: UUID, conversation_ids: list[UUID]
    ) -> list[ConversationDTO]:
        query = self._base_select_query.where(
            ConversationDTO.user_id == user_id,
            ConversationDTO.id.in_(conversation_ids),
            ConversationDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    # Add single

    def _add(self, entity: ConversationDTO) -> ConversationDTO:
        return self._sql_service.upsert_row(entity)

    async def _aadd(self, entity: ConversationDTO) -> ConversationDTO:
        return await self._sql_service.aupsert_row(entity)

    def add_for_user(self, user_id: UUID, entity: ConversationDTO) -> ConversationDTO:
        entity.user_id = user_id
        return self._sql_service.upsert_row(entity)

    async def aadd_for_user(
        self, user_id: UUID, entity: ConversationDTO
    ) -> ConversationDTO:
        entity.user_id = user_id
        return await self._sql_service.aupsert_row(entity)

    def create_for_user(
        self, user_id: UUID, request: CreateConversationRequest
    ) -> ConversationDTO:
        entity = self._build_conversation_entity(user_id, request)
        return self._sql_service.upsert_row(entity)

    async def acreate_for_user(
        self, user_id: UUID, request: CreateConversationRequest
    ) -> ConversationDTO:
        entity = self._build_conversation_entity(user_id, request)
        return await self._sql_service.aupsert_row(entity)

    # Add many

    def _add_many(self, entities: list[ConversationDTO]) -> list[ConversationDTO]:
        return self._sql_service.upsert_rows(entities)

    async def _aadd_many(
        self, entities: list[ConversationDTO]
    ) -> list[ConversationDTO]:
        return await self._sql_service.aupsert_rows(entities)

    def add_many_for_user(
        self, user_id: UUID, entities: list[ConversationDTO]
    ) -> list[ConversationDTO]:
        for entity in entities:
            entity.user_id = user_id
        return self._sql_service.upsert_rows(entities)

    async def aadd_many_for_user(
        self, user_id: UUID, entities: list[ConversationDTO]
    ) -> list[ConversationDTO]:
        for entity in entities:
            entity.user_id = user_id
        return await self._sql_service.aupsert_rows(entities)

    # Edit

    def _edit(
        self,
        value: Any,
        entity: ConversationDTO,
        column_name: str = "id",
    ) -> ConversationDTO | None:
        existing = self._get(value, column_name)
        if existing is None:
            return None

        existing.update_from_dict(
            entity.to_dict(
                exclude={"id", "user_id", "created_at", "updated_at", "deleted_at"}
            )
        )
        return self._sql_service.upsert_row(existing)

    async def _aedit(
        self,
        value: Any,
        entity: ConversationDTO,
        column_name: str = "id",
    ) -> ConversationDTO | None:
        existing = await self._aget(value, column_name)
        if existing is None:
            return None

        existing.update_from_dict(
            entity.to_dict(
                exclude={"id", "user_id", "created_at", "updated_at", "deleted_at"}
            )
        )
        return await self._sql_service.aupsert_row(existing)

    def edit_for_user(
        self,
        user_id: UUID,
        value: Any,
        request: EditConversationRequest,
    ) -> ConversationDTO | None:
        existing = self.get_for_user(user_id, value)
        if existing is None:
            return None

        updated = self._apply_edit_request(existing, request)
        return self._sql_service.upsert_row(updated)

    async def aedit_for_user(
        self,
        user_id: UUID,
        value: Any,
        request: EditConversationRequest,
    ) -> ConversationDTO | None:
        existing = await self.aget_for_user(user_id, value)
        if existing is None:
            return None

        updated = self._apply_edit_request(existing, request)
        return await self._sql_service.aupsert_row(updated)

    # Delete

    def _delete(self, value: Any, column_name: str = "id") -> bool:
        entity = self._get(value, column_name)
        if entity is None:
            return False

        entity.soft_delete()

        message_query = select(ChatHistoryMessageDTO).where(
            ChatHistoryMessageDTO.conversation_id == entity.id,
            ChatHistoryMessageDTO.deleted_at.is_(None),
        )
        messages = self._sql_service.query(
            message_query, SQLResultFormats.all_scalar_list
        )
        for message in messages:
            message.soft_delete()

        self._sql_service.upsert_rows([entity, *messages])
        return True

    async def _adelete(self, value: Any, column_name: str = "id") -> bool:
        entity = await self._aget(value, column_name)
        if entity is None:
            return False

        entity.soft_delete()

        message_query = select(ChatHistoryMessageDTO).where(
            ChatHistoryMessageDTO.conversation_id == entity.id,
            ChatHistoryMessageDTO.deleted_at.is_(None),
        )
        messages = await self._sql_service.aquery(
            message_query, SQLResultFormats.all_scalar_list
        )
        for message in messages:
            message.soft_delete()

        await self._sql_service.aupsert_rows([entity, *messages])
        return True

    def delete_for_user(self, user_id: UUID, value: Any) -> bool:
        entity = self.get_for_user(user_id, value)
        if entity is None:
            return False

        entity.soft_delete()

        message_query = select(ChatHistoryMessageDTO).where(
            ChatHistoryMessageDTO.conversation_id == entity.id,
            ChatHistoryMessageDTO.deleted_at.is_(None),
        )
        messages = self._sql_service.query(
            message_query, SQLResultFormats.all_scalar_list
        )
        for message in messages:
            message.soft_delete()

        self._sql_service.upsert_rows([entity, *messages])
        return True

    async def adelete_for_user(self, user_id: UUID, value: Any) -> bool:
        entity = await self.aget_for_user(user_id, value)
        if entity is None:
            return False

        entity.soft_delete()

        message_query = select(ChatHistoryMessageDTO).where(
            ChatHistoryMessageDTO.conversation_id == entity.id,
            ChatHistoryMessageDTO.deleted_at.is_(None),
        )
        messages = await self._sql_service.aquery(
            message_query, SQLResultFormats.all_scalar_list
        )
        for message in messages:
            message.soft_delete()

        await self._sql_service.aupsert_rows([entity, *messages])
        return True

    # Get all

    def _get_all(self, **kwargs: Any) -> list[ConversationDTO]:
        query = self._base_select_query.where(ConversationDTO.deleted_at.is_(None))
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def _aget_all(self, **kwargs: Any) -> list[ConversationDTO]:
        query = self._base_select_query.where(ConversationDTO.deleted_at.is_(None))
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    def get_all_for_user(self, user_id: UUID) -> list[ConversationDTO]:
        query = self._base_select_query.where(
            ConversationDTO.user_id == user_id,
            ConversationDTO.deleted_at.is_(None),
        )
        return self._sql_service.query(query, SQLResultFormats.all_scalar_list)

    async def aget_all_for_user(self, user_id: UUID) -> list[ConversationDTO]:
        query = self._base_select_query.where(
            ConversationDTO.user_id == user_id,
            ConversationDTO.deleted_at.is_(None),
        )
        return await self._sql_service.aquery(query, SQLResultFormats.all_scalar_list)

    # Get all paged

    def _get_all_paged(
        self,
        filter_page_params: FilteredPaginationParams,
        **kwargs: Any,
    ) -> PaginatedResult[ConversationDTO]:
        query = (
            self._base_select_query.where(ConversationDTO.deleted_at.is_(None))
            .where(ConversationDTO.created_at >= filter_page_params.from_date)
            .where(ConversationDTO.created_at <= filter_page_params.to_date)
        )
        if filter_page_params.search:
            query = query.where(
                ConversationDTO.title.ilike(f"%{filter_page_params.search}%")
            )
        return self._sql_service.paginate(query, filter_page_params)

    async def _aget_all_paged(
        self,
        filter_page_params: FilteredPaginationParams,
        **kwargs: Any,
    ) -> PaginatedResult[ConversationDTO]:
        query = (
            self._base_select_query.where(ConversationDTO.deleted_at.is_(None))
            .where(ConversationDTO.created_at >= filter_page_params.from_date)
            .where(ConversationDTO.created_at <= filter_page_params.to_date)
        )
        if filter_page_params.search:
            query = query.where(
                ConversationDTO.title.ilike(f"%{filter_page_params.search}%")
            )
        return await self._sql_service.apaginate(query, filter_page_params)

    # Get all paged for user

    def get_all_paged_for_user(
        self,
        user_id: UUID,
        filter_page_params: FilteredPaginationParams,
    ) -> PaginatedResult[ConversationDTO]:
        query = (
            self._base_select_query.where(ConversationDTO.user_id == user_id)
            .where(ConversationDTO.deleted_at.is_(None))
            .where(ConversationDTO.created_at >= filter_page_params.from_date)
            .where(ConversationDTO.created_at <= filter_page_params.to_date)
        )
        if filter_page_params.search:
            query = query.where(
                ConversationDTO.title.ilike(f"%{filter_page_params.search}%")
            )
        return self._sql_service.paginate(query, filter_page_params)

    async def aget_all_paged_for_user(
        self,
        user_id: UUID,
        filter_page_params: FilteredPaginationParams,
    ) -> PaginatedResult[ConversationDTO]:
        query = (
            self._base_select_query.where(ConversationDTO.user_id == user_id)
            .where(ConversationDTO.deleted_at.is_(None))
            .where(ConversationDTO.created_at >= filter_page_params.from_date)
            .where(ConversationDTO.created_at <= filter_page_params.to_date)
        )
        if filter_page_params.search:
            query = query.where(
                ConversationDTO.title.ilike(f"%{filter_page_params.search}%")
            )
        return await self._sql_service.apaginate(query, filter_page_params)
