from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from app.integrity.domain import AuditEventType, register_evidence
from app.integrity.services import AppendOnlyAuditService, HashRegistry


def _evidence():
    return register_evidence(
        tenant_id=uuid4(),
        case_id=uuid4(),
        evidence_source_id=uuid4(),
        evidence_kind="SOURCE_FILE",
        source_type="SYNTHETIC_APPLE_BACKUP_CANDIDATE",
        source_locator="candidate/Manifest.db",
        logical_identifier="synthetic-manifest",
        intake_method="SYNTHETIC_TEST",
        registered_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
        registered_by_actor_id=uuid4(),
    )


def test_intake_adopts_shared_hash_registry_with_complete_provenance(tmp_path):
    content = b"deterministic synthetic manifest bytes"
    source = tmp_path / "Manifest.db"
    source.write_bytes(content)
    before = source.stat()
    actor_id, correlation_id = uuid4(), uuid4()
    item = _evidence()
    audit = AppendOnlyAuditService()

    observation = HashRegistry(audit).compute(
        source,
        item,
        purpose="intake_registration",
        role="source_manifest",
        actor_id=actor_id,
        correlation_id=correlation_id,
        component_version="1.0.0",
    )

    after = source.stat()
    assert observation.success
    assert observation.algorithm == "SHA-256"
    assert observation.digest == hashlib.sha256(content).hexdigest()
    assert observation.byte_length == len(content)
    assert (
        observation.tenant_id,
        observation.case_id,
        observation.evidence_uuid,
    ) == (item.tenant_id, item.case_id, item.evidence_uuid)
    assert observation.purpose == "intake_registration"
    assert observation.role == "source_manifest"
    assert observation.actor_id == actor_id
    assert observation.component == "integrity.hash_registry"
    assert observation.component_version == "1.0.0"
    assert observation.observed_at.tzinfo is not None
    assert source.read_bytes() == content
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    assert audit.events[-1].event_type is AuditEventType.HASH_COMPUTED
    assert audit.events[-1].correlation_id == correlation_id


def test_intake_hash_failure_is_an_immutable_observation_and_audited(tmp_path):
    item = _evidence()
    audit = AppendOnlyAuditService()
    registry = HashRegistry(audit)

    first = registry.compute(
        tmp_path / "missing.db",
        item,
        purpose="intake_registration",
        role="source_manifest",
        actor_id=uuid4(),
        correlation_id=uuid4(),
    )
    second = registry.compute(
        tmp_path / "also-missing.db",
        item,
        purpose="intake_verification",
        role="source_manifest",
        actor_id=uuid4(),
        correlation_id=uuid4(),
    )

    assert not first.success and first.digest is None
    assert first.failure_code == "hash_failed"
    assert first.observation_id != second.observation_id
    assert registry.observations == (first, second)
    assert [event.event_type for event in audit.events] == [
        AuditEventType.SYSTEM_FAILURE,
        AuditEventType.SYSTEM_FAILURE,
    ]
    assert all(event.result == "FAILED" for event in audit.events)

