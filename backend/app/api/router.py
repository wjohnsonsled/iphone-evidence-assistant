"""Top-level API router."""

from fastapi import APIRouter

from app.api import cases, evidence, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(evidence.router, prefix="/cases", tags=["evidence"])
