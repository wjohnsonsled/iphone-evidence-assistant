"""Fail-closed candidate observations for uninterpreted Manifest Files.flags."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid5

from app.manifest.files_query import FilesQueryContext, FilesRowObservation
from app.manifest.files_query_v2 import V2RowObservation
from app.manifest.identifier_normalization import StorageClass

PROFILE_ID = "manifestdb-flags-observation"
PROFILE_VERSION = "1"
SOURCE_TABLE = "Files"
SOURCE_COLUMN = "flags"
_NAMESPACE = UUID("06060000-0000-4000-8000-000000000001")
LIMITATIONS = (
    "No Files.flags bit meaning is approved by the governing repository; every set bit remains unknown.",
    "A numeric flags value does not establish file type, existence, deletion, tampering, or corruption.",
    "Zero does not establish absence, an ordinary file, or any physical-object state.",
    "No metadata BLOB field is decoded or interpreted by this profile.",
    "No capability is Supported by this candidate profile.",
)


class FlagsState(str, Enum):
    INTEGER_UNKNOWN_BITS = "INTEGER_UNKNOWN_BITS"
    ZERO_NO_BITS_SET = "ZERO_NO_BITS_SET"
    NEGATIVE_INTEGER_UNINTERPRETED = "NEGATIVE_INTEGER_UNINTERPRETED"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    NULL = "NULL"
    UNSUPPORTED_STORAGE_CLASS = "UNSUPPORTED_STORAGE_CLASS"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    READ_FAILURE = "READ_FAILURE"
    NOT_EVALUATED = "NOT_EVALUATED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class FlagsPolicy:
    max_bit_width: int

    def __post_init__(self) -> None:
        if type(self.max_bit_width) is not int or not 1 <= self.max_bit_width <= 4096:
            raise ValueError("flags_policy_invalid")


@dataclass(frozen=True, slots=True)
class FlagsSourceObservation:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    controlled_copy_identity_id: UUID
    database_identity_id: UUID
    processing_run_id: UUID
    row_locator: int
    query_profile_id: str
    query_profile_version: str
    locator_profile_id: str
    locator_profile_version: str
    source_table: str
    source_column: str
    storage_class: StorageClass
    upstream_value_state: str
    raw_value: str | int | float | bytes | None
    observed_at: datetime
    synthetic_fixture: bool = False

    def __post_init__(self) -> None:
        identities = (
            self.tenant_id, self.case_id, self.evidence_source_id,
            self.source_artifact_id, self.controlled_copy_identity_id,
            self.database_identity_id, self.processing_run_id,
        )
        if any(not isinstance(item, UUID) for item in identities):
            raise ValueError("flags_provenance_incomplete")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("flags_time_invalid")
        if (self.source_table, self.source_column) != (SOURCE_TABLE, SOURCE_COLUMN):
            raise ValueError("flags_source_invalid")
        if (
            self.query_profile_id != "manifestdb-files-query"
            or self.query_profile_version not in {"1", "2"}
            or self.locator_profile_id != "manifestdb-row-locator"
            or self.locator_profile_version != "1"
        ):
            raise ValueError("flags_upstream_profile_invalid")
        expected = {
            StorageClass.NULL: type(None), StorageClass.INTEGER: int,
            StorageClass.REAL: float, StorageClass.TEXT: str, StorageClass.BLOB: bytes,
        }[self.storage_class]
        unavailable = {"NOT_AVAILABLE", "NOT_PROJECTED", "READ_FAILURE", "NOT_EVALUATED", "INDETERMINATE"}
        if type(self.raw_value) is not expected and not (
            self.upstream_value_state in unavailable and self.raw_value is None
        ):
            raise ValueError("flags_storage_value_mismatch")


@dataclass(frozen=True, slots=True)
class FlagsObservation:
    observation_id: UUID
    source: FlagsSourceObservation
    profile_id: str
    profile_version: str
    state: FlagsState
    numeric_representation: int | None
    known_meanings: tuple[str, ...]
    unknown_bit_positions: tuple[int, ...]
    bit_width: int | None
    observed_at: datetime
    limitations: tuple[str, ...] = LIMITATIONS

    def canonical_json(self) -> str:
        source = asdict(self.source)
        for key in ("tenant_id", "case_id", "evidence_source_id", "source_artifact_id",
                    "controlled_copy_identity_id", "database_identity_id", "processing_run_id"):
            source[key] = str(source[key])
        source["storage_class"] = self.source.storage_class.value
        source["observed_at"] = self.source.observed_at.isoformat()
        if isinstance(self.source.raw_value, bytes):
            source["raw_value"] = {"representation": "BLOB_NOT_SERIALIZED", "byte_length": len(self.source.raw_value)}
        payload = {
            "observation_id": str(self.observation_id), "source": source,
            "profile_id": self.profile_id, "profile_version": self.profile_version,
            "state": self.state.value, "numeric_representation": self.numeric_representation,
            "known_meanings": list(self.known_meanings),
            "unknown_bit_positions": list(self.unknown_bit_positions),
            "bit_width": self.bit_width, "observed_at": self.observed_at.isoformat(),
            "limitations": list(self.limitations),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def observe_flags(source: FlagsSourceObservation, policy: FlagsPolicy) -> FlagsObservation:
    state = FlagsState.INDETERMINATE
    numeric = None
    unknown: tuple[int, ...] = ()
    width = None
    upstream = source.upstream_value_state
    if upstream == "READ_FAILURE":
        state = FlagsState.READ_FAILURE
    elif upstream in {"NOT_AVAILABLE", "NOT_PROJECTED"}:
        state = FlagsState.SOURCE_UNAVAILABLE
    elif upstream == "NOT_EVALUATED":
        state = FlagsState.NOT_EVALUATED
    elif upstream == "INDETERMINATE":
        state = FlagsState.INDETERMINATE
    elif source.storage_class is StorageClass.NULL:
        state = FlagsState.NULL
    elif source.storage_class is not StorageClass.INTEGER:
        state = FlagsState.UNSUPPORTED_STORAGE_CLASS
    elif type(source.raw_value) is not int:
        state = FlagsState.INDETERMINATE
    else:
        numeric = source.raw_value
        if numeric < 0:
            state = FlagsState.NEGATIVE_INTEGER_UNINTERPRETED
        else:
            width = numeric.bit_length()
            if width > policy.max_bit_width:
                state = FlagsState.RESOURCE_LIMIT_EXCEEDED
            elif numeric == 0:
                state = FlagsState.ZERO_NO_BITS_SET
            else:
                state = FlagsState.INTEGER_UNKNOWN_BITS
                unknown = tuple(index for index in range(width) if numeric & (1 << index))
    stable = uuid5(_NAMESPACE, "|".join((
        str(source.tenant_id), str(source.case_id), str(source.source_artifact_id),
        str(source.processing_run_id), str(source.row_locator), repr(source.raw_value),
        str(policy.max_bit_width), PROFILE_ID, PROFILE_VERSION,
    )))
    return FlagsObservation(
        stable, source, PROFILE_ID, PROFILE_VERSION, state, numeric, (), unknown,
        width, source.observed_at,
    )


def _source(row: FilesRowObservation | V2RowObservation, context: FilesQueryContext, copy_id: UUID) -> FlagsSourceObservation:
    if (
        (context.tenant_id, context.case_id, context.evidence_source_id, context.processing_run_id) != context.authorized_scope
        or row.processing_run_id != context.processing_run_id
        or row.source_artifact_id != context.source_artifact_id
        or row.database_identity_id != context.database_identity_id
    ):
        raise ValueError("flags_scope_mismatch")
    value = next((item for item in row.projected_values if item.column_name == SOURCE_COLUMN), None)
    if value is None:
        raise ValueError("flags_not_projected")
    if isinstance(row, FilesRowObservation):
        storage = StorageClass({"NoneType": "NULL", "int": "INTEGER", "float": "REAL", "str": "TEXT", "bytes": "BLOB"}[value.observed_sqlite_type])
        observed_at = row.queried_at
    else:
        storage = StorageClass(value.observed_storage_class)
        observed_at = row.observed_at
    return FlagsSourceObservation(
        context.tenant_id, context.case_id, context.evidence_source_id,
        context.source_artifact_id, copy_id, context.database_identity_id,
        context.processing_run_id, row.row_locator.locator_value,
        row.query_profile_id, row.query_profile_version, "manifestdb-row-locator",
        row.row_locator.locator_version, SOURCE_TABLE, SOURCE_COLUMN, storage,
        value.state.value, value.raw_value, observed_at,
    )


def source_from_v1(row: FilesRowObservation, context: FilesQueryContext, copy_id: UUID) -> FlagsSourceObservation:
    return _source(row, context, copy_id)


def source_from_v2(row: V2RowObservation, context: FilesQueryContext, copy_id: UUID) -> FlagsSourceObservation:
    return _source(row, context, copy_id)


def synthetic_source(value: str | int | float | bytes | None, storage: StorageClass, *, state: str = "VALUE_PRESENT") -> FlagsSourceObservation:
    def uid(n: int) -> UUID:
        return UUID(f"06060000-0000-4000-8000-{n:012d}")
    return FlagsSourceObservation(
        uid(1), uid(2), uid(3), uid(4), uid(5), uid(6), uid(7), 1,
        "manifestdb-files-query", "2", "manifestdb-row-locator", "1",
        SOURCE_TABLE, SOURCE_COLUMN, storage, state, value,
        datetime(2026, 7, 29, tzinfo=timezone.utc), True,
    )
