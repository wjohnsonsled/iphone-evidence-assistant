"""Additive relational persistence models for candidate integrity infrastructure."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IntegrityEvidenceObject(Base):
    __tablename__ = "integrity_evidence_objects"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    case_id: Mapped[UUID] = mapped_column(index=True)
    evidence_source_id: Mapped[UUID] = mapped_column(index=True)
    evidence_uuid: Mapped[UUID] = mapped_column(unique=True, index=True)
    parent_evidence_uuid: Mapped[UUID | None]
    evidence_kind: Mapped[str] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(64))
    source_locator: Mapped[str] = mapped_column(Text)
    logical_identifier: Mapped[str] = mapped_column(String(255))
    intake_method: Mapped[str] = mapped_column(String(128))
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registered_by_actor_id: Mapped[UUID]
    integrity_state: Mapped[str] = mapped_column(String(64))
    lifecycle_state: Mapped[str] = mapped_column(String(64))
    lock_state: Mapped[str] = mapped_column(String(64))
    provenance_node_id: Mapped[UUID]
    version: Mapped[int] = mapped_column(Integer, default=1)


class IntegrityHashObservation(Base):
    __tablename__ = "integrity_hash_observations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    case_id: Mapped[UUID] = mapped_column(index=True)
    evidence_uuid: Mapped[UUID] = mapped_column(index=True)
    algorithm: Mapped[str] = mapped_column(String(32))
    digest: Mapped[str | None] = mapped_column(String(128))
    byte_length: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(String(128))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_id: Mapped[UUID]
    component: Mapped[str] = mapped_column(String(128))
    component_version: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(64))
    success: Mapped[bool] = mapped_column(Boolean)
    failure_code: Mapped[str | None] = mapped_column(String(128))


class IntegrityAuditEvent(Base):
    __tablename__ = "integrity_audit_events"
    __table_args__ = (UniqueConstraint("tenant_id", "sequence", name="uq_integrity_audit_tenant_sequence"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    case_id: Mapped[UUID] = mapped_column(index=True)
    evidence_uuid: Mapped[UUID] = mapped_column(index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(128))
    actor_id: Mapped[UUID]
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    result: Mapped[str] = mapped_column(String(64))
    correlation_id: Mapped[UUID]
    failure_code: Mapped[str | None] = mapped_column(String(128))


class IntegrityCustodyEvent(Base):
    __tablename__ = "integrity_custody_events"
    __table_args__ = (UniqueConstraint("evidence_uuid", "sequence", name="uq_integrity_custody_evidence_sequence"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    case_id: Mapped[UUID] = mapped_column(index=True)
    evidence_uuid: Mapped[UUID] = mapped_column(index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    prior_event_id: Mapped[UUID | None]
    actor_id: Mapped[UUID]
    actor_type: Mapped[str] = mapped_column(String(64))
    action_type: Mapped[str] = mapped_column(String(128))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    component: Mapped[str] = mapped_column(String(128))
    component_version: Mapped[str] = mapped_column(String(64))
    environment_id: Mapped[str] = mapped_column(String(128))
    purpose: Mapped[str] = mapped_column(String(255))
    result: Mapped[str] = mapped_column(String(64))
    correlation_id: Mapped[UUID]
    failure_code: Mapped[str | None] = mapped_column(String(128))
    failure_detail: Mapped[str | None] = mapped_column(Text)


class IntegrityProvenanceNode(Base):
    __tablename__ = "integrity_provenance_nodes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    case_id: Mapped[UUID] = mapped_column(index=True)
    node_type: Mapped[str] = mapped_column(String(64))
    stable_locator: Mapped[str] = mapped_column(Text)


class IntegrityProvenanceEdge(Base):
    __tablename__ = "integrity_provenance_edges"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    case_id: Mapped[UUID] = mapped_column(index=True)
    source_node_id: Mapped[UUID] = mapped_column(index=True)
    target_node_id: Mapped[UUID] = mapped_column(index=True)
    relationship: Mapped[str] = mapped_column(String(64))
    parser_id: Mapped[str | None] = mapped_column(String(128))
    parser_version: Mapped[str | None] = mapped_column(String(64))
