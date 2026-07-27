"""Typed evidence-integrity domain contracts for WP-0250."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class EvidenceLifecycle(str, Enum):
    REGISTERED = "REGISTERED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    HASH_VERIFIED = "HASH_VERIFIED"
    PROCESSING = "PROCESSING"
    DERIVED_RECORDS_CREATED = "DERIVED_RECORDS_CREATED"
    REPORTABLE = "REPORTABLE"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


class IntegrityState(str, Enum):
    UNKNOWN = "UNKNOWN"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    SOURCE_UNSTABLE = "SOURCE_UNSTABLE"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class LockState(str, Enum):
    UNLOCKED = "UNLOCKED"
    LOCKED = "LOCKED"


class AccessIntent(str, Enum):
    INSPECT_METADATA = "INSPECT_METADATA"
    COMPUTE_HASH = "COMPUTE_HASH"
    CREATE_CONTROLLED_COPY = "CREATE_CONTROLLED_COPY"
    INSPECT_CONTROLLED_COPY = "INSPECT_CONTROLLED_COPY"
    VERIFY_INTEGRITY = "VERIFY_INTEGRITY"
    PARSE_CONTROLLED_COPY = "PARSE_CONTROLLED_COPY"
    ARCHIVE = "ARCHIVE"


class AuditEventType(str, Enum):
    EVIDENCE_REGISTERED = "EVIDENCE_REGISTERED"
    EVIDENCE_VALIDATION_STARTED = "EVIDENCE_VALIDATION_STARTED"
    EVIDENCE_VALIDATION_COMPLETED = "EVIDENCE_VALIDATION_COMPLETED"
    EVIDENCE_VALIDATION_FAILED = "EVIDENCE_VALIDATION_FAILED"
    HASH_COMPUTED = "HASH_COMPUTED"
    HASH_VERIFIED = "HASH_VERIFIED"
    HASH_MISMATCH = "HASH_MISMATCH"
    CONTROLLED_COPY_CREATED = "CONTROLLED_COPY_CREATED"
    CONTROLLED_COPY_VERIFIED = "CONTROLLED_COPY_VERIFIED"
    CONTROLLED_COPY_RELEASED = "CONTROLLED_COPY_RELEASED"
    CONTROLLED_COPY_CLEANUP_FAILED = "CONTROLLED_COPY_CLEANUP_FAILED"
    EVIDENCE_LOCK_ACQUIRED = "EVIDENCE_LOCK_ACQUIRED"
    EVIDENCE_LOCK_RELEASED = "EVIDENCE_LOCK_RELEASED"
    EVIDENCE_LOCK_DENIED = "EVIDENCE_LOCK_DENIED"
    LIFECYCLE_TRANSITION = "LIFECYCLE_TRANSITION"
    LIFECYCLE_TRANSITION_DENIED = "LIFECYCLE_TRANSITION_DENIED"
    PARSER_EXECUTION_STARTED = "PARSER_EXECUTION_STARTED"
    PARSER_EXECUTION_COMPLETED = "PARSER_EXECUTION_COMPLETED"
    PARSER_EXECUTION_FAILED = "PARSER_EXECUTION_FAILED"
    NORMALIZED_RECORD_CREATED = "NORMALIZED_RECORD_CREATED"
    PROVENANCE_LINK_CREATED = "PROVENANCE_LINK_CREATED"
    PROVENANCE_VALIDATION_FAILED = "PROVENANCE_VALIDATION_FAILED"
    INTEGRITY_POLICY_BLOCKED = "INTEGRITY_POLICY_BLOCKED"
    EXPORT_CREATED = "EXPORT_CREATED"
    REPORT_CREATED = "REPORT_CREATED"
    AI_RETRIEVAL_PERFORMED = "AI_RETRIEVAL_PERFORMED"
    ARCHIVE_COMPLETED = "ARCHIVE_COMPLETED"
    SYSTEM_FAILURE = "SYSTEM_FAILURE"


class ProvenanceNodeType(str, Enum):
    TENANT = "TENANT"
    CASE = "CASE"
    EVIDENCE_SOURCE = "EVIDENCE_SOURCE"
    SOURCE_ARTIFACT = "SOURCE_ARTIFACT"
    CONTROLLED_COPY = "CONTROLLED_COPY"
    PROCESSING_RUN = "PROCESSING_RUN"
    PARSER_EXECUTION = "PARSER_EXECUTION"
    NORMALIZED_RECORD = "NORMALIZED_RECORD"
    TIMELINE_EVENT = "TIMELINE_EVENT"
    REPORT_CITATION = "REPORT_CITATION"
    AI_CITATION = "AI_CITATION"
    EXPORT = "EXPORT"


class ProvenanceRelationship(str, Enum):
    BELONGS_TO = "BELONGS_TO"
    DERIVED_FROM = "DERIVED_FROM"
    COPIED_FROM = "COPIED_FROM"
    HASHED_AS = "HASHED_AS"
    PROCESSED_BY = "PROCESSED_BY"
    CREATED_BY = "CREATED_BY"
    NORMALIZED_FROM = "NORMALIZED_FROM"
    CITED_BY = "CITED_BY"
    INCLUDED_IN = "INCLUDED_IN"
    SUPERSEDES = "SUPERSEDES"


@dataclass(frozen=True, slots=True)
class EvidenceObject:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    evidence_uuid: UUID
    evidence_kind: str
    source_type: str
    source_locator: str
    logical_identifier: str
    intake_method: str
    registered_at: datetime
    registered_by_actor_id: UUID
    provenance_node_id: UUID
    parent_evidence_uuid: UUID | None = None
    processing_run_id: UUID | None = None
    integrity_state: IntegrityState = IntegrityState.UNKNOWN
    lifecycle_state: EvidenceLifecycle = EvidenceLifecycle.REGISTERED
    lock_state: LockState = LockState.UNLOCKED
    current_hash_set_id: UUID | None = None
    last_verified_at: datetime | None = None
    version: int = 1

    def __post_init__(self) -> None:
        for value in (self.evidence_kind, self.source_type, self.source_locator, self.logical_identifier, self.intake_method):
            if not value.strip():
                raise ValueError("Evidence identity fields must be nonempty.")
        if self.registered_at.tzinfo is None:
            raise ValueError("Registration timestamp must be timezone-aware.")
        if self.version < 1:
            raise ValueError("Evidence version must be positive.")


def register_evidence(**values) -> EvidenceObject:
    """Create a path/content-independent application UUIDv4 identity."""
    now = values.pop("registered_at", datetime.now(timezone.utc))
    return EvidenceObject(
        evidence_uuid=values.pop("evidence_uuid", uuid4()),
        provenance_node_id=values.pop("provenance_node_id", uuid4()),
        registered_at=now,
        **values,
    )


@dataclass(frozen=True, slots=True)
class HashObservation:
    observation_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_uuid: UUID
    algorithm: str
    digest: str | None
    byte_length: int
    purpose: str
    observed_at: datetime
    actor_id: UUID
    component: str
    component_version: str
    role: str
    success: bool
    failure_code: str | None = None
    related_audit_event_id: UUID | None = None
    superseded_by_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: UUID
    sequence: int
    tenant_id: UUID
    case_id: UUID
    evidence_uuid: UUID
    event_type: AuditEventType
    actor_id: UUID
    occurred_at: datetime
    result: str
    correlation_id: UUID
    failure_code: str | None = None


@dataclass(frozen=True, slots=True)
class CustodyEvent:
    event_id: UUID
    sequence: int
    tenant_id: UUID
    case_id: UUID
    evidence_uuid: UUID
    actor_id: UUID
    actor_type: str
    action_type: str
    occurred_at: datetime
    timezone_representation: str
    component: str
    component_version: str
    environment_id: str
    purpose: str
    result: str
    correlation_id: UUID
    prior_event_id: UUID | None = None
    before_hash_id: UUID | None = None
    after_hash_id: UUID | None = None
    related_audit_event_id: UUID | None = None
    failure_code: str | None = None
    failure_detail: str | None = None


@dataclass(frozen=True, slots=True)
class ProvenanceNode:
    node_id: UUID
    tenant_id: UUID
    case_id: UUID
    node_type: ProvenanceNodeType
    stable_locator: str


@dataclass(frozen=True, slots=True)
class ProvenanceEdge:
    edge_id: UUID
    tenant_id: UUID
    case_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    relationship: ProvenanceRelationship
    parser_id: str | None = None
    parser_version: str | None = None


@dataclass(frozen=True, slots=True)
class ProvenanceValidationReport:
    valid: bool
    failures: tuple[str, ...] = field(default_factory=tuple)
