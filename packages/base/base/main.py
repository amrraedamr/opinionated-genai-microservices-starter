"""Thin shim preserving the single-application entrypoint.

Kept only so `base.main:app` keeps resolving during the migration. The real
composition root moves into the service in phase 2, and this module goes away
with it.
"""

from sse_starlette.sse import EventSourceResponse

from base import routers
from base.app import create_app
from base.capabilities.prompts import Prompts
from base.capabilities.terminal_capture import TerminalCapture
from base.services.auth.dependencies import validate_user_dependency
from base.services.configuration import settings
from base.services.logging.tee_stream import TerminalCaptureService
from base.tools.stream import StreamIterator

app = create_app(
    settings=settings,
    routers=routers,
    prefix="/api/7r",
    capabilities=[
        TerminalCapture(settings.app_name),
        Prompts(),
    ],
)


@app.post(
    "/logs",
    dependencies=[validate_user_dependency],
)
async def get_logs():
    capture_service = TerminalCaptureService(settings.app_name)
    stream_iterator = StreamIterator(source=capture_service.subscribe())
    return EventSourceResponse(stream_iterator, media_type="text/event-stream")
