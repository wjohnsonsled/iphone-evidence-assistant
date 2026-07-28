"""Candidate source-artifact ORM contract; migration is deferred to DEV-0410."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SupportedSourceArtifactModel(Base):
    __tablename__ = "supported_source_artifacts"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_supported_artifacts_version_positive"),
        CheckConstraint(
            "authorization_policy_version > 0",
            name="ck_supported_artifacts_policy_version_positive",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("security_tenants.id", ondelete="RESTRICT"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("security_cases.id", ondelete="RESTRICT"), index=True)
    evidence_source_id: Mapped[UUID] = mapped_column(ForeignKey("security_evidence_sources.id", ondelete="RESTRICT"), index=True)
    processing_run_id: Mapped[UUID] = mapped_column(ForeignKey("supported_processing_runs.id", ondelete="RESTRICT"), index=True)
    evidence_uuid: Mapped[UUID] = mapped_column(index=True)
    artifact_family_key: Mapped[str] = mapped_column(String(128), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observed_by_actor_id: Mapped[UUID] = mapped_column(index=True)
    authorization_policy_id: Mapped[UUID]
    authorization_policy_version: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
