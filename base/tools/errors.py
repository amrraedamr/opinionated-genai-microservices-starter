from enum import Enum
from typing import Never


class ErrorsException(Exception):
    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
        error_enum: Enum | None = None,
    ) -> None:
        self.error_enum = error_enum
        self.message = message
        self.status_code = status_code
        super().__init__(
            f"Error: {error_enum.value['message']}"
            if error_enum
            else message or "Unknown Error"
        )


class StateDecodeError(ValueError):
    """Raised when the encoded state is invalid, tampered, or cannot be decoded."""


def raise_error(
    error: Enum | None = None,
    message: str | None = None,
    status_code: int | None = None,
) -> Never:
    if error is not None:
        raise ErrorsException(error_enum=error)

    raise ErrorsException(message=message, status_code=status_code)
