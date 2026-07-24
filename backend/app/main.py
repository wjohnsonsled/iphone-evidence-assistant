"""Default supported-path FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import add_exception_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Create the default application without legacy evidence routes.

    Evidence intake and processing remain unavailable until their approved
    tasks implement the required authorization, provenance, and quarantine
    boundaries.
    """

    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="AI-Powered iPhone Evidence Assistant",
        version="0.1.0",
        description=(
            "Pre-validation backend foundation. No evidence input, parser, "
            "artifact, or processing workflow is currently supported."
        ),
    )
    add_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
