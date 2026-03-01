from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from base.models.orm.user import UserDTO
from base.services.auth import AuthService
from base.services.auth.auths import http_bearer


async def validate_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> UserDTO:
    return await AuthService().validate_user(credentials)
