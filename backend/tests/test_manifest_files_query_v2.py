from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.controlled_copy import ControlledCopyError, ControlledCopyManager
from app.manifest.files_query import (
    FilesQueryContext,
    LocatorConfidence,
    RowLocator,
)
from app.manifest.files_query_v2 import *
from app.manifest.files_query_v2 import _memory_for_row
from app.manifest.files_query_v2 import _sqlite_failure_reason
from app.manifest.schema_profile import (
    CompatibilityOutcome,
    SchemaValidationContext,
    validate_controlled_manifest_schema,
)
from tests.support.resource_policy import TEST_RESOURCE_POLICY

NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)


def u(n: int) -> UUID:
    return UUID(f"0602a000-0000-4000-8000-{n:012d}")


SCHEMA_CONTEXT = SchemaValidationContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
QUERY_CONTEXT = FilesQueryContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
POLICY = QueryResourcePolicy(
    max_rows=100,
    max_page_size=100,
    max_wall_clock_seconds=60,
    max_projected_bytes=1_000_000,
    max_memory_estimate_bytes=2_000_000,
    max_projected_columns=5,
    max_process_queries=4,
    max_tenant_queries=3,
    max_case_queries=2,
)


def create_manifest(path: Path, rows=(), *, without_rowid=False) -> None:
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
            (
                "INSERT INTO Files(fileID,domain,relativePath,flags,file) "
                "VALUES(?,?,?,?,?)"
                if without_rowid
                else "INSERT INTO Files(rowid,fileID,domain,relativePath,flags,file) "
                "VALUES(?,?,?,?,?,?)"
            ),
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
    workspace.mkdir()
    controlled = ControlledCopyManager(
        workspace_root=workspace,
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: NOW,
    ).create(database, evidence_source_root=source, correlation_id=u(100))
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


def policy(**changes):
    values = {
        name: getattr(POLICY, name)
        for name in QueryResourcePolicy.__dataclass_fields__
    }
    values.update(changes)
    return QueryResourcePolicy(**values)


def test_profiles_are_separate_candidate_versions_and_policy_fails_closed():
    assert (QUERY_PROFILE_ID, QUERY_PROFILE_VERSION) == (
        "manifestdb-files-query",
        "2",
    )
    assert (RESOURCE_PROFILE_ID, RESOURCE_PROFILE_VERSION) == (
        "manifestdb-query-resource-controls",
        "1",
    )
    from app.manifest import files_query

    assert files_query.QUERY_PROFILE_VERSION == "1"
    with pytest.raises(ValueError):
        policy(max_projected_bytes=0)
    with pytest.raises(ValueError):
        policy(max_projected_columns=4)


def test_default_blob_projection_is_bounded_and_dynamic_types_are_lossless(tmp_path):
    rows = ((1, b"\x08", "", None, "seven", b"\x00\xffraw"),)
    database, controlled = controlled_query(tmp_path, rows)
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with controlled:
        result = enumerate_files_rows_v2(
            controlled, schema_for(controlled), QUERY_CONTEXT, POLICY, page_size=10
        )
    assert result.completion is QueryCompletion.QUERY_COMPLETE
    values = result.observations[0].projected_values
    assert [(v.column_name, v.declared_affinity, v.observed_storage_class) for v in values] == [
        ("fileID", "TEXT", "BLOB"),
        ("domain", "TEXT", "TEXT"),
        ("relativePath", "TEXT", "NULL"),
        ("flags", "INTEGER", "TEXT"),
        ("file", "BLOB", "BLOB"),
    ]
    assert values[0].raw_value == b"\x08"
    assert values[1].state is RowValueState.VALUE_EMPTY
    assert values[2].state is RowValueState.VALUE_NULL
    assert values[3].raw_value == "seven"
    assert values[4].blob_length == 5
    assert values[4].blob_availability is BlobAvailability.PRESENT_BOUNDED
    assert values[4].raw_blob is None
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_raw_blob_requires_explicit_internal_authorization(tmp_path):
    _, controlled = controlled_query(
        tmp_path, ((1, "id", "D", "p", 1, b"opaque"),)
    )
    with controlled:
        schema = schema_for(controlled)
        denied = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            POLICY,
            page_size=1,
            include_raw_blob=True,
        )
        allowed = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            POLICY,
            page_size=1,
            include_raw_blob=True,
            raw_blob_authorized=True,
        )
    assert denied.termination_reason is TerminationReason.AUTHORIZATION_FAILURE
    blob = allowed.observations[0].projected_values[-1]
    assert blob.raw_blob == b"opaque"
    assert blob.blob_availability is BlobAvailability.AVAILABLE_INTERNAL


def test_pagination_has_no_skip_or_repeat_and_single_retrieval_matches(tmp_path):
    rows = tuple(
        (n, f"id-{n}", "D", f"p-{n}", n, bytes([n]))
        for n in (9, 2, 7, 4, 12)
    )
    _, controlled = controlled_query(tmp_path, rows)
    with controlled:
        schema = schema_for(controlled)
        first = enumerate_files_rows_v2(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=2
        )
        second = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            POLICY,
            page_size=3,
            continuation=first.continuation,
        )
        locators = [
            row.row_locator.locator_value
            for row in (*first.observations, *second.observations)
        ]
        target = second.observations[0]
        single = retrieve_files_row_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            POLICY,
            target.row_locator,
        )
    assert locators == [2, 4, 7, 9, 12]
    assert len(set(locators)) == 5
    assert single.observations[0].projected_values == target.projected_values


def test_cross_scope_and_profile_continuations_fail_closed(tmp_path):
    _, controlled = controlled_query(
        tmp_path, ((1, "id", "D", "p", 1, b"x"),)
    )
    with controlled:
        schema = schema_for(controlled)
        token = V2ContinuationToken(
            None,
            QUERY_PROFILE_ID,
            "1",
            QUERY_CONTEXT.tenant_id,
            QUERY_CONTEXT.case_id,
            QUERY_CONTEXT.evidence_source_id,
            QUERY_CONTEXT.source_artifact_id,
            QUERY_CONTEXT.database_identity_id,
            QUERY_CONTEXT.processing_run_id,
        )
        result = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            POLICY,
            page_size=1,
            continuation=token,
        )
    assert result.completion is QueryCompletion.QUERY_NOT_EVALUATED
    assert result.termination_reason is TerminationReason.AUTHORIZATION_FAILURE
    assert result.observations == ()


def test_byte_and_memory_limits_stop_before_next_row_with_continuation(tmp_path):
    rows = (
        (1, "a" * 20, "D", "p", 1, b"x" * 20),
        (2, "b" * 20, "D", "p", 2, b"y" * 20),
    )
    _, controlled = controlled_query(tmp_path, rows)
    with controlled:
        schema = schema_for(controlled)
        baseline = enumerate_files_rows_v2(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=2
        )
        one_row_bytes = baseline.projected_bytes // 2
        byte_limited = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            policy(max_projected_bytes=one_row_bytes + 1),
            page_size=2,
        )
        first_memory = (
            PAGE_OVERHEAD_BYTES
            + CONTINUATION_OVERHEAD_BYTES
            + _memory_for_row(one_row_bytes)
        )
        memory_limited = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            policy(max_memory_estimate_bytes=first_memory + 1),
            page_size=2,
        )
    assert byte_limited.termination_reason is TerminationReason.BYTE_LIMIT_REACHED
    assert byte_limited.rows_completed == 1
    assert byte_limited.continuation is not None
    assert (
        memory_limited.termination_reason
        is TerminationReason.MEMORY_ESTIMATE_LIMIT_REACHED
    )
    assert memory_limited.rows_completed == 1


def test_cancellation_and_controlled_clock_preserve_finalized_rows(tmp_path):
    rows = tuple((n, str(n), "D", "p", n, b"x") for n in range(1, 4))
    _, controlled = controlled_query(tmp_path, rows)
    cancel_calls = 0

    def cancel():
        nonlocal cancel_calls
        cancel_calls += 1
        return cancel_calls == 3

    ticks = iter((0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6))
    with controlled:
        schema = schema_for(controlled)
        cancelled = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            POLICY,
            page_size=3,
            cancelled=cancel,
        )
        timed = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            policy(max_wall_clock_seconds=0.15),
            page_size=3,
            monotonic_clock=lambda: next(ticks),
            audit_clock=lambda: NOW,
        )
    assert cancelled.termination_reason is TerminationReason.CALLER_CANCELLED
    assert cancelled.rows_completed == 1
    assert cancelled.continuation is not None
    assert timed.termination_reason is TerminationReason.WALL_CLOCK_LIMIT_REACHED
    assert timed.resource_control.measurement_method == "monotonic elapsed seconds"


def test_hierarchical_concurrency_denial_is_safe(tmp_path):
    _, controlled = controlled_query(tmp_path)
    limiter = HierarchicalQueryLimiter()
    with controlled:
        schema = schema_for(controlled)
        with limiter.acquire(QUERY_CONTEXT, policy(max_process_queries=1)):
            denied = enumerate_files_rows_v2(
                controlled,
                schema,
                QUERY_CONTEXT,
                policy(max_process_queries=1),
                page_size=1,
                limiter=limiter,
            )
    assert denied.completion is QueryCompletion.QUERY_NOT_EVALUATED
    assert denied.termination_reason is TerminationReason.CONCURRENCY_LIMIT_REACHED
    assert denied.resource_control.enforcement_scope is EnforcementScope.PROCESS
    assert denied.observations == ()


def test_without_rowid_and_candidate_boundaries_fail_closed(tmp_path):
    _, controlled = controlled_query(
        tmp_path, (("id", "D", "p", 1, b"x"),), without_rowid=True
    )
    with controlled:
        result = enumerate_files_rows_v2(
            controlled, schema_for(controlled), QUERY_CONTEXT, POLICY, page_size=1
        )
    assert result.termination_reason is TerminationReason.LOCATOR_FAILURE
    assert result.observations == ()

    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry

    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0


def test_null_and_empty_blob_remain_distinct_and_rerun_is_logically_deterministic(
    tmp_path,
):
    rows = (
        (1, "a", "D", "p", 1, None),
        (2, "b", "D", "p", 2, b""),
    )
    _, controlled = controlled_query(tmp_path, rows)
    with controlled:
        schema = schema_for(controlled)
        first = enumerate_files_rows_v2(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=2
        )
        second = enumerate_files_rows_v2(
            controlled, schema, QUERY_CONTEXT, POLICY, page_size=2
        )
    first_blobs = [row.projected_values[-1] for row in first.observations]
    assert first_blobs[0].state is RowValueState.VALUE_NULL
    assert first_blobs[0].blob_availability is BlobAvailability.ABSENT
    assert first_blobs[1].state is RowValueState.VALUE_EMPTY
    assert first_blobs[1].blob_length == 0
    assert first.observations == second.observations
    assert first.projected_bytes == second.projected_bytes
    assert first.deterministic_memory_estimate == second.deterministic_memory_estimate


def test_page_limit_and_controlled_copy_mutation_fail_closed(tmp_path):
    _, controlled = controlled_query(
        tmp_path, ((1, "id", "D", "p", 1, b"x"),)
    )
    with pytest.raises(ControlledCopyError):
        with controlled:
            schema = schema_for(controlled)
            page_denied = enumerate_files_rows_v2(
                controlled, schema, QUERY_CONTEXT, policy(max_page_size=1), page_size=2
            )
            assert page_denied.termination_reason is TerminationReason.PAGE_LIMIT_REACHED
            with controlled.main_working_path.open("ab") as stream:
                stream.write(b"x")
            changed = enumerate_files_rows_v2(
                controlled, schema, QUERY_CONTEXT, POLICY, page_size=1
            )
            assert changed.termination_reason is TerminationReason.CONTROLLED_COPY_FAILURE
            assert changed.continuation is None


def test_sqlite_failure_codes_have_closed_database_classification():
    corrupt = sqlite3.DatabaseError("safe")
    corrupt.sqlite_errorcode = sqlite3.SQLITE_CORRUPT
    invalid = sqlite3.DatabaseError("safe")
    invalid.sqlite_errorcode = sqlite3.SQLITE_NOTADB
    read = sqlite3.DatabaseError("safe")
    assert _sqlite_failure_reason(corrupt) is TerminationReason.DATABASE_CORRUPT
    assert _sqlite_failure_reason(invalid) is TerminationReason.DATABASE_INVALID
    assert _sqlite_failure_reason(read) is TerminationReason.SQLITE_READ_FAILURE


def test_no_api_persistence_logging_or_interpretation_surface():
    source = Path(__import__("app.manifest.files_query_v2", fromlist=["x"]).__file__).read_text(
        encoding="utf-8"
    ).lower()
    assert all(
        forbidden not in source
        for forbidden in (
            "fastapi",
            "insert into",
            "update files",
            "delete from",
            "import plistlib",
            "from plistlib",
            "logging.",
            " offset ?",
        )
    )
