from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Union

from base.models.definitions.exceptions import ExceptionCategory
from base.services.logging.helper.log_builder import LazyLogMessage

LogMessage = Union[Enum, str, LazyLogMessage]


class AbstractLoggerService(ABC):
    @abstractmethod
    def info(self, message: LogMessage, *args: Any) -> None: ...

    @abstractmethod
    def error(
        self,
        message: LogMessage,
        *args: Any,
        status: str | int | None = None,
        category: ExceptionCategory | None = ExceptionCategory.INTERNAL,
        location: str | None = None,
        tag: str = "Internal",
    ) -> None: ...

    @abstractmethod
    def exception(
        self,
        message: LogMessage,
        *args: Any,
        status: str | int | None = None,
        category: ExceptionCategory | None = ExceptionCategory.INTERNAL,
        location: str | None = None,
        tag: str = "Internal",
    ) -> None: ...

    @abstractmethod
    def warning(self, message: LogMessage, *args: Any) -> None: ...

    @abstractmethod
    def debug(self, message: LogMessage, *args: Any) -> None: ...
