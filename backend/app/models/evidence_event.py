"""Evidence event database model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.case import utcnow
from app.models.types import JSONBType


class EvidenceEvent(Base):
    """Normalized evidence event persisted for querying."""

    __tablename__ = "evidence_events"
    __table_args__ = (
        Index("ix_evidence_events_case_timestamp", "case_id", "timestamp"),
        Index("ix_evidence_events_case_event_type", "case_id", "event_type"),
        Index("ix_evidence_events_case_conversation_key", "case_id", "conversation_key"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[UUID | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"), index=True)
    external_event_id: Mapped[str | None] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(128), index=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    timestamp_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone_name: Mapped[str | None] = mapped_column(String(128))
    summary: Mapped[str | None] = mapped_column(Text)
    details_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    raw_values_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    source_artifact: Mapped[str | None] = mapped_column(String(255), index=True)
    source_database: Mapped[str | None] = mapped_column(String(255))
    source_table: Mapped[str | None] = mapped_column(String(255))
    source_record_id: Mapped[str | None] = mapped_column(String(255))
    source_path: Mapped[str | None] = mapped_column(Text)
    parser_name: Mapped[str | None] = mapped_column(String(128))
    parser_version: Mapped[str | None] = mapped_column(String(64))
    confidence_score: Mapped[int | None] = mapped_column(Integer)
    confidence_basis_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    artifact_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    conversation_key: Mapped[str | None] = mapped_column(String(255), index=True)
    contact_key: Mapped[str | None] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    case = relationship("Case", back_populates="evidence_events")
    device = relationship("Device", back_populates="evidence_events")
