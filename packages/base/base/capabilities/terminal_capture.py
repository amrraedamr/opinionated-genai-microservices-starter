from fastapi import FastAPI

from base.capabilities import BaseCapability
from base.models.definitions.health import ProbeStatus
from base.models.view_models.health import ProbeResult
from base.services.logging.tee_stream import TerminalCaptureService


class TerminalCapture(BaseCapability):
    """Tees stdout/stderr onto a pub/sub channel so `/logs` can stream them.

    The underlying service is a `KeyedSingleton` keyed on `app_name`, so any
    other holder of the same name gets the same instance. It is resolved
    lazily rather than in `__init__` to keep nothing alive across `fork()`.
    """

    name = "terminal-capture"

    def __init__(self, app_name: str) -> None:
        self._app_name = app_name

    @property
    def service(self) -> TerminalCaptureService:
        return TerminalCaptureService(self._app_name)

    async def startup(self, app: FastAPI) -> None:
        self.service.start()

    async def shutdown(self, app: FastAPI) -> None:
        await self.service.stop()

    async def probe(self) -> ProbeResult:
        active = self.service.is_active
        return ProbeResult(
            name=self.name,
            status=ProbeStatus.OK if active else ProbeStatus.DEGRADED,
            detail=None if active else "Terminal capture is not active.",
        )
