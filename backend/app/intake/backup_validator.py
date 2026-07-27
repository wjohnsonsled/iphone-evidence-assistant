"""Isolated DEV-0202 Apple local-backup structure validator.

This module classifies synthetic compatibility-profile observations only. It
does not parse artifact rows, expose an API, or establish input support.
"""

from __future__ import annotations

import hashlib
import json
import plistlib
import sqlite3
import stat
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from app.intake.apple_backup import InputAdapterStatus, InputInspectionResult
from app.intake.controlled_copy import ControlledCopyError, ControlledCopyManager

VALIDATOR_NAME = "apple_local_backup_structure_validator"
VALIDATOR_VERSION = "1.0.0"
REQUIRED_FILES = ("Manifest.db", "Manifest.plist", "Info.plist", "Status.plist")
PLIST_NAMES = REQUIRED_FILES[1:]
RECOGNIZED_FIELDS = {
    "Manifest.plist": ("IsEncrypted",),
    "Info.plist": ("Product Version", "Target Identifier", "Unique Identifier"),
    "Status.plist": ("SnapshotState",),
}
LIMITATIONS = (
    "Structural validity does not establish evidentiary completeness.",
    "Candidate identity does not establish artifact or input support.",
    "Synthetic compatibility characterization is not production validation.",
    "No artifact content or encrypted database content was parsed.",
)
Clock = Callable[[], datetime]
PlistReader = Callable[[Path], Any]


class BackupValidationOutcome(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    APPLE_BACKUP_VALIDATION_FAILED = "APPLE_BACKUP_VALIDATION_FAILED"
    NOT_AN_APPLE_BACKUP = "NOT_AN_APPLE_BACKUP"
    APPLE_BACKUP_INCOMPLETE = "APPLE_BACKUP_INCOMPLETE"
    APPLE_BACKUP_INDETERMINATE = "APPLE_BACKUP_INDETERMINATE"
    APPLE_BACKUP_CORRUPT = "APPLE_BACKUP_CORRUPT"
    APPLE_BACKUP_UNSUPPORTED_VERSION = "APPLE_BACKUP_UNSUPPORTED_VERSION"
    APPLE_BACKUP_ENCRYPTED = "APPLE_BACKUP_ENCRYPTED"
    APPLE_BACKUP_UNENCRYPTED = "APPLE_BACKUP_UNENCRYPTED"


@dataclass(frozen=True, slots=True)
class ValidationObservation:
    code: str
    source_locator: str
    value: Any


@dataclass(frozen=True, slots=True)
class BackupValidationResult:
    outcome: BackupValidationOutcome
    explanation: str
    observations: tuple[ValidationObservation, ...]
    provenance: dict[str, Any]
    limitations: tuple[str, ...]
    validated_at: datetime
    correlation_id: UUID
    schema_description: dict[str, Any] | None = None
    schema_fingerprint_sha256: str | None = None
    controlled_copy_audit: dict[str, Any] | None = None

    def to_audit_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["outcome"] = self.outcome.value
        data["validated_at"] = self.validated_at.isoformat()
        data["correlation_id"] = str(self.correlation_id)
        return data

    def canonical_json(self) -> str:
        return json.dumps(self.to_audit_dict(), sort_keys=True, separators=(",", ":"))


class AppleBackupValidator:
    def __init__(
        self,
        copy_manager: ControlledCopyManager,
        *,
        clock: Clock | None = None,
        plist_reader: PlistReader | None = None,
    ) -> None:
        self._copy_manager = copy_manager
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._plist_reader = plist_reader or _read_plist

    def validate(self, inspection: InputInspectionResult) -> BackupValidationResult:
        observations: list[ValidationObservation] = []
        validated_at = self._validated_at()
        base = dict(
            observations=observations,
            provenance={
                "validator_name": VALIDATOR_NAME,
                "validator_version": VALIDATOR_VERSION,
                "adapter": inspection.to_audit_dict(),
            },
            validated_at=validated_at,
            correlation_id=inspection.correlation_id,
        )
        if not inspection.is_ready or not inspection.resolved_path or not inspection.evidence_root:
            return self._result(BackupValidationOutcome.INVALID_INPUT, "Input adapter did not provide a valid ready directory.", **base)

        root = Path(inspection.resolved_path)
        manifest = root / "Manifest.db"
        present: dict[str, bool] = {}
        try:
            for name in REQUIRED_FILES:
                path = root / name
                present[name] = path.exists() and stat.S_ISREG(path.lstat().st_mode)
                observations.append(ValidationObservation("required_file_present", name, present[name]))
        except OSError:
            return self._result(BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED, "Required-file metadata could not be inspected.", **base)

        parsed: dict[str, dict[str, Any]] = {}
        malformed: set[str] = set()
        operational_failure = False
        for name in PLIST_NAMES:
            if not present[name]:
                continue
            try:
                value = self._plist_reader(root / name)
                if not isinstance(value, dict):
                    malformed.add(name)
                else:
                    parsed[name] = value
            except (plistlib.InvalidFileException, ValueError, TypeError):
                malformed.add(name)
            except OSError:
                operational_failure = True

        if operational_failure:
            return self._result(BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED, "A required identity plist could not be safely read.", **base)

        identity_fields = tuple(
            f"{name}:{key}"
            for name, values in parsed.items()
            for key in RECOGNIZED_FIELDS[name]
            if key in values
        )
        identity = present["Manifest.db"] and any(present[name] for name in PLIST_NAMES) and bool(identity_fields)
        observations.append(ValidationObservation("recognized_identity_fields", ".", identity_fields))
        observations.append(ValidationObservation("independent_identity_established", ".", identity))

        if not present["Manifest.db"]:
            return self._result(BackupValidationOutcome.NOT_AN_APPLE_BACKUP, "Manifest.db is absent; minimum candidate identity is not established.", **base)
        if not identity:
            if malformed or parsed:
                outcome = BackupValidationOutcome.APPLE_BACKUP_INDETERMINATE if malformed and not parsed else BackupValidationOutcome.NOT_AN_APPLE_BACKUP
                return self._result(outcome, "Readable plist observations did not establish Apple-backup identity.", **base)
            return self._result(BackupValidationOutcome.NOT_AN_APPLE_BACKUP, "No independent Apple-backup identity evidence was found.", **base)

        missing = tuple(name for name in REQUIRED_FILES if not present[name])
        if missing:
            observations.append(ValidationObservation("missing_required_files", ".", missing))
            return self._result(BackupValidationOutcome.APPLE_BACKUP_INCOMPLETE, "Candidate identity exists but required top-level files are missing.", **base)
        if malformed:
            observations.append(ValidationObservation("malformed_required_plists", ".", tuple(sorted(malformed))))
            return self._result(BackupValidationOutcome.APPLE_BACKUP_CORRUPT, "A present required plist is structurally invalid.", **base)

        status = parsed["Status.plist"].get("SnapshotState")
        if status is None or not isinstance(status, str):
            return self._result(BackupValidationOutcome.APPLE_BACKUP_INDETERMINATE, "SnapshotState is missing or cannot be interpreted.", **base)
        if status != "finished":
            return self._result(BackupValidationOutcome.APPLE_BACKUP_INCOMPLETE, "SnapshotState does not report a finished backup.", **base)

        encryption = parsed["Manifest.plist"].get("IsEncrypted")
        if type(encryption) is not bool:
            return self._result(BackupValidationOutcome.APPLE_BACKUP_INDETERMINATE, "IsEncrypted is missing or is not Boolean.", **base)
        observations.append(ValidationObservation("encryption_state_observed", "Manifest.plist:IsEncrypted", encryption))

        controlled = None
        try:
            controlled = self._copy_manager.create(
                manifest,
                evidence_source_root=Path(inspection.evidence_root),
                correlation_id=inspection.correlation_id,
            )
            with controlled:
                schema, fingerprint, integrity = _inspect_manifest(controlled.read_only_uri)
                controlled.verify_working_files()
        except ControlledCopyError:
            audit = controlled.audit.to_dict() if controlled else None
            return self._result(BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED, "Controlled-copy or SQLite inspection failed operationally.", controlled_copy_audit=audit, **base)
        except sqlite3.DatabaseError:
            audit = controlled.audit.to_dict() if controlled else None
            return self._result(BackupValidationOutcome.APPLE_BACKUP_CORRUPT, "Manifest.db is not a structurally valid SQLite database.", controlled_copy_audit=audit, **base)

        audit = controlled.audit.to_dict()
        if integrity != ("ok",):
            return self._result(BackupValidationOutcome.APPLE_BACKUP_CORRUPT, "SQLite integrity check reported structural failure.", schema_description=schema, schema_fingerprint_sha256=fingerprint, controlled_copy_audit=audit, **base)
        files = next((table for table in schema["tables"] if table["name"] == "files"), None)
        required_columns = {"fileid", "domain", "relativepath", "flags", "file"}
        if files is None or not required_columns.issubset({column["name"] for column in files["columns"]}):
            return self._result(BackupValidationOutcome.APPLE_BACKUP_UNSUPPORTED_VERSION, "Manifest.db does not match MANIFEST_FILES_V1.", schema_description=schema, schema_fingerprint_sha256=fingerprint, controlled_copy_audit=audit, **base)
        outcome = BackupValidationOutcome.APPLE_BACKUP_ENCRYPTED if encryption else BackupValidationOutcome.APPLE_BACKUP_UNENCRYPTED
        return self._result(outcome, "Candidate passed the approved synthetic structural compatibility profile.", schema_description=schema, schema_fingerprint_sha256=fingerprint, controlled_copy_audit=audit, **base)

    def _validated_at(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Validator clock must be timezone-aware.")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _result(outcome: BackupValidationOutcome, explanation: str, *, observations: list[ValidationObservation], schema_description=None, schema_fingerprint_sha256=None, controlled_copy_audit=None, **kwargs) -> BackupValidationResult:
        return BackupValidationResult(outcome, explanation, tuple(observations), limitations=LIMITATIONS, schema_description=schema_description, schema_fingerprint_sha256=schema_fingerprint_sha256, controlled_copy_audit=controlled_copy_audit, **kwargs)


def _read_plist(path: Path) -> Any:
    with path.open("rb") as stream:
        return plistlib.load(stream)


def _inspect_manifest(uri: str) -> tuple[dict[str, Any], str, tuple[str, ...]]:
    connection = sqlite3.connect(uri, uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        integrity = tuple(str(row[0]) for row in connection.execute("PRAGMA integrity_check"))
        tables = []
        names = [str(row[0]) for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table_name in names:
            quoted = table_name.replace('"', '""')
            columns = [
                {"name": str(row[1]).casefold(), "type": str(row[2]).casefold(), "not_null": bool(row[3]), "primary_key_position": int(row[5])}
                for row in connection.execute(f'PRAGMA table_info("{quoted}")')
            ]
            indexes = []
            for index_row in connection.execute(f'PRAGMA index_list("{quoted}")'):
                index_name = str(index_row[1])
                index_quoted = index_name.replace('"', '""')
                index_columns = sorted(str(row[2]).casefold() for row in connection.execute(f'PRAGMA index_info("{index_quoted}")'))
                indexes.append({"name": index_name.casefold(), "unique": bool(index_row[2]), "columns": index_columns})
            tables.append({"name": table_name.casefold(), "columns": sorted(columns, key=lambda item: item["name"]), "indexes": sorted(indexes, key=lambda item: item["name"])})
        schema = {"tables": sorted(tables, key=lambda item: item["name"])}
        encoded = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return schema, hashlib.sha256(encoded).hexdigest(), integrity
    finally:
        connection.close()
