from enum import Enum
from typing import Union

from base.services.logging.helper.log_builder import LazyLogMessage

LogMessage = Union[Enum, str, LazyLogMessage]
