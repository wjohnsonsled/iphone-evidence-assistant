"""Unsupported legacy compatibility API router."""

from fastapi import APIRouter

from app.api import cases, evidence, health

legacy_api_router = APIRouter(prefix="/api/v1")
legacy_api_router.include_router(health.router, tags=["health"])
legacy_api_router.include_router(cases.router, prefix="/cases", tags=["legacy-cases"])
legacy_api_router.include_router(evidence.router, prefix="/cases", tags=["legacy-evidence"])
