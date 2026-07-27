"""Supported-boundary evidence intake contracts."""

from app.intake.apple_backup import (
    AppleBackupInputAdapter,
    InputAdapterStatus,
    InputInspectionIssue,
    InputInspectionResult,
)
from app.intake.controlled_copy import (
    CleanupStatus,
    ControlledCopyError,
    ControlledCopyManager,
    ControlledSQLiteCopy,
    SQLiteStructuralObservation,
)

__all__ = [
    "AppleBackupInputAdapter",
    "CleanupStatus",
    "ControlledCopyError",
    "ControlledCopyManager",
    "ControlledSQLiteCopy",
    "InputAdapterStatus",
    "InputInspectionIssue",
    "InputInspectionResult",
    "SQLiteStructuralObservation",
]
