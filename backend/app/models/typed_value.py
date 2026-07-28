"""Candidate typed-value ORM metadata; migration deferred to DEV-0410."""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.types import JSONBType

class TypedRepresentationModel(Base):
    __tablename__ = "evidence_typed_representations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    state: Mapped[str] = mapped_column(String(32))
    type_id: Mapped[str] = mapped_column(String(128))
    serialization_profile_id: Mapped[str] = mapped_column(String(128))
    serialization_profile_version: Mapped[str] = mapped_column(String(64))
    serialized_value: Mapped[str | None] = mapped_column(Text)
    failure_code: Mapped[str | None] = mapped_column(String(128))

class TypedValueObservationModel(Base):
    __tablename__ = "evidence_typed_value_observations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_artifact_id: Mapped[UUID] = mapped_column(ForeignKey("supported_source_artifacts.id"), index=True)
    processing_run_id: Mapped[UUID] = mapped_column(ForeignKey("supported_processing_runs.id"), index=True)
    parser_identity_id: Mapped[UUID | None] = mapped_column(ForeignKey("evidence_parser_identities.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_representation_id: Mapped[UUID] = mapped_column(ForeignKey("evidence_typed_representations.id"))
    normalized_representation_id: Mapped[UUID | None] = mapped_column(ForeignKey("evidence_typed_representations.id"))
    transformation_id: Mapped[UUID | None] = mapped_column(ForeignKey("evidence_value_transformations.id"))

class ValueTransformationModel(Base):
    __tablename__ = "evidence_value_transformations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    method_id: Mapped[str] = mapped_column(String(128))
    method_version: Mapped[str] = mapped_column(String(64))
    processing_run_id: Mapped[UUID] = mapped_column(ForeignKey("supported_processing_runs.id"), index=True)
    parser_identity_id: Mapped[UUID | None] = mapped_column(ForeignKey("evidence_parser_identities.id"), index=True)
    transformed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    limitations: Mapped[list[str]] = mapped_column(JSONBType, nullable=False)
