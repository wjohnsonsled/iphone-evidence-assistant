from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.integrity.domain import AuditEventType, register_evidence
from app.integrity.services import AppendOnlyAuditService


INTAKE_EVENT_TYPES = {
    AuditEventType.EVIDENCE_REGISTERED,
    AuditEventType.EVIDENCE_VALIDATION_STARTED,
    AuditEventType.EVIDENCE_VALIDATION_COMPLETED,
    AuditEventType.EVIDENCE_VALIDATION_FAILED,
    AuditEventType.HASH_COMPUTED,
    AuditEventType.HASH_VERIFIED,
    AuditEventType.HASH_MISMATCH,
    AuditEventType.CONTROLLED_COPY_CREATED,
    AuditEventType.CONTROLLED_COPY_VERIFIED,
    AuditEventType.CONTROLLED_COPY_RELEASED,
    AuditEventType.CONTROLLED_COPY_CLEANUP_FAILED,
    AuditEventType.LIFECYCLE_TRANSITION,
    AuditEventType.LIFECYCLE_TRANSITION_DENIED,
    AuditEventType.SYSTEM_FAILURE,
}


def _evidence():
    return register_evidence(
        tenant_id=uuid4(),
        case_id=uuid4(),
        evidence_source_id=uuid4(),
        evidence_kind="SOURCE",
        source_type="SYNTHETIC_APPLE_BACKUP_CANDIDATE",
        source_locator="candidate",
        logical_identifier="synthetic-candidate",
        intake_method="SYNTHETIC_TEST",
        registered_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
        registered_by_actor_id=uuid4(),
    )


def test_closed_wp0250_taxonomy_contains_every_intake_event():
    assert INTAKE_EVENT_TYPES <= set(AuditEventType)


def test_intake_audit_history_is_scoped_ordered_immutable_and_failure_aware():
    item, actor, correlation = _evidence(), uuid4(), uuid4()
    service = AppendOnlyAuditService()
    succeeded = service.append(
        evidence=item,
        event_type=AuditEventType.EVIDENCE_VALIDATION_COMPLETED,
        actor_id=actor,
        result="SUCCEEDED",
        correlation_id=correlation,
    )
    failed = service.append(
        evidence=item,
        event_type=AuditEventType.CONTROLLED_COPY_CLEANUP_FAILED,
        actor_id=actor,
        result="FAILED",
        correlation_id=correlation,
        failure_code="working_copy_cleanup_failed",
    )

    assert service.events == (succeeded, failed)
    assert (succeeded.sequence, failed.sequence) == (1, 2)
    assert succeeded.event_id != failed.event_id
    assert (failed.tenant_id, failed.case_id, failed.evidence_uuid) == (
        item.tenant_id,
        item.case_id,
        item.evidence_uuid,
    )
    assert failed.actor_id == actor
    assert failed.correlation_id == correlation
    assert failed.occurred_at.tzinfo is not None
    assert succeeded.failure_code is None
    assert failed.failure_code == "working_copy_cleanup_failed"
    with pytest.raises(FrozenInstanceError):
        failed.result = "SUCCEEDED"

