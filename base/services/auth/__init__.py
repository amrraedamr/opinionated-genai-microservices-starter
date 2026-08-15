import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from jwt import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAlgorithmError,
    decode,
    encode,
)

from base.models.definitions.errors import AuthErrors
from base.models.orm.user import UserDTO
from base.models.view_models.auth import (
    AccessToken,
    RefreshToken,
    TokenPair,
)
from base.services.auth.auths import http_bearer
from base.services.common.meta import Singleton
from base.services.configuration.local_config import LocalConfig
from base.services.store.user import UserStore
from base.tools.errors import raise_error


class AuthService(metaclass=Singleton):
    def __init__(self) -> None:
        self._user_store: UserStore = UserStore()
        self._private_key: str = self._load_key(
            LocalConfig.get("auth_private_key_path") or ""
        )
        self._public_key: str = self._load_key(
            LocalConfig.get("auth_public_key_path") or ""
        )
        self._access_token_expiry: int = LocalConfig.get_int(
            "access_token_expiry_seconds", 900
        )  # 15 min
        self._refresh_token_expiry: int = LocalConfig.get_int(
            "refresh_token_expiry_seconds", 604800
        )  # 7 days

    # Public

    def generate_token_pair(self, user: UserDTO) -> TokenPair:
        access_token = self._generate_access_token(
            payload={"user_id": str(user.id), "email": user.email, "type": "access"},
        )
        refresh_token = self._generate_refresh_token(
            payload={"user_id": str(user.id), "type": "refresh"},
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def refresh_access_token(self, refresh_token: RefreshToken) -> TokenPair:
        payload = self._decode_token(refresh_token, expected_type="refresh")
        user_id: str = payload.get("user_id", "")
        user = await self._user_store.aget(uuid.UUID(user_id))
        return self.generate_token_pair(user)

    async def validate_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    ) -> UserDTO:
        payload = self._decode_token(
            AccessToken(credentials.credentials), expected_type="access"
        )
        user_id: str | None = payload.get("user_id")
        email: str | None = payload.get("email")
        if not user_id or not email:
            raise_error(AuthErrors.USER_TOKEN_INCOMPLETE)
        return await self._user_store.aget(uuid.UUID(user_id))

    # Private

    def _generate_access_token(self, payload: dict[str, Any]) -> AccessToken:
        return AccessToken(self._generate_token(payload, self._access_token_expiry))

    def _generate_refresh_token(self, payload: dict[str, Any]) -> RefreshToken:
        return RefreshToken(self._generate_token(payload, self._refresh_token_expiry))

    def _generate_token(self, payload: dict[str, Any], expiry: int) -> str:
        now = datetime.now(UTC)
        return encode(
            payload={
                **payload,
                "iat": now,
                "exp": now.timestamp() + expiry,
            },
            key=self._private_key,
            algorithm="RS256",
        )

    def _decode_token(
        self, token: AccessToken | RefreshToken, expected_type: str
    ) -> dict[str, Any]:
        try:
            payload: dict[str, Any] = decode(
                token,
                key=self._public_key,
                algorithms=["RS256"],
            )
            if payload.get("type") != expected_type:
                raise_error(AuthErrors.USER_TOKEN_INCOMPLETE)
            return payload
        except (DecodeError, InvalidAlgorithmError):
            raise_error(AuthErrors.USER_DECODE_FAILED)
        except ExpiredSignatureError:
            raise_error(AuthErrors.USER_TOKEN_EXPIRED)

    # Helpers

    @staticmethod
    def _load_key(path: str) -> str:
        with open(path) as f:
            return f.read()
