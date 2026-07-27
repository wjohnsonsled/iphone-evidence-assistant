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

__all__ = [
    "AppleBackupValidator",
    "AppleBackupInputAdapter",
    "BackupValidationOutcome",
    "BackupValidationResult",
    "CleanupStatus",
    "ControlledCopyError",
    "ControlledCopyManager",
    "ControlledSQLiteCopy",
    "InputAdapterStatus",
    "InputInspectionIssue",
    "InputInspectionResult",
    "SQLiteStructuralObservation",
]
