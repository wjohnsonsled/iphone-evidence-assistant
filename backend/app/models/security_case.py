"""Tenant-scoped case ORM contract; migration is owned by DEV-0308."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKey, Index, Integer, String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SecurityCaseModel(Base):
    __tablename__ = "security_cases"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_security_cases_version_positive"),
        UniqueConstraint("id", "tenant_id", name="uq_security_cases_id_tenant"),
        Index("ix_security_cases_tenant_name", "tenant_id", "name"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("security_tenants.id", ondelete="RESTRICT"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by_actor_id: Mapped[UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
