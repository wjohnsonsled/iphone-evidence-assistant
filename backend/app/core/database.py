"""Database engine, session, and SQLAlchemy metadata."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


def make_engine(database_url: str | None = None):
    """Create a synchronous SQLAlchemy engine."""

    return create_engine(database_url or get_settings().database_url, pool_pre_ping=True)


_engine: Engine | None = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False)


def get_engine() -> Engine:
    """Return the lazily created application engine."""

    global _engine
    if _engine is None:
        _engine = make_engine()
        SessionLocal.configure(bind=_engine)
    return _engine


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI dependencies."""

    get_engine()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
