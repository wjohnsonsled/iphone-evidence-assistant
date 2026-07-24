"""Health check endpoints."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.core.database import get_session
from app.core.errors import ApiError

router = APIRouter()


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    """Return service and database health."""

    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ApiError(503, "database_unavailable", "Database is unavailable.") from exc
    return {"status": "ok", "database": "connected"}
