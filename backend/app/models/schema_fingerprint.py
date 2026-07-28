from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.types import JSONBType

class SchemaFingerprintObservationModel(Base):
    __tablename__ = "evidence_schema_fingerprint_observations"
    __table_args__ = (CheckConstraint("version > 0", name="ck_schema_fingerprint_version_positive"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_artifact_id: Mapped[UUID] = mapped_column(ForeignKey("supported_source_artifacts.id"), index=True)
    processing_run_id: Mapped[UUID] = mapped_column(ForeignKey("supported_processing_runs.id"), index=True)
    parser_identity_id: Mapped[UUID | None] = mapped_column(ForeignKey("evidence_parser_identities.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String(128), index=True)
    profile_version: Mapped[str] = mapped_column(String(64))
    canonical_input_reference: Mapped[str] = mapped_column(Text)
    sha256_digest: Mapped[str] = mapped_column(String(64), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    limitations: Mapped[list[str]] = mapped_column(JSONBType, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
