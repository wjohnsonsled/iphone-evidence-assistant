"""Supported-boundary evidence intake contracts."""

from app.intake.apple_backup import (
    AppleBackupInputAdapter,
    InputAdapterStatus,
    InputInspectionIssue,
    InputInspectionResult,
)

__all__ = [
    "AppleBackupInputAdapter",
    "InputAdapterStatus",
    "InputInspectionIssue",
    "InputInspectionResult",
]
