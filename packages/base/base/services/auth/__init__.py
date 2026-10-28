"""Authentication mechanism, shared by every service.

What lives here: signing and verifying tokens, the bearer scheme, the OAuth
provider protocol, and `Principal` — the caller as asserted by verified claims.

What does **not** live here: users. Registration, login, password hashing
policy, OAuth account linking and the `user` table belong to whichever service
owns identity. Every other service verifies a token and trusts the claims.

See `docs/architecture/05-service-contracts.md`.
"""

from base.services.auth.bearer import (
    current_principal,
    http_bearer,
    http_bearer_dependency,
    principal_dependency,
)
from base.services.auth.models import (
    AccessToken,
    Principal,
    RefreshToken,
    TokenPair,
)
from base.services.auth.protocol import (
    SupportsIdpConfig,
    SupportsTokenIssuingConfig,
    SupportsTokenVerificationConfig,
)
from base.services.auth.tokens import TokenIssuer, TokenVerifier, load_key

__all__ = [
    "AccessToken",
    "Principal",
    "RefreshToken",
    "SupportsIdpConfig",
    "SupportsTokenIssuingConfig",
    "SupportsTokenVerificationConfig",
    "TokenIssuer",
    "TokenPair",
    "TokenVerifier",
    "current_principal",
    "http_bearer",
    "http_bearer_dependency",
    "load_key",
    "principal_dependency",
]
