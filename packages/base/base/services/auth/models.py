"""Token and identity types that carry no domain.

`Principal` is deliberately not a user record. It is what a verified token
asserts — an id, maybe an email, maybe some roles. A service that only needs to
know *who is calling* reads this and never touches a user table, which is what
lets every service verify tokens while exactly one service owns users.
"""

from typing import NewType
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel

from base.models.definitions.errors import AuthErrors
from base.models.view_models import BaseModel
from base.tools.errors import raise_error

AccessToken = NewType("AccessToken", str)
RefreshToken = NewType("RefreshToken", str)


class TokenPair(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken


class Principal(PydanticBaseModel):
    """The verified caller, reconstructed from token claims alone."""

    subject: str
    """Raw `sub`/`user_id` claim as the issuer wrote it."""

    user_id: UUID | None = None
    """Parsed `subject` when it is a UUID. `None` for IdP subjects that are not."""

    email: str | None = None
    roles: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()
    issuer: str | None = None
    token_type: str | None = None
    claims: dict = {}

    def require_role(self, role: str) -> None:
        if role not in self.roles:
            raise_error(AuthErrors.USER_UNAUTHORIZED)

    def require_scope(self, scope: str) -> None:
        if scope not in self.scopes:
            raise_error(AuthErrors.USER_UNAUTHORIZED)
