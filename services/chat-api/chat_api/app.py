"""Composition root for chat-api.

This is where the service decides what it is: which routers it exposes, which
capabilities it needs, and how it is served. `base` supplies the machinery and
knows none of it.
"""

from sse_starlette.sse import EventSourceResponse

from base.app import create_app
from base.capabilities.prompts import Prompts
from base.capabilities.terminal_capture import TerminalCapture
from base.services.configuration import settings
from base.services.logging.tee_stream import TerminalCaptureService
from base.tools.stream import StreamIterator
from chat_api import routers
from chat_api.prompts import templates
from chat_api.services.auth.dependencies import validate_user_dependency

app = create_app(
    settings=settings,
    routers=routers,
    prefix="/api/7r",
    capabilities=[
        TerminalCapture(settings.app_name),
        Prompts(templates=[templates]),
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


def start() -> None:
    from base.tools.webserver import run_webserver

    run_webserver(app_path="chat_api.app:app", settings=settings)
