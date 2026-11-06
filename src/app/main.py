"""App factory. `create_app()` wires settings, logging, middleware, error handlers, the
task backend, and whichever modules ENABLED_MODULES selects."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.db.session import get_engine
from app.modules.registry import Module, load_modules
from app.tasks import get_backend

log = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)
    modules: list[Module] = load_modules(settings.enabled_modules)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        import app.tasks.examples  # noqa: F401  (registers example tasks)

        for m in modules:
            if m.on_startup:
                m.on_startup()
        await get_backend().startup()
        log.info("startup", service=settings.service_name, modules=[m.name for m in modules])
        yield
        await get_backend().shutdown()
        if not settings.is_test:
            await get_engine().dispose()
        log.info("shutdown", service=settings.service_name)

    app = FastAPI(
        title=settings.service_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
    )

    app.add_middleware(RequestContextMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    register_exception_handlers(app)

    app.include_router(health_router)
    api = APIRouter(prefix=settings.api_prefix)
    for m in modules:
        api.include_router(m.router)
    app.include_router(api)
    return app


app = create_app()
