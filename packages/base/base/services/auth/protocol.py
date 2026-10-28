from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsTokenVerificationConfig(Protocol):
    """Satisfied by `TokenVerificationMixin`. Every service needs this."""

    auth_public_key_path: str


@runtime_checkable
class SupportsTokenIssuingConfig(SupportsTokenVerificationConfig, Protocol):
    """Satisfied by `TokenIssuingMixin`. Only a token-issuing service needs it."""

    auth_private_key_path: str
    access_token_expiry_seconds: int
    refresh_token_expiry_seconds: int


@runtime_checkable
class SupportsIdpConfig(Protocol):
    """Satisfied by `IdpResourceServerMixin`.

    Lets a service accept tokens from an enterprise IdP (Entra and friends)
    alongside first-party ones.
    """

    idp_resource_server_enabled: bool
    idp_issuer: str
    idp_audience: str
    idp_jwks_url: str
    idp_discovery_url: str
    idp_algorithms: str
    idp_email_claim: str
