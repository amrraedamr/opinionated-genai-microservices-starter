from typing import Any, Self

from pydantic import BaseModel, ConfigDict


class HttpResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    status_code: int | None = None
    data: dict[str, Any] | None = None
    error: Exception | None = None
    error_detail: dict[str, Any] | str | None = None

    @property
    def failed(self) -> bool:
        return not self.success

    @classmethod
    def ok(cls, status_code: int, data: dict[str, Any]) -> Self:
        return cls(success=True, status_code=status_code, data=data)

    @classmethod
    def fail(
        cls,
        error: Exception,
        status_code: int | None = None,
        error_detail: dict[str, Any] | str | None = None,
    ) -> Self:
        return cls(
            success=False,
            error=error,
            status_code=status_code,
            error_detail=error_detail,
        )
