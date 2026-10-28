from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from chat_api.models.orm.user import UserDTO
from chat_api.services.auth import AuthService
from chat_api.services.auth.auths import http_bearer

http_bearer_dependency = Depends(http_bearer)


async def validate_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = http_bearer_dependency,
) -> UserDTO:
    return await AuthService().validate_user(credentials)


validate_user_dependency = Depends(validate_user)
