"""OAuth/OIDC provider protocol mechanics — provider-agnostic, user-agnostic.

Building authorize URLs, exchanging codes, fetching profiles and minting the
Apple client-secret JWT are all protocol plumbing, so they belong to every
service that might speak OAuth.

Turning a resolved `OAuthProfile` into a user record does **not** live here —
that is the identity-owning service's job.
"""

from base.services.auth.oauth.providers import (
    OAuthProfile,
    OAuthProviderConfig,
    OAuthProviderRegistry,
    build_apple_client_secret,
    load_oauth_provider_configs,
)

__all__ = [
    "OAuthProfile",
    "OAuthProviderConfig",
    "OAuthProviderRegistry",
    "build_apple_client_secret",
    "load_oauth_provider_configs",
]
