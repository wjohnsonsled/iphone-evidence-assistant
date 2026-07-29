"""Candidate-only lexical observations for Manifest.db Files.relativePath."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid5

from app.manifest.files_query import FilesQueryContext, FilesRowObservation
from app.manifest.files_query_v2 import V2RowObservation
from app.manifest.identifier_normalization import StorageClass

PROFILE_ID = "manifestdb-relative-path-lexical"
PROFILE_VERSION = "1"
IMPLEMENTATION_ID = "manifestdb-relative-path-observer"
IMPLEMENTATION_VERSION = "1"
SOURCE_TABLE = "Files"
SOURCE_COLUMN = "relativePath"
_NAMESPACE = UUID("06050000-0000-4000-8000-000000000001")
_DRIVE_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")

LIMITATIONS = (
    "Lexical path safety is not filesystem resolution, file existence, or artifact identity.",
    "No host path is constructed and no symlink, case, or filesystem semantics are evaluated.",
    "Canonical comparison representation is lexical agreement only, not physical-object identity.",
    "An empty path is preserved and is not interpreted as a root or existing object.",
    "No capability is Supported by this candidate profile.",
)


class PathState(str, Enum):
    SAFE_RELATIVE = "SAFE_RELATIVE"
    EMPTY = "EMPTY"
    UNSAFE_ABSOLUTE = "UNSAFE_ABSOLUTE"
    UNSAFE_PARENT_TRAVERSAL = "UNSAFE_PARENT_TRAVERSAL"
    UNSAFE_DOT_SEGMENT = "UNSAFE_DOT_SEGMENT"
    UNSAFE_REPEATED_SEPARATOR = "UNSAFE_REPEATED_SEPARATOR"
    UNSAFE_ALTERNATE_SEPARATOR = "UNSAFE_ALTERNATE_SEPARATOR"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    NULL = "NULL"
    UNSUPPORTED_STORAGE_CLASS = "UNSUPPORTED_STORAGE_CLASS"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    READ_FAILURE = "READ_FAILURE"
    NOT_EVALUATED = "NOT_EVALUATED"
    INDETERMINATE = "INDETERMINATE"


class EncodingState(str, Enum):
    ASCII = "ASCII"
    UNICODE_TEXT = "UNICODE_TEXT"
    EMPTY = "EMPTY"
    NOT_TEXT = "NOT_TEXT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class RelativePathPolicy:
    max_characters: int
    max_utf8_bytes: int
    max_segments: int

    def __post_init__(self) -> None:
        for value in (self.max_characters, self.max_utf8_bytes, self.max_segments):
            if type(value) is not int or value <= 0:
                raise ValueError("relative_path_policy_invalid")


@dataclass(frozen=True, slots=True)
class RelativePathSourceObservation:
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
            raise ValueError("relative_path_provenance_incomplete")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("relative_path_time_invalid")
        if (self.source_table, self.source_column) != (SOURCE_TABLE, SOURCE_COLUMN):
            raise ValueError("relative_path_source_invalid")
        if (
            self.query_profile_id != "manifestdb-files-query"
            or self.query_profile_version not in {"1", "2"}
            or self.locator_profile_id != "manifestdb-row-locator"
            or self.locator_profile_version != "1"
        ):
            raise ValueError("relative_path_upstream_profile_invalid")
        expected = {
            StorageClass.NULL: type(None), StorageClass.INTEGER: int,
            StorageClass.REAL: float, StorageClass.TEXT: str,
            StorageClass.BLOB: bytes,
        }[self.storage_class]
        unavailable = {
            "NOT_AVAILABLE", "NOT_PROJECTED", "READ_FAILURE",
            "NOT_EVALUATED", "INDETERMINATE",
        }
        if type(self.raw_value) is not expected and not (
            self.upstream_value_state in unavailable and self.raw_value is None
        ):
            raise ValueError("relative_path_storage_value_mismatch")


@dataclass(frozen=True, slots=True)
class RelativePathObservation:
    observation_id: UUID
    source: RelativePathSourceObservation
    profile_id: str
    profile_version: str
    state: PathState
    encoding_state: EncodingState
    lexical_segments: tuple[str, ...]
    canonical_comparison_representation: str | None
    character_length: int | None
    utf8_byte_length: int | None
    segment_count: int | None
    has_forward_separator: bool | None
    has_alternate_separator: bool | None
    implementation_id: str
    implementation_version: str
    observed_at: datetime
    limitations: tuple[str, ...] = LIMITATIONS

    def canonical_json(self) -> str:
        source = asdict(self.source)
        for key in (
            "tenant_id", "case_id", "evidence_source_id", "source_artifact_id",
            "controlled_copy_identity_id", "database_identity_id", "processing_run_id",
        ):
            source[key] = str(source[key])
        source["storage_class"] = self.source.storage_class.value
        source["observed_at"] = self.source.observed_at.isoformat()
        if isinstance(self.source.raw_value, bytes):
            source["raw_value"] = {
                "representation": "BLOB_NOT_SERIALIZED",
                "byte_length": len(self.source.raw_value),
            }
        payload = {
            "observation_id": str(self.observation_id),
            "source": source,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "state": self.state.value,
            "encoding_state": self.encoding_state.value,
            "lexical_segments": list(self.lexical_segments),
            "canonical_comparison_representation": self.canonical_comparison_representation,
            "character_length": self.character_length,
            "utf8_byte_length": self.utf8_byte_length,
            "segment_count": self.segment_count,
            "has_forward_separator": self.has_forward_separator,
            "has_alternate_separator": self.has_alternate_separator,
            "implementation_id": self.implementation_id,
            "implementation_version": self.implementation_version,
            "observed_at": self.observed_at.isoformat(),
            "limitations": list(self.limitations),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _stable_id(source: RelativePathSourceObservation, policy: RelativePathPolicy) -> UUID:
    return uuid5(
        _NAMESPACE,
        "|".join((
            str(source.tenant_id), str(source.case_id), str(source.source_artifact_id),
            str(source.controlled_copy_identity_id), str(source.processing_run_id),
            str(source.row_locator), source.storage_class.value, repr(source.raw_value),
            str(policy.max_characters), str(policy.max_utf8_bytes),
            str(policy.max_segments), PROFILE_ID, PROFILE_VERSION,
        )),
    )


def observe_relative_path(
    source: RelativePathSourceObservation, policy: RelativePathPolicy
) -> RelativePathObservation:
    if source.source_column != SOURCE_COLUMN:
        raise ValueError("relative_path_source_invalid")
    state = PathState.INDETERMINATE
    encoding = EncodingState.UNKNOWN
    segments: tuple[str, ...] = ()
    canonical = None
    characters = byte_length = segment_count = None
    forward = alternate = None

    if source.upstream_value_state == "READ_FAILURE":
        state = PathState.READ_FAILURE
    elif source.upstream_value_state in {"NOT_AVAILABLE", "NOT_PROJECTED"}:
        state = PathState.SOURCE_UNAVAILABLE
    elif source.upstream_value_state == "NOT_EVALUATED":
        state = PathState.NOT_EVALUATED
    elif source.upstream_value_state == "INDETERMINATE":
        state = PathState.INDETERMINATE
    elif source.storage_class is StorageClass.NULL:
        state, encoding = PathState.NULL, EncodingState.NOT_TEXT
    elif source.storage_class is not StorageClass.TEXT:
        state, encoding = PathState.UNSUPPORTED_STORAGE_CLASS, EncodingState.NOT_TEXT
    elif not isinstance(source.raw_value, str):
        state = PathState.INDETERMINATE
    else:
        raw = source.raw_value
        characters = len(raw)
        byte_length = len(raw.encode("utf-8"))
        encoding = EncodingState.EMPTY if not raw else (
            EncodingState.ASCII if raw.isascii() else EncodingState.UNICODE_TEXT
        )
        forward, alternate = "/" in raw, "\\" in raw
        segments = tuple(raw.split("/")) if raw else ()
        segment_count = len(segments)
        if (
            characters > policy.max_characters
            or byte_length > policy.max_utf8_bytes
            or segment_count > policy.max_segments
        ):
            state = PathState.RESOURCE_LIMIT_EXCEEDED
            segments = ()
        elif not raw:
            state = PathState.EMPTY
        elif raw.startswith(("/", "\\")) or _DRIVE_ABSOLUTE.match(raw):
            state = PathState.UNSAFE_ABSOLUTE
        elif "\\" in raw:
            state = PathState.UNSAFE_ALTERNATE_SEPARATOR
        elif "//" in raw:
            state = PathState.UNSAFE_REPEATED_SEPARATOR
        elif ".." in segments:
            state = PathState.UNSAFE_PARENT_TRAVERSAL
        elif "." in segments:
            state = PathState.UNSAFE_DOT_SEGMENT
        else:
            state = PathState.SAFE_RELATIVE
            canonical = raw

    return RelativePathObservation(
        _stable_id(source, policy), source, PROFILE_ID, PROFILE_VERSION, state,
        encoding, segments, canonical, characters, byte_length, segment_count,
        forward, alternate, IMPLEMENTATION_ID, IMPLEMENTATION_VERSION,
        source.observed_at,
    )


def _context_valid(context: FilesQueryContext) -> bool:
    return (
        context.tenant_id, context.case_id, context.evidence_source_id,
        context.processing_run_id,
    ) == context.authorized_scope


def _source(
    row: FilesRowObservation | V2RowObservation,
    context: FilesQueryContext,
    controlled_copy_identity_id: UUID,
) -> RelativePathSourceObservation:
    if (
        not _context_valid(context)
        or row.processing_run_id != context.processing_run_id
        or row.source_artifact_id != context.source_artifact_id
        or row.database_identity_id != context.database_identity_id
    ):
        raise ValueError("relative_path_scope_mismatch")
    value = next((item for item in row.projected_values if item.column_name == SOURCE_COLUMN), None)
    if value is None:
        raise ValueError("relative_path_not_projected")
    if isinstance(row, FilesRowObservation):
        mapping = {"NoneType": "NULL", "int": "INTEGER", "float": "REAL", "str": "TEXT", "bytes": "BLOB"}
        storage = StorageClass(mapping[value.observed_sqlite_type])
        observed_at = row.queried_at
    else:
        storage = StorageClass(value.observed_storage_class)
        observed_at = row.observed_at
    return RelativePathSourceObservation(
        context.tenant_id, context.case_id, context.evidence_source_id,
        context.source_artifact_id, controlled_copy_identity_id,
        context.database_identity_id, context.processing_run_id,
        row.row_locator.locator_value, row.query_profile_id,
        row.query_profile_version, "manifestdb-row-locator",
        row.row_locator.locator_version, SOURCE_TABLE, SOURCE_COLUMN, storage,
        value.state.value, value.raw_value, observed_at,
    )


def source_from_v1(row: FilesRowObservation, context: FilesQueryContext, copy_id: UUID) -> RelativePathSourceObservation:
    return _source(row, context, copy_id)


def source_from_v2(row: V2RowObservation, context: FilesQueryContext, copy_id: UUID) -> RelativePathSourceObservation:
    return _source(row, context, copy_id)


def synthetic_source(
    value: str | int | float | bytes | None,
    storage_class: StorageClass,
    *,
    state: str = "VALUE_PRESENT",
    seed: int = 1,
) -> RelativePathSourceObservation:
    def uid(n: int) -> UUID:
        return UUID(f"06050000-0000-4000-8000-{n:012d}")
    return RelativePathSourceObservation(
        uid(1), uid(2), uid(3), uid(4), uid(5), uid(6), uid(7), seed,
        "manifestdb-files-query", "2", "manifestdb-row-locator", "1",
        SOURCE_TABLE, SOURCE_COLUMN, storage_class, state, value,
        datetime(2026, 7, 29, tzinfo=timezone.utc), True,
    )
