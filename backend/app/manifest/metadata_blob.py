"""Bounded, non-instantiating binary-plist characterization for Files.file."""

from __future__ import annotations

import json
import struct
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable
from uuid import UUID, uuid5

from app.manifest.files_query import FilesQueryContext, FilesRowObservation
from app.manifest.files_query_v2 import V2RowObservation
from app.manifest.identifier_normalization import StorageClass

PROFILE_ID = "manifestdb-file-bplist-syntax"
PROFILE_VERSION = "1"
SOURCE_TABLE = "Files"
SOURCE_COLUMN = "file"
_NAMESPACE = UUID("06070000-0000-4000-8000-000000000001")
LIMITATIONS = (
    "This profile characterizes bounded binary-plist syntax only; it does not instantiate archived classes.",
    "Decoded scalar syntax and graph references do not establish metadata-field meaning.",
    "Unknown tokens, classes, keys, versions, and object graphs remain uninterpreted.",
    "Metadata syntax does not establish file existence, artifact identity, completeness, compatibility, or support.",
    "No capability is Supported by this candidate profile.",
)


class BlobState(str, Enum):
    BINARY_PLIST_SYNTACTICALLY_DECODED = "BINARY_PLIST_SYNTACTICALLY_DECODED"
    EMPTY = "EMPTY"
    UNKNOWN_FORMAT = "UNKNOWN_FORMAT"
    MALFORMED = "MALFORMED"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    CANCELLED = "CANCELLED"
    NULL = "NULL"
    UNSUPPORTED_STORAGE_CLASS = "UNSUPPORTED_STORAGE_CLASS"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    READ_FAILURE = "READ_FAILURE"
    NOT_EVALUATED = "NOT_EVALUATED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class BlobPolicy:
    max_blob_bytes: int
    max_objects: int
    max_nesting_depth: int
    max_string_bytes: int
    max_collection_items: int
    max_decoded_bytes: int
    max_wall_seconds: float

    def __post_init__(self) -> None:
        integers = (
            self.max_blob_bytes, self.max_objects, self.max_nesting_depth,
            self.max_string_bytes, self.max_collection_items,
            self.max_decoded_bytes,
        )
        if any(type(value) is not int or value <= 0 for value in integers):
            raise ValueError("metadata_blob_policy_invalid")
        if type(self.max_wall_seconds) not in {int, float} or self.max_wall_seconds <= 0:
            raise ValueError("metadata_blob_policy_invalid")


@dataclass(frozen=True, slots=True)
class BlobSourceObservation:
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
    raw_blob_authorized: bool
    synthetic_fixture: bool = False

    def __post_init__(self) -> None:
        identities = (
            self.tenant_id, self.case_id, self.evidence_source_id,
            self.source_artifact_id, self.controlled_copy_identity_id,
            self.database_identity_id, self.processing_run_id,
        )
        if any(not isinstance(item, UUID) for item in identities):
            raise ValueError("metadata_blob_provenance_incomplete")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("metadata_blob_time_invalid")
        if (self.source_table, self.source_column) != (SOURCE_TABLE, SOURCE_COLUMN):
            raise ValueError("metadata_blob_source_invalid")
        if (
            self.query_profile_id != "manifestdb-files-query"
            or self.query_profile_version not in {"1", "2"}
            or self.locator_profile_id != "manifestdb-row-locator"
            or self.locator_profile_version != "1"
        ):
            raise ValueError("metadata_blob_upstream_profile_invalid")
        if self.storage_class is StorageClass.BLOB and isinstance(self.raw_value, bytes):
            if not self.raw_blob_authorized:
                raise ValueError("metadata_blob_bytes_not_authorized")


@dataclass(frozen=True, slots=True)
class SyntacticNode:
    object_index: int
    byte_offset: int
    type_name: str
    logical_length: int | None
    references: tuple[int, ...]
    scalar_value: str | int | float | bool | None
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BlobObservation:
    observation_id: UUID
    source: BlobSourceObservation
    profile_id: str
    profile_version: str
    state: BlobState
    format_name: str | None
    format_version: str | None
    declared_object_count: int | None
    top_object_index: int | None
    nodes: tuple[SyntacticNode, ...]
    decoded_bytes_estimate: int
    max_observed_depth: int | None
    failure_code: str | None
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
            "observation_id": str(self.observation_id), "source": source,
            "profile_id": self.profile_id, "profile_version": self.profile_version,
            "state": self.state.value, "format_name": self.format_name,
            "format_version": self.format_version,
            "declared_object_count": self.declared_object_count,
            "top_object_index": self.top_object_index,
            "nodes": [asdict(node) for node in self.nodes],
            "decoded_bytes_estimate": self.decoded_bytes_estimate,
            "max_observed_depth": self.max_observed_depth,
            "failure_code": self.failure_code,
            "observed_at": self.observed_at.isoformat(),
            "limitations": list(self.limitations),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class _Stop(Exception):
    def __init__(self, state: BlobState, code: str) -> None:
        self.state, self.code = state, code


def _unsigned(data: bytes) -> int:
    return int.from_bytes(data, "big", signed=False)


def _read(data: bytes, start: int, size: int, boundary: int) -> bytes:
    if size < 0 or start < 8 or start + size > boundary:
        raise ValueError("object_payload_out_of_bounds")
    return data[start:start + size]


def _length(data: bytes, position: int, nibble: int, boundary: int) -> tuple[int, int]:
    if nibble < 15:
        return nibble, position
    marker = _read(data, position, 1, boundary)[0]
    if marker >> 4 != 1 or marker & 0x0F > 3:
        raise ValueError("extended_length_invalid")
    width = 1 << (marker & 0x0F)
    raw = _read(data, position + 1, width, boundary)
    return _unsigned(raw), position + 1 + width


def characterize_metadata_blob(
    source: BlobSourceObservation,
    policy: BlobPolicy,
    *,
    cancel: Callable[[], bool] = lambda: False,
    monotonic: Callable[[], float],
) -> BlobObservation:
    nodes: list[SyntacticNode] = []
    state, code = BlobState.INDETERMINATE, None
    format_name = format_version = None
    count = top = depth = None
    decoded = 0
    started = monotonic()

    def stop_check() -> None:
        if cancel():
            raise _Stop(BlobState.CANCELLED, "metadata_blob_cancelled")
        if monotonic() - started >= policy.max_wall_seconds:
            raise _Stop(BlobState.RESOURCE_LIMIT_EXCEEDED, "metadata_blob_time_limit")

    try:
        upstream = source.upstream_value_state
        if upstream == "READ_FAILURE":
            raise _Stop(BlobState.READ_FAILURE, "source_read_failure")
        if upstream in {"NOT_AVAILABLE", "NOT_PROJECTED"}:
            raise _Stop(BlobState.SOURCE_UNAVAILABLE, "source_unavailable")
        if upstream == "NOT_EVALUATED":
            raise _Stop(BlobState.NOT_EVALUATED, "source_not_evaluated")
        if upstream == "INDETERMINATE":
            raise _Stop(BlobState.INDETERMINATE, "source_indeterminate")
        if source.storage_class is StorageClass.NULL:
            raise _Stop(BlobState.NULL, "source_null")
        if source.storage_class is not StorageClass.BLOB:
            raise _Stop(BlobState.UNSUPPORTED_STORAGE_CLASS, "source_not_blob")
        if not isinstance(source.raw_value, bytes):
            raise _Stop(BlobState.INDETERMINATE, "blob_bytes_unavailable")
        data = source.raw_value
        if not data:
            raise _Stop(BlobState.EMPTY, "blob_empty")
        if len(data) > policy.max_blob_bytes:
            raise _Stop(BlobState.RESOURCE_LIMIT_EXCEEDED, "blob_size_limit")
        if not data.startswith(b"bplist"):
            raise _Stop(BlobState.UNKNOWN_FORMAT, "format_unrecognized")
        if len(data) < 40 or data[:8] != b"bplist00":
            raise _Stop(BlobState.MALFORMED, "binary_plist_header_invalid")
        format_name, format_version = "BINARY_PLIST", "00"
        offset_size, ref_size, count, top, table_offset = struct.unpack(
            ">6xBBQQQ", data[-32:]
        )
        if not (1 <= offset_size <= 8 and 1 <= ref_size <= 8):
            raise _Stop(BlobState.MALFORMED, "binary_plist_width_invalid")
        if count == 0 or count > policy.max_objects:
            raise _Stop(BlobState.RESOURCE_LIMIT_EXCEEDED, "object_count_limit")
        if top >= count:
            raise _Stop(BlobState.MALFORMED, "top_object_invalid")
        table_bytes = count * offset_size
        if table_offset < 8 or table_offset + table_bytes > len(data) - 32:
            raise _Stop(BlobState.MALFORMED, "offset_table_invalid")
        offsets = tuple(
            _unsigned(data[table_offset + i * offset_size:table_offset + (i + 1) * offset_size])
            for i in range(count)
        )
        if any(offset < 8 or offset >= table_offset for offset in offsets):
            raise _Stop(BlobState.MALFORMED, "object_offset_invalid")
        if len(set(offsets)) != len(offsets):
            raise _Stop(BlobState.MALFORMED, "object_offset_duplicate")
        ordered_offsets = sorted(offsets)
        object_boundaries = {
            offset: (
                ordered_offsets[position + 1]
                if position + 1 < len(ordered_offsets)
                else table_offset
            )
            for position, offset in enumerate(ordered_offsets)
        }

        for index, offset in enumerate(offsets):
            stop_check()
            object_boundary = object_boundaries[offset]
            token = _read(data, offset, 1, object_boundary)[0]
            high, low = token >> 4, token & 0x0F
            position = offset + 1
            references: tuple[int, ...] = ()
            scalar: str | int | float | bool | None = None
            logical: int | None = None
            node_limits: tuple[str, ...] = ()
            if token in {0x00, 0x08, 0x09, 0x0F}:
                names = {0x00: "NULL", 0x08: "FALSE", 0x09: "TRUE", 0x0F: "FILL"}
                name = names[token]
                scalar = {0x00: None, 0x08: False, 0x09: True, 0x0F: None}[token]
            elif high == 1:
                width = 1 << low
                if width > 16:
                    raise ValueError("integer_width_unsupported")
                raw = _read(data, position, width, object_boundary)
                name, logical, scalar = "INTEGER", width, int.from_bytes(raw, "big", signed=width >= 8)
                decoded += width
            elif high == 2 and low in {2, 3}:
                width = 1 << low
                raw = _read(data, position, width, object_boundary)
                name, logical = "REAL", width
                scalar = struct.unpack(">f" if width == 4 else ">d", raw)[0]
                decoded += width
            elif token == 0x33:
                raw = _read(data, position, 8, object_boundary)
                name, logical, scalar = "DATE_SECONDS_2001_EPOCH", 8, struct.unpack(">d", raw)[0]
                decoded += 8
            elif high in {4, 5, 6}:
                length, position = _length(data, position, low, object_boundary)
                size = length * (2 if high == 6 else 1)
                if size > policy.max_string_bytes:
                    raise _Stop(BlobState.RESOURCE_LIMIT_EXCEEDED, "scalar_size_limit")
                raw = _read(data, position, size, object_boundary)
                logical = length
                if high == 4:
                    name, scalar = "DATA", None
                    node_limits = ("Raw DATA bytes are not emitted or interpreted.",)
                elif high == 5:
                    name, scalar = "ASCII_STRING", raw.decode("ascii")
                else:
                    name, scalar = "UNICODE_STRING", raw.decode("utf-16be")
                decoded += size
            elif high == 8:
                width = low + 1
                raw = _read(data, position, width, object_boundary)
                name, logical, scalar = "UID", width, _unsigned(raw)
                node_limits = ("UID is a syntactic scalar, not an instantiated object reference.",)
                decoded += width
            elif high in {10, 13}:
                length, position = _length(data, position, low, object_boundary)
                if length > policy.max_collection_items:
                    raise _Stop(BlobState.RESOURCE_LIMIT_EXCEEDED, "collection_size_limit")
                ref_count = length * (2 if high == 13 else 1)
                raw = _read(data, position, ref_count * ref_size, object_boundary)
                references = tuple(
                    _unsigned(raw[i:i + ref_size]) for i in range(0, len(raw), ref_size)
                )
                if any(reference >= count for reference in references):
                    raise ValueError("object_reference_invalid")
                name = "DICTIONARY" if high == 13 else "ARRAY"
                logical = length
                decoded += len(raw)
            else:
                raise ValueError("object_token_unsupported")
            decoded += 64
            if decoded > policy.max_decoded_bytes:
                raise _Stop(BlobState.RESOURCE_LIMIT_EXCEEDED, "decoded_memory_limit")
            nodes.append(SyntacticNode(index, offset, name, logical, references, scalar, node_limits))

        adjacency = {node.object_index: node.references for node in nodes}
        stack: list[tuple[int, int, frozenset[int]]] = [(top, 1, frozenset())]
        depth = 0
        while stack:
            stop_check()
            current, current_depth, ancestors = stack.pop()
            if current in ancestors:
                raise _Stop(BlobState.MALFORMED, "object_graph_cycle")
            if current_depth > policy.max_nesting_depth:
                raise _Stop(BlobState.RESOURCE_LIMIT_EXCEEDED, "nesting_depth_limit")
            depth = max(depth, current_depth)
            next_ancestors = ancestors | {current}
            stack.extend((child, current_depth + 1, next_ancestors) for child in adjacency[current])
        state = BlobState.BINARY_PLIST_SYNTACTICALLY_DECODED
    except _Stop as stopped:
        state, code = stopped.state, stopped.code
    except (UnicodeDecodeError, ValueError, struct.error, OverflowError, IndexError):
        state, code = BlobState.MALFORMED, "binary_plist_malformed"

    stable = uuid5(_NAMESPACE, "|".join((
        str(source.tenant_id), str(source.case_id), str(source.source_artifact_id),
        str(source.processing_run_id), str(source.row_locator), str(len(source.raw_value) if isinstance(source.raw_value, bytes) else -1),
        PROFILE_ID, PROFILE_VERSION,
    )))
    return BlobObservation(
        stable, source, PROFILE_ID, PROFILE_VERSION, state, format_name,
        format_version, count, top, tuple(nodes), decoded, depth, code,
        source.observed_at,
    )


def _source(row: FilesRowObservation | V2RowObservation, context: FilesQueryContext, copy_id: UUID, *, authorized: bool) -> BlobSourceObservation:
    if (
        (context.tenant_id, context.case_id, context.evidence_source_id, context.processing_run_id) != context.authorized_scope
        or row.processing_run_id != context.processing_run_id
        or row.source_artifact_id != context.source_artifact_id
        or row.database_identity_id != context.database_identity_id
    ):
        raise ValueError("metadata_blob_scope_mismatch")
    value = next((item for item in row.projected_values if item.column_name == SOURCE_COLUMN), None)
    if value is None:
        raise ValueError("metadata_blob_not_projected")
    if isinstance(row, FilesRowObservation):
        storage = StorageClass({"NoneType": "NULL", "int": "INTEGER", "float": "REAL", "str": "TEXT", "bytes": "BLOB"}[value.observed_sqlite_type])
        raw, observed_at = value.raw_value, row.queried_at
    else:
        storage = StorageClass(value.observed_storage_class)
        raw, observed_at = value.raw_blob, row.observed_at
    return BlobSourceObservation(
        context.tenant_id, context.case_id, context.evidence_source_id,
        context.source_artifact_id, copy_id, context.database_identity_id,
        context.processing_run_id, row.row_locator.locator_value,
        row.query_profile_id, row.query_profile_version, "manifestdb-row-locator",
        row.row_locator.locator_version, SOURCE_TABLE, SOURCE_COLUMN, storage,
        value.state.value, raw, observed_at, authorized,
    )


def source_from_v1(row: FilesRowObservation, context: FilesQueryContext, copy_id: UUID, *, raw_blob_authorized: bool) -> BlobSourceObservation:
    return _source(row, context, copy_id, authorized=raw_blob_authorized)


def source_from_v2(row: V2RowObservation, context: FilesQueryContext, copy_id: UUID, *, raw_blob_authorized: bool) -> BlobSourceObservation:
    return _source(row, context, copy_id, authorized=raw_blob_authorized)


def synthetic_source(value: bytes | None, storage: StorageClass = StorageClass.BLOB, *, state: str = "VALUE_PRESENT") -> BlobSourceObservation:
    def uid(n: int) -> UUID:
        return UUID(f"06070000-0000-4000-8000-{n:012d}")
    return BlobSourceObservation(
        uid(1), uid(2), uid(3), uid(4), uid(5), uid(6), uid(7), 1,
        "manifestdb-files-query", "2", "manifestdb-row-locator", "1",
        SOURCE_TABLE, SOURCE_COLUMN, storage, state, value,
        datetime(2026, 7, 30, tzinfo=timezone.utc), True, True,
    )
