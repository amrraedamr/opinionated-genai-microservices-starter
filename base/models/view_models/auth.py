from typing import NewType

from pydantic import EmailStr, field_validator

from base.models.view_models import BaseModel
from base.tools.validators import validate_name, validate_password

AccessToken = NewType("AccessToken", str)
RefreshToken = NewType("RefreshToken", str)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None

    _validate_first_name = field_validator("first_name")(validate_name)
    _validate_last_name = field_validator("last_name")(validate_name)
    _validate_password = field_validator("password")(validate_password)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken


class RefreshRequest(BaseModel):
    refresh_token: RefreshToken


class RefreshResponse(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken


class TokenPair(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken


class OAuthExchangeRequest(BaseModel):
    code: str


class OAuthProvidersResponse(BaseModel):
    providers: list[str]
