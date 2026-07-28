"""Synthetic tests for the schema-neutral DEV-0202/DEV-0205 controlled copy."""

from __future__ import annotations

import ast
import hashlib
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.controlled_copy import (
    CleanupStatus,
    ControlledCopyError,
    ControlledCopyManager,
)
from tests.support.resource_policy import TEST_RESOURCE_POLICY


FIXED_TIME = datetime(2026, 7, 27, 14, 0, tzinfo=timezone.utc)
CORRELATION_ID = UUID("20000000-0000-0000-0000-000000000002")
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def create_synthetic_sqlite(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE synthetic_metadata (id INTEGER PRIMARY KEY, label TEXT)")
    connection.execute("INSERT INTO synthetic_metadata(label) VALUES ('fixture')")
    connection.execute("PRAGMA user_version = 7")
    connection.execute("PRAGMA application_id = 1234")
    connection.commit()
    connection.close()


def fixed_workspace_creator(path: Path):
    def create(_: Path | None) -> Path:
        path.mkdir()
        return path

    return create


def manager_for(source_parent: Path, workspace: Path, **kwargs) -> ControlledCopyManager:
    workspace_root = workspace.parent
    workspace_root.mkdir(parents=True, exist_ok=True)
    return ControlledCopyManager(
        workspace_root=workspace_root,
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: FIXED_TIME,
        workspace_creator=fixed_workspace_creator(workspace),
        **kwargs,
    )


def test_main_only_copy_records_matching_hashes_and_cleans_up(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)
    manager = manager_for(source_root, workspace)

    controlled = manager.create(
        main,
        evidence_source_root=source_root,
        correlation_id=CORRELATION_ID,
    )
    with controlled:
        assert controlled.workspace_path == workspace.resolve()
        assert len(controlled.audit.files) == 1
        record = controlled.audit.files[0]
        assert record.role == "main"
        assert record.source_sha256_before == record.copied_sha256 == record.source_sha256_after
        assert Path(record.working_path).read_bytes() == main.read_bytes()

    assert controlled.audit.cleanup_status is CleanupStatus.SUCCEEDED
    assert not workspace.exists()


def test_companions_preserve_exact_names_and_relationships(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)
    for suffix in ("-wal", "-shm", "-journal"):
        main.with_name(f"{main.name}{suffix}").write_bytes(f"synthetic{suffix}".encode())

    controlled = manager_for(source_root, workspace).create(
        main,
        evidence_source_root=source_root,
        correlation_id=CORRELATION_ID,
        retain_for_testing=True,
    )
    with controlled:
        assert controlled.audit.companion_names_before == (
            "synthetic.db-wal",
            "synthetic.db-shm",
            "synthetic.db-journal",
        )
        assert controlled.audit.companion_names_after == controlled.audit.companion_names_before
        assert sorted(path.name for path in workspace.iterdir()) == [
            "synthetic.db",
            "synthetic.db-journal",
            "synthetic.db-shm",
            "synthetic.db-wal",
        ]

    assert controlled.audit.cleanup_status is CleanupStatus.RETAINED_FOR_TEST
    shutil.rmtree(workspace)


def test_source_mutation_during_copy_fails_closed_and_cleans_up(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)

    def mutate_after_copy(source: Path, target: Path) -> None:
        shutil.copyfile(source, target)
        source.write_bytes(source.read_bytes() + b"changed")

    manager = manager_for(source_root, workspace, copier=mutate_after_copy)
    with pytest.raises(ControlledCopyError) as caught:
        manager.create(main, evidence_source_root=source_root, correlation_id=CORRELATION_ID)

    assert caught.value.code == "source_changed_during_copy"
    assert caught.value.audit.cleanup_status is CleanupStatus.SUCCEEDED
    assert not workspace.exists()


def test_companion_set_mutation_is_detected(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)
    added = False

    def add_companion_after_copy(source: Path, target: Path) -> None:
        nonlocal added
        shutil.copyfile(source, target)
        if not added:
            main.with_name(f"{main.name}-wal").write_bytes(b"synthetic wal")
            added = True

    manager = manager_for(source_root, workspace, copier=add_companion_after_copy)
    with pytest.raises(ControlledCopyError) as caught:
        manager.create(main, evidence_source_root=source_root, correlation_id=CORRELATION_ID)

    assert caught.value.code == "source_companion_set_changed"
    assert caught.value.audit.cleanup_status is CleanupStatus.SUCCEEDED


def test_copy_operation_failure_is_structured_and_cleans_up(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)

    def fail_copy(_: Path, __: Path) -> None:
        raise PermissionError("synthetic copy failure")

    manager = manager_for(source_root, workspace, copier=fail_copy)
    with pytest.raises(ControlledCopyError) as caught:
        manager.create(main, evidence_source_root=source_root, correlation_id=CORRELATION_ID)

    assert caught.value.code == "controlled_copy_creation_failed"
    assert caught.value.audit.cleanup_status is CleanupStatus.SUCCEEDED
    assert "synthetic copy failure" not in str(caught.value)
    assert not workspace.exists()


def test_read_only_sqlite_observation_and_working_hash_verification(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)
    controlled = manager_for(source_root, workspace).create(
        main,
        evidence_source_root=source_root,
        correlation_id=CORRELATION_ID,
    )

    with controlled:
        observation = controlled.inspect_sqlite_structure()
        assert observation.integrity_rows == ("ok",)
        assert observation.table_names == ("synthetic_metadata",)
        assert observation.user_version == 7
        assert observation.application_id == 1234
        before = hashlib.sha256(controlled.main_working_path.read_bytes()).hexdigest()
        controlled.verify_working_files()
        after = hashlib.sha256(controlled.main_working_path.read_bytes()).hexdigest()
        assert before == after

        connection = sqlite3.connect(controlled.read_only_uri, uri=True)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("CREATE TABLE forbidden_write (id INTEGER)")
        connection.close()

    assert controlled.audit.sqlite_access_mode == "READ_ONLY_QUERY_ONLY_IMMUTABLE_PRIVATE"


def test_changed_working_file_fails_closed_before_cleanup(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)
    controlled = manager_for(source_root, workspace).create(
        main,
        evidence_source_root=source_root,
        correlation_id=CORRELATION_ID,
        retain_for_testing=True,
    )
    controlled.main_working_path.write_bytes(b"changed synthetic working copy")

    with pytest.raises(ControlledCopyError) as caught:
        controlled.close()

    assert caught.value.code == "working_copy_changed"
    assert controlled.audit.verification_status == "FAILED"
    assert controlled.audit.cleanup_status is CleanupStatus.RETAINED_FOR_TEST
    shutil.rmtree(workspace)


def test_invalid_sqlite_fails_structural_observation_and_still_cleans_up(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    main.write_bytes(b"not a sqlite database")
    controlled = manager_for(source_root, workspace).create(
        main,
        evidence_source_root=source_root,
        correlation_id=CORRELATION_ID,
    )

    with pytest.raises(ControlledCopyError) as caught:
        with controlled:
            controlled.inspect_sqlite_structure()

    assert caught.value.code == "sqlite_validation_failed"
    assert controlled.audit.cleanup_status is CleanupStatus.SUCCEEDED
    assert not workspace.exists()


def test_missing_outside_nonfile_and_injected_link_sources_fail_closed(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace_root = tmp_path / "work"
    source_root.mkdir()
    workspace_root.mkdir()
    manager = ControlledCopyManager(
        workspace_root=workspace_root,
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: FIXED_TIME,
    )

    missing = source_root / "missing.db"
    with pytest.raises(ControlledCopyError) as missing_error:
        manager.create(missing, evidence_source_root=source_root, correlation_id=CORRELATION_ID)
    assert missing_error.value.code == "controlled_copy_creation_failed"

    outside = tmp_path / "outside.db"
    create_synthetic_sqlite(outside)
    with pytest.raises(ControlledCopyError):
        manager.create(outside, evidence_source_root=source_root, correlation_id=CORRELATION_ID)

    directory = source_root / "directory.db"
    directory.mkdir()
    with pytest.raises(ControlledCopyError):
        manager.create(directory, evidence_source_root=source_root, correlation_id=CORRELATION_ID)

    link_candidate = source_root / "link.db"
    create_synthetic_sqlite(link_candidate)
    link_manager = ControlledCopyManager(
        workspace_root=workspace_root,
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: FIXED_TIME,
        link_detector=lambda path: path == link_candidate,
    )
    with pytest.raises(ControlledCopyError):
        link_manager.create(
            link_candidate,
            evidence_source_root=source_root,
            correlation_id=CORRELATION_ID,
        )


def test_workspace_inside_source_fails_closed(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)
    workspace_root = source_root / "work"
    workspace_root.mkdir()
    workspace = workspace_root / "copy"
    manager = manager_for(source_root, workspace)

    with pytest.raises(ControlledCopyError):
        manager.create(main, evidence_source_root=source_root, correlation_id=CORRELATION_ID)

    assert not workspace.exists()


def test_cleanup_failure_is_recorded_and_surfaced(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)

    def fail_cleanup(_: Path) -> None:
        raise PermissionError("synthetic cleanup failure")

    controlled = manager_for(source_root, workspace, cleanup=fail_cleanup).create(
        main,
        evidence_source_root=source_root,
        correlation_id=CORRELATION_ID,
    )
    with pytest.raises(ControlledCopyError) as caught:
        with controlled:
            pass

    assert caught.value.code == "working_copy_cleanup_failed"
    assert controlled.audit.cleanup_status is CleanupStatus.FAILED
    shutil.rmtree(workspace)


def test_audit_is_deterministic_with_fixed_workspace_clock_and_correlation(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    workspace = tmp_path / "work" / "copy"
    source_root.mkdir()
    main = source_root / "synthetic.db"
    create_synthetic_sqlite(main)

    def run() -> str:
        controlled = manager_for(source_root, workspace).create(
            main,
            evidence_source_root=source_root,
            correlation_id=CORRELATION_ID,
        )
        with controlled:
            pass
        return controlled.audit.canonical_json()

    assert run() == run()


def test_static_boundary_has_no_legacy_or_apple_compatibility_assumptions() -> None:
    source_path = BACKEND_ROOT / "app" / "intake" / "controlled_copy.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    assert not any(module.startswith(("evidence_engine", "app.legacy")) for module in imports)
    assert "Files" not in source
    assert "IsEncrypted" not in source
    assert "Product Version" not in source
    assert "Manifest.plist" not in source
