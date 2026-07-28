from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.intake.controlled_copy import (
    WORKSPACE_PREFIX,
    ControlledWorkspaceRecovery,
    RecoveryStatus,
)


NOW = datetime(2026, 7, 28, 18, 0, tzinfo=timezone.utc)


def _set_age(path: Path, age: timedelta) -> None:
    timestamp = (NOW - age).timestamp()
    os.utime(path, (timestamp, timestamp))


def test_recovery_removes_only_stale_owned_directories(tmp_path):
    stale = tmp_path / f"{WORKSPACE_PREFIX}stale"
    recent = tmp_path / f"{WORKSPACE_PREFIX}recent"
    unrelated = tmp_path / "unrelated"
    for path in (stale, recent, unrelated):
        path.mkdir()
    (stale / "synthetic.bin").write_bytes(b"synthetic controlled material")
    _set_age(stale, timedelta(hours=3))
    _set_age(recent, timedelta(minutes=5))
    _set_age(unrelated, timedelta(hours=3))

    report = ControlledWorkspaceRecovery(
        tmp_path,
        clock=lambda: NOW,
    ).recover_stale(older_than=timedelta(hours=1))

    assert [(Path(record.workspace_path).name, record.status) for record in report.records] == [
        (recent.name, RecoveryStatus.SKIPPED_RECENT),
        (stale.name, RecoveryStatus.REMOVED),
    ]
    assert not stale.exists()
    assert recent.is_dir()
    assert unrelated.is_dir()
    assert report.scanned_at == NOW
    assert report.stale_before == NOW - timedelta(hours=1)
    assert report.canonical_json() == report.canonical_json()


def test_recovery_rejects_owned_non_directory_and_injected_link(tmp_path):
    file_candidate = tmp_path / f"{WORKSPACE_PREFIX}file"
    link_candidate = tmp_path / f"{WORKSPACE_PREFIX}link"
    file_candidate.write_bytes(b"not a workspace")
    link_candidate.mkdir()
    _set_age(file_candidate, timedelta(hours=3))
    _set_age(link_candidate, timedelta(hours=3))

    report = ControlledWorkspaceRecovery(
        tmp_path,
        clock=lambda: NOW,
        link_detector=lambda path: path == link_candidate,
    ).recover_stale(older_than=timedelta(hours=1))

    assert [record.status for record in report.records] == [
        RecoveryStatus.REJECTED_NON_DIRECTORY,
        RecoveryStatus.REJECTED_LINK,
    ]
    assert file_candidate.exists()
    assert link_candidate.exists()


def test_recovery_failure_is_explicit_and_candidate_remains(tmp_path):
    candidate = tmp_path / f"{WORKSPACE_PREFIX}failure"
    candidate.mkdir()
    _set_age(candidate, timedelta(hours=3))

    def fail_cleanup(_: Path) -> None:
        raise PermissionError("synthetic failure")

    report = ControlledWorkspaceRecovery(
        tmp_path,
        clock=lambda: NOW,
        cleanup=fail_cleanup,
    ).recover_stale(older_than=timedelta(hours=1))

    assert len(report.records) == 1
    assert report.records[0].status is RecoveryStatus.FAILED
    assert report.records[0].failure_code == "workspace_recovery_failed"
    assert candidate.is_dir()


def test_recovery_rejects_invalid_root_and_age(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises((FileNotFoundError, ValueError)):
        ControlledWorkspaceRecovery(missing)

    root = tmp_path / "root"
    root.mkdir()
    recovery = ControlledWorkspaceRecovery(root, clock=lambda: NOW)
    for invalid_age in (timedelta(0), timedelta(seconds=-1)):
        with pytest.raises(ValueError):
            recovery.recover_stale(older_than=invalid_age)

    linked_root = tmp_path / "linked-root"
    linked_root.mkdir()
    with pytest.raises(ValueError):
        ControlledWorkspaceRecovery(
            linked_root,
            link_detector=lambda path: path == linked_root,
        )
