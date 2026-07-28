"""Additive candidate processing-run ORM contract; migration is deferred."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SupportedProcessingRunModel(Base):
    __tablename__ = "supported_processing_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["case_id", "tenant_id"],
            ["security_cases.id", "security_cases.tenant_id"],
            name="fk_supported_run_case_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("version > 0", name="ck_supported_runs_version_positive"),
        CheckConstraint(
            "authorization_policy_version > 0",
            name="ck_supported_runs_policy_version_positive",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("security_tenants.id", ondelete="RESTRICT"), index=True
    )
    case_id: Mapped[UUID] = mapped_column(index=True)
    evidence_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("security_evidence_sources.id", ondelete="RESTRICT"), index=True
    )
    purpose_key: Mapped[str] = mapped_column(String(128))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    requested_by_actor_id: Mapped[UUID] = mapped_column(index=True)
    correlation_id: Mapped[UUID] = mapped_column(index=True)
    authorization_policy_id: Mapped[UUID]
    authorization_policy_version: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
