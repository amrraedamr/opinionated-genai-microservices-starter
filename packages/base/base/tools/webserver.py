import importlib
import logging
import multiprocessing
import os
from typing import Any

import uvicorn
from gunicorn.app.base import BaseApplication

from base.services.configuration import Settings
from base.services.configuration import settings as default_settings


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
    settings: Settings | None = None,
) -> None:
    """Serve `app_path` with uvicorn locally and gunicorn everywhere else.

    `app_path` is the service's own import path — `base` no longer knows which
    application it is serving.
    """
    settings = settings or default_settings
    host = host or os.environ.get("API_HOST", "0.0.0.0")
    port = int(port or os.environ.get("API_PORT", 8000))
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
    settings: Settings | None = None,
) -> None:
    settings = settings or default_settings

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
