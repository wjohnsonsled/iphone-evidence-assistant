from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.discovery.apple_backup import MetadataObservation, ValueState
from app.discovery.metadata_normalization import *


def u(n: int) -> UUID:
    return UUID(f"05050000-0000-4000-8000-{n:012d}")


NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)
SCOPE = NormalizationScope(u(1), u(2), u(3), u(4), u(5), NOW)


def observation(value, *, state=ValueState.PRESENT, field="Target Identifier", source=u(6)):
    return MetadataObservation(
        u(1), u(2), u(3), source, u(4), "Info.plist",
        f"top-level:Info.plist:{field}", "metadata_field", field, state, value,
        value, "python.plistlib", "1", ("Synthetic candidate observation.",),
    )


def identifier(value, kind=IdentifierClass.DEVICE_IDENTIFIER, **kwargs):
    return normalize_identifier(observation(value, **kwargs), kind, SCOPE)


def version(value, **kwargs):
    return normalize_product_version(
        observation(value, field="Product Version", **kwargs), SCOPE
    )


def test_profiles_raw_preservation_hex_syntax_case_and_separator():
    raw = "  ABCDEF0123456789ABCDEF0123456789ABCDEF01  "
    result = identifier(raw)
    assert (result.profile_id, result.profile_version) == (
        "apple-backup-identifier-normalization", "1"
    )
    assert result.raw_value == raw
    assert result.normalized_value == raw.strip().lower()
    assert result.syntax is IdentifierSyntax.HEXADECIMAL_40
    assert result.state is NormalizationState.NORMALIZED
    assert result.typed_value.raw.serialized_value == raw
    assert result.typed_value.normalized.serialized_value == raw.strip().lower()
    assert result.typed_value.transformation.method_id == result.profile_id

    separated = identifier("00008020-001C2D3E4F5A6B7C")
    assert separated.syntax is IdentifierSyntax.HEXADECIMAL_PREFIX_AND_SUFFIX
    assert separated.normalized_value == "00008020-001c2d3e4f5a6b7c"


@pytest.mark.parametrize(
    "value,state,source_state",
    [
        ("", NormalizationState.EMPTY, ValueState.PRESENT),
        (None, NormalizationState.NULL, ValueState.PRESENT),
        (None, NormalizationState.MISSING, ValueState.MISSING),
        (None, NormalizationState.MALFORMED, ValueState.MALFORMED),
        ({"x": 1}, NormalizationState.UNSUPPORTED_FORMAT, ValueState.UNSUPPORTED),
    ],
)
def test_identifier_semantic_states_remain_distinct(value, state, source_state):
    result = identifier(value, state=source_state)
    assert result.state is state and result.normalized_value is None


def test_identifier_classes_are_not_converted_or_fuzzed():
    raw = "ABCDEF0123456789ABCDEF0123456789ABCDEF01"
    root = identifier(raw, IdentifierClass.BACKUP_ROOT_NAME)
    device = identifier(raw, IdentifierClass.DEVICE_IDENTIFIER)
    assert root.identifier_class is IdentifierClass.BACKUP_ROOT_NAME
    assert compare_identifiers(root, device, ComparisonMode.EXACT_CANONICAL_TEXT_MATCH).outcome is ComparisonOutcome.NOT_COMPARABLE
    assert identifier(raw[:-1], IdentifierClass.DEVICE_IDENTIFIER).state is NormalizationState.UNSUPPORTED_FORMAT
    assert identifier(raw[:20] + " " + raw[20:]).state is NormalizationState.UNSUPPORTED_FORMAT
    assert identifier(raw + "!").state is NormalizationState.UNSUPPORTED_FORMAT
    assert identifier("Ａ" + raw[1:]).state is NormalizationState.INVALID_CHARACTER_SET
    assert identifier(raw, IdentifierClass.UNKNOWN_IDENTIFIER_CLASS).state is NormalizationState.AMBIGUOUS_IDENTIFIER_CLASS


def test_serial_is_opaque_and_product_identifier_has_its_own_syntax():
    serial = identifier("  Ab c-01  ", IdentifierClass.SERIAL_NUMBER)
    assert serial.normalized_value == "Ab c-01"
    assert identifier("iPhone15,2", IdentifierClass.PRODUCT_IDENTIFIER).state is NormalizationState.ALREADY_CANONICAL
    assert identifier("17.0", IdentifierClass.PRODUCT_IDENTIFIER).state is NormalizationState.UNSUPPORTED_FORMAT


def test_exact_identifier_comparison_preserves_raw_difference():
    left = identifier("ABCDEF0123456789ABCDEF0123456789ABCDEF01")
    right = identifier("abcdef0123456789abcdef0123456789abcdef01")
    assert compare_identifiers(left, right, ComparisonMode.EXACT_RAW_MATCH).outcome is ComparisonOutcome.DIFFERENT
    assert compare_identifiers(left, right, ComparisonMode.EXACT_CANONICAL_TEXT_MATCH).outcome is ComparisonOutcome.MATCH


@pytest.mark.parametrize("raw,count", [("17", 1), ("17.0", 2), ("17.0.0", 3), ("17.0.1.0", 4)])
def test_product_version_component_counts_and_raw_preservation(raw, count):
    result = version(raw)
    assert result.raw_value == raw and result.normalized_value == raw
    assert len(result.components) == count
    assert result.profile_id == "apple-product-version-normalization"


def test_product_version_leading_zero_and_exact_comparison_modes():
    left = version("01.002")
    right = version("1.2")
    assert [(x.raw_text, x.numeric_value, x.leading_zero) for x in left.components] == [
        ("01", 1, True), ("002", 2, True)
    ]
    assert compare_product_versions(left, right, ComparisonMode.EXACT_RAW_MATCH).outcome is ComparisonOutcome.DIFFERENT
    assert compare_product_versions(left, right, ComparisonMode.EXACT_CANONICAL_TEXT_MATCH).outcome is ComparisonOutcome.DIFFERENT
    assert compare_product_versions(left, right, ComparisonMode.EXACT_COMPONENT_SEQUENCE_MATCH).outcome is ComparisonOutcome.MATCH


@pytest.mark.parametrize("raw", ["17.", ".17", "17..1", "17 0", "17.0b", "+17", "0x11", "21A123"])
def test_unsupported_versions_remain_raw_only_and_not_comparable(raw):
    result = version(raw)
    assert result.raw_value == raw and result.normalized_value is None
    assert result.state is NormalizationState.UNSUPPORTED_FORMAT
    assert compare_product_versions(result, version("17"), ComparisonMode.ORDERED_COMPONENT_COMPARISON).outcome is ComparisonOutcome.NOT_COMPARABLE


def test_whitespace_large_component_ordering_and_no_zero_padding():
    transformed = version("\t17.01\r\n")
    assert transformed.normalized_value == "17.01"
    assert transformed.state is NormalizationState.NORMALIZED
    huge = version("9" * 5000)
    assert huge.components[0].numeric_value >= 10**4999
    assert compare_product_versions(version("17"), version("17.0"), ComparisonMode.EXACT_COMPONENT_SEQUENCE_MATCH).outcome is ComparisonOutcome.DIFFERENT_COMPONENT_COUNT
    assert compare_product_versions(version("17.0.1"), version("17.0.2"), ComparisonMode.ORDERED_COMPONENT_COMPARISON).outcome is ComparisonOutcome.LESS_THAN


def test_scope_provenance_immutability_and_determinism():
    source = observation("ABCDEF0123456789ABCDEF0123456789ABCDEF01")
    first = normalize_identifier(source, IdentifierClass.DEVICE_IDENTIFIER, SCOPE)
    second = normalize_identifier(source, IdentifierClass.DEVICE_IDENTIFIER, SCOPE)
    assert source.raw_value == "ABCDEF0123456789ABCDEF0123456789ABCDEF01"
    assert (first.state, first.normalized_value, first.syntax, first.limitations) == (
        second.state, second.normalized_value, second.syntax, second.limitations
    )
    assert first.source_artifact_id == source.source_artifact_id
    assert first.processing_run_id == source.processing_run_id
    assert first.reader_id == source.reader_id
    for wrong in (
        NormalizationScope(u(99), u(2), u(3), u(4), u(5), NOW),
        NormalizationScope(u(1), u(99), u(3), u(4), u(5), NOW),
        NormalizationScope(u(1), u(2), u(99), u(4), u(5), NOW),
    ):
        with pytest.raises(PermissionError, match="scope"):
            normalize_identifier(source, IdentifierClass.DEVICE_IDENTIFIER, wrong)


def test_no_registry_or_supported_store_side_effect():
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry

    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0
