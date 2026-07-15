"""FastAPI application factory."""

from fastapi import FastAPI

from onssa_ai.api.routes import health, metrics, rag, search
from onssa_ai.core.config import Settings, get_settings
from onssa_ai.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.runtime.log_level)
    app = FastAPI(title=resolved.app.name)
    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(rag.router, prefix=resolved.app.api_prefix)
    app.include_router(search.router, prefix=resolved.app.api_prefix)
    return app


app = create_app()
