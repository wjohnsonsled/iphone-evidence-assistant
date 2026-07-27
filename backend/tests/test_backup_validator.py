from __future__ import annotations

import json
import plistlib
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.apple_backup import AppleBackupInputAdapter
from app.intake.backup_validator import AppleBackupValidator, BackupValidationOutcome
from app.intake.controlled_copy import ControlledCopyManager

NOW = datetime(2026, 7, 27, 18, 0, tzinfo=timezone.utc)
CID = UUID("10000000-0000-0000-0000-000000000002")


def write_plist(path: Path, value: dict) -> None:
    with path.open("wb") as stream:
        plistlib.dump(value, stream, sort_keys=True)


def make_backup(
    root: Path,
    *,
    encrypted: object = False,
    snapshot: object = "finished",
    schema: str = "valid",
) -> Path:
    backup = root / "candidate"
    backup.mkdir()
    write_plist(backup / "Info.plist", {"Product Version": "synthetic"})
    write_plist(backup / "Manifest.plist", {} if encrypted is None else {"IsEncrypted": encrypted})
    write_plist(backup / "Status.plist", {} if snapshot is None else {"SnapshotState": snapshot})
    database = backup / "Manifest.db"
    if schema == "invalid":
        database.write_bytes(b"not sqlite")
    else:
        connection = sqlite3.connect(database)
        if schema == "valid":
            connection.execute(
                "CREATE TABLE Files(fileID TEXT, domain TEXT, relativePath TEXT, "
                "flags INTEGER, file BLOB, extra TEXT)"
            )
            connection.execute("CREATE INDEX files_domain_idx ON Files(domain)")
            connection.execute("CREATE TABLE Extra(value TEXT)")
        elif schema == "missing_table":
            connection.execute("CREATE TABLE Other(value TEXT)")
        elif schema.startswith("missing:"):
            missing = schema.split(":", 1)[1]
            columns = {
                "fileID": "TEXT", "domain": "TEXT", "relativePath": "TEXT",
                "flags": "INTEGER", "file": "BLOB",
            }
            columns.pop(missing)
            connection.execute("CREATE TABLE Files(" + ",".join(f"{k} {v}" for k, v in columns.items()) + ")")
        connection.commit()
        connection.close()
    return backup


def validate(root: Path, backup: Path, **validator_kwargs):
    adapter = AppleBackupInputAdapter([root], clock=lambda: NOW)
    inspection = adapter.inspect(backup, correlation_id=CID)
    manager = validator_kwargs.pop("copy_manager", ControlledCopyManager(workspace_root=root.parent))
    return AppleBackupValidator(manager, clock=lambda: NOW, **validator_kwargs).validate(inspection)


@pytest.mark.parametrize("encrypted,outcome", [
    (False, BackupValidationOutcome.APPLE_BACKUP_UNENCRYPTED),
    (True, BackupValidationOutcome.APPLE_BACKUP_ENCRYPTED),
])
def test_valid_candidate_outcomes_and_deterministic_fingerprint(tmp_path, encrypted, outcome):
    root = tmp_path / "evidence"
    root.mkdir()
    backup = make_backup(root, encrypted=encrypted)
    first = validate(root, backup)
    second = validate(root, backup)
    assert first.outcome is outcome
    assert first.schema_fingerprint_sha256 == second.schema_fingerprint_sha256
    assert json.loads(first.canonical_json())["outcome"] == outcome.value
    assert first.controlled_copy_audit["cleanup_status"] == "SUCCEEDED"


def test_invalid_manifest_with_identity_is_corrupt(tmp_path):
    root = tmp_path / "evidence"; root.mkdir()
    result = validate(root, make_backup(root, schema="invalid"))
    assert result.outcome is BackupValidationOutcome.APPLE_BACKUP_CORRUPT


def test_invalid_manifest_with_unrecognized_plist_is_not_apple(tmp_path):
    root = tmp_path / "evidence"; root.mkdir()
    backup = root / "candidate"; backup.mkdir()
    (backup / "Manifest.db").write_bytes(b"not sqlite")
    write_plist(backup / "Info.plist", {"Unrecognized": "value"})
    result = validate(root, backup)
    assert result.outcome is BackupValidationOutcome.NOT_AN_APPLE_BACKUP


def test_invalid_manifest_and_malformed_plist_without_other_identity_is_indeterminate(tmp_path):
    root = tmp_path / "evidence"; root.mkdir()
    backup = root / "candidate"; backup.mkdir()
    (backup / "Manifest.db").write_bytes(b"not sqlite")
    (backup / "Info.plist").write_bytes(b"malformed")
    assert validate(root, backup).outcome is BackupValidationOutcome.APPLE_BACKUP_INDETERMINATE


def test_invalid_manifest_and_malformed_plist_with_other_identity_is_corrupt(tmp_path):
    root = tmp_path / "evidence"; root.mkdir()
    backup = make_backup(root, schema="invalid")
    (backup / "Info.plist").write_bytes(b"malformed")
    assert validate(root, backup).outcome is BackupValidationOutcome.APPLE_BACKUP_CORRUPT


def test_operational_identity_plist_failure_is_validation_failed(tmp_path):
    root = tmp_path / "evidence"; root.mkdir()
    backup = make_backup(root, schema="invalid")
    def fail_reader(path):
        raise PermissionError("synthetic")
    assert validate(root, backup, plist_reader=fail_reader).outcome is BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED


def test_valid_sqlite_without_identity_is_not_apple(tmp_path):
    root = tmp_path / "evidence"; root.mkdir()
    backup = make_backup(root)
    for name in ("Info.plist", "Manifest.plist", "Status.plist"):
        write_plist(backup / name, {"Unrecognized": True})
    assert validate(root, backup).outcome is BackupValidationOutcome.NOT_AN_APPLE_BACKUP


@pytest.mark.parametrize("missing", ["Manifest.plist", "Info.plist", "Status.plist"])
def test_identity_plus_missing_required_plist_is_incomplete(tmp_path, missing):
    root = tmp_path / "evidence"; root.mkdir()
    backup = make_backup(root)
    (backup / missing).unlink()
    assert validate(root, backup).outcome is BackupValidationOutcome.APPLE_BACKUP_INCOMPLETE


@pytest.mark.parametrize("schema", ["missing_table", "missing:fileID", "missing:domain", "missing:relativePath", "missing:flags", "missing:file"])
def test_unsupported_manifest_schema(tmp_path, schema):
    root = tmp_path / "evidence"; root.mkdir()
    assert validate(root, make_backup(root, schema=schema)).outcome is BackupValidationOutcome.APPLE_BACKUP_UNSUPPORTED_VERSION


@pytest.mark.parametrize("snapshot,outcome", [
    ("not-finished", BackupValidationOutcome.APPLE_BACKUP_INCOMPLETE),
    (None, BackupValidationOutcome.APPLE_BACKUP_INDETERMINATE),
])
def test_snapshot_classification(tmp_path, snapshot, outcome):
    root = tmp_path / "evidence"; root.mkdir()
    assert validate(root, make_backup(root, snapshot=snapshot)).outcome is outcome


@pytest.mark.parametrize("encrypted", [None, "false", 0])
def test_malformed_or_missing_encryption_is_indeterminate(tmp_path, encrypted):
    root = tmp_path / "evidence"; root.mkdir()
    assert validate(root, make_backup(root, encrypted=encrypted)).outcome is BackupValidationOutcome.APPLE_BACKUP_INDETERMINATE


def test_missing_and_non_directory_adapter_results_are_invalid_input(tmp_path):
    root = tmp_path / "evidence"; root.mkdir()
    adapter = AppleBackupInputAdapter([root], clock=lambda: NOW)
    validator = AppleBackupValidator(ControlledCopyManager(workspace_root=tmp_path), clock=lambda: NOW)
    missing = adapter.inspect(root / "missing", correlation_id=CID)
    file_path = root / "file"; file_path.write_text("x")
    file_result = adapter.inspect(file_path, correlation_id=CID)
    assert validator.validate(missing).outcome is BackupValidationOutcome.INVALID_INPUT
    assert validator.validate(file_result).outcome is BackupValidationOutcome.INVALID_INPUT


def test_cleanup_failure_is_validation_failed(tmp_path):
    root = tmp_path / "evidence"; root.mkdir()
    backup = make_backup(root)
    workspace = tmp_path / "workspace"
    def creator(_):
        workspace.mkdir()
        return workspace
    def fail_cleanup(_):
        raise OSError("synthetic cleanup failure")
    manager = ControlledCopyManager(workspace_creator=creator, cleanup=fail_cleanup)
    result = validate(root, backup, copy_manager=manager)
    assert result.outcome is BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED
    shutil.rmtree(workspace)


def test_integrity_failure_is_corrupt(tmp_path, monkeypatch):
    root = tmp_path / "evidence"; root.mkdir()
    backup = make_backup(root)
    from app.intake import backup_validator
    original = backup_validator._inspect_manifest
    def failed_integrity(uri):
        schema, fingerprint, _ = original(uri)
        return schema, fingerprint, ("synthetic integrity failure",)
    monkeypatch.setattr(backup_validator, "_inspect_manifest", failed_integrity)
    assert validate(root, backup).outcome is BackupValidationOutcome.APPLE_BACKUP_CORRUPT


def test_validator_has_no_api_or_legacy_dependency():
    source = Path(__file__).parents[1] / "app" / "intake" / "backup_validator.py"
    text = source.read_text(encoding="utf-8")
    assert "app.api" not in text
    assert "legacy" not in text.lower()
