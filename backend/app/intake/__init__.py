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
    ControlledWorkspaceRecovery,
    RecoveryStatus,
    SQLiteStructuralObservation,
    WorkspaceRecoveryRecord,
    WorkspaceRecoveryReport,
)
from app.intake.encryption_state import (
    BackupEncryptionState,
    EncryptionStateReport,
    report_encryption_state,
)
from app.intake.resource_limits import (
    IntakeResourcePolicy,
    ResourceLimitExceeded,
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
    "ControlledWorkspaceRecovery",
    "InputAdapterStatus",
    "InputInspectionIssue",
    "InputInspectionResult",
    "IntakeResourcePolicy",
    "RecoveryStatus",
    "ResourceLimitExceeded",
    "EncryptionStateReport",
    "SQLiteStructuralObservation",
    "WorkspaceRecoveryRecord",
    "WorkspaceRecoveryReport",
    "report_encryption_state",
]
