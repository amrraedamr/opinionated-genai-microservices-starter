import importlib
import logging
import multiprocessing
import os

import uvicorn
from gunicorn.app.base import BaseApplication

from base.services.configuration import settings


def run_webserver(
    host: str = os.environ.get("API_HOST", "0.0.0.0"),
    port: int = int(os.environ.get("API_PORT", 8000)),
    environment: str | None = settings.environment,
):
    logging.info(f"Starting webserver (environment={environment})")
    if environment == "local":
        run_uvicorn(host, port)
    else:
        run_gunicorn(host, port)


def run_uvicorn(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(
        "base.main:app",
        host=host,
        port=int(port),
        reload=True,
    )


def run_gunicorn(host: str = "0.0.0.0", port: int = 8000):
    app = importlib.import_module("base.main").app

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
