from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsServerConfig(Protocol):
    """Settings shape `run_webserver` requires.

    Satisfied by composing `ServerSettingsMixin`. A service that calls
    `run_webserver` without it fails at type-check time rather than with an
    `AttributeError` on `max_gunicorn_workers` during container start — which
    would otherwise only surface outside `environment == "local"`, since the
    uvicorn path never reads it.
    """

    environment: str
    api_host: str
    api_port: int
    max_gunicorn_workers: int
