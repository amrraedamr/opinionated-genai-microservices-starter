from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsTokenVerificationConfig(Protocol):
    """Satisfied by `TokenVerificationMixin`."""

    auth_public_key_path: str


@runtime_checkable
class SupportsTokenIssuingConfig(SupportsTokenVerificationConfig, Protocol):
    """Satisfied by `TokenIssuingMixin`."""

    auth_private_key_path: str
    access_token_expiry_seconds: int
    refresh_token_expiry_seconds: int


@runtime_checkable
class SupportsIdpConfig(Protocol):
    """Satisfied by `IdpResourceServerMixin`."""

    idp_resource_server_enabled: bool
    idp_issuer: str
    idp_audience: str
    idp_jwks_url: str
    idp_discovery_url: str
    idp_algorithms: str
    idp_email_claim: str
