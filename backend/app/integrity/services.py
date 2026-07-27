"""Application-level integrity, lifecycle, custody, audit, and provenance services."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from app.integrity.domain import (
    AccessIntent, AuditEvent, AuditEventType, CustodyEvent, EvidenceLifecycle,
    EvidenceObject, HashObservation, IntegrityState, LockState, ProvenanceEdge,
    ProvenanceNode, ProvenanceRelationship, ProvenanceValidationReport,
)

TRANSITIONS = {
    EvidenceLifecycle.REGISTERED: {EvidenceLifecycle.VALIDATING, EvidenceLifecycle.QUARANTINED, EvidenceLifecycle.REJECTED, EvidenceLifecycle.FAILED},
    EvidenceLifecycle.VALIDATING: {EvidenceLifecycle.VALIDATED, EvidenceLifecycle.QUARANTINED, EvidenceLifecycle.FAILED, EvidenceLifecycle.REJECTED},
    EvidenceLifecycle.VALIDATED: {EvidenceLifecycle.HASH_VERIFIED, EvidenceLifecycle.QUARANTINED, EvidenceLifecycle.FAILED},
    EvidenceLifecycle.HASH_VERIFIED: {EvidenceLifecycle.PROCESSING, EvidenceLifecycle.QUARANTINED, EvidenceLifecycle.FAILED},
    EvidenceLifecycle.PROCESSING: {EvidenceLifecycle.DERIVED_RECORDS_CREATED, EvidenceLifecycle.QUARANTINED, EvidenceLifecycle.FAILED},
    EvidenceLifecycle.DERIVED_RECORDS_CREATED: {EvidenceLifecycle.REPORTABLE, EvidenceLifecycle.QUARANTINED, EvidenceLifecycle.FAILED},
    EvidenceLifecycle.REPORTABLE: {EvidenceLifecycle.ARCHIVED, EvidenceLifecycle.QUARANTINED},
    EvidenceLifecycle.QUARANTINED: set(),
    EvidenceLifecycle.FAILED: {EvidenceLifecycle.QUARANTINED, EvidenceLifecycle.ARCHIVED},
    EvidenceLifecycle.ARCHIVED: set(),
    EvidenceLifecycle.REJECTED: set(),
}


class AppendOnlyAuditService:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def append(self, *, evidence: EvidenceObject, event_type: AuditEventType, actor_id: UUID, result: str, correlation_id: UUID, failure_code: str | None = None) -> AuditEvent:
        event = AuditEvent(uuid4(), len(self._events) + 1, evidence.tenant_id, evidence.case_id, evidence.evidence_uuid, event_type, actor_id, datetime.now(timezone.utc), result, correlation_id, failure_code)
        self._events.append(event)
        return event


class LifecycleService:
    def __init__(self, audit: AppendOnlyAuditService) -> None:
        self.audit = audit

    def transition(self, evidence: EvidenceObject, target: EvidenceLifecycle, *, actor_id: UUID, correlation_id: UUID) -> EvidenceObject:
        if target not in TRANSITIONS[evidence.lifecycle_state]:
            self.audit.append(evidence=evidence, event_type=AuditEventType.LIFECYCLE_TRANSITION_DENIED, actor_id=actor_id, result="DENIED", correlation_id=correlation_id, failure_code="invalid_transition")
            raise ValueError("Lifecycle transition is not permitted.")
        updated = replace(evidence, lifecycle_state=target, version=evidence.version + 1)
        self.audit.append(evidence=updated, event_type=AuditEventType.LIFECYCLE_TRANSITION, actor_id=actor_id, result="SUCCEEDED", correlation_id=correlation_id)
        return updated


class HashRegistry:
    def __init__(self, audit: AppendOnlyAuditService) -> None:
        self._observations: list[HashObservation] = []
        self.audit = audit

    @property
    def observations(self) -> tuple[HashObservation, ...]:
        return tuple(self._observations)

    def compute(self, path: Path, evidence: EvidenceObject, *, purpose: str, role: str, actor_id: UUID, correlation_id: UUID, component_version: str = "1.0.0") -> HashObservation:
        digest = hashlib.sha256()
        length = 0
        try:
            before = path.stat()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
                    length += len(chunk)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError("source_unstable")
            observation = HashObservation(uuid4(), evidence.tenant_id, evidence.case_id, evidence.evidence_uuid, "SHA-256", digest.hexdigest(), length, purpose, datetime.now(timezone.utc), actor_id, "integrity.hash_registry", component_version, role, True)
            event_type = AuditEventType.HASH_COMPUTED
        except (OSError, RuntimeError) as exc:
            code = "source_unstable" if isinstance(exc, RuntimeError) else "hash_failed"
            observation = HashObservation(uuid4(), evidence.tenant_id, evidence.case_id, evidence.evidence_uuid, "SHA-256", None, length, purpose, datetime.now(timezone.utc), actor_id, "integrity.hash_registry", component_version, role, False, code)
            event_type = AuditEventType.SYSTEM_FAILURE
        self._observations.append(observation)
        self.audit.append(evidence=evidence, event_type=event_type, actor_id=actor_id, result="SUCCEEDED" if observation.success else "FAILED", correlation_id=correlation_id, failure_code=observation.failure_code)
        return observation

    def verify(self, expected: HashObservation, current: HashObservation, evidence: EvidenceObject, *, actor_id: UUID, correlation_id: UUID) -> IntegrityState:
        if not expected.success or not current.success:
            state = IntegrityState.SOURCE_UNSTABLE if "source_unstable" in {expected.failure_code, current.failure_code} else IntegrityState.VERIFICATION_FAILED
        elif expected.algorithm != current.algorithm or expected.digest != current.digest or expected.byte_length != current.byte_length:
            state = IntegrityState.MISMATCH
        else:
            state = IntegrityState.VERIFIED
        event_type = AuditEventType.HASH_VERIFIED if state is IntegrityState.VERIFIED else AuditEventType.HASH_MISMATCH
        self.audit.append(evidence=evidence, event_type=event_type, actor_id=actor_id, result=state.value, correlation_id=correlation_id)
        return state


class EvidenceLockService:
    def __init__(self, audit: AppendOnlyAuditService) -> None:
        self._locks: dict[UUID, tuple[UUID, AccessIntent, datetime]] = {}
        self.audit = audit

    def acquire(self, evidence: EvidenceObject, *, actor_id: UUID, intent: AccessIntent, correlation_id: UUID, now: datetime | None = None) -> EvidenceObject:
        if evidence.evidence_uuid in self._locks:
            self.audit.append(evidence=evidence, event_type=AuditEventType.EVIDENCE_LOCK_DENIED, actor_id=actor_id, result="DENIED", correlation_id=correlation_id, failure_code="lock_conflict")
            raise PermissionError("Evidence lock conflict.")
        self._locks[evidence.evidence_uuid] = (actor_id, intent, now or datetime.now(timezone.utc))
        self.audit.append(evidence=evidence, event_type=AuditEventType.EVIDENCE_LOCK_ACQUIRED, actor_id=actor_id, result="SUCCEEDED", correlation_id=correlation_id)
        return replace(evidence, lock_state=LockState.LOCKED)

    def release(self, evidence: EvidenceObject, *, actor_id: UUID, correlation_id: UUID) -> EvidenceObject:
        lock = self._locks.get(evidence.evidence_uuid)
        if lock is None or lock[0] != actor_id:
            raise PermissionError("Only the lock owner may release it.")
        del self._locks[evidence.evidence_uuid]
        self.audit.append(evidence=evidence, event_type=AuditEventType.EVIDENCE_LOCK_RELEASED, actor_id=actor_id, result="SUCCEEDED", correlation_id=correlation_id)
        return replace(evidence, lock_state=LockState.UNLOCKED)

    def release_stale(self, evidence: EvidenceObject, *, older_than: datetime, actor_id: UUID, correlation_id: UUID) -> EvidenceObject:
        lock = self._locks.get(evidence.evidence_uuid)
        if lock is None or lock[2] >= older_than:
            raise PermissionError("No stale lock is eligible for release.")
        del self._locks[evidence.evidence_uuid]
        self.audit.append(evidence=evidence, event_type=AuditEventType.EVIDENCE_LOCK_RELEASED, actor_id=actor_id, result="STALE_RELEASED", correlation_id=correlation_id)
        return replace(evidence, lock_state=LockState.UNLOCKED)


class CustodyService:
    def __init__(self) -> None:
        self._events: list[CustodyEvent] = []

    @property
    def events(self) -> tuple[CustodyEvent, ...]:
        return tuple(self._events)

    def append(self, *, evidence: EvidenceObject, actor_id: UUID, actor_type: str, action_type: str, component: str, component_version: str, environment_id: str, purpose: str, result: str, correlation_id: UUID, related_audit_event_id: UUID | None = None, before_hash_id: UUID | None = None, after_hash_id: UUID | None = None, failure_code: str | None = None, failure_detail: str | None = None) -> CustodyEvent:
        prior = self._events[-1].event_id if self._events and self._events[-1].evidence_uuid == evidence.evidence_uuid else None
        event = CustodyEvent(uuid4(), len(self._events) + 1, evidence.tenant_id, evidence.case_id, evidence.evidence_uuid, actor_id, actor_type, action_type, datetime.now(timezone.utc), "UTC", component, component_version, environment_id, purpose, result, correlation_id, prior, before_hash_id, after_hash_id, related_audit_event_id, failure_code, failure_detail)
        self._events.append(event)
        return event


class ProvenanceService:
    ACYCLIC = {ProvenanceRelationship.DERIVED_FROM, ProvenanceRelationship.COPIED_FROM, ProvenanceRelationship.NORMALIZED_FROM, ProvenanceRelationship.SUPERSEDES}

    def __init__(self) -> None:
        self.nodes: dict[UUID, ProvenanceNode] = {}
        self.edges: list[ProvenanceEdge] = []

    def add_node(self, node: ProvenanceNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError("Duplicate provenance node.")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: ProvenanceEdge) -> None:
        source, target = self.nodes.get(edge.source_node_id), self.nodes.get(edge.target_node_id)
        if source is None or target is None:
            raise ValueError("Dangling provenance edge.")
        if len({source.tenant_id, target.tenant_id, edge.tenant_id}) != 1 or len({source.case_id, target.case_id, edge.case_id}) != 1:
            raise PermissionError("Cross-tenant or cross-case provenance is prohibited.")
        if edge.relationship in self.ACYCLIC and self._reachable(edge.target_node_id, edge.source_node_id):
            raise ValueError("Cyclic derivation is prohibited.")
        if edge.relationship in {ProvenanceRelationship.PROCESSED_BY, ProvenanceRelationship.NORMALIZED_FROM} and (not edge.parser_id or not edge.parser_version):
            raise ValueError("Parser-derived edges require parser identity and version.")
        self.edges.append(edge)

    def validate_path(self, start: UUID, source: UUID) -> ProvenanceValidationReport:
        failures = []
        if start not in self.nodes or source not in self.nodes:
            failures.append("missing_required_node")
        elif self.nodes[start].tenant_id != self.nodes[source].tenant_id:
            failures.append("cross_tenant_path")
        elif not self._reachable(start, source):
            failures.append("source_path_unresolved")
        return ProvenanceValidationReport(not failures, tuple(failures))

    def _reachable(self, start: UUID, target: UUID) -> bool:
        pending, visited = [start], set()
        while pending:
            current = pending.pop()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)
            pending.extend(edge.target_node_id for edge in self.edges if edge.source_node_id == current)
        return False


class MutationDetector:
    """Compare immutable observations and return a new evidence state."""

    def __init__(self, registry: HashRegistry) -> None:
        self.registry = registry

    def evaluate(self, evidence: EvidenceObject, baseline: HashObservation, checkpoint: HashObservation, *, actor_id: UUID, correlation_id: UUID) -> EvidenceObject:
        state = self.registry.verify(baseline, checkpoint, evidence, actor_id=actor_id, correlation_id=correlation_id)
        return replace(
            evidence,
            integrity_state=state,
            last_verified_at=datetime.now(timezone.utc),
            version=evidence.version + 1,
        )
