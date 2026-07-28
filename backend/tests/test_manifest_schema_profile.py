from __future__ import annotations

import ast
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.controlled_copy import CleanupStatus, ControlledCopyManager
from app.manifest.schema_profile import *
from tests.support.resource_policy import TEST_RESOURCE_POLICY


NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)


def u(n: int) -> UUID:
    return UUID(f"06010000-0000-4000-8000-{n:012d}")


CONTEXT = SchemaValidationContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)


def create_database(path: Path, statements: tuple[str, ...]) -> None:
    connection = sqlite3.connect(path)
    for statement in statements:
        connection.execute(statement)
    connection.commit()
    connection.close()


def validate(path: Path, tmp_path: Path):
    source_root = path.parent
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir(exist_ok=True)
    manager = ControlledCopyManager(
        workspace_root=workspace_root,
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: NOW,
    )
    controlled = manager.create(
        path, evidence_source_root=source_root, correlation_id=u(100)
    )
    with controlled:
        result = validate_controlled_manifest_schema(
            controlled, CONTEXT, TEST_RESOURCE_POLICY
        )
        assert controlled.audit.sqlite_access_mode in {
            "NOT_OPENED",
            "READ_ONLY_QUERY_ONLY_IMMUTABLE_PRIVATE",
            "READ_ONLY_FAILED",
        }
    assert controlled.audit.cleanup_status is CleanupStatus.SUCCEEDED
    return result


def files_sql(*, missing: str | None = None, flags_type: str = "INTEGER", extra: bool = False):
    columns = {
        "fileID": "TEXT",
        "domain": "TEXT",
        "relativePath": "TEXT",
        "flags": flags_type,
        "file": "BLOB",
    }
    columns.pop(missing, None)
    if extra:
        columns["futureColumn"] = "TEXT"
    return "CREATE TABLE Files(" + ",".join(f"{name} {kind}" for name, kind in columns.items()) + ")"


def test_profile_is_candidate_complete_and_immutable():
    profile = MANIFEST_SCHEMA_PROFILE
    assert (profile.profile_id, profile.profile_version) == (
        "apple-manifestdb-schema", "1"
    )
    assert tuple(rule.name for rule in profile.required_tables) == ("Files",)
    assert tuple(column.name for column in profile.required_tables[0].columns) == (
        "fileID", "domain", "relativePath", "flags", "file"
    )
    assert tuple(column.affinity for column in profile.required_tables[0].columns) == (
        SQLiteAffinity.TEXT, SQLiteAffinity.TEXT, SQLiteAffinity.TEXT,
        SQLiteAffinity.INTEGER, SQLiteAffinity.BLOB,
    )
    assert profile.optional_tables == ()
    assert profile.required_tables[0].foreign_keys_required == ()
    with pytest.raises(Exception):
        profile.profile_version = "2"  # type: ignore[misc]


def test_perfect_profile_and_fingerprint_are_deterministic(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    database = source / "Manifest.db"
    create_database(database, (files_sql(),))
    first = validate(database, tmp_path)
    second = validate(database, tmp_path)
    assert first.outcome is CompatibilityOutcome.SCHEMA_COMPATIBLE
    assert first.tables[0].state is TableState.PRESENT
    assert all(item.state is ColumnState.PRESENT for item in first.tables[0].columns)
    assert first.canonical_schema_json == second.canonical_schema_json
    assert first.fingerprint.sha256_digest == second.fingerprint.sha256_digest
    assert first.fingerprint.profile_id == "manifestdb-schema-canonical-json-sha256"
    assert first.fingerprint.source_artifact_id == CONTEXT.source_artifact_id
    assert first.fingerprint.processing_run_id == CONTEXT.processing_run_id


@pytest.mark.parametrize("missing", ["fileID", "domain", "relativePath", "flags", "file"])
def test_each_missing_required_column_fails_separately(tmp_path, missing):
    source = tmp_path / f"source-{missing}"
    source.mkdir()
    database = source / "Manifest.db"
    create_database(database, (files_sql(missing=missing),))
    result = validate(database, tmp_path)
    assert result.outcome is CompatibilityOutcome.SCHEMA_REQUIRED_COMPONENT_MISSING
    item = next(column for column in result.tables[0].columns if column.column_name == missing)
    assert item.state is ColumnState.ABSENT
    assert result.reason_code == "REQUIRED_SCHEMA_COMPONENT_MISSING"


def test_empty_and_unknown_schemas_are_distinct(tmp_path):
    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    empty = empty_root / "Manifest.db"
    create_database(empty, ("PRAGMA user_version=1",))
    empty_result = validate(empty, tmp_path)
    assert empty_result.outcome is CompatibilityOutcome.SCHEMA_INVALID
    assert empty_result.reason_code == "sqlite_header_characteristics_invalid"

    missing_result = evaluate_schema((), CONTEXT)
    assert missing_result.outcome is CompatibilityOutcome.SCHEMA_REQUIRED_COMPONENT_MISSING
    assert missing_result.tables[0].state is TableState.ABSENT

    unknown_root = tmp_path / "unknown"
    unknown_root.mkdir()
    unknown = unknown_root / "Manifest.db"
    create_database(unknown, ("CREATE TABLE FutureManifest(value TEXT)",))
    unknown_result = validate(unknown, tmp_path)
    assert unknown_result.outcome is CompatibilityOutcome.SCHEMA_UNKNOWN
    assert any(item.state is TableState.UNKNOWN for item in unknown_result.tables)


def test_extra_table_column_and_mixed_additions_are_preserved(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    database = source / "Manifest.db"
    create_database(
        database,
        (
            files_sql(extra=True),
            "CREATE TABLE FutureTable(id INTEGER PRIMARY KEY, value TEXT)",
            "CREATE INDEX future_index ON FutureTable(value)",
        ),
    )
    result = validate(database, tmp_path)
    assert result.outcome is CompatibilityOutcome.SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS
    assert any(
        column.state is ColumnState.UNKNOWN
        for table in result.tables
        for column in table.columns
    )
    assert any(table.state is TableState.UNKNOWN for table in result.tables)
    assert "futuretable" in result.canonical_schema_json
    assert "future_index" in result.canonical_schema_json


def test_affinity_not_type_spelling_and_type_mismatch(tmp_path):
    accepted_root = tmp_path / "accepted"
    accepted_root.mkdir()
    accepted = accepted_root / "Manifest.db"
    create_database(
        accepted,
        ("CREATE TABLE Files(fileID VARCHAR(40),domain CLOB,relativePath TEXT,flags BIGINT,file)",),
    )
    assert validate(accepted, tmp_path).outcome is CompatibilityOutcome.SCHEMA_COMPATIBLE

    mismatch_root = tmp_path / "mismatch"
    mismatch_root.mkdir()
    mismatch = mismatch_root / "Manifest.db"
    create_database(mismatch, (files_sql(flags_type="TEXT"),))
    result = validate(mismatch, tmp_path)
    assert result.outcome is CompatibilityOutcome.SCHEMA_INVALID
    flags = next(item for item in result.tables[0].columns if item.column_name.casefold() == "flags")
    assert flags.state is ColumnState.TYPE_MISMATCH


def test_case_insensitive_identifiers_match_without_altering_raw_names(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    database = source / "Manifest.db"
    create_database(
        database,
        ("CREATE TABLE FILES(FILEID TEXT,DOMAIN TEXT,RELATIVEPATH TEXT,FLAGS INTEGER,FILE BLOB)",),
    )
    result = validate(database, tmp_path)
    assert result.outcome is CompatibilityOutcome.SCHEMA_COMPATIBLE
    assert result.raw_schema[0].name == "FILES"
    assert result.tables[0].table_name == "FILES"


def test_duplicate_schema_observations_fail_closed():
    columns = (
        RawColumn("fileID", "TEXT", False, False, 0),
        RawColumn("domain", "TEXT", False, False, 0),
        RawColumn("relativePath", "TEXT", False, False, 0),
        RawColumn("flags", "INTEGER", False, False, 0),
        RawColumn("file", "BLOB", False, False, 0),
    )
    result = evaluate_schema(
        (RawTable("Files", columns, ()), RawTable("FILES", columns, ())), CONTEXT
    )
    assert result.outcome is CompatibilityOutcome.SCHEMA_INVALID
    assert result.tables[0].state is TableState.DUPLICATE


def test_non_sqlite_corrupt_and_header_invalid_are_distinct(tmp_path):
    non_root = tmp_path / "non"
    non_root.mkdir()
    non_sqlite = non_root / "Manifest.db"
    non_sqlite.write_bytes(b"not sqlite")
    assert validate(non_sqlite, tmp_path).outcome is CompatibilityOutcome.SCHEMA_NOT_RECOGNIZED

    corrupt_root = tmp_path / "corrupt"
    corrupt_root.mkdir()
    corrupt = corrupt_root / "Manifest.db"
    create_database(corrupt, (files_sql(),))
    content = bytearray(corrupt.read_bytes())
    content[100:] = b"\xff" * (len(content) - 100)
    corrupt.write_bytes(content)
    assert validate(corrupt, tmp_path).outcome is CompatibilityOutcome.SCHEMA_CORRUPT

    invalid_root = tmp_path / "invalid"
    invalid_root.mkdir()
    invalid = invalid_root / "Manifest.db"
    create_database(invalid, (files_sql(),))
    content = bytearray(invalid.read_bytes())
    content[16:18] = (513).to_bytes(2, "big")
    invalid.write_bytes(content)
    result = validate(invalid, tmp_path)
    assert result.outcome is CompatibilityOutcome.SCHEMA_INVALID
    assert result.reason_code == "sqlite_header_characteristics_invalid"


def test_scope_fails_closed_and_result_has_no_path_or_content_fields(tmp_path):
    wrong = SchemaValidationContext(
        u(99), u(2), u(3), u(4), u(5), u(6), CONTEXT.authorized_scope, NOW
    )
    with pytest.raises(PermissionError, match="scope"):
        evaluate_schema((), wrong)
    fields = set(ManifestSchemaValidationResult.__dataclass_fields__)
    assert not {"path", "rows", "values", "secrets", "stack_trace"} & fields


def test_outcome_vocabulary_is_exact_and_no_row_or_write_sql_exists():
    assert {item.value for item in CompatibilityOutcome} == {
        "SCHEMA_COMPATIBLE",
        "SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS",
        "SCHEMA_UNKNOWN",
        "SCHEMA_NOT_RECOGNIZED",
        "SCHEMA_REQUIRED_COMPONENT_MISSING",
        "SCHEMA_INVALID",
        "SCHEMA_CORRUPT",
        "SCHEMA_NOT_EVALUATED",
        "SCHEMA_INDETERMINATE",
    }
    module = Path(__file__).parents[1] / "app" / "manifest" / "schema_profile.py"
    source = module.read_text(encoding="utf-8")
    ast.parse(source)
    lowered = source.lower()
    assert "from files" not in lowered and "from properties" not in lowered
    assert all(token not in lowered for token in ("vacuum", "checkpoint", "insert into", "update files", "delete from"))


def test_registry_and_supported_store_remain_empty():
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry

    registry = create_supported_registry()
    assert registry.entries == () and SupportedEvidenceStore(registry).count == 0
