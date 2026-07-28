"""Synthetic deterministic tests for the DEV-0201 input adapter."""

from __future__ import annotations

import ast
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.apple_backup import (
    AppleBackupInputAdapter,
    InputAdapterStatus,
)
from tests.support.resource_policy import TEST_RESOURCE_POLICY


FIXED_TIME = datetime(2026, 7, 24, 16, 0, tzinfo=timezone.utc)
CORRELATION_ID = UUID("10000000-0000-0000-0000-000000000001")
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def make_adapter(root: Path, **kwargs) -> AppleBackupInputAdapter:
    return AppleBackupInputAdapter(
        [root],
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: FIXED_TIME,
        **kwargs,
    )


def test_controlled_outcomes_are_exact() -> None:
    assert {status.value for status in InputAdapterStatus} == {
        "READY_FOR_STRUCTURE_VALIDATION",
        "READY_ZERO_RESULTS",
        "MISSING",
        "UNSUPPORTED_INPUT",
        "VALIDATION_FAILED",
        "PROCESSING_FAILED",
    }


def test_nonempty_directory_is_ready_with_provenance_and_limitations(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    candidate = root / "synthetic-backup"
    candidate.mkdir(parents=True)
    (candidate / "synthetic.txt").write_text("not evidence", encoding="utf-8")

    result = make_adapter(root).inspect(str(candidate), correlation_id=CORRELATION_ID)

    assert result.status is InputAdapterStatus.READY_FOR_STRUCTURE_VALIDATION
    assert result.is_ready
    assert result.original_path == str(candidate)
    assert result.resolved_path == str(candidate.resolve())
    assert result.evidence_root == str(root.resolve())
    assert result.source_locator == "synthetic-backup"
    assert result.inspected_at == FIXED_TIME
    assert result.correlation_id == CORRELATION_ID
    assert result.adapter_name == "apple_local_backup_input"
    assert result.adapter_version == "1.0.0"
    assert result.observed_entry_count == 1
    assert result.issues == ()
    assert len(result.unassessed_limitations) == 4
    assert all(term in " ".join(result.unassessed_limitations).lower() for term in ("structure", "encryption", "hash", "support"))


def test_empty_directory_is_successful_zero_result_without_support_claim(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    candidate = root / "empty"
    candidate.mkdir(parents=True)

    result = make_adapter(root).inspect(candidate, correlation_id=CORRELATION_ID)

    assert result.status is InputAdapterStatus.READY_ZERO_RESULTS
    assert result.is_ready
    assert result.observed_entry_count == 0
    assert "not an input-support determination" in " ".join(result.unassessed_limitations)


def test_missing_input_is_distinct(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()

    result = make_adapter(root).inspect(root / "missing", correlation_id=CORRELATION_ID)

    assert result.status is InputAdapterStatus.MISSING
    assert not result.is_ready
    assert result.issues[0].code == "input_missing"


def test_existing_file_is_unsupported_input(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    candidate = root / "archive.zip"
    candidate.write_bytes(b"synthetic")

    result = make_adapter(root).inspect(candidate, correlation_id=CORRELATION_ID)

    assert result.status is InputAdapterStatus.UNSUPPORTED_INPUT
    assert result.issues[0].code == "input_not_directory"


def test_root_escape_fails_validation(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()

    result = make_adapter(root).inspect(outside, correlation_id=CORRELATION_ID)

    assert result.status is InputAdapterStatus.VALIDATION_FAILED
    assert result.issues[0].code == "input_outside_evidence_root"


def test_link_boundary_fails_validation_without_os_symlink_fixture(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    candidate = root / "linked"
    candidate.mkdir(parents=True)
    resolved_candidate = candidate.resolve()

    adapter = make_adapter(root, link_detector=lambda path: path.resolve() == resolved_candidate)
    result = adapter.inspect(candidate, correlation_id=CORRELATION_ID)

    assert result.status is InputAdapterStatus.VALIDATION_FAILED
    assert result.issues[0].code == "input_link_boundary_rejected"


def test_enumeration_error_is_processing_failure(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    candidate = root / "synthetic"
    candidate.mkdir(parents=True)

    def fail_enumeration(_: Path) -> int:
        raise PermissionError("synthetic error text must not be returned")

    result = make_adapter(root, entry_counter=fail_enumeration).inspect(
        candidate,
        correlation_id=CORRELATION_ID,
    )

    assert result.status is InputAdapterStatus.PROCESSING_FAILED
    assert result.issues[0].code == "input_enumeration_failed"
    assert "synthetic error text" not in result.issues[0].message


@pytest.mark.parametrize("root_kind", ["missing", "file", "link"])
def test_invalid_configured_root_fails_closed(tmp_path: Path, root_kind: str) -> None:
    root = tmp_path / "root"
    link_detector = None
    if root_kind == "file":
        root.write_text("synthetic", encoding="utf-8")
    elif root_kind == "link":
        root.mkdir()
        link_detector = lambda path: path == root.resolve()

    with pytest.raises(ValueError, match="evidence root"):
        AppleBackupInputAdapter(
            [root],
            resource_policy=TEST_RESOURCE_POLICY,
            link_detector=link_detector,
        )


def test_inspection_is_deterministic_and_audit_serializable(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    candidate = root / "synthetic"
    candidate.mkdir(parents=True)
    adapter = make_adapter(root)

    first = adapter.inspect(candidate, correlation_id=CORRELATION_ID)
    second = adapter.inspect(candidate, correlation_id=CORRELATION_ID)

    assert first == second
    assert first.to_audit_dict() == second.to_audit_dict()
    assert first.to_audit_dict()["correlation_id"] == str(CORRELATION_ID)
    assert first.to_audit_dict()["inspected_at"] == FIXED_TIME.isoformat()


def test_source_fixture_is_byte_for_byte_unchanged_and_not_recursed(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    candidate = root / "synthetic"
    nested = candidate / "nested"
    nested.mkdir(parents=True)
    source_file = nested / "source.bin"
    source_file.write_bytes(b"synthetic immutable bytes")
    before_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
    before_entries = sorted(path.relative_to(candidate).as_posix() for path in candidate.rglob("*"))

    result = make_adapter(root).inspect(candidate, correlation_id=CORRELATION_ID)

    after_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
    after_entries = sorted(path.relative_to(candidate).as_posix() for path in candidate.rglob("*"))
    assert result.status is InputAdapterStatus.READY_FOR_STRUCTURE_VALIDATION
    assert result.observed_entry_count == 1
    assert before_hash == after_hash
    assert before_entries == after_entries


def test_supported_adapter_has_no_legacy_or_file_content_operations() -> None:
    source_path = BACKEND_ROOT / "app" / "intake" / "apple_backup.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert not any(module.startswith(("evidence_engine", "app.legacy")) for module in imported_modules)
    assert called_names.isdisjoint(
        {
            "open",
            "read_bytes",
            "read_text",
            "write_bytes",
            "write_text",
            "unlink",
            "mkdir",
            "rmdir",
            "rename",
            "replace",
            "rglob",
            "glob",
        }
    )
