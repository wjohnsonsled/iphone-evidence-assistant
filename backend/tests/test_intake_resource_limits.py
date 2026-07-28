from __future__ import annotations

import plistlib
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.intake.apple_backup import AppleBackupInputAdapter, InputAdapterStatus
from app.intake.backup_validator import AppleBackupValidator, BackupValidationOutcome
from app.intake.controlled_copy import ControlledCopyError, ControlledCopyManager
from app.intake.resource_limits import (
    IntakeResourcePolicy,
    ResourceLimitExceeded,
    VALID_RANGES,
)
from tests.support.resource_policy import TEST_RESOURCE_POLICY


NOW = datetime(2026, 7, 28, 20, 0, tzinfo=timezone.utc)


def _write_plist(path: Path, value: dict) -> None:
    with path.open("wb") as stream:
        plistlib.dump(value, stream)


def _backup(root: Path, *, rows: int = 0) -> Path:
    candidate = root / "candidate"
    candidate.mkdir()
    _write_plist(candidate / "Info.plist", {"Product Version": "synthetic"})
    _write_plist(candidate / "Manifest.plist", {"IsEncrypted": False})
    _write_plist(candidate / "Status.plist", {"SnapshotState": "finished"})
    connection = sqlite3.connect(candidate / "Manifest.db")
    connection.execute(
        "CREATE TABLE Files(fileID TEXT, domain TEXT, relativePath TEXT, "
        "flags INTEGER, file BLOB)"
    )
    if rows:
        connection.executemany(
            "INSERT INTO Files VALUES (?, 'd', 'p', 1, X'00')",
            ((str(index),) for index in range(rows)),
        )
    connection.commit()
    connection.close()
    return candidate


def _validate(root: Path, candidate: Path, policy: IntakeResourcePolicy):
    inspection = AppleBackupInputAdapter(
        [root],
        resource_policy=policy,
        clock=lambda: NOW,
    ).inspect(candidate, correlation_id=uuid4())
    return AppleBackupValidator(
        ControlledCopyManager(
            workspace_root=root.parent,
            resource_policy=policy,
        ),
        resource_policy=policy,
        clock=lambda: NOW,
    ).validate(inspection)


def test_policy_rejects_every_missing_malformed_and_out_of_range_value():
    values = {
        name: getattr(TEST_RESOURCE_POLICY, name)
        for name in VALID_RANGES
    }
    for field_name, (_, maximum) in VALID_RANGES.items():
        for invalid in (0, -1, "1", maximum + 1):
            changed = {**values, field_name: invalid}
            with pytest.raises(ValueError):
                IntakeResourcePolicy(**changed)


def test_input_entry_depth_and_path_limits_are_validation_failures(tmp_path):
    root = tmp_path / "evidence"
    candidate = root / "one" / "two"
    candidate.mkdir(parents=True)
    (candidate / "a").write_bytes(b"a")
    (candidate / "b").write_bytes(b"b")

    policies = (
        replace(TEST_RESOURCE_POLICY, max_directory_entries=1),
        replace(TEST_RESOURCE_POLICY, max_directory_depth=1),
        replace(TEST_RESOURCE_POLICY, max_pathname_length=len(str(candidate)) - 1),
    )
    for policy in policies:
        result = AppleBackupInputAdapter(
            [root],
            resource_policy=policy,
            clock=lambda: NOW,
        ).inspect(candidate, correlation_id=uuid4())
        assert result.status is InputAdapterStatus.VALIDATION_FAILED
        assert result.issues[0].code == "resource_limit_exceeded"


def test_plist_and_sqlite_size_limits_are_validation_failed_not_other_classes(tmp_path):
    root = tmp_path / "evidence"
    root.mkdir()
    candidate = _backup(root)
    policies = (
        replace(TEST_RESOURCE_POLICY, max_plist_bytes=1),
        replace(TEST_RESOURCE_POLICY, max_sqlite_main_bytes=1),
        replace(TEST_RESOURCE_POLICY, max_controlled_copy_bytes=1),
    )
    for policy in policies:
        result = _validate(root, candidate, policy)
        assert result.outcome is BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED
        assert any(
            observation.code == "resource_limit_exceeded"
            for observation in result.observations
        )


def test_schema_and_sqlite_work_limits_fail_validation_without_reclassification(tmp_path):
    root = tmp_path / "evidence"
    root.mkdir()
    candidate = _backup(root, rows=2_000)
    for policy in (
        replace(TEST_RESOURCE_POLICY, max_schema_entries=1),
        replace(TEST_RESOURCE_POLICY, max_sqlite_work_units=1),
    ):
        result = _validate(root, candidate, policy)
        assert result.outcome is BackupValidationOutcome.APPLE_BACKUP_VALIDATION_FAILED
        assert any(
            observation.code == "resource_limit_exceeded"
            for observation in result.observations
        )


def test_companion_role_and_aggregate_limits_fail_before_copy(tmp_path):
    source = tmp_path / "source"
    work = tmp_path / "work"
    source.mkdir()
    work.mkdir()
    main = source / "synthetic.db"
    main.write_bytes(b"main")
    main.with_name("synthetic.db-wal").write_bytes(b"wal")
    policy = replace(TEST_RESOURCE_POLICY, max_sqlite_wal_bytes=1)

    with pytest.raises(ControlledCopyError) as caught:
        ControlledCopyManager(
            workspace_root=work,
            resource_policy=policy,
        ).create(main, evidence_source_root=source, correlation_id=uuid4())

    assert caught.value.code == "resource_limit_exceeded"
    assert caught.value.audit.cleanup_status.value == "SUCCEEDED"


def test_resource_exception_has_safe_fixed_message():
    error = ResourceLimitExceeded("synthetic_secret_resource_name")
    assert str(error) == "Configured intake resource limit was exceeded."
