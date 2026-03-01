from abc import ABC

from base.services.logging import AbstractLoggerService
from base.services.logging.console import ConsoleLoggerService


class AbstractService(ABC):
    def __init__(self, logger: AbstractLoggerService | None = None) -> None:
        self._logger = logger or ConsoleLoggerService()
