"""chat_api's authenticated-user dependency.

`base` provides `principal_dependency`, which authenticates with no database
access. This service additionally owns the user table, so it offers a
dependency that resolves the principal to a full `UserDTO`.

Routes that only need an id or an email should prefer `principal_dependency`
from `base.services.auth` — it costs no query, and it keeps working unchanged
once the user table moves to the identity service.
"""

from fastapi import Depends

from base.services.auth import Principal, principal_dependency
from chat_api.models.orm.user import UserDTO
from chat_api.services.auth import AuthService


async def validate_user(principal: Principal = principal_dependency) -> UserDTO:
    return await AuthService().resolve_principal(principal)


validate_user_dependency = Depends(validate_user)
