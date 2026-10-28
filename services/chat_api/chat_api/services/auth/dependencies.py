"""Authenticated-user dependency."""

from fastapi import Depends

from base.services.auth import Principal, principal_dependency
from chat_api.models.orm.user import UserDTO
from chat_api.services.auth import AuthService


async def avalidate_user(principal: Principal = principal_dependency) -> UserDTO:
    return await AuthService().aresolve_principal(principal)


validate_user_dependency = Depends(avalidate_user)
