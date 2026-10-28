import importlib
import logging
import multiprocessing
from typing import Any, cast

from base.tools.errors import MissingExtraError

try:
    import uvicorn
    from gunicorn.app.base import BaseApplication
except ModuleNotFoundError as exc:  # pragma: no cover
    raise MissingExtraError(
        "server", "uvicorn / gunicorn", feature="run_webserver"
    ) from exc

from base.services.configuration import get_settings
from base.tools.server_protocol import SupportsServerConfig


def _import_app(app_path: str) -> Any:
    """Resolve an ASGI application from a `"package.module:attribute"` string."""
    module_name, separator, attribute = app_path.partition(":")
    if not separator or not attribute:
        raise ValueError(
            f"Invalid app path {app_path!r}. Expected 'package.module:attribute'."
        )
    return getattr(importlib.import_module(module_name), attribute)


def run_webserver(
    app_path: str,
    host: str | None = None,
    port: int | None = None,
    environment: str | None = None,
    settings: SupportsServerConfig | None = None,
) -> None:
    """Serve `app_path` with uvicorn locally and gunicorn everywhere else.

    `app_path` is the service's own import path — `base` no longer knows which
    application it is serving.

    `settings` must satisfy `SupportsServerConfig`, i.e. the service composed
    `ServerSettingsMixin`. Host and port come from there (populated from
    `API_HOST` / `API_PORT` like any other setting); the explicit arguments
    stay as an override for tests and embedding.
    """
    settings = settings or cast(SupportsServerConfig, get_settings())
    host = host or settings.api_host
    port = int(port if port is not None else settings.api_port)
    environment = environment if environment is not None else settings.environment

    logging.info(f"Starting webserver (environment={environment})")
    if environment == "local":
        run_uvicorn(app_path, host, port)
    else:
        run_gunicorn(app_path, host, port, settings=settings)


def run_uvicorn(app_path: str, host: str = "0.0.0.0", port: int = 8000) -> None:
    uvicorn.run(
        app_path,
        host=host,
        port=int(port),
        reload=True,
    )


def run_gunicorn(
    app_path: str,
    host: str = "0.0.0.0",
    port: int = 8000,
    settings: SupportsServerConfig | None = None,
) -> None:
    settings = settings or cast(SupportsServerConfig, get_settings())

    # `preload: True` below imports the application in the master process, so
    # this runs pre-fork. Anything that must not be shared between workers —
    # engines, connection pools, clients — belongs in a capability's
    # `startup()`, which the ASGI lifespan runs once per worker post-fork.
    app = _import_app(app_path)

    class AIPlatform(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            cfg = self.cfg
            if cfg is None:
                return

            config = {
                key: value
                for key, value in self.options.items()
                if key in cfg.settings and value is not None
            }
            for key, value in config.items():
                cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        "bind": f"{host}:{port}",
        "workers": min(multiprocessing.cpu_count() + 1, settings.max_gunicorn_workers),
        "worker_class": "uvicorn.workers.UvicornWorker",
        "preload": True,
        "timeout": 500,
        "graceful_timeout": 300,
    }

    AIPlatform(app, options).run()
