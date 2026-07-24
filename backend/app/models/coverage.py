"""Artifact coverage database model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.case import utcnow
from app.models.types import JSONBType


class ArtifactCoverage(Base):
    """Artifact coverage and parser status record."""

    __tablename__ = "artifact_coverage"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[UUID | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"), index=True)
    artifact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    coverage_status: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    parser_name: Mapped[str | None] = mapped_column(String(128))
    source_path: Mapped[str | None] = mapped_column(Text)
    records_parsed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    details_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    case = relationship("Case", back_populates="coverage_records")
    device = relationship("Device", back_populates="coverage_records")
