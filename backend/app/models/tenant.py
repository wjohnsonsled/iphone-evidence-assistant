"""Additive tenant ORM contract; migration is owned by DEV-0308."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TenantModel(Base):
    __tablename__ = "security_tenants"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_security_tenants_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(63), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by_actor_id: Mapped[UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
