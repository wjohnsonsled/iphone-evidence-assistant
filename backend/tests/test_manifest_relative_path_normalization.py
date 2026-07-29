import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.manifest.identifier_normalization import StorageClass
from app.manifest.relative_path_normalization import *
from app.intake.controlled_copy import ControlledCopyManager
from app.manifest.files_query import FilesQueryContext, FilesQueryPolicy, enumerate_files_rows
from app.manifest.files_query_v2 import QueryResourcePolicy, enumerate_files_rows_v2
from app.manifest.schema_profile import SchemaValidationContext, validate_controlled_manifest_schema
from tests.support.resource_policy import TEST_RESOURCE_POLICY

POLICY = RelativePathPolicy(128, 256, 16)
NOW = datetime(2026, 7, 29, tzinfo=timezone.utc)


def u(n: int) -> UUID:
    return UUID(f"06050000-0000-4000-8000-{n:012d}")


SCHEMA_CONTEXT = SchemaValidationContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
QUERY_CONTEXT = FilesQueryContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)


@pytest.mark.parametrize("raw", ["Library/SMS/sms.db", "file.txt", "資料/項目.txt"])
def test_safe_relative_paths_preserve_exact_raw_and_canonical(raw):
    result = observe_relative_path(synthetic_source(raw, StorageClass.TEXT), POLICY)
    assert result.state is PathState.SAFE_RELATIVE
    assert result.canonical_comparison_representation == raw
    assert result.source.raw_value == raw


@pytest.mark.parametrize(
    "raw,state",
    [
        ("", PathState.EMPTY),
        ("/etc/passwd", PathState.UNSAFE_ABSOLUTE),
        ("C:\\temp\\x", PathState.UNSAFE_ABSOLUTE),
        ("a\\b", PathState.UNSAFE_ALTERNATE_SEPARATOR),
        ("a//b", PathState.UNSAFE_REPEATED_SEPARATOR),
        ("a/../b", PathState.UNSAFE_PARENT_TRAVERSAL),
        ("a/./b", PathState.UNSAFE_DOT_SEGMENT),
    ],
)
def test_unsafe_and_empty_paths_are_not_repaired(raw, state):
    result = observe_relative_path(synthetic_source(raw, StorageClass.TEXT), POLICY)
    assert result.state is state
    assert result.source.raw_value == raw
    assert result.canonical_comparison_representation is None


@pytest.mark.parametrize(
    "value,storage,state,outcome",
    [
        (None, StorageClass.NULL, "VALUE_NULL", PathState.NULL),
        (1, StorageClass.INTEGER, "TYPE_MISMATCH", PathState.UNSUPPORTED_STORAGE_CLASS),
        (1.5, StorageClass.REAL, "TYPE_MISMATCH", PathState.UNSUPPORTED_STORAGE_CLASS),
        (b"a/b", StorageClass.BLOB, "TYPE_MISMATCH", PathState.UNSUPPORTED_STORAGE_CLASS),
        (None, StorageClass.TEXT, "NOT_AVAILABLE", PathState.SOURCE_UNAVAILABLE),
        (None, StorageClass.TEXT, "READ_FAILURE", PathState.READ_FAILURE),
        (None, StorageClass.TEXT, "NOT_EVALUATED", PathState.NOT_EVALUATED),
        (None, StorageClass.TEXT, "INDETERMINATE", PathState.INDETERMINATE),
    ],
)
def test_dynamic_types_and_failure_states_are_distinct(value, storage, state, outcome):
    result = observe_relative_path(synthetic_source(value, storage, state=state), POLICY)
    assert result.state is outcome


def test_policy_is_explicit_positive_and_limits_before_token_retention():
    for values in ((0, 1, 1), (1, -1, 1), (1, 1, 0)):
        with pytest.raises(ValueError, match="relative_path_policy_invalid"):
            RelativePathPolicy(*values)
    result = observe_relative_path(
        synthetic_source("a/b/c", StorageClass.TEXT), RelativePathPolicy(3, 3, 2)
    )
    assert result.state is PathState.RESOURCE_LIMIT_EXCEEDED
    assert result.lexical_segments == ()


def test_unicode_encoding_and_serialization_are_explicit_and_deterministic():
    source = synthetic_source("資料/x", StorageClass.TEXT)
    first = observe_relative_path(source, POLICY)
    second = observe_relative_path(source, POLICY)
    assert first.encoding_state is EncodingState.UNICODE_TEXT
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert str(Path.cwd()) not in first.canonical_json()


def test_blob_serialization_never_exposes_raw_bytes():
    result = observe_relative_path(
        synthetic_source(b"secret/path", StorageClass.BLOB), POLICY
    )
    serialized = result.canonical_json()
    assert "secret/path" not in serialized
    assert "BLOB_NOT_SERIALIZED" in serialized


def _controlled(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir(parents=True)
    database = source / "Manifest.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE Files(fileID TEXT,domain TEXT,relativePath TEXT,flags INTEGER,file BLOB)"
    )
    connection.execute(
        "INSERT INTO Files VALUES('0123456789abcdef0123456789abcdef01234567','HomeDomain','Library/x',1,X'')"
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
        v1 = observe_relative_path(source_from_v1(row, QUERY_CONTEXT, u(200)), POLICY)
    assert v1.state is PathState.SAFE_RELATIVE
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
        v2 = observe_relative_path(source_from_v2(row, QUERY_CONTEXT, u(201)), POLICY)
    assert v2.state is PathState.SAFE_RELATIVE
    assert v2.source.query_profile_version == "2"


def test_no_filesystem_api_parser_or_support_surface():
    module = Path(
        __import__("app.manifest.relative_path_normalization", fromlist=["x"]).__file__
    ).read_text(encoding="utf-8").lower()
    for token in ("pathlib", "os.path", "resolve(", "exists(", "open(", "fastapi", "supportedparser"):
        assert token not in module
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry
    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0
