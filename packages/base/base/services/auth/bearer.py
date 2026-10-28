"""The bearer scheme and the dependency every service can use.

`principal_dependency` resolves a caller from token claims with no database
access, so a service that does not own users can still authenticate requests.
A service that *does* own users wraps this with its own lookup.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from base.services.auth.models import Principal
from base.services.auth.tokens import TokenVerifier

http_bearer = HTTPBearer()
http_bearer_dependency = Depends(http_bearer)


async def current_principal(
    credentials: HTTPAuthorizationCredentials = http_bearer_dependency,
) -> Principal:
    return TokenVerifier().verify(credentials.credentials)


principal_dependency = Depends(current_principal)
