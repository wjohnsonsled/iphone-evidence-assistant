"""Controlled raw observation access to candidate Manifest.db Files rows."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from app.intake.controlled_copy import ControlledCopyError, ControlledSQLiteCopy
from app.manifest.schema_profile import (
    CompatibilityOutcome,
    ManifestSchemaValidationResult,
)

QUERY_PROFILE_ID = "manifestdb-files-query"
QUERY_PROFILE_VERSION = "1"
LOCATOR_PROFILE_ID = "manifestdb-row-locator"
LOCATOR_PROFILE_VERSION = "1"
READER_ID = "sqlite-files-raw-reader"
READER_VERSION = "1"
SOURCE_TABLE = "Files"
PROJECTION = ("fileID", "domain", "relativePath", "flags", "file")
LIMITATIONS = (
    "Rows are raw source observations and are not parsed or interpreted evidence.",
    "ROWID is stable only for the controlled input and processing run.",
    "The file BLOB is preserved raw and is not decoded, reconstructed, or interpreted.",
    "Query completion does not establish backup, inventory, artifact, parser, or evidentiary completeness.",
    "No capability is Supported by this candidate query profile.",
)


class QueryOperation(str, Enum):
    ENUMERATE_ROWS = "ENUMERATE_ROWS"
    RETRIEVE_SINGLE_ROW = "RETRIEVE_SINGLE_ROW"


class QueryOutcome(str, Enum):
    PAGE_COMPLETE = "PAGE_COMPLETE"
    ENUMERATION_COMPLETE = "ENUMERATION_COMPLETE"
    COMPLETE_ZERO_ROWS = "COMPLETE_ZERO_ROWS"
    SINGLE_ROW = "SINGLE_ROW"
    ROW_NOT_FOUND = "ROW_NOT_FOUND"
    ROW_LOCATOR_UNAVAILABLE = "ROW_LOCATOR_UNAVAILABLE"
    ROW_LOCATOR_DUPLICATE = "ROW_LOCATOR_DUPLICATE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    CONTROLLED_COPY_VIOLATION = "CONTROLLED_COPY_VIOLATION"
    READ_FAILED = "READ_FAILED"
    CANCELLED = "CANCELLED"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"


class LocatorConfidence(str, Enum):
    SQLITE_ROWID_CONTROLLED_RUN = "SQLITE_ROWID_CONTROLLED_RUN"


class ColumnValueState(str, Enum):
    VALUE_PRESENT = "VALUE_PRESENT"
    VALUE_NULL = "VALUE_NULL"
    VALUE_EMPTY = "VALUE_EMPTY"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    NOT_PROJECTED = "NOT_PROJECTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    READ_FAILURE = "READ_FAILURE"


class ContinuationState(str, Enum):
    AVAILABLE = "AVAILABLE"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class FilesQueryPolicy:
    max_page_size: int
    max_rows_per_operation: int
    max_sqlite_work_units: int

    def __post_init__(self) -> None:
        if min(
            self.max_page_size,
            self.max_rows_per_operation,
            self.max_sqlite_work_units,
        ) <= 0:
            raise ValueError("files_query_policy_values_must_be_positive")
        if self.max_page_size > self.max_rows_per_operation:
            raise ValueError("page_size_cannot_exceed_operation_row_limit")


@dataclass(frozen=True, slots=True)
class RowLocator:
    locator_type: str
    locator_value: int
    locator_version: str
    locator_confidence: LocatorConfidence
    source_table: str
    processing_run_id: UUID

    def __post_init__(self) -> None:
        if self.locator_type != "ROW_LOCATOR_V1" or self.locator_version != "1":
            raise ValueError("row_locator_profile_invalid")
        if self.source_table.casefold() != SOURCE_TABLE.casefold():
            raise ValueError("row_locator_table_invalid")


@dataclass(frozen=True, slots=True)
class ContinuationToken:
    locator: int
    query_profile_version: str
    processing_run_id: UUID

    def __post_init__(self) -> None:
        if self.query_profile_version != QUERY_PROFILE_VERSION:
            raise ValueError("continuation_profile_mismatch")


@dataclass(frozen=True, slots=True)
class ColumnValueObservation:
    column_name: str
    state: ColumnValueState
    raw_value: str | int | float | bytes | None
    observed_sqlite_type: str
    expected_python_type: str


@dataclass(frozen=True, slots=True)
class FilesRowObservation:
    processing_run_id: UUID
    source_artifact_id: UUID
    database_identity_id: UUID
    schema_profile_id: str
    schema_profile_version: str
    query_profile_id: str
    query_profile_version: str
    row_locator: RowLocator
    projected_values: tuple[ColumnValueObservation, ...]
    queried_at: datetime
    reader_id: str
    reader_version: str
    limitations: tuple[str, ...] = LIMITATIONS


@dataclass(frozen=True, slots=True)
class FilesQueryContext:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    database_identity_id: UUID
    processing_run_id: UUID
    authorized_scope: tuple[UUID, UUID, UUID, UUID]
    queried_at: datetime

    def __post_init__(self) -> None:
        if self.queried_at.tzinfo is None or self.queried_at.utcoffset() is None:
            raise ValueError("files_query_time_invalid")


@dataclass(frozen=True, slots=True)
class FilesQueryResult:
    operation: QueryOperation
    outcome: QueryOutcome
    context: FilesQueryContext
    query_profile_id: str
    query_profile_version: str
    locator_profile_id: str
    locator_profile_version: str
    page_size: int
    starting_locator: int | None
    ending_locator: int | None
    continuation_state: ContinuationState
    continuation_token: ContinuationToken | None
    observations: tuple[FilesRowObservation, ...]
    reason_code: str
    limitations: tuple[str, ...] = LIMITATIONS


CancelCheck = Callable[[], bool]


def _scope_check(
    context: FilesQueryContext, schema: ManifestSchemaValidationResult
) -> None:
    actual = (
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.processing_run_id,
    )
    if actual != context.authorized_scope:
        raise PermissionError("files_query_scope_mismatch")
    schema_context = schema.context
    if (
        schema_context.tenant_id,
        schema_context.case_id,
        schema_context.evidence_source_id,
        schema_context.source_artifact_id,
        schema_context.database_identity_id,
        schema_context.processing_run_id,
    ) != (
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.source_artifact_id,
        context.database_identity_id,
        context.processing_run_id,
    ):
        raise PermissionError("files_query_schema_scope_mismatch")


def _result(
    operation: QueryOperation,
    outcome: QueryOutcome,
    context: FilesQueryContext,
    *,
    page_size: int,
    starting_locator: int | None,
    observations: list[FilesRowObservation],
    reason_code: str,
    continuation_state: ContinuationState,
    has_more: bool = False,
) -> FilesQueryResult:
    ending = (
        observations[-1].row_locator.locator_value if observations else starting_locator
    )
    token = (
        ContinuationToken(ending, QUERY_PROFILE_VERSION, context.processing_run_id)
        if has_more and ending is not None
        else None
    )
    return FilesQueryResult(
        operation,
        outcome,
        context,
        QUERY_PROFILE_ID,
        QUERY_PROFILE_VERSION,
        LOCATOR_PROFILE_ID,
        LOCATOR_PROFILE_VERSION,
        page_size,
        starting_locator,
        ending,
        continuation_state,
        token,
        tuple(observations),
        reason_code,
    )


def _column_observation(name: str, value: object) -> ColumnValueObservation:
    expected = {
        "fileID": str,
        "domain": str,
        "relativePath": str,
        "flags": int,
        "file": bytes,
    }[name]
    if value is None:
        state = ColumnValueState.VALUE_NULL
        raw = None
    elif not isinstance(value, expected) or (
        expected is int and isinstance(value, bool)
    ):
        state = ColumnValueState.TYPE_MISMATCH
        raw = value if isinstance(value, (str, int, float, bytes)) else None
    elif value == "" or value == b"":
        state = ColumnValueState.VALUE_EMPTY
        raw = value
    else:
        state = ColumnValueState.VALUE_PRESENT
        raw = value
    return ColumnValueObservation(
        name, state, raw, type(value).__name__, expected.__name__
    )


def _row_observation(
    row: tuple[object, ...],
    context: FilesQueryContext,
    schema: ManifestSchemaValidationResult,
) -> FilesRowObservation:
    locator = row[0]
    if not isinstance(locator, int) or isinstance(locator, bool):
        raise ValueError("row_locator_invalid")
    return FilesRowObservation(
        context.processing_run_id,
        context.source_artifact_id,
        context.database_identity_id,
        schema.profile_id,
        schema.profile_version,
        QUERY_PROFILE_ID,
        QUERY_PROFILE_VERSION,
        RowLocator(
            "ROW_LOCATOR_V1",
            locator,
            LOCATOR_PROFILE_VERSION,
            LocatorConfidence.SQLITE_ROWID_CONTROLLED_RUN,
            SOURCE_TABLE,
            context.processing_run_id,
        ),
        tuple(
            _column_observation(name, value)
            for name, value in zip(PROJECTION, row[1:], strict=True)
        ),
        context.queried_at,
        READER_ID,
        READER_VERSION,
    )


def _table_is_without_rowid(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT sql FROM sqlite_schema "
        "WHERE type='table' AND name=? COLLATE NOCASE",
        (SOURCE_TABLE,),
    ).fetchone()
    return bool(row and isinstance(row[0], str) and "WITHOUT ROWID" in row[0].upper())


def _locator_sequence_invalid(
    locator: object, seen: set[int], prior: int | None
) -> bool:
    return (
        not isinstance(locator, int)
        or isinstance(locator, bool)
        or locator in seen
        or (prior is not None and locator <= prior)
    )


def _execute(
    controlled: ControlledSQLiteCopy,
    schema: ManifestSchemaValidationResult,
    context: FilesQueryContext,
    policy: FilesQueryPolicy,
    *,
    operation: QueryOperation,
    page_size: int,
    starting_locator: int | None,
    single_locator: int | None,
    cancelled: CancelCheck,
) -> FilesQueryResult:
    try:
        _scope_check(context, schema)
    except PermissionError:
        return _result(
            operation, QueryOutcome.NOT_AUTHORIZED, context, page_size=page_size,
            starting_locator=starting_locator, observations=[],
            reason_code="files_query_not_authorized",
            continuation_state=ContinuationState.FAILED,
        )
    if schema.outcome not in {
        CompatibilityOutcome.SCHEMA_COMPATIBLE,
        CompatibilityOutcome.SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS,
    }:
        return _result(
            operation, QueryOutcome.SCHEMA_MISMATCH, context, page_size=page_size,
            starting_locator=starting_locator, observations=[],
            reason_code="manifest_schema_not_compatible",
            continuation_state=ContinuationState.FAILED,
        )
    if page_size <= 0 or page_size > policy.max_page_size:
        return _result(
            operation, QueryOutcome.RESOURCE_LIMIT_EXCEEDED, context,
            page_size=page_size, starting_locator=starting_locator, observations=[],
            reason_code="page_size_limit_exceeded",
            continuation_state=ContinuationState.FAILED,
        )
    if starting_locator is not None and not isinstance(starting_locator, int):
        return _result(
            operation, QueryOutcome.READ_FAILED, context, page_size=page_size,
            starting_locator=None, observations=[],
            reason_code="continuation_locator_invalid",
            continuation_state=ContinuationState.FAILED,
        )
    if cancelled():
        return _result(
            operation, QueryOutcome.CANCELLED, context, page_size=page_size,
            starting_locator=starting_locator, observations=[],
            reason_code="query_cancelled",
            continuation_state=ContinuationState.CANCELLED,
        )

    observations: list[FilesRowObservation] = []
    connection: sqlite3.Connection | None = None
    interrupted = False
    work_units = 0

    def progress() -> int:
        nonlocal work_units, interrupted
        work_units += 1_000
        if work_units > policy.max_sqlite_work_units:
            interrupted = True
            return 1
        return 0

    try:
        controlled.verify_working_files()
        connection = sqlite3.connect(controlled.read_only_uri, uri=True)
        connection.execute("PRAGMA query_only=ON")
        connection.set_progress_handler(progress, 1_000)
        if _table_is_without_rowid(connection):
            return _result(
                operation, QueryOutcome.ROW_LOCATOR_UNAVAILABLE, context,
                page_size=page_size, starting_locator=starting_locator,
                observations=[], reason_code="without_rowid_locator_unavailable",
                continuation_state=ContinuationState.FAILED,
            )
        projection_sql = ",".join(f'"{name}"' for name in PROJECTION)
        if operation is QueryOperation.RETRIEVE_SINGLE_ROW:
            cursor = connection.execute(
                f'SELECT rowid,{projection_sql} FROM "Files" WHERE rowid=? ORDER BY rowid ASC',
                (single_locator,),
            )
            maximum = 1
        else:
            if starting_locator is None:
                cursor = connection.execute(
                    f'SELECT rowid,{projection_sql} FROM "Files" '
                    "ORDER BY rowid ASC LIMIT ?",
                    (page_size + 1,),
                )
            else:
                cursor = connection.execute(
                    f'SELECT rowid,{projection_sql} FROM "Files" '
                    "WHERE rowid>? ORDER BY rowid ASC LIMIT ?",
                    (starting_locator, page_size + 1),
                )
            maximum = page_size + 1
        seen: set[int] = set()
        prior = (
            None
            if operation is QueryOperation.RETRIEVE_SINGLE_ROW
            else starting_locator
        )
        rows: list[tuple[object, ...]] = []
        while len(rows) < maximum:
            if cancelled():
                return _result(
                    operation, QueryOutcome.CANCELLED, context, page_size=page_size,
                    starting_locator=starting_locator, observations=observations,
                    reason_code="query_cancelled",
                    continuation_state=ContinuationState.CANCELLED,
                )
            row = cursor.fetchone()
            if row is None:
                break
            locator = row[0]
            if _locator_sequence_invalid(locator, seen, prior):
                return _result(
                    operation, QueryOutcome.ROW_LOCATOR_DUPLICATE, context,
                    page_size=page_size, starting_locator=starting_locator,
                    observations=observations,
                    reason_code="row_locator_duplicate_or_nonmonotonic",
                    continuation_state=ContinuationState.FAILED,
                )
            seen.add(locator)
            prior = locator
            rows.append(row)
            if len(rows) <= page_size:
                observations.append(_row_observation(row, context, schema))
            if len(observations) > policy.max_rows_per_operation:
                return _result(
                    operation, QueryOutcome.RESOURCE_LIMIT_EXCEEDED, context,
                    page_size=page_size, starting_locator=starting_locator,
                    observations=observations[:-1],
                    reason_code="operation_row_limit_exceeded",
                    continuation_state=ContinuationState.FAILED,
                )
        controlled.verify_working_files()
    except ControlledCopyError:
        return _result(
            operation, QueryOutcome.CONTROLLED_COPY_VIOLATION, context,
            page_size=page_size, starting_locator=starting_locator,
            observations=observations, reason_code="controlled_copy_violation",
            continuation_state=ContinuationState.FAILED,
        )
    except sqlite3.Error:
        return _result(
            operation,
            (
                QueryOutcome.RESOURCE_LIMIT_EXCEEDED
                if interrupted
                else QueryOutcome.READ_FAILED
            ),
            context,
            page_size=page_size,
            starting_locator=starting_locator,
            observations=observations,
            reason_code=(
                "sqlite_work_limit_exceeded" if interrupted else "files_query_read_failed"
            ),
            continuation_state=ContinuationState.FAILED,
        )
    finally:
        if connection is not None:
            connection.set_progress_handler(None, 0)
            connection.close()

    if operation is QueryOperation.RETRIEVE_SINGLE_ROW:
        outcome = QueryOutcome.SINGLE_ROW if observations else QueryOutcome.ROW_NOT_FOUND
        return _result(
            operation, outcome, context, page_size=1,
            starting_locator=single_locator, observations=observations,
            reason_code="single_row_observed" if observations else "row_not_found",
            continuation_state=ContinuationState.COMPLETE,
        )
    has_more = len(rows) > page_size
    if not observations and starting_locator is None:
        outcome = QueryOutcome.COMPLETE_ZERO_ROWS
    elif has_more:
        outcome = QueryOutcome.PAGE_COMPLETE
    else:
        outcome = QueryOutcome.ENUMERATION_COMPLETE
    return _result(
        operation, outcome, context, page_size=page_size,
        starting_locator=starting_locator, observations=observations,
        reason_code=(
            "continuation_available" if has_more else "enumeration_complete"
        ),
        continuation_state=(
            ContinuationState.AVAILABLE if has_more else ContinuationState.COMPLETE
        ),
        has_more=has_more,
    )


def enumerate_files_rows(
    controlled: ControlledSQLiteCopy,
    schema: ManifestSchemaValidationResult,
    context: FilesQueryContext,
    policy: FilesQueryPolicy,
    *,
    page_size: int,
    continuation: ContinuationToken | None = None,
    cancelled: CancelCheck = lambda: False,
) -> FilesQueryResult:
    if continuation is not None and continuation.processing_run_id != context.processing_run_id:
        return _result(
            QueryOperation.ENUMERATE_ROWS, QueryOutcome.NOT_AUTHORIZED, context,
            page_size=page_size, starting_locator=None, observations=[],
            reason_code="continuation_run_mismatch",
            continuation_state=ContinuationState.FAILED,
        )
    return _execute(
        controlled,
        schema,
        context,
        policy,
        operation=QueryOperation.ENUMERATE_ROWS,
        page_size=page_size,
        starting_locator=continuation.locator if continuation else None,
        single_locator=None,
        cancelled=cancelled,
    )


def retrieve_files_row(
    controlled: ControlledSQLiteCopy,
    schema: ManifestSchemaValidationResult,
    context: FilesQueryContext,
    policy: FilesQueryPolicy,
    locator: RowLocator,
    *,
    cancelled: CancelCheck = lambda: False,
) -> FilesQueryResult:
    if (
        locator.processing_run_id != context.processing_run_id
        or locator.locator_version != LOCATOR_PROFILE_VERSION
    ):
        return _result(
            QueryOperation.RETRIEVE_SINGLE_ROW, QueryOutcome.NOT_AUTHORIZED,
            context, page_size=1, starting_locator=None, observations=[],
            reason_code="row_locator_scope_mismatch",
            continuation_state=ContinuationState.FAILED,
        )
    return _execute(
        controlled,
        schema,
        context,
        policy,
        operation=QueryOperation.RETRIEVE_SINGLE_ROW,
        page_size=1,
        starting_locator=locator.locator_value,
        single_locator=locator.locator_value,
        cancelled=cancelled,
    )
