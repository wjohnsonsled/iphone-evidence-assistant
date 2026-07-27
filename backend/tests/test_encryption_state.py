from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.backup_validator import (
    BackupValidationOutcome,
    BackupValidationResult,
    ValidationObservation,
)
from app.intake.encryption_state import BackupEncryptionState, report_encryption_state

CID = UUID("20000000-0000-0000-0000-000000000003")


def result(outcome, raw=None):
    observations = ()
    if raw is not None:
        observations = (ValidationObservation("encryption_state_observed", "Manifest.plist:IsEncrypted", raw),)
    return BackupValidationResult(
        outcome=outcome,
        explanation="synthetic",
        observations=observations,
        provenance={"validator_name": "validator", "validator_version": "1.0.0"},
        limitations=("candidate only",),
        validated_at=datetime(2026, 7, 27, tzinfo=timezone.utc),
        correlation_id=CID,
    )


@pytest.mark.parametrize("outcome,raw,state,eligible", [
    (BackupValidationOutcome.APPLE_BACKUP_ENCRYPTED, True, BackupEncryptionState.ENCRYPTED, False),
    (BackupValidationOutcome.APPLE_BACKUP_UNENCRYPTED, False, BackupEncryptionState.UNENCRYPTED, True),
    (BackupValidationOutcome.APPLE_BACKUP_INDETERMINATE, None, BackupEncryptionState.INDETERMINATE, False),
    (BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED, None, BackupEncryptionState.FAILED, False),
    (BackupValidationOutcome.APPLE_BACKUP_CORRUPT, None, BackupEncryptionState.NOT_APPLICABLE, False),
])
def test_closed_mapping(outcome, raw, state, eligible):
    report = report_encryption_state(result(outcome, raw))
    assert report.state is state
    assert report.processing_eligible is eligible
    assert report.raw_is_encrypted is raw
    assert report.source_locator == ("Manifest.plist:IsEncrypted" if raw is not None else None)
    assert report.correlation_id == CID


def test_audit_is_deterministic_and_preserves_provenance():
    first = report_encryption_state(result(BackupValidationOutcome.APPLE_BACKUP_ENCRYPTED, True))
    second = report_encryption_state(result(BackupValidationOutcome.APPLE_BACKUP_ENCRYPTED, True))
    assert first.canonical_json() == second.canonical_json()
    assert first.source_validator == "validator"
    assert "support" in " ".join(first.limitations).lower()


def test_module_has_no_prohibited_boundary():
    source = Path(__file__).parents[1] / "app" / "intake" / "encryption_state.py"
    text = source.read_text(encoding="utf-8").lower()
    for prohibited in ("app.api", "legacy", "sqlalchemy", "secondary_indicator"):
        assert prohibited not in text
