"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import add_exception_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="AI-Powered iPhone Evidence Assistant", version="0.1.0")
    add_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
