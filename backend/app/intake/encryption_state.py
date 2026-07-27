"""DEV-0203 encryption-state reporting projection.

This module does not inspect source files, decrypt backups, accept passwords,
or establish input support.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from app.intake.backup_validator import BackupValidationOutcome, BackupValidationResult


class BackupEncryptionState(str, Enum):
    ENCRYPTED = "ENCRYPTED"
    UNENCRYPTED = "UNENCRYPTED"
    INDETERMINATE = "INDETERMINATE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class EncryptionStateReport:
    state: BackupEncryptionState
    raw_is_encrypted: bool | None
    source_locator: str | None
    processing_eligible: bool
    correlation_id: UUID
    source_validator: str
    source_validator_version: str
    explanation: str
    limitations: tuple[str, ...]

    def to_audit_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        data["correlation_id"] = str(self.correlation_id)
        return data

    def canonical_json(self) -> str:
        return json.dumps(self.to_audit_dict(), sort_keys=True, separators=(",", ":"))


def report_encryption_state(result: BackupValidationResult) -> EncryptionStateReport:
    """Project an already validated result into a closed reporting state."""

    mapping = {
        BackupValidationOutcome.APPLE_BACKUP_ENCRYPTED: BackupEncryptionState.ENCRYPTED,
        BackupValidationOutcome.APPLE_BACKUP_UNENCRYPTED: BackupEncryptionState.UNENCRYPTED,
        BackupValidationOutcome.APPLE_BACKUP_INDETERMINATE: BackupEncryptionState.INDETERMINATE,
        BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED: BackupEncryptionState.FAILED,
    }
    state = mapping.get(result.outcome, BackupEncryptionState.NOT_APPLICABLE)
    observation = next(
        (item for item in result.observations if item.code == "encryption_state_observed"),
        None,
    )
    raw = observation.value if observation is not None and type(observation.value) is bool else None
    locator = observation.source_locator if observation is not None and raw is not None else None
    provenance = result.provenance
    limitations = tuple(result.limitations) + (
        "Encryption detection does not authorize decryption or password handling.",
        "Processing eligibility is a handoff control, not an input-support claim.",
    )
    return EncryptionStateReport(
        state=state,
        raw_is_encrypted=raw,
        source_locator=locator,
        processing_eligible=state is BackupEncryptionState.UNENCRYPTED,
        correlation_id=result.correlation_id,
        source_validator=str(provenance.get("validator_name", "unknown")),
        source_validator_version=str(provenance.get("validator_version", "unknown")),
        explanation=_explanation(state),
        limitations=limitations,
    )


def _explanation(state: BackupEncryptionState) -> str:
    return {
        BackupEncryptionState.ENCRYPTED: "The sole approved validation signal reported an encrypted candidate.",
        BackupEncryptionState.UNENCRYPTED: "The sole approved validation signal reported an unencrypted candidate.",
        BackupEncryptionState.INDETERMINATE: "Validation could not defensibly determine encryption state.",
        BackupEncryptionState.FAILED: "An operational validation failure prevented encryption-state determination.",
        BackupEncryptionState.NOT_APPLICABLE: "The controlling validation outcome does not carry an encryption-state conclusion.",
    }[state]
