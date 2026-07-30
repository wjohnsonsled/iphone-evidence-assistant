import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.manifest.flags_observation import *
from app.manifest.identifier_normalization import StorageClass
from app.intake.controlled_copy import ControlledCopyManager
from app.manifest.files_query import FilesQueryContext, FilesQueryPolicy, enumerate_files_rows
from app.manifest.files_query_v2 import QueryResourcePolicy, enumerate_files_rows_v2
from app.manifest.schema_profile import SchemaValidationContext, validate_controlled_manifest_schema
from tests.support.resource_policy import TEST_RESOURCE_POLICY

POLICY = FlagsPolicy(64)
NOW = datetime(2026, 7, 30, tzinfo=timezone.utc)


def u(n: int) -> UUID:
    return UUID(f"06060000-0000-4000-8000-{n:012d}")


SCHEMA_CONTEXT = SchemaValidationContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
QUERY_CONTEXT = FilesQueryContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)


@pytest.mark.parametrize(
    "value,state,bits",
    [
        (0, FlagsState.ZERO_NO_BITS_SET, ()),
        (1, FlagsState.INTEGER_UNKNOWN_BITS, (0,)),
        (5, FlagsState.INTEGER_UNKNOWN_BITS, (0, 2)),
        (255, FlagsState.INTEGER_UNKNOWN_BITS, tuple(range(8))),
        (-1, FlagsState.NEGATIVE_INTEGER_UNINTERPRETED, ()),
    ],
)
def test_integer_flags_preserve_raw_and_every_set_bit_remains_unknown(value, state, bits):
    result = observe_flags(synthetic_source(value, StorageClass.INTEGER), POLICY)
    assert result.state is state
    assert result.numeric_representation == value
    assert result.known_meanings == ()
    assert result.unknown_bit_positions == bits
    assert result.source.raw_value == value


@pytest.mark.parametrize(
    "value,storage,upstream,state",
    [
        (None, StorageClass.NULL, "VALUE_NULL", FlagsState.NULL),
        ("1", StorageClass.TEXT, "TYPE_MISMATCH", FlagsState.UNSUPPORTED_STORAGE_CLASS),
        (1.0, StorageClass.REAL, "TYPE_MISMATCH", FlagsState.UNSUPPORTED_STORAGE_CLASS),
        (b"1", StorageClass.BLOB, "TYPE_MISMATCH", FlagsState.UNSUPPORTED_STORAGE_CLASS),
        (None, StorageClass.INTEGER, "NOT_AVAILABLE", FlagsState.SOURCE_UNAVAILABLE),
        (None, StorageClass.INTEGER, "READ_FAILURE", FlagsState.READ_FAILURE),
        (None, StorageClass.INTEGER, "NOT_EVALUATED", FlagsState.NOT_EVALUATED),
        (None, StorageClass.INTEGER, "INDETERMINATE", FlagsState.INDETERMINATE),
    ],
)
def test_dynamic_types_and_failures_remain_distinct(value, storage, upstream, state):
    assert observe_flags(synthetic_source(value, storage, state=upstream), POLICY).state is state


def test_resource_policy_is_explicit_and_fails_closed():
    for value in (0, -1, 4097, True):
        with pytest.raises(ValueError, match="flags_policy_invalid"):
            FlagsPolicy(value)
    result = observe_flags(synthetic_source(1 << 64, StorageClass.INTEGER), POLICY)
    assert result.state is FlagsState.RESOURCE_LIMIT_EXCEEDED
    assert result.unknown_bit_positions == ()


def test_serialization_is_deterministic_and_blob_safe():
    source = synthetic_source(5, StorageClass.INTEGER)
    assert observe_flags(source, POLICY).canonical_json() == observe_flags(source, POLICY).canonical_json()
    blob = observe_flags(synthetic_source(b"secret", StorageClass.BLOB), POLICY).canonical_json()
    assert "secret" not in blob
    assert "BLOB_NOT_SERIALIZED" in blob


def _controlled(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir(parents=True)
    database = source / "Manifest.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE Files(fileID TEXT,domain TEXT,relativePath TEXT,flags INTEGER,file BLOB)"
    )
    connection.execute(
        "INSERT INTO Files VALUES('0123456789abcdef0123456789abcdef01234567','HomeDomain','p',5,X'')"
    )
    connection.commit()
    connection.close()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return ControlledCopyManager(
        workspace_root=workspace,
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: NOW,
    ).create(database, evidence_source_root=source, correlation_id=u(100))


def test_query_v1_and_v2_provenance_adapters(tmp_path):
    controlled = _controlled(tmp_path / "v1")
    with controlled:
        schema = validate_controlled_manifest_schema(controlled, SCHEMA_CONTEXT, TEST_RESOURCE_POLICY)
        row = enumerate_files_rows(
            controlled, schema, QUERY_CONTEXT, FilesQueryPolicy(10, 10, 1_000_000), page_size=1
        ).observations[0]
        v1 = observe_flags(source_from_v1(row, QUERY_CONTEXT, u(200)), POLICY)
    assert v1.unknown_bit_positions == (0, 2)
    assert v1.source.query_profile_version == "1"

    controlled = _controlled(tmp_path / "v2")
    with controlled:
        schema = validate_controlled_manifest_schema(controlled, SCHEMA_CONTEXT, TEST_RESOURCE_POLICY)
        row = enumerate_files_rows_v2(
            controlled,
            schema,
            QUERY_CONTEXT,
            QueryResourcePolicy(10, 10, 60, 1_000_000, 2_000_000, 5, 4, 3, 2),
            page_size=1,
        ).observations[0]
        v2 = observe_flags(source_from_v2(row, QUERY_CONTEXT, u(201)), POLICY)
    assert v2.unknown_bit_positions == (0, 2)
    assert v2.source.query_profile_version == "2"


def test_no_bit_meaning_filesystem_parser_or_support_surface():
    module = Path(__import__("app.manifest.flags_observation", fromlist=["x"]).__file__).read_text(encoding="utf-8").lower()
    for token in ("pathlib", "os.path", "exists(", "open(", "fastapi", "supportedparser"):
        assert token not in module
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry
    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0
