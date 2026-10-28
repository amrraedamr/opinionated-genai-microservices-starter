from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsCacheConfig(Protocol):
    """Settings shape the Redis cache client requires."""

    redis_url: str
    redis_ssl_cert_reqs: str
    redis_max_connections: int
    redis_socket_timeout: float
    redis_socket_connect_timeout: float
    redis_retry_on_timeout: bool
    redis_health_check_interval: int
    redis_decode_responses: bool
