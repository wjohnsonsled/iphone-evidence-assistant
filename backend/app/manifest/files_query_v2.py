"""Candidate v2 hardening for controlled Manifest.db Files queries.

Version 1 remains in :mod:`app.manifest.files_query` and is intentionally not
changed by this module.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterator
from uuid import UUID

from app.intake.controlled_copy import ControlledCopyError, ControlledSQLiteCopy
from app.manifest.files_query import (
    FilesQueryContext,
    LocatorConfidence,
    RowLocator,
)
from app.manifest.schema_profile import (
    CompatibilityOutcome,
    ManifestSchemaValidationResult,
)

QUERY_PROFILE_ID = "manifestdb-files-query"
QUERY_PROFILE_VERSION = "2"
RESOURCE_PROFILE_ID = "manifestdb-query-resource-controls"
RESOURCE_PROFILE_VERSION = "1"
LOCATOR_PROFILE_ID = "manifestdb-row-locator"
LOCATOR_PROFILE_VERSION = "1"
READER_ID = "sqlite-files-bounded-reader"
READER_VERSION = "2"
PROJECTION = ("fileID", "domain", "relativePath", "flags", "file")

# Versioned deterministic estimate constants. These are logical accounting
# units, not measurements of operating-system or Python process memory.
PAGE_OVERHEAD_BYTES = 128
ROW_OVERHEAD_BYTES = 96
COLUMN_OVERHEAD_BYTES = 40
LOCATOR_OVERHEAD_BYTES = 16
CONTINUATION_OVERHEAD_BYTES = 96
SCALAR_ENCODED_BYTES = 8

LIMITATIONS = (
    "Candidate query-hardening infrastructure is not a parser or Supported capability.",
    "BLOB metadata is not decoded, interpreted, persisted, logged, or publicly exposed.",
    "The deterministic query memory estimate is not actual process-memory usage.",
    "Wall-clock and concurrency controls are operational and may vary by environment.",
    "A resource outcome is not evidence loss, corruption, absence, or tampering.",
    "Query completion does not establish backup, inventory, artifact, or evidentiary completeness.",
)


class QueryCompletion(str, Enum):
    QUERY_COMPLETE = "QUERY_COMPLETE"
    QUERY_PARTIAL = "QUERY_PARTIAL"
    QUERY_FAILED = "QUERY_FAILED"
    QUERY_NOT_EVALUATED = "QUERY_NOT_EVALUATED"
    QUERY_INDETERMINATE = "QUERY_INDETERMINATE"


class TerminationReason(str, Enum):
    COMPLETED = "COMPLETED"
    CALLER_CANCELLED = "CALLER_CANCELLED"
    SYSTEM_INTERRUPTED = "SYSTEM_INTERRUPTED"
    ROW_LIMIT_REACHED = "ROW_LIMIT_REACHED"
    PAGE_LIMIT_REACHED = "PAGE_LIMIT_REACHED"
    BYTE_LIMIT_REACHED = "BYTE_LIMIT_REACHED"
    WALL_CLOCK_LIMIT_REACHED = "WALL_CLOCK_LIMIT_REACHED"
    MEMORY_ESTIMATE_LIMIT_REACHED = "MEMORY_ESTIMATE_LIMIT_REACHED"
    CONCURRENCY_LIMIT_REACHED = "CONCURRENCY_LIMIT_REACHED"
    SCHEMA_INCOMPATIBLE = "SCHEMA_INCOMPATIBLE"
    CONTROLLED_COPY_FAILURE = "CONTROLLED_COPY_FAILURE"
    AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"
    LOCATOR_FAILURE = "LOCATOR_FAILURE"
    SQLITE_READ_FAILURE = "SQLITE_READ_FAILURE"
    DATABASE_INVALID = "DATABASE_INVALID"
    DATABASE_CORRUPT = "DATABASE_CORRUPT"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RowValueState(str, Enum):
    VALUE_PRESENT = "VALUE_PRESENT"
    VALUE_NULL = "VALUE_NULL"
    VALUE_EMPTY = "VALUE_EMPTY"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    READ_FAILURE = "READ_FAILURE"
    NOT_PROJECTED = "NOT_PROJECTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_EVALUATED = "NOT_EVALUATED"


class BlobAvailability(str, Enum):
    ABSENT = "ABSENT"
    PRESENT_BOUNDED = "PRESENT_BOUNDED"
    AVAILABLE_INTERNAL = "AVAILABLE_INTERNAL"


class EnforcementScope(str, Enum):
    PROCESS = "PROCESS"
    TENANT = "TENANT"
    CASE = "CASE"
    EVIDENCE_SOURCE = "EVIDENCE_SOURCE"
    PROCESSING_RUN = "PROCESSING_RUN"


@dataclass(frozen=True, slots=True)
class QueryResourcePolicy:
    max_rows: int
    max_page_size: int
    max_wall_clock_seconds: float
    max_projected_bytes: int
    max_memory_estimate_bytes: int
    max_projected_columns: int
    max_process_queries: int
    max_tenant_queries: int
    max_case_queries: int

    def __post_init__(self) -> None:
        values = (
            self.max_rows,
            self.max_page_size,
            self.max_wall_clock_seconds,
            self.max_projected_bytes,
            self.max_memory_estimate_bytes,
            self.max_projected_columns,
            self.max_process_queries,
            self.max_tenant_queries,
            self.max_case_queries,
        )
        if any(isinstance(value, bool) or value <= 0 for value in values):
            raise ValueError("query_resource_policy_values_must_be_positive")
        if self.max_page_size > self.max_rows:
            raise ValueError("page_size_cannot_exceed_row_limit")
        if self.max_projected_columns < len(PROJECTION):
            raise ValueError("projected_column_limit_too_small")


@dataclass(frozen=True, slots=True)
class V2ContinuationToken:
    after_locator: int | None
    query_profile_id: str
    query_profile_version: str
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    database_identity_id: UUID
    processing_run_id: UUID


@dataclass(frozen=True, slots=True)
class V2ColumnObservation:
    column_name: str
    state: RowValueState
    declared_affinity: str
    observed_storage_class: str
    raw_value: str | int | float | bytes | None
    blob_availability: BlobAvailability | None = None
    blob_length: int | None = None
    raw_blob: bytes | None = None


@dataclass(frozen=True, slots=True)
class V2RowObservation:
    processing_run_id: UUID
    source_artifact_id: UUID
    database_identity_id: UUID
    schema_profile_id: str
    schema_profile_version: str
    query_profile_id: str
    query_profile_version: str
    row_locator: RowLocator
    projected_values: tuple[V2ColumnObservation, ...]
    observed_at: datetime
    reader_id: str
    reader_version: str
    limitations: tuple[str, ...] = LIMITATIONS


@dataclass(frozen=True, slots=True)
class ResourceControlState:
    limit_type: str
    configured_ceiling: int | float
    observed_usage_or_estimate: int | float
    enforcement_scope: EnforcementScope
    limit_reached: bool
    continuation_available: bool
    measurement_method: str


@dataclass(frozen=True, slots=True)
class V2QueryResult:
    completion: QueryCompletion
    termination_reason: TerminationReason
    context: FilesQueryContext
    query_profile_id: str
    query_profile_version: str
    resource_profile_id: str
    resource_profile_version: str
    observations: tuple[V2RowObservation, ...]
    rows_attempted: int
    rows_completed: int
    last_completed_locator: int | None
    continuation: V2ContinuationToken | None
    resource_control: ResourceControlState | None
    projected_bytes: int
    deterministic_memory_estimate: int
    started_at: datetime
    stopped_at: datetime
    monotonic_elapsed_seconds: float
    reason_code: str
    limitations: tuple[str, ...] = LIMITATIONS


class ConcurrencyDenied(RuntimeError):
    def __init__(self, scope: EnforcementScope) -> None:
        super().__init__("query_concurrency_limit_reached")
        self.scope = scope


class HierarchicalQueryLimiter:
    """Application-level counters acquired in the mandated hierarchy."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: dict[tuple[EnforcementScope, UUID | None], int] = {}

    @contextmanager
    def acquire(
        self, context: FilesQueryContext, policy: QueryResourcePolicy
    ) -> Iterator[None]:
        ordered = (
            (EnforcementScope.PROCESS, None, policy.max_process_queries),
            (EnforcementScope.TENANT, context.tenant_id, policy.max_tenant_queries),
            (EnforcementScope.CASE, context.case_id, policy.max_case_queries),
            (EnforcementScope.EVIDENCE_SOURCE, context.evidence_source_id, 1),
            (EnforcementScope.PROCESSING_RUN, context.processing_run_id, 1),
        )
        acquired: list[tuple[EnforcementScope, UUID | None]] = []
        with self._lock:
            for scope, identity, ceiling in ordered:
                key = (scope, identity)
                if self._counts.get(key, 0) >= ceiling:
                    raise ConcurrencyDenied(scope)
                self._counts[key] = self._counts.get(key, 0) + 1
                acquired.append(key)
        try:
            yield
        finally:
            with self._lock:
                for key in reversed(acquired):
                    remaining = self._counts[key] - 1
                    if remaining:
                        self._counts[key] = remaining
                    else:
                        del self._counts[key]


DEFAULT_LIMITER = HierarchicalQueryLimiter()
CancelCheck = Callable[[], bool]
MonotonicClock = Callable[[], float]
AuditClock = Callable[[], datetime]


def _scope_matches(
    context: FilesQueryContext, schema: ManifestSchemaValidationResult
) -> bool:
    return (
        (
            context.tenant_id,
            context.case_id,
            context.evidence_source_id,
            context.processing_run_id,
        )
        == context.authorized_scope
        and (
            schema.context.tenant_id,
            schema.context.case_id,
            schema.context.evidence_source_id,
            schema.context.source_artifact_id,
            schema.context.database_identity_id,
            schema.context.processing_run_id,
        )
        == (
            context.tenant_id,
            context.case_id,
            context.evidence_source_id,
            context.source_artifact_id,
            context.database_identity_id,
            context.processing_run_id,
        )
    )


def _token(context: FilesQueryContext, after: int | None) -> V2ContinuationToken:
    return V2ContinuationToken(
        after,
        QUERY_PROFILE_ID,
        QUERY_PROFILE_VERSION,
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.source_artifact_id,
        context.database_identity_id,
        context.processing_run_id,
    )


def _token_valid(token: V2ContinuationToken, context: FilesQueryContext) -> bool:
    return token == _token(context, token.after_locator)


def _payload_size(storage_class: str, value: object, blob_length: int | None) -> int:
    if storage_class == "null":
        return 0
    if storage_class == "text":
        return len(str(value).encode("utf-8"))
    if storage_class == "blob":
        return blob_length or 0
    return SCALAR_ENCODED_BYTES


def _value_state(
    storage_class: str, expected: str, value: object, blob_length: int | None
) -> RowValueState:
    if storage_class == "null":
        return RowValueState.VALUE_NULL
    if (storage_class == "text" and value == "") or (
        storage_class == "blob" and blob_length == 0
    ):
        return RowValueState.VALUE_EMPTY
    expected_storage = {
        "TEXT": "text",
        "INTEGER": "integer",
        "BLOB": "blob",
    }[expected]
    if storage_class != expected_storage:
        return RowValueState.TYPE_MISMATCH
    return RowValueState.VALUE_PRESENT


def _row_from_sql(
    row: tuple[object, ...],
    context: FilesQueryContext,
    schema: ManifestSchemaValidationResult,
    *,
    include_raw_blob: bool,
) -> tuple[V2RowObservation, int]:
    locator = row[0]
    if not isinstance(locator, int) or isinstance(locator, bool):
        raise ValueError("row_locator_invalid")
    affinities = ("TEXT", "TEXT", "TEXT", "INTEGER", "BLOB")
    values: list[V2ColumnObservation] = []
    projected_bytes = LOCATOR_OVERHEAD_BYTES
    offset = 1
    for name, affinity in zip(PROJECTION[:4], affinities[:4], strict=True):
        raw, storage_class = row[offset], row[offset + 1]
        offset += 2
        if not isinstance(storage_class, str):
            raise ValueError("storage_class_invalid")
        projected_bytes += _payload_size(storage_class, raw, None)
        values.append(
            V2ColumnObservation(
                name,
                _value_state(storage_class, affinity, raw, None),
                affinity,
                storage_class.upper(),
                raw if isinstance(raw, (str, int, float, bytes)) else None,
            )
        )
    blob_length, blob_storage = row[offset], row[offset + 1]
    raw_blob = row[offset + 2] if include_raw_blob else None
    if blob_length is not None and (
        not isinstance(blob_length, int) or isinstance(blob_length, bool)
    ):
        raise ValueError("blob_length_invalid")
    if not isinstance(blob_storage, str):
        raise ValueError("storage_class_invalid")
    projected_bytes += _payload_size(blob_storage, None, blob_length)
    values.append(
        V2ColumnObservation(
            "file",
            _value_state(blob_storage, "BLOB", None, blob_length),
            "BLOB",
            blob_storage.upper(),
            None,
            (
                BlobAvailability.ABSENT
                if blob_storage == "null"
                else (
                    BlobAvailability.AVAILABLE_INTERNAL
                    if include_raw_blob
                    else BlobAvailability.PRESENT_BOUNDED
                )
            ),
            blob_length,
            raw_blob if isinstance(raw_blob, bytes) else None,
        )
    )
    return (
        V2RowObservation(
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
                "Files",
                context.processing_run_id,
            ),
            tuple(values),
            context.queried_at,
            READER_ID,
            READER_VERSION,
        ),
        projected_bytes,
    )


def _memory_for_row(projected_bytes: int) -> int:
    return (
        projected_bytes
        + ROW_OVERHEAD_BYTES
        + len(PROJECTION) * COLUMN_OVERHEAD_BYTES
        + LOCATOR_OVERHEAD_BYTES
    )


def _sqlite_failure_reason(error: sqlite3.Error) -> TerminationReason:
    code = getattr(error, "sqlite_errorcode", None)
    if code == sqlite3.SQLITE_CORRUPT:
        return TerminationReason.DATABASE_CORRUPT
    if code == sqlite3.SQLITE_NOTADB:
        return TerminationReason.DATABASE_INVALID
    return TerminationReason.SQLITE_READ_FAILURE


def _failure(
    context: FilesQueryContext,
    started_at: datetime,
    start_tick: float,
    stop_tick: float,
    stopped_at: datetime,
    completion: QueryCompletion,
    reason: TerminationReason,
    reason_code: str,
    *,
    observations: list[V2RowObservation] | None = None,
    attempted: int = 0,
    projected_bytes: int = 0,
    memory_estimate: int = PAGE_OVERHEAD_BYTES,
    continuation: V2ContinuationToken | None = None,
    resource: ResourceControlState | None = None,
) -> V2QueryResult:
    completed = observations or []
    last = completed[-1].row_locator.locator_value if completed else None
    return V2QueryResult(
        completion,
        reason,
        context,
        QUERY_PROFILE_ID,
        QUERY_PROFILE_VERSION,
        RESOURCE_PROFILE_ID,
        RESOURCE_PROFILE_VERSION,
        tuple(completed),
        attempted,
        len(completed),
        last,
        continuation,
        resource,
        projected_bytes,
        memory_estimate,
        started_at,
        stopped_at,
        max(0.0, stop_tick - start_tick),
        reason_code,
    )


def enumerate_files_rows_v2(
    controlled: ControlledSQLiteCopy,
    schema: ManifestSchemaValidationResult,
    context: FilesQueryContext,
    policy: QueryResourcePolicy,
    *,
    page_size: int,
    continuation: V2ContinuationToken | None = None,
    include_raw_blob: bool = False,
    raw_blob_authorized: bool = False,
    cancelled: CancelCheck = lambda: False,
    monotonic_clock: MonotonicClock = time.monotonic,
    audit_clock: AuditClock = lambda: datetime.now(timezone.utc),
    limiter: HierarchicalQueryLimiter = DEFAULT_LIMITER,
    _single_locator: int | None = None,
) -> V2QueryResult:
    """Enumerate v2 observations; callers must explicitly select this function."""

    start_tick = monotonic_clock()
    started_at = audit_clock()

    def fail(
        completion: QueryCompletion,
        reason: TerminationReason,
        code: str,
        **kwargs: object,
    ) -> V2QueryResult:
        return _failure(
            context,
            started_at,
            start_tick,
            monotonic_clock(),
            audit_clock(),
            completion,
            reason,
            code,
            **kwargs,  # type: ignore[arg-type]
        )

    if not _scope_matches(context, schema):
        return fail(
            QueryCompletion.QUERY_NOT_EVALUATED,
            TerminationReason.AUTHORIZATION_FAILURE,
            "query_not_authorized",
        )
    if schema.outcome not in {
        CompatibilityOutcome.SCHEMA_COMPATIBLE,
        CompatibilityOutcome.SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS,
    }:
        return fail(
            QueryCompletion.QUERY_NOT_EVALUATED,
            TerminationReason.SCHEMA_INCOMPATIBLE,
            "schema_incompatible",
        )
    if include_raw_blob and not raw_blob_authorized:
        return fail(
            QueryCompletion.QUERY_NOT_EVALUATED,
            TerminationReason.AUTHORIZATION_FAILURE,
            "raw_blob_projection_not_authorized",
        )
    if page_size <= 0 or page_size > policy.max_page_size:
        return fail(
            QueryCompletion.QUERY_NOT_EVALUATED,
            TerminationReason.PAGE_LIMIT_REACHED,
            "page_limit_reached",
            resource=ResourceControlState(
                "PAGE_SIZE",
                policy.max_page_size,
                page_size,
                EnforcementScope.PROCESSING_RUN,
                True,
                False,
                "configured logical row count",
            ),
        )
    if continuation is not None and not _token_valid(continuation, context):
        return fail(
            QueryCompletion.QUERY_NOT_EVALUATED,
            TerminationReason.AUTHORIZATION_FAILURE,
            "continuation_scope_or_profile_mismatch",
        )
    if cancelled():
        return fail(
            QueryCompletion.QUERY_NOT_EVALUATED,
            TerminationReason.CALLER_CANCELLED,
            "caller_cancelled",
        )

    observations: list[V2RowObservation] = []
    attempted = 0
    projected_bytes = 0
    memory_estimate = PAGE_OVERHEAD_BYTES + CONTINUATION_OVERHEAD_BYTES
    after = continuation.after_locator if continuation else None
    connection: sqlite3.Connection | None = None
    try:
        with limiter.acquire(context, policy):
            controlled.verify_working_files()
            connection = sqlite3.connect(controlled.read_only_uri, uri=True)
            connection.execute("PRAGMA query_only=ON")
            table = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE type='table' "
                "AND name='Files' COLLATE NOCASE"
            ).fetchone()
            if table and isinstance(table[0], str) and "WITHOUT ROWID" in table[0].upper():
                return fail(
                    QueryCompletion.QUERY_FAILED,
                    TerminationReason.LOCATOR_FAILURE,
                    "rowid_unavailable",
                )
            scalar_projection = (
                '"fileID",typeof("fileID"),"domain",typeof("domain"),'
                '"relativePath",typeof("relativePath"),"flags",typeof("flags"),'
                'length("file"),typeof("file")'
            )
            if _single_locator is not None:
                cursor = connection.execute(
                    f'SELECT rowid,{scalar_projection} FROM "Files" '
                    "WHERE rowid=? ORDER BY rowid ASC",
                    (_single_locator,),
                )
            elif after is None:
                cursor = connection.execute(
                    f'SELECT rowid,{scalar_projection} FROM "Files" '
                    "ORDER BY rowid ASC LIMIT ?",
                    (min(page_size, policy.max_rows) + 1,),
                )
            else:
                cursor = connection.execute(
                    f'SELECT rowid,{scalar_projection} FROM "Files" '
                    "WHERE rowid>? ORDER BY rowid ASC LIMIT ?",
                    (after, min(page_size, policy.max_rows) + 1),
                )
            while True:
                elapsed = monotonic_clock() - start_tick
                if cancelled():
                    token = _token(context, observations[-1].row_locator.locator_value if observations else after)
                    return fail(
                        QueryCompletion.QUERY_PARTIAL if observations else QueryCompletion.QUERY_NOT_EVALUATED,
                        TerminationReason.CALLER_CANCELLED,
                        "caller_cancelled",
                        observations=observations,
                        attempted=attempted,
                        projected_bytes=projected_bytes,
                        memory_estimate=memory_estimate,
                        continuation=token,
                    )
                if elapsed >= policy.max_wall_clock_seconds:
                    token = _token(context, observations[-1].row_locator.locator_value if observations else after)
                    return fail(
                        QueryCompletion.QUERY_PARTIAL if observations else QueryCompletion.QUERY_NOT_EVALUATED,
                        TerminationReason.WALL_CLOCK_LIMIT_REACHED,
                        "wall_clock_limit_reached",
                        observations=observations,
                        attempted=attempted,
                        projected_bytes=projected_bytes,
                        memory_estimate=memory_estimate,
                        continuation=token,
                        resource=ResourceControlState(
                            "WALL_CLOCK",
                            policy.max_wall_clock_seconds,
                            elapsed,
                            EnforcementScope.PROCESSING_RUN,
                            True,
                            True,
                            "monotonic elapsed seconds",
                        ),
                    )
                row = cursor.fetchone()
                if row is None:
                    break
                attempted += 1
                if len(observations) >= min(page_size, policy.max_rows):
                    token = _token(context, observations[-1].row_locator.locator_value)
                    reason = (
                        TerminationReason.ROW_LIMIT_REACHED
                        if policy.max_rows <= page_size
                        else TerminationReason.COMPLETED
                    )
                    completion = (
                        QueryCompletion.QUERY_PARTIAL
                        if reason is TerminationReason.ROW_LIMIT_REACHED
                        else QueryCompletion.QUERY_COMPLETE
                    )
                    return fail(
                        completion,
                        reason,
                        "row_limit_reached" if completion is QueryCompletion.QUERY_PARTIAL else "page_complete",
                        observations=observations,
                        attempted=attempted,
                        projected_bytes=projected_bytes,
                        memory_estimate=memory_estimate,
                        continuation=token,
                        resource=(
                            ResourceControlState(
                                "ROWS",
                                policy.max_rows,
                                len(observations),
                                EnforcementScope.PROCESSING_RUN,
                                True,
                                True,
                                "finalized row count",
                            )
                            if completion is QueryCompletion.QUERY_PARTIAL
                            else None
                        ),
                    )
                observation, row_bytes = _row_from_sql(
                    row, context, schema, include_raw_blob=False
                )
                next_memory = memory_estimate + _memory_for_row(row_bytes)
                if projected_bytes + row_bytes > policy.max_projected_bytes:
                    return fail(
                        QueryCompletion.QUERY_PARTIAL if observations else QueryCompletion.QUERY_NOT_EVALUATED,
                        TerminationReason.BYTE_LIMIT_REACHED,
                        "projected_byte_limit_reached",
                        observations=observations,
                        attempted=attempted,
                        projected_bytes=projected_bytes,
                        memory_estimate=memory_estimate,
                        continuation=_token(context, observations[-1].row_locator.locator_value if observations else after),
                        resource=ResourceControlState(
                            "PROJECTED_BYTES",
                            policy.max_projected_bytes,
                            projected_bytes + row_bytes,
                            EnforcementScope.PROCESSING_RUN,
                            True,
                            True,
                            "UTF-8/BLOB exact length plus fixed scalar and locator lengths",
                        ),
                    )
                if next_memory > policy.max_memory_estimate_bytes:
                    return fail(
                        QueryCompletion.QUERY_PARTIAL if observations else QueryCompletion.QUERY_NOT_EVALUATED,
                        TerminationReason.MEMORY_ESTIMATE_LIMIT_REACHED,
                        "memory_estimate_limit_reached",
                        observations=observations,
                        attempted=attempted,
                        projected_bytes=projected_bytes,
                        memory_estimate=memory_estimate,
                        continuation=_token(context, observations[-1].row_locator.locator_value if observations else after),
                        resource=ResourceControlState(
                            "DETERMINISTIC_QUERY_MEMORY_ESTIMATE",
                            policy.max_memory_estimate_bytes,
                            next_memory,
                            EnforcementScope.PROCESSING_RUN,
                            True,
                            True,
                            "resource profile v1 fixed overhead plus projected payload",
                        ),
                    )
                if include_raw_blob:
                    raw_blob_row = connection.execute(
                        'SELECT "file" FROM "Files" WHERE rowid=?',
                        (observation.row_locator.locator_value,),
                    ).fetchone()
                    if raw_blob_row is None:
                        raise sqlite3.DatabaseError("bounded_blob_row_unavailable")
                    observation, _ = _row_from_sql(
                        (*row, raw_blob_row[0]),
                        context,
                        schema,
                        include_raw_blob=True,
                    )
                observations.append(observation)
                projected_bytes += row_bytes
                memory_estimate = next_memory
            controlled.verify_working_files()
    except ConcurrencyDenied as error:
        return fail(
            QueryCompletion.QUERY_NOT_EVALUATED,
            TerminationReason.CONCURRENCY_LIMIT_REACHED,
            "concurrency_limit_reached",
            resource=ResourceControlState(
                "ACTIVE_QUERIES",
                1,
                1,
                error.scope,
                True,
                False,
                "application-level hierarchical active-query counter",
            ),
        )
    except ControlledCopyError:
        return fail(
            QueryCompletion.QUERY_PARTIAL if observations else QueryCompletion.QUERY_FAILED,
            TerminationReason.CONTROLLED_COPY_FAILURE,
            "controlled_copy_failure",
            observations=observations,
            attempted=attempted,
            projected_bytes=projected_bytes,
            memory_estimate=memory_estimate,
        )
    except (sqlite3.DatabaseError, sqlite3.OperationalError) as error:
        failure_reason = _sqlite_failure_reason(error)
        return fail(
            QueryCompletion.QUERY_PARTIAL if observations else QueryCompletion.QUERY_FAILED,
            failure_reason,
            {
                TerminationReason.DATABASE_CORRUPT: "database_corrupt",
                TerminationReason.DATABASE_INVALID: "database_invalid",
            }.get(failure_reason, "sqlite_read_failure"),
            observations=observations,
            attempted=attempted,
            projected_bytes=projected_bytes,
            memory_estimate=memory_estimate,
            continuation=(
                _token(context, observations[-1].row_locator.locator_value)
                if observations
                else None
            ),
        )
    finally:
        if connection is not None:
            connection.close()
    return fail(
        QueryCompletion.QUERY_COMPLETE,
        TerminationReason.COMPLETED,
        "query_complete",
        observations=observations,
        attempted=attempted,
        projected_bytes=projected_bytes,
        memory_estimate=memory_estimate,
    )


def retrieve_files_row_v2(
    controlled: ControlledSQLiteCopy,
    schema: ManifestSchemaValidationResult,
    context: FilesQueryContext,
    policy: QueryResourcePolicy,
    locator: RowLocator,
    *,
    include_raw_blob: bool = False,
    raw_blob_authorized: bool = False,
    cancelled: CancelCheck = lambda: False,
    monotonic_clock: MonotonicClock = time.monotonic,
    audit_clock: AuditClock = lambda: datetime.now(timezone.utc),
    limiter: HierarchicalQueryLimiter = DEFAULT_LIMITER,
) -> V2QueryResult:
    if (
        locator.processing_run_id != context.processing_run_id
        or locator.locator_version != LOCATOR_PROFILE_VERSION
        or locator.source_table.casefold() != "files"
    ):
        start = monotonic_clock()
        now = audit_clock()
        return _failure(
            context,
            now,
            start,
            monotonic_clock(),
            audit_clock(),
            QueryCompletion.QUERY_NOT_EVALUATED,
            TerminationReason.AUTHORIZATION_FAILURE,
            "row_locator_scope_mismatch",
        )
    return enumerate_files_rows_v2(
        controlled,
        schema,
        context,
        policy,
        page_size=1,
        include_raw_blob=include_raw_blob,
        raw_blob_authorized=raw_blob_authorized,
        cancelled=cancelled,
        monotonic_clock=monotonic_clock,
        audit_clock=audit_clock,
        limiter=limiter,
        _single_locator=locator.locator_value,
    )
