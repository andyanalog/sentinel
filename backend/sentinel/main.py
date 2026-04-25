import sys
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sentinel.api.routes import dashboard, evaluate, health, operators
from sentinel.config import Settings, get_settings
from sentinel.container import build_container

logger = structlog.get_logger(__name__)


def _settings_from_cli() -> Settings:
    settings = get_settings()
    if "--dummy" in sys.argv:
        settings = settings.model_copy(update={"dummy_mode": True})
    return settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or _settings_from_cli()
    container = build_container(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = container
        if not settings.dummy_mode:
            # Only run the batch worker when a real ledger adapter is active;
            # dummy mode flushes synchronously through the repository path.
            container.batch_worker.start()
            container.debit_worker.start()
        logger.info(
            "sentinel.startup",
            dummy_mode=settings.dummy_mode,
            eval_cost_usdc=settings.eval_cost_usdc,
        )
        try:
            yield
        finally:
            if not settings.dummy_mode:
                await container.batch_worker.stop()
                await container.debit_worker.stop()
            for adapter in (container.cache, container.payments):
                close = getattr(adapter, "close", None)
                if close is not None:
                    await close()

    app = FastAPI(
        title="Sentinel — Trust-as-a-Service",
        version="0.1.0",
        lifespan=lifespan,
    )
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(operators.router)
    app.include_router(evaluate.router)
    app.include_router(dashboard.router)
    return app


app = create_app()
