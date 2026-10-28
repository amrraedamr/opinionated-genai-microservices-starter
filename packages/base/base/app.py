import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from types import ModuleType
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from base.capabilities import Capability
from base.models.definitions.health import ProbeStatus
from base.models.view_models.health import HealthReport, ProbeResult
from base.services.common.meta import Stored, scope_id
from base.services.configuration import CoreSettings
from base.services.logging.console import ConsoleLoggerService
from base.tools.exception_handlers import AppExceptionHandler
from base.tools.routers import init_routers

LifespanHook = Callable[[FastAPI], AbstractAsyncContextManager[None]]

DEFAULT_TITLE = "Opinionated GenAI Starter API"
DEFAULT_VERSION = "0.1"


def _resolve_cors_origins(
    cors_origins: Sequence[str] | None,
    environment: str,
    logger: ConsoleLoggerService,
) -> list[str]:
    """`["*"]` is a local-development convenience, never a deployed default."""
    if cors_origins is not None:
        return list(cors_origins)
    if environment == "local":
        return ["*"]
    logger.warning(
        "No cors_origins passed to create_app and environment is %r; "
        "cross-origin requests will be refused. Pass cors_origins explicitly.",
        environment,
    )
    return []


async def _run_probe(capability: Capability) -> ProbeResult:
    try:
        return await capability.probe()
    except Exception as exc:  # noqa: BLE001 — a probe must never break /readyz
        return ProbeResult(
            name=capability.name,
            status=ProbeStatus.FAILED,
            detail=f"{type(exc).__name__}: {exc}",
        )


def create_app(
    *,
    settings: CoreSettings,
    routers: ModuleType | None = None,
    prefix: str = "/api",
    capabilities: Sequence[Capability] = (),
    lifespan_hooks: Sequence[LifespanHook] = (),
    cors_origins: Sequence[str] | None = None,
    title: str = DEFAULT_TITLE,
    version: str = DEFAULT_VERSION,
) -> FastAPI:
    """Build a FastAPI application for one service.

    `base` supplies the composition machinery; the service decides what goes
    in. Nothing here is specific to any domain: routers, capabilities and CORS
    policy are all arguments.

    Capabilities start in the order given and shut down in reverse. Their
    `probe()` results back `/readyz`.
    """
    logger = ConsoleLoggerService()
    capabilities = tuple(capabilities)
    lifespan_hooks = tuple(lifespan_hooks)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Application starting")
        started: list[Capability] = []
        try:
            async with AsyncExitStack() as stack:
                for hook in lifespan_hooks:
                    await stack.enter_async_context(hook(app))
                for capability in capabilities:
                    await capability.startup(app)
                    started.append(capability)
                    logger.info("Capability started: %s", capability.name)
                yield
        finally:
            logger.info("Application shutting down")
            for capability in reversed(started):
                try:
                    await capability.shutdown(app)
                except Exception:  # noqa: BLE001 — one failure must not strand the rest
                    logger.exception(
                        "Capability failed to shut down: %s", capability.name
                    )

    app = FastAPI(title=title, version=version, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_resolve_cors_origins(cors_origins, settings.environment, logger),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def register_request(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        scope_id.set(uuid4())
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            should_delete = response is None or not response.headers.get(
                "content-type", ""
            ).startswith("text/event-stream")
            if should_delete:
                Stored.delete_scope()

    if routers is not None:
        init_routers(app, routers=routers, prefix=prefix)

    AppExceptionHandler().register(app)

    @app.get("/", tags=["Main"])
    def root() -> dict[str, str]:
        return {"message": f"Welcome to the {title}!", "version": version}

    @app.get("/health-check", tags=["Main"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/livez", tags=["Main"])
    async def livez() -> HealthReport:
        """The process is up. Deliberately does not touch any dependency."""
        return HealthReport(status=ProbeStatus.OK)

    @app.get("/readyz", tags=["Main"])
    async def readyz() -> Response:
        """Every capability reports whether its backing dependency is usable."""
        checks = list(await asyncio.gather(*(_run_probe(c) for c in capabilities)))
        report = HealthReport.aggregate(checks)
        status_code = 503 if report.status is ProbeStatus.FAILED else 200
        return JSONResponse(
            content=report.serialize(exclude_none=True),
            status_code=status_code,
        )

    return app
