from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, final

from base.models.definitions.errors import DatabaseErrors
from base.models.view_models.database import FilteredPaginationParams, PaginatedResult
from base.services import AbstractService
from base.tools.errors import raise_error

T = TypeVar("T")


class AbstractStore(AbstractService, ABC, Generic[T]):
    """Database-agnostic abstract store. Works with SQL and NoSQL services.

    Subclasses are responsible for:
    - Setting up their own database service (SQL or NoSQL) in __init__
    - Implementing all abstract CRUD methods
    - Overriding _is_duplicate_error() to map their DB's duplicate-key
      exception (e.g. SQLAlchemy IntegrityError, PyMongo DuplicateKeyError)
    """

    def __init__(self) -> None:
        super().__init__()

    # -------------------------
    # Duplicate error hook
    # -------------------------

    def _is_duplicate_error(self, error: Exception) -> bool:
        """Return True if the exception represents a duplicate-key / unique
        constraint violation. Subclasses should override for their DB driver."""
        return False

    # -------------------------
    # Get single
    # -------------------------

    @abstractmethod
    def _get(self, value: Any, column_name: str = "id") -> T | None:
        """Retrieve a single entity by column value."""

    @abstractmethod
    async def _aget(self, value: Any, column_name: str = "id") -> T | None:
        """Asynchronously retrieve a single entity by column value."""

    @final
    def get(self, value: Any, column_name: str = "id") -> T:
        result = self._get(value, column_name)
        return result if result else raise_error(DatabaseErrors.RECORD_NOT_FOUND)

    @final
    async def aget(self, value: Any, column_name: str = "id") -> T:
        result = await self._aget(value, column_name)
        return result if result else raise_error(DatabaseErrors.RECORD_NOT_FOUND)

    # -------------------------
    # Get many
    # -------------------------

    @abstractmethod
    def _get_many(self, keys: list[Any], column_name: str = "id") -> list[T]:
        """Retrieve many entities by a list of column values."""

    @abstractmethod
    async def _aget_many(self, keys: list[Any], column_name: str = "id") -> list[T]:
        """Asynchronously retrieve many entities by a list of column values."""

    @final
    def get_many(self, keys: list[Any], column_name: str = "id") -> list[T]:
        return self._get_many(keys, column_name)

    @final
    async def aget_many(self, keys: list[Any], column_name: str = "id") -> list[T]:
        return await self._aget_many(keys, column_name)

    # -------------------------
    # Add single
    # -------------------------

    @abstractmethod
    def _add(self, entity: T) -> T:
        """Add a single entity to the database."""

    @abstractmethod
    async def _aadd(self, entity: T) -> T:
        """Asynchronously add a single entity to the database."""

    @final
    def add(self, entity: T) -> T:
        try:
            return self._add(entity)
        except Exception as e:
            if self._is_duplicate_error(e):
                raise_error(DatabaseErrors.UNIQUE_CONSTRAINT_VIOLATION)
            raise

    @final
    async def aadd(self, entity: T) -> T:
        try:
            return await self._aadd(entity)
        except Exception as e:
            if self._is_duplicate_error(e):
                raise_error(DatabaseErrors.UNIQUE_CONSTRAINT_VIOLATION)
            raise

    # -------------------------
    # Add many
    # -------------------------

    @abstractmethod
    def _add_many(self, entities: list[T]) -> list[T]:
        """Add many entities to the database."""

    @abstractmethod
    async def _aadd_many(self, entities: list[T]) -> list[T]:
        """Asynchronously add many entities to the database."""

    @final
    def add_many(self, entities: list[T]) -> list[T]:
        try:
            return self._add_many(entities)
        except Exception as e:
            if self._is_duplicate_error(e):
                raise_error(DatabaseErrors.UNIQUE_CONSTRAINT_VIOLATION)
            raise

    @final
    async def aadd_many(self, entities: list[T]) -> list[T]:
        try:
            return await self._aadd_many(entities)
        except Exception as e:
            if self._is_duplicate_error(e):
                raise_error(DatabaseErrors.UNIQUE_CONSTRAINT_VIOLATION)
            raise

    # -------------------------
    # Edit
    # -------------------------

    @abstractmethod
    def _edit(self, value: Any, entity: T, column_name: str = "id") -> T:
        """Edit an entity in the database."""

    @abstractmethod
    async def _aedit(self, value: Any, entity: T, column_name: str = "id") -> T:
        """Asynchronously edit an entity in the database."""

    @final
    def edit(self, value: Any, entity: T, column_name: str = "id") -> T:
        try:
            return self._edit(value, entity, column_name)
        except Exception as e:
            if self._is_duplicate_error(e):
                raise_error(DatabaseErrors.UNIQUE_CONSTRAINT_VIOLATION)
            raise

    @final
    async def aedit(self, value: Any, entity: T, column_name: str = "id") -> T:
        try:
            return await self._aedit(value, entity, column_name)
        except Exception as e:
            if self._is_duplicate_error(e):
                raise_error(DatabaseErrors.UNIQUE_CONSTRAINT_VIOLATION)
            raise

    # -------------------------
    # Delete
    # -------------------------

    @abstractmethod
    def _delete(self, value: Any, column_name: str = "id") -> None:
        """Soft delete an entity in the database."""

    @abstractmethod
    async def _adelete(self, value: Any, column_name: str = "id") -> None:
        """Asynchronously soft delete an entity in the database."""

    @final
    def delete(self, value: Any, column_name: str = "id") -> None:
        self._delete(value, column_name)

    @final
    async def adelete(self, value: Any, column_name: str = "id") -> None:
        await self._adelete(value, column_name)

    # -------------------------
    # Get all
    # -------------------------

    @abstractmethod
    def _get_all(self, **kwargs: Any) -> list[T]:
        """Retrieve all entities."""

    @final
    def get_all(self, **kwargs: Any) -> list[T]:
        return self._get_all(**kwargs)

    @abstractmethod
    async def _aget_all(self, **kwargs: Any) -> list[T]:
        """Asynchronously retrieve all entities."""

    @final
    async def aget_all(self, **kwargs: Any) -> list[T]:
        return await self._aget_all(**kwargs)

    # -------------------------
    # Get all paged
    # -------------------------

    @abstractmethod
    def _get_all_paged(
        self, filter_page_params: FilteredPaginationParams, **kwargs: Any
    ) -> PaginatedResult[T]:
        """Retrieve all entities with pagination."""

    @final
    def get_all_paged(
        self, filter_page_params: FilteredPaginationParams, **kwargs: Any
    ) -> PaginatedResult[T]:
        return self._get_all_paged(filter_page_params, **kwargs)

    @abstractmethod
    async def _aget_all_paged(
        self, filter_page_params: FilteredPaginationParams, **kwargs: Any
    ) -> PaginatedResult[T]:
        """Asynchronously retrieve all entities with pagination."""

    @final
    async def aget_all_paged(
        self, filter_page_params: FilteredPaginationParams, **kwargs: Any
    ) -> PaginatedResult[T]:
        """Asynchronously retrieve all entities with pagination."""
        return await self._aget_all_paged(filter_page_params, **kwargs)
