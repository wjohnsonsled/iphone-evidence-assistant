import plistlib
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.controlled_copy import ControlledCopyManager
from app.manifest.files_query import FilesQueryContext, FilesQueryPolicy, enumerate_files_rows
from app.manifest.files_query_v2 import QueryResourcePolicy, enumerate_files_rows_v2
from app.manifest.metadata_blob import *
from app.manifest.schema_profile import SchemaValidationContext, validate_controlled_manifest_schema
from tests.support.resource_policy import TEST_RESOURCE_POLICY

NOW = datetime(2026, 7, 30, tzinfo=timezone.utc)
POLICY = BlobPolicy(4096, 100, 16, 512, 50, 20_000, 5)


def binary(value) -> bytes:
    return plistlib.dumps(value, fmt=plistlib.FMT_BINARY, sort_keys=True)


def clock(value=0.0):
    return lambda: value


def u(n: int) -> UUID:
    return UUID(f"06070000-0000-4000-8000-{n:012d}")


SCHEMA_CONTEXT = SchemaValidationContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
QUERY_CONTEXT = FilesQueryContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)


def test_binary_plist_is_syntactically_decoded_without_class_instantiation():
    result = characterize_metadata_blob(
        synthetic_source(binary({"$archiver": "NSKeyedArchiver", "$objects": ["x", 5]})),
        POLICY,
        monotonic=clock(),
    )
    assert result.state is BlobState.BINARY_PLIST_SYNTACTICALLY_DECODED
    assert result.format_name == "BINARY_PLIST"
    assert result.declared_object_count == len(result.nodes)
    assert {node.type_name for node in result.nodes} >= {"DICTIONARY", "ASCII_STRING", "ARRAY", "INTEGER"}
    assert all("class" not in node.type_name.lower() for node in result.nodes)


@pytest.mark.parametrize(
    "value,storage,state,outcome",
    [
        (b"", StorageClass.BLOB, "VALUE_PRESENT", BlobState.EMPTY),
        (b"not a plist", StorageClass.BLOB, "VALUE_PRESENT", BlobState.UNKNOWN_FORMAT),
        (None, StorageClass.NULL, "VALUE_NULL", BlobState.NULL),
        (None, StorageClass.BLOB, "NOT_AVAILABLE", BlobState.SOURCE_UNAVAILABLE),
        (None, StorageClass.BLOB, "READ_FAILURE", BlobState.READ_FAILURE),
        (None, StorageClass.BLOB, "NOT_EVALUATED", BlobState.NOT_EVALUATED),
        (None, StorageClass.BLOB, "INDETERMINATE", BlobState.INDETERMINATE),
    ],
)
def test_empty_unknown_dynamic_and_failure_states_are_explicit(value, storage, state, outcome):
    result = characterize_metadata_blob(
        synthetic_source(value, storage, state=state), POLICY, monotonic=clock()
    )
    assert result.state is outcome


@pytest.mark.parametrize("blob", [b"bplist00", b"bplist01" + b"x" * 64, b"bplist00" + b"\0" * 32])
def test_malformed_binary_plists_fail_closed(blob):
    result = characterize_metadata_blob(synthetic_source(blob), POLICY, monotonic=clock())
    assert result.state is BlobState.MALFORMED
    assert result.failure_code


def test_duplicate_object_offsets_fail_closed():
    data = bytearray(binary({"a": 1}))
    offset_size, _, count, _, table_offset = struct.unpack(">6xBBQQQ", data[-32:])
    assert count > 1
    first = data[table_offset:table_offset + offset_size]
    data[table_offset + offset_size:table_offset + 2 * offset_size] = first
    result = characterize_metadata_blob(
        synthetic_source(bytes(data)), POLICY, monotonic=clock()
    )
    assert result.state is BlobState.MALFORMED
    assert result.failure_code == "object_offset_duplicate"


def test_caller_resource_limits_fail_closed_and_preserve_completed_nodes():
    data = binary({"a": ["one", "two", "three"], "b": "value"})
    too_small = BlobPolicy(len(data) - 1, 100, 16, 512, 50, 20_000, 5)
    assert characterize_metadata_blob(
        synthetic_source(data), too_small, monotonic=clock()
    ).failure_code == "blob_size_limit"

    string_limit = BlobPolicy(4096, 100, 16, 2, 50, 20_000, 5)
    stopped = characterize_metadata_blob(
        synthetic_source(data), string_limit, monotonic=clock()
    )
    assert stopped.state is BlobState.RESOURCE_LIMIT_EXCEEDED
    assert stopped.failure_code == "scalar_size_limit"
    assert len(stopped.nodes) < stopped.declared_object_count

    collection_limit = BlobPolicy(4096, 100, 16, 512, 1, 20_000, 5)
    assert characterize_metadata_blob(
        synthetic_source(data), collection_limit, monotonic=clock()
    ).failure_code == "collection_size_limit"

    object_limit = BlobPolicy(4096, 2, 16, 512, 50, 20_000, 5)
    assert characterize_metadata_blob(
        synthetic_source(data), object_limit, monotonic=clock()
    ).failure_code == "object_count_limit"

    memory_limit = BlobPolicy(4096, 100, 16, 512, 50, 64, 5)
    memory_stopped = characterize_metadata_blob(
        synthetic_source(data), memory_limit, monotonic=clock()
    )
    assert memory_stopped.failure_code == "decoded_memory_limit"
    assert memory_stopped.nodes == ()


def test_depth_limit_and_invalid_policy_fail_closed():
    nested = binary([[[["x"]]]])
    depth_limit = BlobPolicy(4096, 100, 2, 512, 50, 20_000, 5)
    result = characterize_metadata_blob(
        synthetic_source(nested), depth_limit, monotonic=clock()
    )
    assert result.state is BlobState.RESOURCE_LIMIT_EXCEEDED
    assert result.failure_code == "nesting_depth_limit"
    assert result.nodes

    invalid = (
        (0, 1, 1, 1, 1, 1, 1),
        (1, 0, 1, 1, 1, 1, 1),
        (1, 1, 0, 1, 1, 1, 1),
        (1, 1, 1, 0, 1, 1, 1),
        (1, 1, 1, 1, 0, 1, 1),
        (1, 1, 1, 1, 1, 0, 1),
        (1, 1, 1, 1, 1, 1, 0),
    )
    for values in invalid:
        with pytest.raises(ValueError, match="metadata_blob_policy_invalid"):
            BlobPolicy(*values)


def test_cancellation_and_monotonic_deadline_preserve_only_complete_nodes():
    data = binary({"a": ["one", "two"], "b": "value"})
    calls = 0

    def cancel():
        nonlocal calls
        calls += 1
        return calls > 2

    stopped = characterize_metadata_blob(
        synthetic_source(data), POLICY, cancel=cancel, monotonic=clock()
    )
    assert stopped.state is BlobState.CANCELLED
    assert len(stopped.nodes) == 2

    times = iter((0.0, 0.0, 6.0))
    timed = characterize_metadata_blob(
        synthetic_source(data), POLICY, monotonic=lambda: next(times, 6.0)
    )
    assert timed.state is BlobState.RESOURCE_LIMIT_EXCEEDED
    assert timed.failure_code == "metadata_blob_time_limit"
    assert len(timed.nodes) == 1


def test_deterministic_serialization_omits_raw_blob_bytes():
    data = binary({"secret-value": "synthetic"})
    first = characterize_metadata_blob(synthetic_source(data), POLICY, monotonic=clock())
    second = characterize_metadata_blob(synthetic_source(data), POLICY, monotonic=clock())
    assert first == second
    serialized = first.canonical_json()
    assert data.hex() not in serialized
    assert "BLOB_NOT_SERIALIZED" in serialized


def test_raw_blob_requires_explicit_authorization():
    source = synthetic_source(binary({"a": 1}))
    values = {field: getattr(source, field) for field in source.__dataclass_fields__}
    values["raw_blob_authorized"] = False
    with pytest.raises(ValueError, match="metadata_blob_bytes_not_authorized"):
        BlobSourceObservation(**values)


def _controlled(tmp_path: Path, blob: bytes):
    source = tmp_path / "source"
    source.mkdir(parents=True)
    database = source / "Manifest.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE Files(fileID TEXT,domain TEXT,relativePath TEXT,flags INTEGER,file BLOB)"
    )
    connection.execute(
        "INSERT INTO Files VALUES('0123456789abcdef0123456789abcdef01234567','HomeDomain','p',0,?)",
        (blob,),
    )
    connection.commit()
    connection.close()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return ControlledCopyManager(
        workspace_root=workspace, resource_policy=TEST_RESOURCE_POLICY, clock=lambda: NOW
    ).create(database, evidence_source_root=source, correlation_id=u(100))


def test_query_v1_and_explicitly_authorized_v2_blob_adapters(tmp_path):
    data = binary({"a": 1})
    controlled = _controlled(tmp_path / "v1", data)
    with controlled:
        schema = validate_controlled_manifest_schema(controlled, SCHEMA_CONTEXT, TEST_RESOURCE_POLICY)
        row = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, FilesQueryPolicy(10, 10, 1_000_000), page_size=1
        ).observations[0]
        v1 = characterize_metadata_blob(
            source_from_v1(row, QUERY_CONTEXT, u(200), raw_blob_authorized=True),
            POLICY,
            monotonic=clock(),
        )
    assert v1.state is BlobState.BINARY_PLIST_SYNTACTICALLY_DECODED

    controlled = _controlled(tmp_path / "v2", data)
    with controlled:
        schema = validate_controlled_manifest_schema(controlled, SCHEMA_CONTEXT, TEST_RESOURCE_POLICY)
        row = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            QueryResourcePolicy(10, 10, 60, 1_000_000, 2_000_000, 5, 4, 3, 2),
            page_size=1,
            include_raw_blob=True,
            raw_blob_authorized=True,
        ).observations[0]
        v2 = characterize_metadata_blob(
            source_from_v2(row, QUERY_CONTEXT, u(201), raw_blob_authorized=True),
            POLICY,
            monotonic=clock(),
        )
    assert v2.state is BlobState.BINARY_PLIST_SYNTACTICALLY_DECODED
    assert v2.source.query_profile_version == "2"


def test_no_plistlib_dynamic_loading_filesystem_api_parser_or_support_surface():
    module = Path(__import__("app.manifest.metadata_blob", fromlist=["x"]).__file__).read_text(encoding="utf-8").lower()
    for token in (
        "plistlib", "pickle", "eval(", "exec(", "__import__(", "pathlib",
        "os.path", "open(", "fastapi", "supportedparser",
    ):
        assert token not in module
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry
    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0
