from typing import Protocol, runtime_checkable

from fastapi import FastAPI

from base.models.definitions.health import ProbeStatus
from base.models.view_models.health import ProbeResult


@runtime_checkable
class Capability(Protocol):
    """A subsystem a service opts into.

    The app factory owns no subsystems of its own. A service lists the
    capabilities it needs, and `create_app` starts them, tears them down in
    reverse order, and exposes their probes on `/readyz`.

    **Construct nothing expensive in `__init__`.** A capability is instantiated
    at module import, and gunicorn is configured with ``preload: True`` — so
    anything built in `__init__` is built *before* `fork()` and shared across
    workers. Connection pools, engines and clients are not fork-safe. Create
    them in `startup()`, which runs per worker after the fork.
    """

    name: str

    async def startup(self, app: FastAPI) -> None: ...

    async def shutdown(self, app: FastAPI) -> None: ...

    async def probe(self) -> ProbeResult: ...


class BaseCapability:
    """Convenience base so implementations override only what they need."""

    name: str = "capability"

    async def startup(self, app: FastAPI) -> None:
        return None

    async def shutdown(self, app: FastAPI) -> None:
        return None

    async def probe(self) -> ProbeResult:
        return ProbeResult(name=self.name, status=ProbeStatus.OK)


__all__ = ["BaseCapability", "Capability", "ProbeResult", "ProbeStatus"]
