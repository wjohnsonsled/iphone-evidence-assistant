"""Device database model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.case import utcnow
from app.models.types import JSONBType


class Device(Base):
    """Device or local backup source associated with a case."""

    __tablename__ = "devices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name: Mapped[str | None] = mapped_column(String(255))
    device_type: Mapped[str] = mapped_column(String(64), nullable=False, default="iphone")
    ios_version: Mapped[str | None] = mapped_column(String(64))
    product_type: Mapped[str | None] = mapped_column(String(128))
    serial_number: Mapped[str | None] = mapped_column(String(128))
    udid: Mapped[str | None] = mapped_column(String(128))
    backup_identifier: Mapped[str | None] = mapped_column(String(255))
    backup_encrypted: Mapped[bool | None] = mapped_column(Boolean)
    backup_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    case = relationship("Case", back_populates="devices")
    evidence_events = relationship("EvidenceEvent", back_populates="device")
    coverage_records = relationship("ArtifactCoverage", back_populates="device")
