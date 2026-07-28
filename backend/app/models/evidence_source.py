"""Tenant/case evidence-source linkage; migration is owned by DEV-0308."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EvidenceSourceModel(Base):
    __tablename__ = "security_evidence_sources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["case_id", "tenant_id"],
            ["security_cases.id", "security_cases.tenant_id"],
            name="fk_security_source_case_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "version > 0",
            name="ck_security_evidence_sources_version_positive",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("security_tenants.id", ondelete="RESTRICT"),
        index=True,
    )
    case_id: Mapped[UUID] = mapped_column(index=True)
    source_type: Mapped[str] = mapped_column(String(128))
    source_locator: Mapped[str] = mapped_column(Text)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registered_by_actor_id: Mapped[UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
