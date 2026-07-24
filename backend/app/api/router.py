"""Default supported-path API router.

Only infrastructure-safe endpoints belong here until their owning tasks add
authorization and supported evidence contracts. Legacy compatibility routes
use ``app.legacy.router`` and must never be included in this router.
"""

from fastapi import APIRouter

from app.api import health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
