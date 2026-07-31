from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import stat
from uuid import UUID

import pytest

from app.physical_inventory.inventory import (
    AuthorizedInventoryContext,
    FileSystemObjectType,
    InventoryCompletion,
    InventoryResourcePolicy,
    LayoutClassification,
    TerminationReason,
    _entry_type,
    inventory_backup_root,
)


class _FakeStat:
    st_file_attributes = 0
    st_mode = 0


class _FakeEntry:
    def __init__(self, *, symlink=False, attributes=0, mode=0):
        self._symlink = symlink
        self._stat = _FakeStat()
        self._stat.st_file_attributes = attributes
        self._stat.st_mode = mode

    def is_symlink(self):
        return self._symlink

    def stat(self, *, follow_symlinks):
        assert follow_symlinks is False
        return self._stat

IDS = tuple(UUID(int=value) for value in range(1, 8))
NOW = datetime(2026, 7, 31, 13, tzinfo=UTC)


def _context(**changes):
    values = dict(
        tenant_id=IDS[0], case_id=IDS[1], evidence_source_id=IDS[2],
        controlled_source_id=IDS[3], processing_run_id=IDS[4],
        authorized_scope=(IDS[0], IDS[1], IDS[2], IDS[4]),
        root_authorized=True, root_validated=True, observed_at=NOW,
    )
    values.update(changes)
    return AuthorizedInventoryContext(**values)


def _policy(**changes):
    values = dict(
        max_directory_entries=100, max_regular_files=100, max_directories=100,
        max_path_depth=2, max_pathname_length=300,
        max_individual_hash_bytes=1024, max_total_hash_bytes=4096,
        max_memory_estimate_bytes=100000, max_elapsed_seconds=30,
        max_concurrent_hash_operations=1, max_unresolved_objects=100,
    )
    values.update(changes)
    return InventoryResourcePolicy(**values)


def _layout(root: Path):
    (root / "Info.plist").write_bytes(b"synthetic metadata")
    (root / "ab").mkdir()
    (root / "ab" / ("ab" + "1" * 38)).write_bytes(b"synthetic object")


def test_exact_layout_is_deterministic_read_only_and_provenance_complete(tmp_path):
    _layout(tmp_path)
    before = {path.relative_to(tmp_path).as_posix(): path.stat().st_mtime_ns for path in tmp_path.rglob("*")}
    first = inventory_backup_root(tmp_path, _context(), _policy())
    second = inventory_backup_root(tmp_path, _context(), _policy())
    after = {path.relative_to(tmp_path).as_posix(): path.stat().st_mtime_ns for path in tmp_path.rglob("*")}
    assert first == second
    assert before == after
    assert first.completion is InventoryCompletion.COMPLETE
    assert first.candidate_objects_observed == 1
    candidate = next(item for item in first.observations if item.eligible_candidate_object)
    assert candidate.layout_classification is LayoutClassification.CANDIDATE_PHYSICAL_OBJECT
    assert candidate.locator.relative_display == "ab/" + "ab" + "1" * 38
    assert candidate.filename.canonical_comparison == "ab" + "1" * 38
    assert all(not value.startswith(("C:", "/")) for value in candidate.locator.relative_components)


@pytest.mark.parametrize(
    ("context", "reason"),
    (
        (_context(root_authorized=False), TerminationReason.ROOT_NOT_AUTHORIZED),
        (_context(root_validated=False), TerminationReason.ROOT_NOT_VALIDATED),
        (_context(authorized_scope=(IDS[0], IDS[1], IDS[2], IDS[5])), TerminationReason.SOURCE_SCOPE_MISMATCH),
    ),
)
def test_authorization_validation_and_scope_fail_closed(tmp_path, context, reason):
    result = inventory_backup_root(tmp_path, context, _policy())
    assert result.completion is InventoryCompletion.FAILED
    assert result.termination_reason is reason
    assert not result.observations


def test_missing_and_file_roots_fail_closed(tmp_path):
    missing = inventory_backup_root(tmp_path / "missing", _context(), _policy())
    assert missing.termination_reason is TerminationReason.ROOT_ACCESS_FAILED
    file = tmp_path / "file"
    file.write_bytes(b"synthetic")
    invalid = inventory_backup_root(file, _context(), _policy())
    assert invalid.termination_reason is TerminationReason.ROOT_INVALID


def test_unknown_entries_are_preserved_without_recursion_or_interpretation(tmp_path):
    (tmp_path / "unknown").mkdir()
    (tmp_path / "unexpected.bin").write_bytes(b"synthetic")
    result = inventory_backup_root(tmp_path, _context(), _policy())
    classes = {item.layout_classification for item in result.observations}
    assert LayoutClassification.UNEXPECTED_DIRECTORY in classes
    assert LayoutClassification.UNEXPECTED_FILE in classes
    assert result.unresolved_objects == 2
    assert result.candidate_objects_observed == 0


def test_uppercase_extra_extension_and_prefix_mismatch_are_not_candidates(tmp_path):
    (tmp_path / "ab").mkdir()
    names = ("AB" + "1" * 38, "ab" + "1" * 38 + ".bin", "cd" + "1" * 38)
    for name in names:
        (tmp_path / "ab" / name).write_bytes(b"synthetic")
    result = inventory_backup_root(tmp_path, _context(), _policy())
    assert result.candidate_objects_observed == 0
    assert all(item.layout_classification is not LayoutClassification.CANDIDATE_PHYSICAL_OBJECT for item in result.observations if item.object_type is FileSystemObjectType.REGULAR_FILE)


@pytest.mark.parametrize(
    ("changes", "reason"),
    (
        ({"max_directory_entries": 1}, TerminationReason.ENTRY_LIMIT),
        ({"max_regular_files": 1}, TerminationReason.REGULAR_FILE_LIMIT),
        ({"max_directories": 1}, TerminationReason.DIRECTORY_LIMIT),
        ({"max_pathname_length": 2}, TerminationReason.PATH_LENGTH_LIMIT),
        ({"max_memory_estimate_bytes": 513}, TerminationReason.MEMORY_ESTIMATE_LIMIT),
        ({"max_unresolved_objects": 1}, TerminationReason.UNRESOLVED_OBJECT_LIMIT),
    ),
)
def test_resource_limits_preserve_completed_observations(tmp_path, changes, reason):
    (tmp_path / "aa").mkdir()
    (tmp_path / "bb").mkdir()
    (tmp_path / "unexpected-a").write_bytes(b"a")
    (tmp_path / "unexpected-b").write_bytes(b"b")
    result = inventory_backup_root(tmp_path, _context(), _policy(**changes))
    assert result.completion is InventoryCompletion.RESOURCE_TERMINATED
    assert result.termination_reason is reason
    assert result.continuation_available


def test_wall_clock_and_cancellation_are_distinct(tmp_path):
    _layout(tmp_path)
    ticks = iter((0.0, 31.0, 31.0))
    timed = inventory_backup_root(tmp_path, _context(), _policy(), clock=lambda: next(ticks))
    assert timed.termination_reason is TerminationReason.WALL_CLOCK_LIMIT
    cancelled = inventory_backup_root(tmp_path, _context(), _policy(), cancel_check=lambda: True)
    assert cancelled.completion is InventoryCompletion.CANCELLED
    assert cancelled.termination_reason is TerminationReason.CANCELLED


def test_policy_rejects_missing_nonpositive_or_wrong_depth():
    with pytest.raises(ValueError, match="must_be_positive"):
        _policy(max_regular_files=0)
    with pytest.raises(ValueError, match="depth_must_equal_two"):
        _policy(max_path_depth=3)


def test_symlink_is_not_followed_when_supported(tmp_path):
    outside = tmp_path.parent / "synthetic-outside-target"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "aa"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    result = inventory_backup_root(tmp_path, _context(), _policy())
    observed = result.observations[0]
    assert observed.object_type is FileSystemObjectType.SYMBOLIC_LINK
    assert observed.layout_classification is LayoutClassification.UNSUPPORTED_OBJECT
    assert result.candidate_objects_observed == 0


def test_root_symlink_fails_closed_when_supported(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    result = inventory_backup_root(link, _context(), _policy())
    assert result.termination_reason is TerminationReason.ROOT_LINK_UNSAFE


def test_symbolic_link_classification_never_stats_target():
    kind, details, reason = _entry_type(_FakeEntry(symlink=True))
    assert kind is FileSystemObjectType.SYMBOLIC_LINK
    assert details is None
    assert reason == "symbolic_link_not_followed"


def test_windows_reparse_classification_fails_closed():
    kind, details, reason = _entry_type(_FakeEntry(attributes=0x400, mode=stat.S_IFDIR))
    assert kind is FileSystemObjectType.WINDOWS_REPARSE_POINT
    assert details is not None
    assert reason == "reparse_point_not_followed"
