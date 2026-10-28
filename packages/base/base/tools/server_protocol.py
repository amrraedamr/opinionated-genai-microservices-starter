from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsServerConfig(Protocol):
    """Satisfied by `ServerSettingsMixin`."""

    environment: str
    api_host: str
    api_port: int
    max_gunicorn_workers: int
