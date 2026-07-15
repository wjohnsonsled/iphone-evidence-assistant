"""Shared SQLAlchemy column types."""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONBType = JSON().with_variant(JSONB, "postgresql")
