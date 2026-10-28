"""chat-api's user-bound authentication.

Everything mechanical — signing, verifying, JWKS, the bearer scheme, the OAuth
provider protocol — now lives in `base.services.auth` and is shared by every
service. What remains here is the part only an identity-owning service can do:
turn a verified `Principal` into a `UserDTO`, and turn a `UserDTO` into claims
worth signing.

When phase 5 extracts the identity service, this module moves with the user
table and chat-api drops to `base`'s `principal_dependency` alone.
"""

import uuid

from fastapi.security import HTTPAuthorizationCredentials

from base.models.definitions.errors import AuthErrors
from base.services.auth import Principal, TokenIssuer, TokenPair, TokenVerifier
from base.services.common.meta import Singleton
from base.tools.errors import raise_error
from chat_api.models.orm.user import UserDTO
from chat_api.models.view_models.auth import RefreshToken
from chat_api.services.auth.oauth import OAuthService
from chat_api.settings import settings
from chat_api.stores.user import UserStore


class AuthService(metaclass=Singleton):
    def __init__(self) -> None:
        self._user_store: UserStore = UserStore()
        self._oauth_service: OAuthService = OAuthService()
        self._issuer: TokenIssuer = TokenIssuer()
        self._verifier: TokenVerifier = TokenVerifier()

    # Issuing

    def generate_token_pair(self, user: UserDTO) -> TokenPair:
        """Decide what this service asserts about a user, then let base sign it."""
        return self._issuer.issue_pair(
            {"user_id": str(user.id), "email": user.email},
        )

    async def refresh_access_token(self, refresh_token: RefreshToken) -> TokenPair:
        payload = self._verifier.decode_local(refresh_token, expected_type="refresh")
        user_id = payload.get("user_id", "")
        user = await self._user_store.aget(uuid.UUID(user_id))
        return self.generate_token_pair(user)

    # Resolving

    async def validate_user(
        self,
        credentials: HTTPAuthorizationCredentials,
    ) -> UserDTO:
        """Verify the token with base, then resolve it to this service's user."""
        principal = self._verifier.verify(credentials.credentials)
        return await self.resolve_principal(principal)

    async def resolve_principal(self, principal: Principal) -> UserDTO:
        if self._is_idp_principal(principal):
            return await self._resolve_idp_principal(principal)
        if principal.user_id is None:
            raise_error(AuthErrors.USER_TOKEN_INCOMPLETE)
        return await self._user_store.aget(principal.user_id)

    def _is_idp_principal(self, principal: Principal) -> bool:
        return bool(
            settings.idp_resource_server_enabled
            and principal.issuer
            and principal.issuer == settings.idp_issuer
        )

    async def _resolve_idp_principal(self, principal: Principal) -> UserDTO:
        """An IdP user may not exist locally yet — link or create on first sight."""
        if not principal.email:
            raise_error(AuthErrors.USER_TOKEN_INCOMPLETE)
        claims = principal.claims
        return await self._oauth_service.aresolve_idp_user(
            provider=settings.idp_provider_name,
            subject=principal.subject,
            email=principal.email,
            email_verified=bool(claims.get("email_verified", True)),
            first_name=claims.get("given_name"),
            last_name=claims.get("family_name"),
        )
