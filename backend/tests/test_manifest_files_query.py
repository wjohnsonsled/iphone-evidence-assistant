from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.controlled_copy import ControlledCopyError, ControlledCopyManager
from app.manifest.files_query import *
from app.manifest.schema_profile import (
    CompatibilityOutcome,
    SchemaValidationContext,
    validate_controlled_manifest_schema,
)
from tests.support.resource_policy import TEST_RESOURCE_POLICY


NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)


def u(n: int) -> UUID:
    return UUID(f"06020000-0000-4000-8000-{n:012d}")


SCHEMA_CONTEXT = SchemaValidationContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
QUERY_CONTEXT = FilesQueryContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
POLICY = FilesQueryPolicy(
    max_page_size=100,
    max_rows_per_operation=100,
    max_sqlite_work_units=10_000_000,
)


def create_manifest(
    path: Path,
    rows=(),
    *,
    without_rowid: bool = False,
) -> None:
    connection = sqlite3.connect(path)
    primary = ",PRIMARY KEY(fileID)" if without_rowid else ""
    suffix = " WITHOUT ROWID" if without_rowid else ""
    connection.execute(
        "CREATE TABLE Files("
        "fileID TEXT,domain TEXT,relativePath TEXT,flags INTEGER,file BLOB"
        f"{primary}){suffix}"
    )
    for row in rows:
        connection.execute(
            "INSERT INTO Files(rowid,fileID,domain,relativePath,flags,file) "
            "VALUES(?,?,?,?,?,?)"
            if not without_rowid
            else "INSERT INTO Files(fileID,domain,relativePath,flags,file) VALUES(?,?,?,?,?)",
            row,
        )
    connection.commit()
    connection.close()


def controlled_query(tmp_path: Path, rows=(), *, without_rowid=False):
    source = tmp_path / "source"
    source.mkdir(parents=True)
    database = source / "Manifest.db"
    create_manifest(database, rows, without_rowid=without_rowid)
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    manager = ControlledCopyManager(
        workspace_root=workspace,
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: NOW,
    )
    controlled = manager.create(
        database, evidence_source_root=source, correlation_id=u(100)
    )
    return database, controlled


def schema_for(controlled):
    schema = validate_controlled_manifest_schema(
        controlled, SCHEMA_CONTEXT, TEST_RESOURCE_POLICY
    )
    assert schema.outcome in {
        CompatibilityOutcome.SCHEMA_COMPATIBLE,
        CompatibilityOutcome.SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS,
    }
    return schema


def test_profile_policy_and_locator_contracts_are_versioned_and_immutable():
    assert (QUERY_PROFILE_ID, QUERY_PROFILE_VERSION) == (
        "manifestdb-files-query", "1"
    )
    assert (LOCATOR_PROFILE_ID, LOCATOR_PROFILE_VERSION) == (
        "manifestdb-row-locator", "1"
    )
    assert PROJECTION == ("fileID", "domain", "relativePath", "flags", "file")
    with pytest.raises(ValueError):
        FilesQueryPolicy(0, 1, 1)
    with pytest.raises(ValueError):
        FilesQueryPolicy(2, 1, 1)
    locator = RowLocator(
        "ROW_LOCATOR_V1", 7, "1",
        LocatorConfidence.SQLITE_ROWID_CONTROLLED_RUN, "Files", u(6)
    )
    with pytest.raises(Exception):
        locator.locator_value = 8  # type: ignore[misc]


def test_enumeration_is_rowid_ordered_paginated_and_source_immutable(tmp_path):
    rows = (
        (10, "c", "HomeDomain", "c", 1, b"c"),
        (2, "a", "HomeDomain", "a", 1, b"a"),
        (7, "b", "HomeDomain", "b", 1, b"b"),
    )
    database, controlled = controlled_query(tmp_path, rows)
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with controlled:
        schema = schema_for(controlled)
        first = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=2
        )
        assert first.outcome is QueryOutcome.PAGE_COMPLETE
        assert [item.row_locator.locator_value for item in first.observations] == [2, 7]
        assert first.starting_locator is None and first.ending_locator == 7
        assert first.continuation_state is ContinuationState.AVAILABLE
        assert first.continuation_token == ContinuationToken(7, "1", u(6))
        assert set(first.continuation_token.__dataclass_fields__) == {
            "locator", "query_profile_version", "processing_run_id"
        }

        second = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=2,
            continuation=first.continuation_token,
        )
        assert second.outcome is QueryOutcome.ENUMERATION_COMPLETE
        assert [item.row_locator.locator_value for item in second.observations] == [10]
        assert second.starting_locator == 7 and second.continuation_token is None
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_zero_single_row_and_not_found_are_distinct(tmp_path):
    _, controlled = controlled_query(tmp_path)
    with controlled:
        schema = schema_for(controlled)
        zero = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=10
        )
        assert zero.outcome is QueryOutcome.COMPLETE_ZERO_ROWS

    _, controlled = controlled_query(
        tmp_path / "second", ((4, "x", "D", "p", 1, b"raw"),)
    )
    with controlled:
        schema = schema_for(controlled)
        page = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=10
        )
        locator = page.observations[0].row_locator
        found = retrieve_files_row(
            controlled, schema, QUERY_CONTEXT, POLICY, locator
        )
        assert found.outcome is QueryOutcome.SINGLE_ROW
        missing = retrieve_files_row(
            controlled,
            schema,
            QUERY_CONTEXT,
            POLICY,
            RowLocator(
                "ROW_LOCATOR_V1", 999, "1",
                LocatorConfidence.SQLITE_ROWID_CONTROLLED_RUN, "Files", u(6)
            ),
        )
        assert missing.outcome is QueryOutcome.ROW_NOT_FOUND


def test_raw_column_states_are_separate_and_no_coercion_occurs(tmp_path):
    rows = ((1, "", None, "", 1.5, b""),)
    _, controlled = controlled_query(tmp_path, rows)
    with controlled:
        schema = schema_for(controlled)
        result = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=10
        )
    values = result.observations[0].projected_values
    assert [item.state for item in values] == [
        ColumnValueState.VALUE_EMPTY,
        ColumnValueState.VALUE_NULL,
        ColumnValueState.VALUE_EMPTY,
        ColumnValueState.TYPE_MISMATCH,
        ColumnValueState.VALUE_EMPTY,
    ]
    assert values[3].raw_value == 1.5
    assert values[4].raw_value == b""


def test_without_rowid_has_no_synthetic_locator(tmp_path):
    rows = (("id", "D", "p", 1, b"raw"),)
    _, controlled = controlled_query(tmp_path, rows, without_rowid=True)
    with controlled:
        schema = schema_for(controlled)
        result = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=10
        )
    assert result.outcome is QueryOutcome.ROW_LOCATOR_UNAVAILABLE
    assert result.observations == () and result.continuation_token is None


def test_schema_scope_continuation_and_locator_mismatch_fail_closed(tmp_path):
    _, controlled = controlled_query(tmp_path)
    with controlled:
        schema = schema_for(controlled)
        wrong_context = FilesQueryContext(
            u(99), u(2), u(3), u(4), u(5), u(6),
            QUERY_CONTEXT.authorized_scope, NOW,
        )
        denied = enumerate_files_rows(
            controlled, schema, wrong_context, POLICY, page_size=10
        )
        assert denied.outcome is QueryOutcome.NOT_AUTHORIZED
        token_denied = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=10,
            continuation=ContinuationToken(1, "1", u(99)),
        )
        assert token_denied.outcome is QueryOutcome.NOT_AUTHORIZED
        locator_denied = retrieve_files_row(
            controlled,
            schema,
            QUERY_CONTEXT,
            POLICY,
            RowLocator(
                "ROW_LOCATOR_V1", 1, "1",
                LocatorConfidence.SQLITE_ROWID_CONTROLLED_RUN, "Files", u(99)
            ),
        )
        assert locator_denied.outcome is QueryOutcome.NOT_AUTHORIZED


def test_schema_mismatch_and_page_limit_fail_without_query(tmp_path):
    _, controlled = controlled_query(tmp_path)
    with controlled:
        schema = schema_for(controlled)
        mismatched = schema.__class__(
            CompatibilityOutcome.SCHEMA_UNKNOWN,
            schema.explanation,
            schema.context,
            schema.profile_id,
            schema.profile_version,
            schema.reader_id,
            schema.reader_version,
            schema.sqlite_page_size,
            schema.sqlite_read_format,
            schema.sqlite_schema_format,
            schema.tables,
            schema.raw_schema,
            schema.canonical_schema_json,
            schema.fingerprint,
            "unknown_schema",
            schema.limitations,
        )
        assert enumerate_files_rows(
            controlled, mismatched, QUERY_CONTEXT, POLICY, page_size=10
        ).outcome is QueryOutcome.SCHEMA_MISMATCH
        assert enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=101
        ).outcome is QueryOutcome.RESOURCE_LIMIT_EXCEEDED


def test_cancellation_preserves_prior_observations(tmp_path):
    rows = tuple(
        (index, f"id-{index}", "D", f"p-{index}", 1, b"raw")
        for index in range(1, 6)
    )
    _, controlled = controlled_query(tmp_path, rows)
    calls = 0

    def cancel():
        nonlocal calls
        calls += 1
        return calls == 3

    with controlled:
        schema = schema_for(controlled)
        result = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=5,
            cancelled=cancel,
        )
    assert result.outcome is QueryOutcome.CANCELLED
    assert [item.row_locator.locator_value for item in result.observations] == [1]
    assert result.continuation_state is ContinuationState.CANCELLED


def test_controlled_copy_change_fails_closed(tmp_path):
    _, controlled = controlled_query(
        tmp_path, ((1, "id", "D", "p", 1, b"raw"),)
    )
    with pytest.raises(ControlledCopyError):
        with controlled:
            schema = schema_for(controlled)
            with controlled.main_working_path.open("ab") as stream:
                stream.write(b"x")
            result = enumerate_files_rows(
                controlled, schema, QUERY_CONTEXT, POLICY, page_size=10
            )
            assert result.outcome is QueryOutcome.CONTROLLED_COPY_VIOLATION


def test_duplicate_locator_guard_and_query_surface_are_closed():
    import app.manifest.files_query as module

    assert {item.value for item in QueryOperation} == {
        "ENUMERATE_ROWS", "RETRIEVE_SINGLE_ROW"
    }
    seen = {1}
    assert module._locator_sequence_invalid(1, seen, 1)
    assert module._locator_sequence_invalid(0, seen, 1)
    assert not module._locator_sequence_invalid(2, seen, 1)
    assert " OFFSET " not in Path(module.__file__).read_text(encoding="utf-8").upper()
    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    assert all(
        token not in source
        for token in (
            " join ", " group by ", "insert into", "update files",
            "delete from", "vacuum", "checkpoint", "reindex", "optimize",
            "create temp", "alter table",
        )
    )


def test_registry_store_and_result_surface_remain_candidate_only():
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry

    registry = create_supported_registry()
    assert registry.entries == () and SupportedEvidenceStore(registry).count == 0
    assert not {"supported", "interpretation", "artifact"} & set(
        FilesQueryResult.__dataclass_fields__
    )
