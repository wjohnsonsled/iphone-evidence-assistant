"""Explicit unsupported legacy compatibility application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import add_exception_handlers
from app.core.logging import configure_logging
from app.legacy.router import legacy_api_router


def create_legacy_app() -> FastAPI:
    """Create the unsupported application used for characterization only."""

    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="Legacy iPhone Evidence Assistant Compatibility API",
        version="0.1.0-legacy",
        description=(
            "Unsupported legacy compatibility and characterization surface. "
            "Its inputs, parsers, evidence, coverage, summaries, and reports "
            "are not supported production functionality."
        ),
    )
    add_exception_handlers(app)
    app.include_router(legacy_api_router)
    return app


legacy_app = create_legacy_app()
