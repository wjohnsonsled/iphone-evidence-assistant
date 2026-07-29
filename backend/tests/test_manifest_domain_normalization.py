from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.controlled_copy import ControlledCopyManager
from app.manifest.domain_normalization import *
from app.manifest.files_query import (
    FilesQueryContext,
    FilesQueryPolicy,
    enumerate_files_rows,
)
from app.manifest.files_query_v2 import QueryResourcePolicy, enumerate_files_rows_v2
from app.manifest.schema_profile import (
    CompatibilityOutcome,
    SchemaValidationContext,
    validate_controlled_manifest_schema,
)
from tests.support.resource_policy import TEST_RESOURCE_POLICY

NOW = datetime(2026, 7, 29, tzinfo=timezone.utc)


def u(n: int) -> UUID:
    return UUID(f"06040000-0000-4000-8000-{n:012d}")


SCHEMA_CONTEXT = SchemaValidationContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
QUERY_CONTEXT = FilesQueryContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
V1_POLICY = FilesQueryPolicy(100, 100, 10_000_000)
V2_POLICY = QueryResourcePolicy(100, 100, 60, 1_000_000, 2_000_000, 5, 4, 3, 2)


@pytest.mark.parametrize(
    "raw,family",
    [
        ("HomeDomain", DomainFamily.HOME),
        ("WirelessDomain", DomainFamily.WIRELESS),
        ("RootDomain", DomainFamily.ROOT),
        ("SystemPreferencesDomain", DomainFamily.SYSTEM_PREFERENCES),
        ("ManagedPreferencesDomain", DomainFamily.MANAGED_PREFERENCES),
        ("MediaDomain", DomainFamily.MEDIA),
        ("CameraRollDomain", DomainFamily.CAMERA_ROLL),
    ],
)
def test_documented_literal_families_are_exact_case_sensitive_observations(raw, family):
    result = normalize_manifest_domain(synthetic_source(raw, StorageClass.TEXT))
    assert result.structure is DomainStructure.RECOGNIZED_LITERAL
    assert result.domain_family is family
    assert result.canonical_representation == raw
    assert result.source.raw_value == raw


@pytest.mark.parametrize(
    "raw,family,field",
    [
        ("AppDomain-com.example.app", DomainFamily.APPLICATION, "application_identifier_component"),
        ("AppDomainGroup-group.example.shared", DomainFamily.APPLICATION_GROUP, "group_identifier_component"),
        ("AppDomainPlugin-com.example.plugin", DomainFamily.APPLICATION_PLUGIN, "plugin_identifier_component"),
        ("SysContainerDomain-com.example.system", DomainFamily.SYSTEM_CONTAINER, "application_identifier_component"),
        ("SysSharedContainerDomain-group.example.system", DomainFamily.SYSTEM_SHARED_CONTAINER, "group_identifier_component"),
    ],
)
def test_prefixed_forms_separate_structure_and_opaque_component(raw, family, field):
    result = normalize_manifest_domain(synthetic_source(raw, StorageClass.TEXT))
    assert result.structure is DomainStructure.RECOGNIZED_PREFIXED
    assert result.domain_family is family
    assert getattr(result, field) == raw.split("-", 1)[1]
    assert result.canonical_representation == raw
    assert "installation" in result.limitations[0]


@pytest.mark.parametrize(
    "raw,structure",
    [
        ("UnknownDomain", DomainStructure.UNKNOWN_STRUCTURE),
        ("homedomain", DomainStructure.UNKNOWN_STRUCTURE),
        (" AppDomain-com.example", DomainStructure.MALFORMED_STRUCTURE),
        ("AppDomain-com example", DomainStructure.MALFORMED_STRUCTURE),
        ("AppDomain-", DomainStructure.MALFORMED_STRUCTURE),
        ("AppDomain-.bad", DomainStructure.MALFORMED_STRUCTURE),
        ("AppDomain-com/example", DomainStructure.MALFORMED_STRUCTURE),
        ("ＨomeDomain", DomainStructure.MALFORMED_STRUCTURE),
        ("", DomainStructure.EMPTY),
    ],
)
def test_unknown_and_malformed_forms_are_preserved_without_repair(raw, structure):
    result = normalize_manifest_domain(synthetic_source(raw, StorageClass.TEXT))
    assert result.structure is structure
    assert result.source.raw_value == raw
    assert result.canonical_representation is None
    assert result.domain_family is DomainFamily.UNKNOWN


@pytest.mark.parametrize(
    "value,storage,state,structure",
    [
        (None, StorageClass.NULL, "VALUE_NULL", DomainStructure.NULL),
        (1, StorageClass.INTEGER, "TYPE_MISMATCH", DomainStructure.UNSUPPORTED_STORAGE_CLASS),
        (1.5, StorageClass.REAL, "TYPE_MISMATCH", DomainStructure.UNSUPPORTED_STORAGE_CLASS),
        (b"HomeDomain", StorageClass.BLOB, "TYPE_MISMATCH", DomainStructure.UNSUPPORTED_STORAGE_CLASS),
        (None, StorageClass.TEXT, "NOT_AVAILABLE", DomainStructure.SOURCE_UNAVAILABLE),
        (None, StorageClass.TEXT, "READ_FAILURE", DomainStructure.READ_FAILURE),
        (None, StorageClass.TEXT, "NOT_EVALUATED", DomainStructure.NOT_EVALUATED),
        (None, StorageClass.TEXT, "INDETERMINATE", DomainStructure.INDETERMINATE),
    ],
)
def test_dynamic_storage_and_failure_states_remain_distinct(value, storage, state, structure):
    result = normalize_manifest_domain(synthetic_source(value, storage, state=state))
    assert result.structure is structure
    assert result.canonical_representation is None


def test_source_rejects_storage_value_mismatch():
    source = synthetic_source("HomeDomain", StorageClass.TEXT)
    values = {field: getattr(source, field) for field in source.__dataclass_fields__}
    values["raw_value"] = b"HomeDomain"
    with pytest.raises(ValueError, match="domain_storage_value_mismatch"):
        DomainSourceObservation(**values)


def test_serialization_and_rerun_are_deterministic_and_bounded():
    source = synthetic_source("AppDomain-com.example.app", StorageClass.TEXT)
    first = normalize_manifest_domain(source)
    second = normalize_manifest_domain(source)
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert "host" not in first.canonical_json().lower()


def _controlled(tmp_path: Path, domain: object):
    source = tmp_path / "source"
    source.mkdir(parents=True)
    database = source / "Manifest.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE Files(fileID TEXT,domain TEXT,relativePath TEXT,flags INTEGER,file BLOB)"
    )
    connection.execute(
        "INSERT INTO Files VALUES('0123456789abcdef0123456789abcdef01234567',?,'p',1,X'')",
        (domain,),
    )
    connection.commit()
    connection.close()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controlled = ControlledCopyManager(
        workspace_root=workspace,
        resource_policy=TEST_RESOURCE_POLICY,
        clock=lambda: NOW,
    ).create(database, evidence_source_root=source, correlation_id=u(100))
    return controlled


def _schema(controlled):
    result = validate_controlled_manifest_schema(
        controlled, SCHEMA_CONTEXT, TEST_RESOURCE_POLICY
    )
    assert result.outcome in {
        CompatibilityOutcome.SCHEMA_COMPATIBLE,
        CompatibilityOutcome.SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS,
    }
    return result


def test_query_v1_and_v2_provenance_adapters(tmp_path):
    controlled = _controlled(tmp_path / "v1", "HomeDomain")
    with controlled:
        row = enumerate_files_rows(
            controlled, _schema(controlled), QUERY_CONTEXT, V1_POLICY, page_size=1
        ).observations[0]
        v1 = normalize_manifest_domain(source_from_v1(row, QUERY_CONTEXT, u(200)))
    assert v1.domain_family is DomainFamily.HOME
    assert v1.source.query_profile_version == "1"

    controlled = _controlled(tmp_path / "v2", "AppDomain-com.example.app")
    with controlled:
        row = enumerate_files_rows_v2(
            controlled, _schema(controlled), QUERY_CONTEXT, V2_POLICY, page_size=1
        ).observations[0]
        v2 = normalize_manifest_domain(source_from_v2(row, QUERY_CONTEXT, u(201)))
    assert v2.domain_family is DomainFamily.APPLICATION
    assert v2.source.query_profile_version == "2"


def test_no_activity_existence_filesystem_api_or_support_surface():
    module = Path(
        __import__("app.manifest.domain_normalization", fromlist=["x"]).__file__
    ).read_text(encoding="utf-8").lower()
    for token in (
        "fastapi",
        "pathlib",
        "os.path",
        "exists(",
        "open(",
        "evidence_engine",
        "supportedparser",
    ):
        assert token not in module

    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry

    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0
