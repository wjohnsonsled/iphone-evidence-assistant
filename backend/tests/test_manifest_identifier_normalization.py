from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.intake.controlled_copy import ControlledCopyManager
from app.manifest.files_query import (
    FilesQueryContext,
    FilesQueryPolicy,
    enumerate_files_rows,
)
from app.manifest.files_query_v2 import (
    QueryResourcePolicy,
    enumerate_files_rows_v2,
)
from app.manifest.identifier_normalization import *
from app.manifest.schema_profile import (
    CompatibilityOutcome,
    SchemaValidationContext,
    validate_controlled_manifest_schema,
)
from tests.support.resource_policy import TEST_RESOURCE_POLICY

NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)


def u(n: int) -> UUID:
    return UUID(f"06030000-0000-4000-8000-{n:012d}")


SCHEMA_CONTEXT = SchemaValidationContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
QUERY_CONTEXT = FilesQueryContext(
    u(1), u(2), u(3), u(4), u(5), u(6), (u(1), u(2), u(3), u(6)), NOW
)
V1_POLICY = FilesQueryPolicy(100, 100, 10_000_000)
V2_POLICY = QueryResourcePolicy(
    100, 100, 60, 1_000_000, 2_000_000, 5, 4, 3, 2
)
LOWER = "0123456789abcdef0123456789abcdef01234567"
UPPER = LOWER.upper()
MIXED = "0123456789aBcDeF0123456789AbCdEf01234567"


def src(
    value,
    storage=StorageClass.TEXT,
    *,
    state="VALUE_PRESENT",
    blob_authorized=False,
    seed=1,
    tenant=None,
    case=None,
):
    return synthetic_source(
        value,
        storage,
        upstream_value_state=state,
        blob_authorized=blob_authorized,
        seed=seed,
        tenant_id=tenant,
        case_id=case,
    )


@pytest.mark.parametrize(
    "value,outcome",
    [
        (LOWER, NormalizationOutcome.FILEID_RECOGNIZED_CANONICAL),
        (UPPER, NormalizationOutcome.FILEID_RECOGNIZED_NORMALIZED),
        (MIXED, NormalizationOutcome.FILEID_RECOGNIZED_NORMALIZED),
        (LOWER[:-1], NormalizationOutcome.FILEID_INVALID_LENGTH),
        (LOWER + "0", NormalizationOutcome.FILEID_INVALID_LENGTH),
        (LOWER[:-1] + "g", NormalizationOutcome.FILEID_INVALID_CHARACTER),
        (" " + LOWER, NormalizationOutcome.FILEID_TEXT_WITH_WHITESPACE),
        (LOWER + " ", NormalizationOutcome.FILEID_TEXT_WITH_WHITESPACE),
        (LOWER[:20] + " " + LOWER[20:], NormalizationOutcome.FILEID_TEXT_WITH_WHITESPACE),
        ("0x" + LOWER, NormalizationOutcome.FILEID_UNSUPPORTED_TEXT_SYNTAX),
        (LOWER[:20] + "-" + LOWER[20:], NormalizationOutcome.FILEID_UNSUPPORTED_TEXT_SYNTAX),
        ("{" + LOWER + "}", NormalizationOutcome.FILEID_UNSUPPORTED_TEXT_SYNTAX),
        ("", NormalizationOutcome.FILEID_EMPTY_TEXT),
        ("Ａ" + LOWER[1:], NormalizationOutcome.FILEID_NON_ASCII_TEXT),
    ],
)
def test_text_fixture_corpus_is_exact_and_nonrepairing(value, outcome):
    result = normalize_manifest_fileid(src(value))
    assert result.normalization_result is outcome
    assert result.source.raw_value == value
    assert result.raw_character_length == len(value)
    assert result.raw_byte_length == len(value.encode("utf-8"))
    if outcome not in {
        NormalizationOutcome.FILEID_RECOGNIZED_CANONICAL,
        NormalizationOutcome.FILEID_RECOGNIZED_NORMALIZED,
    }:
        assert result.canonical_representation is None


def test_profile_framework_classes_and_exact_canonicalization():
    assert (FRAMEWORK_ID, FRAMEWORK_VERSION) == (
        "canonical-identifier-normalization",
        "1",
    )
    assert (PROFILE_ID, PROFILE_VERSION) == ("manifestdb-fileid-normalization", "1")
    assert set(IdentifierClass) == {
        IdentifierClass.MANIFEST_FILE_ID,
        IdentifierClass.SOURCE_DEFINED_IDENTIFIER,
        IdentifierClass.UNKNOWN_IDENTIFIER_CLASS,
    }
    lower = normalize_manifest_fileid(src(LOWER))
    upper = normalize_manifest_fileid(src(UPPER, seed=2))
    mixed = normalize_manifest_fileid(src(MIXED, seed=3))
    assert lower.canonical_representation == upper.canonical_representation == LOWER
    assert mixed.canonical_representation == LOWER
    assert lower.transformations[0].transformation_type is TransformationType.NONE
    assert (
        upper.transformations[0].transformation_type
        is TransformationType.ASCII_HEX_CASE_CANONICALIZATION
    )
    assert [item.sequence_number for item in upper.transformations] == [1]


@pytest.mark.parametrize(
    "value,outcome,canonical,transform_count",
    [
        (LOWER.encode(), NormalizationOutcome.FILEID_BLOB_ASCII_RECOGNIZED, LOWER, 1),
        (UPPER.encode(), NormalizationOutcome.FILEID_BLOB_ASCII_RECOGNIZED, LOWER, 2),
        (MIXED.encode(), NormalizationOutcome.FILEID_BLOB_ASCII_RECOGNIZED, LOWER, 2),
        (b"not-40-hex", NormalizationOutcome.FILEID_BLOB_ASCII_UNRECOGNIZED, None, 1),
        (b"\xff" * 40, NormalizationOutcome.FILEID_BLOB_NON_ASCII, None, 0),
        (b"", NormalizationOutcome.FILEID_EMPTY_BLOB, None, 0),
        (b"\x01" * 20, NormalizationOutcome.FILEID_BLOB_ASCII_UNRECOGNIZED, None, 1),
    ],
)
def test_blob_rules_are_strict_bounded_and_never_hex_expand(
    value, outcome, canonical, transform_count
):
    result = normalize_manifest_fileid(
        src(value, StorageClass.BLOB, blob_authorized=True)
    )
    assert result.normalization_result is outcome
    assert result.source.raw_value == value
    assert result.raw_byte_length == len(value)
    assert result.canonical_representation == canonical
    assert len(result.transformations) == transform_count
    if value:
        assert value.hex() not in result.canonical_json()


def test_blob_requires_upstream_authorization():
    with pytest.raises(ValueError, match="identifier_blob_not_authorized"):
        src(LOWER.encode(), StorageClass.BLOB)


@pytest.mark.parametrize(
    "value,storage,state,outcome",
    [
        (None, StorageClass.NULL, "VALUE_NULL", NormalizationOutcome.FILEID_NULL),
        (7, StorageClass.INTEGER, "TYPE_MISMATCH", NormalizationOutcome.FILEID_UNSUPPORTED_STORAGE_CLASS),
        (7.5, StorageClass.REAL, "TYPE_MISMATCH", NormalizationOutcome.FILEID_UNSUPPORTED_STORAGE_CLASS),
        (None, StorageClass.TEXT, "NOT_AVAILABLE", NormalizationOutcome.FILEID_SOURCE_VALUE_UNAVAILABLE),
        (None, StorageClass.TEXT, "READ_FAILURE", NormalizationOutcome.FILEID_READ_FAILURE),
        (None, StorageClass.TEXT, "NOT_EVALUATED", NormalizationOutcome.FILEID_NOT_EVALUATED),
        (None, StorageClass.TEXT, "INDETERMINATE", NormalizationOutcome.FILEID_INDETERMINATE),
    ],
)
def test_null_dynamic_and_failure_states_remain_distinct(value, storage, state, outcome):
    result = normalize_manifest_fileid(src(value, storage, state=state))
    assert result.normalization_result is outcome
    assert result.canonical_representation is None


def test_comparison_modes_scope_and_profile_compatibility_are_explicit():
    lower = normalize_manifest_fileid(src(LOWER, seed=1))
    upper = normalize_manifest_fileid(src(UPPER, seed=2))
    assert compare_identifiers(
        lower, upper, ComparisonMode.EXACT_RAW
    ).outcome is ComparisonOutcome.DIFFERENT
    canonical = compare_identifiers(lower, upper, ComparisonMode.EXACT_CANONICAL)
    assert canonical.outcome is ComparisonOutcome.EQUAL
    assert "content" in " ".join(canonical.limitations).lower()

    blob = normalize_manifest_fileid(
        src(LOWER.encode(), StorageClass.BLOB, blob_authorized=True, seed=3)
    )
    assert compare_identifiers(
        lower, blob, ComparisonMode.EXACT_RAW
    ).outcome is ComparisonOutcome.NOT_COMPARABLE
    assert compare_identifiers(
        lower, blob, ComparisonMode.EXACT_CANONICAL
    ).outcome is ComparisonOutcome.EQUAL

    malformed = normalize_manifest_fileid(src("bad", seed=4))
    assert compare_identifiers(
        lower, malformed, ComparisonMode.EXACT_CANONICAL
    ).mode is ComparisonMode.NOT_COMPARABLE

    incompatible = replace(upper, normalization_profile_version="2")
    assert compare_identifiers(
        lower, incompatible, ComparisonMode.EXACT_CANONICAL
    ).outcome is ComparisonOutcome.NOT_COMPARABLE

    other_case = normalize_manifest_fileid(src(LOWER, seed=5, case=u(99)))
    other_tenant = normalize_manifest_fileid(src(LOWER, seed=6, tenant=u(98)))
    for other in (other_case, other_tenant):
        denied = compare_identifiers(lower, other, ComparisonMode.EXACT_CANONICAL)
        assert denied.outcome is ComparisonOutcome.NOT_COMPARABLE
        assert denied.reason_code == "identifier_comparison_scope_denied"


def test_repeated_identifiers_are_observations_not_duplicate_conclusions():
    left = normalize_manifest_fileid(src(LOWER, seed=1))
    right = normalize_manifest_fileid(src(LOWER, seed=2))
    result = compare_identifiers(left, right, ComparisonMode.EXACT_CANONICAL)
    assert result.outcome is ComparisonOutcome.EQUAL
    serialized = json_text = left.canonical_json() + right.canonical_json()
    assert "duplicate file" not in serialized.lower()
    assert "orphan" not in result.reason_code
    assert any(
        item.startswith("Repeated fileID observations are not duplicate-file")
        for item in left.limitations
    )


def test_serialization_is_deterministic_immutable_and_blob_safe():
    source = src(UPPER.encode(), StorageClass.BLOB, blob_authorized=True)
    first = normalize_manifest_fileid(source)
    second = normalize_manifest_fileid(source)
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.decoded_blob_text == UPPER
    assert "BOUNDED_BLOB_NOT_SERIALIZED" in first.canonical_json()
    with pytest.raises(Exception):
        first.canonical_representation = "changed"  # type: ignore[misc]
    rerun = normalize_manifest_fileid(
        replace(source, processing_run_id=u(88)),
        prior_observation_id=first.observation_id,
    )
    assert rerun.observation_id != first.observation_id
    assert rerun.prior_observation_id == first.observation_id


def test_missing_provenance_and_detached_sources_fail_closed():
    with pytest.raises(ValueError, match="provenance_incomplete"):
        replace(src(LOWER), tenant_id=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="query_profile_unapproved"):
        replace(src(LOWER), query_profile_id="caller-string")
    with pytest.raises(ValueError, match="not_manifest_fileid"):
        replace(src(LOWER), source_column="domain")


def test_batch_limits_and_cancellation_preserve_completed_observations():
    sources = tuple(src(LOWER, seed=n) for n in range(1, 5))
    base = BatchResourcePolicy(10, 10, 10_000, 10_000, 60)
    limited = normalize_batch(sources, replace(base, max_observations=2))
    assert limited.termination_reason == "OBSERVATION_LIMIT_REACHED"
    assert len(limited.observations) == 2 and limited.continuation_index == 2

    byte_limited = normalize_batch(sources, replace(base, max_projected_bytes=50))
    assert byte_limited.termination_reason == "BYTE_LIMIT_REACHED"
    assert len(byte_limited.observations) == 1

    memory_limited = normalize_batch(
        sources, replace(base, max_memory_estimate_bytes=700)
    )
    assert memory_limited.termination_reason == "MEMORY_ESTIMATE_LIMIT_REACHED"
    assert len(memory_limited.observations) == 1

    calls = 0

    def cancel():
        nonlocal calls
        calls += 1
        return calls == 3

    cancelled = normalize_batch(sources, base, cancelled=cancel)
    assert cancelled.termination_reason == "CANCELLED"
    assert len(cancelled.observations) == 2

    ticks = iter((0.0, 0.1, 0.3))
    timed = normalize_batch(
        sources,
        replace(base, max_wall_clock_seconds=0.2),
        monotonic_clock=lambda: next(ticks),
    )
    assert timed.termination_reason == "WALL_CLOCK_LIMIT_REACHED"
    assert len(timed.observations) == 1

    normalized = tuple(normalize_manifest_fileid(item) for item in sources)
    pairs = tuple(
        (normalized[0], item, ComparisonMode.EXACT_CANONICAL)
        for item in normalized[1:]
    )
    comparisons = compare_explicit_pairs(
        pairs, replace(base, max_comparisons=2)
    )
    assert comparisons.termination_reason == "COMPARISON_LIMIT_REACHED"
    assert len(comparisons.comparisons) == 2
    assert comparisons.continuation_index == 2


def test_caller_directed_comparison_forms_enforce_every_resource_boundary():
    observations = tuple(
        normalize_manifest_fileid(src(LOWER, seed=n)) for n in range(1, 5)
    )
    base = BatchResourcePolicy(10, 10, 10_000, 10_000, 60)
    pairs = tuple(
        (observations[0], item, ComparisonMode.EXACT_CANONICAL)
        for item in observations[1:]
    )

    against = compare_against_bounded_set(
        observations[0], observations[1:], ComparisonMode.EXACT_CANONICAL, base
    )
    explicit = compare_explicit_pairs(pairs, base)
    assert against == explicit
    assert [item.right_observation_id for item in explicit.comparisons] == [
        item.observation_id for item in observations[1:]
    ]
    assert compare_explicit_pairs(pairs, base) == explicit

    one_pair_cost = explicit.projected_bytes // 3
    byte_limited = compare_explicit_pairs(
        pairs, replace(base, max_projected_bytes=one_pair_cost + 1)
    )
    assert byte_limited.termination_reason == "BYTE_LIMIT_REACHED"
    assert len(byte_limited.comparisons) == 1

    one_pair_memory = (explicit.deterministic_memory_estimate - 128) // 3
    memory_limited = compare_explicit_pairs(
        pairs, replace(base, max_memory_estimate_bytes=128 + one_pair_memory + 1)
    )
    assert memory_limited.termination_reason == "MEMORY_ESTIMATE_LIMIT_REACHED"
    assert len(memory_limited.comparisons) == 1

    calls = 0

    def cancel():
        nonlocal calls
        calls += 1
        return calls == 3

    cancelled = compare_explicit_pairs(pairs, base, cancelled=cancel)
    assert cancelled.termination_reason == "CANCELLED"
    assert len(cancelled.comparisons) == 2

    ticks = iter((0.0, 0.1, 0.3))
    timed = compare_explicit_pairs(
        pairs,
        replace(base, max_wall_clock_seconds=0.2),
        monotonic_clock=lambda: next(ticks),
    )
    assert timed.termination_reason == "WALL_CLOCK_LIMIT_REACHED"
    assert len(timed.comparisons) == 1


def test_comparison_policy_missing_zero_invalid_and_excessive_fail_closed():
    with pytest.raises(TypeError):
        BatchResourcePolicy(1, max_projected_bytes=1, max_memory_estimate_bytes=1, max_wall_clock_seconds=1)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="policy_invalid"):
        BatchResourcePolicy(1, 0, 1, 1, 1)
    with pytest.raises(ValueError, match="policy_invalid"):
        BatchResourcePolicy(1, -1, 1, 1, 1)
    with pytest.raises(ValueError, match="policy_excessive"):
        BatchResourcePolicy(1, MAX_POLICY_COUNTER + 1, 1, 1, 1)


def test_public_surface_has_no_all_pairs_or_cartesian_entry_point():
    import app.manifest.identifier_normalization as module

    names = {
        name
        for name, value in vars(module).items()
        if callable(value) and not name.startswith("_")
    }
    assert {"compare_identifiers", "compare_explicit_pairs", "compare_against_bounded_set"} <= names
    assert not {
        "compare_all",
        "compare_every",
        "all_pairs",
        "cartesian_compare",
        "compare_collections",
    } & names


def _controlled_query(tmp_path: Path, value):
    source = tmp_path / "source"
    source.mkdir(parents=True)
    database = source / "Manifest.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE Files(fileID TEXT,domain TEXT,relativePath TEXT,flags INTEGER,file BLOB)"
    )
    connection.execute(
        "INSERT INTO Files(rowid,fileID,domain,relativePath,flags,file) VALUES(1,?,'D','p',1,X'')",
        (value,),
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


def test_dev0602_and_dev0602a_integrations_accept_only_proven_rows(tmp_path):
    controlled = _controlled_query(tmp_path / "v1", UPPER)
    with controlled:
        v1 = enumerate_files_rows(
            controlled, _schema(controlled), QUERY_CONTEXT, V1_POLICY, page_size=1
        ).observations[0]
        source_v1 = source_from_v1(v1, QUERY_CONTEXT, u(200))
        normalized_v1 = normalize_manifest_fileid(source_v1)
    assert normalized_v1.canonical_representation == LOWER
    assert normalized_v1.source.query_profile_version == "1"

    controlled = _controlled_query(tmp_path / "v2", LOWER)
    with controlled:
        v2 = enumerate_files_rows_v2(
            controlled, _schema(controlled), QUERY_CONTEXT, V2_POLICY, page_size=1
        ).observations[0]
        source_v2 = source_from_v2(v2, QUERY_CONTEXT, u(201))
        normalized_v2 = normalize_manifest_fileid(source_v2)
    assert normalized_v2.canonical_representation == LOWER
    assert normalized_v2.source.query_profile_version == "2"

    with pytest.raises(ValueError, match="scope_mismatch"):
        source_from_v2(v2, replace(QUERY_CONTEXT, case_id=u(99)), u(201))


def test_no_hash_physical_resolution_api_or_interpretation_surface():
    module = Path(
        __import__("app.manifest.identifier_normalization", fromlist=["x"]).__file__
    ).read_text(encoding="utf-8").lower()
    assert all(
        forbidden not in module
        for forbidden in (
            "import hashlib",
            "from hashlib",
            "sha1(",
            "sha256(",
            "fastapi",
            "plistlib",
            "nskeyedarchiver",
            "relativepath",
            "os.path",
            "pathlib",
        )
    )
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry

    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0
