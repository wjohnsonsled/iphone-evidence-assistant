"""Supported-boundary evidence intake contracts."""

from app.intake.apple_backup import (
    AppleBackupInputAdapter,
    InputAdapterStatus,
    InputInspectionIssue,
    InputInspectionResult,
)
from app.intake.backup_validator import (
    AppleBackupValidator,
    BackupValidationOutcome,
    BackupValidationResult,
)
from app.intake.controlled_copy import (
    CleanupStatus,
    ControlledCopyError,
    ControlledCopyManager,
    ControlledSQLiteCopy,
    SQLiteStructuralObservation,
)
from app.intake.encryption_state import (
    BackupEncryptionState,
    EncryptionStateReport,
    report_encryption_state,
)

__all__ = [
    "AppleBackupValidator",
    "AppleBackupInputAdapter",
    "BackupValidationOutcome",
    "BackupValidationResult",
    "BackupEncryptionState",
    "CleanupStatus",
    "ControlledCopyError",
    "ControlledCopyManager",
    "ControlledSQLiteCopy",
    "InputAdapterStatus",
    "InputInspectionIssue",
    "InputInspectionResult",
    "EncryptionStateReport",
    "SQLiteStructuralObservation",
    "report_encryption_state",
]
