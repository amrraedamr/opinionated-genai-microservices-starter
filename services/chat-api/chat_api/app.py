"""Composition root for chat-api.

This is where the service decides what it is: its settings, which routers it
exposes, which capabilities it needs, and how it is served. `base` supplies the
machinery and knows none of it.
"""

from base.services.configuration import configure
from chat_api.settings import settings

# Register the service's settings before importing anything that reads them.
configure(settings)

from sse_starlette.sse import EventSourceResponse  # noqa: E402

from base.app import create_app  # noqa: E402
from base.capabilities.prompts import Prompts  # noqa: E402
from base.capabilities.terminal_capture import TerminalCapture  # noqa: E402
from base.services.logging.tee_stream import TerminalCaptureService  # noqa: E402
from base.tools.stream import StreamIterator  # noqa: E402
from chat_api import routers  # noqa: E402
from chat_api.prompts import templates  # noqa: E402
from chat_api.services.auth.dependencies import (  # noqa: E402
    validate_user_dependency,
)

app = create_app(
    settings=settings,
    routers=routers,
    prefix=settings.api_prefix,
    capabilities=[
        TerminalCapture(settings.service_name),
        Prompts(templates=[templates]),
    ],
    cors_origins=settings.cors_origins_list or None,
)


@app.post(
    "/logs",
    dependencies=[validate_user_dependency],
)
async def get_logs():
    capture_service = TerminalCaptureService(settings.service_name)
    stream_iterator = StreamIterator(source=capture_service.subscribe())
    return EventSourceResponse(stream_iterator, media_type="text/event-stream")


def start() -> None:
    from base.tools.webserver import run_webserver

    run_webserver(app_path="chat_api.app:app", settings=settings)
