from __future__ import annotations

import hashlib
import plistlib
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.integrity.domain import (
    AuditEventType,
    IntegrityState,
    ProvenanceEdge,
    ProvenanceNode,
    ProvenanceNodeType,
    ProvenanceRelationship,
    register_evidence,
)
from app.integrity.services import (
    AppendOnlyAuditService,
    HashRegistry,
    ProvenanceService,
)
from app.intake.apple_backup import AppleBackupInputAdapter, InputAdapterStatus
from app.intake.backup_validator import AppleBackupValidator, BackupValidationOutcome
from app.intake.controlled_copy import ControlledCopyManager
from app.support.registry import create_supported_registry
from tests.support.resource_policy import TEST_RESOURCE_POLICY


NOW = datetime(2026, 7, 28, 21, 0, tzinfo=timezone.utc)


def _plist(path: Path, value: dict) -> None:
    with path.open("wb") as stream:
        plistlib.dump(value, stream)


def _candidate(root: Path, *, encrypted: bool) -> Path:
    candidate = root / "candidate"
    candidate.mkdir()
    _plist(candidate / "Info.plist", {"Product Version": "synthetic"})
    _plist(candidate / "Manifest.plist", {"IsEncrypted": encrypted})
    _plist(candidate / "Status.plist", {"SnapshotState": "finished"})
    connection = sqlite3.connect(candidate / "Manifest.db")
    connection.execute(
        "CREATE TABLE Files(fileID TEXT, domain TEXT, relativePath TEXT, "
        "flags INTEGER, file BLOB)"
    )
    connection.commit()
    connection.close()
    return candidate


@pytest.mark.parametrize(
    ("encrypted", "expected"),
    [
        (False, BackupValidationOutcome.APPLE_BACKUP_UNENCRYPTED),
        (True, BackupValidationOutcome.APPLE_BACKUP_ENCRYPTED),
    ],
)
def test_candidate_intake_flow_is_integrity_provenance_and_failure_aware(
    tmp_path,
    encrypted,
    expected,
):
    evidence_root = tmp_path / "evidence"
    workspace_root = tmp_path / "work"
    evidence_root.mkdir()
    workspace_root.mkdir()
    candidate = _candidate(evidence_root, encrypted=encrypted)
    source_before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in candidate.iterdir()
    }
    tenant_id, case_id, actor_id, correlation_id = (
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
    )

    inspection = AppleBackupInputAdapter(
        [evidence_root],
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: NOW,
    ).inspect(candidate, correlation_id=correlation_id)
    assert inspection.status is InputAdapterStatus.READY_FOR_STRUCTURE_VALIDATION

    evidence = register_evidence(
        tenant_id=tenant_id,
        case_id=case_id,
        evidence_source_id=uuid4(),
        evidence_kind="APPLE_BACKUP_CANDIDATE",
        source_type="APPLE_LOCAL_BACKUP_CANDIDATE",
        source_locator=inspection.source_locator,
        logical_identifier="synthetic-candidate",
        intake_method="SYNTHETIC_TEST",
        registered_at=NOW,
        registered_by_actor_id=actor_id,
    )
    audit = AppendOnlyAuditService()
    audit.append(
        evidence=evidence,
        event_type=AuditEventType.EVIDENCE_REGISTERED,
        actor_id=actor_id,
        result="SUCCEEDED",
        correlation_id=correlation_id,
    )
    audit.append(
        evidence=evidence,
        event_type=AuditEventType.EVIDENCE_VALIDATION_STARTED,
        actor_id=actor_id,
        result="STARTED",
        correlation_id=correlation_id,
    )
    hashes = HashRegistry(audit)
    baseline = hashes.compute(
        candidate / "Manifest.db",
        evidence,
        purpose="intake_registration",
        role="source_manifest",
        actor_id=actor_id,
        correlation_id=correlation_id,
    )

    result = AppleBackupValidator(
        ControlledCopyManager(
            workspace_root=workspace_root,
            resource_policy=TEST_RESOURCE_POLICY,
        ),
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: NOW,
    ).validate(inspection)
    assert result.outcome is expected
    assert result.controlled_copy_audit["verification_status"] == "VERIFIED"
    assert result.controlled_copy_audit["cleanup_status"] == "SUCCEEDED"
    assert not Path(result.controlled_copy_audit["workspace_path"]).exists()

    checkpoint = hashes.compute(
        candidate / "Manifest.db",
        evidence,
        purpose="post_validation",
        role="source_manifest",
        actor_id=actor_id,
        correlation_id=correlation_id,
    )
    assert (
        hashes.verify(
            baseline,
            checkpoint,
            evidence,
            actor_id=actor_id,
            correlation_id=correlation_id,
        )
        is IntegrityState.VERIFIED
    )
    audit.append(
        evidence=evidence,
        event_type=AuditEventType.EVIDENCE_VALIDATION_COMPLETED,
        actor_id=actor_id,
        result=result.outcome.value,
        correlation_id=correlation_id,
    )

    provenance = ProvenanceService()
    source = ProvenanceNode(
        evidence.provenance_node_id,
        tenant_id,
        case_id,
        ProvenanceNodeType.EVIDENCE_SOURCE,
        f"evidence-source:{inspection.source_locator}",
    )
    artifact = ProvenanceNode(
        uuid4(),
        tenant_id,
        case_id,
        ProvenanceNodeType.SOURCE_ARTIFACT,
        "source:Manifest.db",
    )
    controlled = ProvenanceNode(
        uuid4(),
        tenant_id,
        case_id,
        ProvenanceNodeType.CONTROLLED_COPY,
        f"working:{result.controlled_copy_audit['workspace_path']}/Manifest.db",
    )
    for node in (source, artifact, controlled):
        provenance.add_node(node)
    provenance.add_edge(
        ProvenanceEdge(
            uuid4(),
            tenant_id,
            case_id,
            artifact.node_id,
            source.node_id,
            ProvenanceRelationship.BELONGS_TO,
        )
    )
    provenance.add_edge(
        ProvenanceEdge(
            uuid4(),
            tenant_id,
            case_id,
            controlled.node_id,
            artifact.node_id,
            ProvenanceRelationship.COPIED_FROM,
        )
    )
    assert provenance.validate_path(controlled.node_id, source.node_id).valid
    assert all(event.correlation_id == correlation_id for event in audit.events)
    assert source_before == {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in candidate.iterdir()
    }
    assert create_supported_registry().entries == ()


def test_zero_result_missing_and_resource_denial_remain_distinct(tmp_path):
    root = tmp_path / "evidence"
    empty = root / "empty"
    root.mkdir()
    empty.mkdir()
    adapter = AppleBackupInputAdapter(
        [root],
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: NOW,
    )
    zero = adapter.inspect(empty, correlation_id=uuid4())
    missing = adapter.inspect(root / "missing", correlation_id=uuid4())
    (empty / "one").write_bytes(b"1")
    (empty / "two").write_bytes(b"2")
    limited = AppleBackupInputAdapter(
        [root],
        resource_policy=replace(
            TEST_RESOURCE_POLICY,
            max_directory_entries=1,
        ),
        clock=lambda: NOW,
    ).inspect(empty, correlation_id=uuid4())

    assert zero.status is InputAdapterStatus.READY_ZERO_RESULTS
    assert missing.status is InputAdapterStatus.MISSING
    assert limited.status is InputAdapterStatus.VALIDATION_FAILED
    assert limited.issues[0].code == "resource_limit_exceeded"
    assert len({zero.status, missing.status, limited.status}) == 3
    assert create_supported_registry().entries == ()

