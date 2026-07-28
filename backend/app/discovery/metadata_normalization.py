"""Lossless candidate normalization for Apple backup metadata observations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.discovery.apple_backup import MetadataObservation, ValueState as SourceValueState
from app.evidence_core.typed_value import (
    TypedRepresentation,
    TypedValueObservation,
    ValueState as TypedValueState,
    ValueTransformation,
)

IDENTIFIER_PROFILE_ID = "apple-backup-identifier-normalization"
IDENTIFIER_PROFILE_VERSION = "1"
PRODUCT_VERSION_PROFILE_ID = "apple-product-version-normalization"
PRODUCT_VERSION_PROFILE_VERSION = "1"
NORMALIZER_ID = "apple-backup-metadata-normalizer"
NORMALIZER_VERSION = "1"

IDENTIFIER_LIMITATIONS = (
    "Canonical equality is textual agreement only and does not establish device identity or attribution.",
    "Backup-root names are non-authoritative and may have been renamed.",
    "Normalization does not establish authenticity, Apple compatibility, parser support, or artifact support.",
)
VERSION_LIMITATIONS = (
    "Version comparison does not establish Apple, schema, parser, or artifact compatibility.",
    "Omitted or additional zero components are not treated as equivalent.",
    "Build versions, product identifiers, and backup-format versions are separate observation types.",
)

_HEX40 = re.compile(r"^[0-9A-Fa-f]{40}$")
_HEX_PREFIX_SUFFIX = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{16}$")
_PRODUCT_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9]*,[0-9]+$")
_DOTTED_NUMERIC = re.compile(r"^[0-9]+(?:\.[0-9]+)*$")
_ASCII_WS = " \t\r\n\v\f"


class IdentifierClass(str, Enum):
    DEVICE_IDENTIFIER = "DEVICE_IDENTIFIER"
    BACKUP_IDENTIFIER = "BACKUP_IDENTIFIER"
    BACKUP_ROOT_NAME = "BACKUP_ROOT_NAME"
    SERIAL_NUMBER = "SERIAL_NUMBER"
    PRODUCT_IDENTIFIER = "PRODUCT_IDENTIFIER"
    SOURCE_DEFINED_IDENTIFIER = "SOURCE_DEFINED_IDENTIFIER"
    UNKNOWN_IDENTIFIER_CLASS = "UNKNOWN_IDENTIFIER_CLASS"


class IdentifierSyntax(str, Enum):
    HEXADECIMAL_40 = "HEXADECIMAL_40"
    HEXADECIMAL_PREFIX_AND_SUFFIX = "HEXADECIMAL_PREFIX_AND_SUFFIX"
    SOURCE_DEFINED_RECOGNIZED = "SOURCE_DEFINED_RECOGNIZED"
    SOURCE_DEFINED_UNRECOGNIZED = "SOURCE_DEFINED_UNRECOGNIZED"
    UNSUPPORTED_DEVICE_IDENTIFIER_FORMAT = "UNSUPPORTED_DEVICE_IDENTIFIER_FORMAT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class NormalizationState(str, Enum):
    NORMALIZED = "NORMALIZED"
    ALREADY_CANONICAL = "ALREADY_CANONICAL"
    RAW_ONLY = "RAW_ONLY"
    EMPTY = "EMPTY"
    MISSING = "MISSING"
    NULL = "NULL"
    MALFORMED = "MALFORMED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    AMBIGUOUS_IDENTIFIER_CLASS = "AMBIGUOUS_IDENTIFIER_CLASS"
    INVALID_CHARACTER_SET = "INVALID_CHARACTER_SET"
    NORMALIZATION_NOT_APPLICABLE = "NORMALIZATION_NOT_APPLICABLE"
    NORMALIZATION_FAILED = "NORMALIZATION_FAILED"
    INDETERMINATE = "INDETERMINATE"


class ComparisonMode(str, Enum):
    EXACT_RAW_MATCH = "EXACT_RAW_MATCH"
    EXACT_CANONICAL_TEXT_MATCH = "EXACT_CANONICAL_TEXT_MATCH"
    EXACT_COMPONENT_SEQUENCE_MATCH = "EXACT_COMPONENT_SEQUENCE_MATCH"
    ORDERED_COMPONENT_COMPARISON = "ORDERED_COMPONENT_COMPARISON"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class ComparisonOutcome(str, Enum):
    MATCH = "MATCH"
    DIFFERENT = "DIFFERENT"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"
    EQUAL = "EQUAL"
    DIFFERENT_COMPONENT_COUNT = "DIFFERENT_COMPONENT_COUNT"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True, slots=True)
class NormalizationScope:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    processing_run_id: UUID
    normalizer_identity_id: UUID
    normalized_at: datetime

    def __post_init__(self) -> None:
        if self.normalized_at.tzinfo is None or self.normalized_at.utcoffset() is None:
            raise ValueError("normalization_time_invalid")


@dataclass(frozen=True, slots=True)
class VersionComponent:
    raw_text: str
    numeric_value: int
    leading_zero: bool


@dataclass(frozen=True, slots=True)
class NormalizedMetadataValue:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    processing_run_id: UUID
    source_file: str
    source_field: str | None
    reader_id: str
    reader_version: str
    raw_value: object
    raw_state: NormalizationState
    normalized_value: str | None
    state: NormalizationState
    profile_id: str
    profile_version: str
    transformation_method: str
    syntax: IdentifierSyntax | None
    identifier_class: IdentifierClass | None
    components: tuple[VersionComponent, ...]
    typed_value: TypedValueObservation
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    mode: ComparisonMode
    outcome: ComparisonOutcome
    left: NormalizedMetadataValue
    right: NormalizedMetadataValue
    limitations: tuple[str, ...]


def _scope_check(observation: MetadataObservation, scope: NormalizationScope) -> None:
    actual = (
        observation.tenant_id,
        observation.case_id,
        observation.evidence_source_id,
        observation.processing_run_id,
    )
    expected = (
        scope.tenant_id,
        scope.case_id,
        scope.evidence_source_id,
        scope.processing_run_id,
    )
    if actual != expected:
        raise PermissionError("metadata_normalization_scope_mismatch")


def _semantic_state(observation: MetadataObservation) -> NormalizationState | None:
    if observation.value_state is SourceValueState.MISSING:
        return NormalizationState.MISSING
    if observation.value_state is SourceValueState.MALFORMED:
        return NormalizationState.MALFORMED
    if observation.value_state is SourceValueState.UNSUPPORTED:
        return NormalizationState.UNSUPPORTED_FORMAT
    if observation.raw_value is None:
        return NormalizationState.NULL
    if not isinstance(observation.raw_value, str):
        return NormalizationState.MALFORMED
    if observation.raw_value == "":
        return NormalizationState.EMPTY
    return None


def _typed_state(state: NormalizationState, normalized: bool = False) -> TypedValueState:
    if normalized:
        return TypedValueState.VALUE
    return {
        NormalizationState.MISSING: TypedValueState.MISSING,
        NormalizationState.NULL: TypedValueState.NULL,
        NormalizationState.EMPTY: TypedValueState.EMPTY,
        NormalizationState.UNSUPPORTED_FORMAT: TypedValueState.UNSUPPORTED,
        NormalizationState.MALFORMED: TypedValueState.UNREPRESENTABLE,
        NormalizationState.INVALID_CHARACTER_SET: TypedValueState.UNSUPPORTED,
        NormalizationState.AMBIGUOUS_IDENTIFIER_CLASS: TypedValueState.UNKNOWN,
    }.get(state, TypedValueState.VALUE)


def _representation(
    *, state: TypedValueState, value: str | None, type_id: str, failure_code: str | None = None
) -> TypedRepresentation:
    return TypedRepresentation(
        uuid4(), state, type_id, "apple-metadata-text", "1", value, failure_code
    )


def _envelope(
    observation: MetadataObservation,
    scope: NormalizationScope,
    *,
    profile_id: str,
    state: NormalizationState,
    normalized: str | None,
    type_id: str,
    limitations: tuple[str, ...],
) -> TypedValueObservation:
    raw_semantic = _semantic_state(observation)
    raw_state = _typed_state(raw_semantic or NormalizationState.RAW_ONLY)
    raw_value = observation.raw_value if isinstance(observation.raw_value, str) else None
    raw_failure = None
    if raw_state in {TypedValueState.UNSUPPORTED, TypedValueState.UNREPRESENTABLE}:
        raw_failure = (
            "metadata_value_unsupported"
            if raw_state is TypedValueState.UNSUPPORTED
            else "metadata_value_malformed"
        )
    raw = _representation(state=raw_state, value=raw_value, type_id=type_id, failure_code=raw_failure)
    if normalized is None:
        return TypedValueObservation(
            uuid4(),
            observation.source_artifact_id,
            observation.processing_run_id,
            scope.normalizer_identity_id,
            scope.normalized_at,
            raw,
        )
    normalized_representation = _representation(
        state=TypedValueState.VALUE, value=normalized, type_id=type_id
    )
    transformation = ValueTransformation(
        uuid4(),
        profile_id,
        "1",
        observation.processing_run_id,
        scope.normalizer_identity_id,
        scope.normalized_at,
        limitations,
    )
    return TypedValueObservation(
        uuid4(),
        observation.source_artifact_id,
        observation.processing_run_id,
        scope.normalizer_identity_id,
        scope.normalized_at,
        raw,
        normalized_representation,
        transformation,
    )


def normalize_identifier(
    observation: MetadataObservation,
    identifier_class: IdentifierClass,
    scope: NormalizationScope,
) -> NormalizedMetadataValue:
    _scope_check(observation, scope)
    semantic = _semantic_state(observation)
    raw_state = semantic or NormalizationState.RAW_ONLY
    normalized: str | None = None
    syntax = IdentifierSyntax.NOT_APPLICABLE
    state = semantic
    raw = observation.raw_value

    if semantic is None:
        assert isinstance(raw, str)
        if not raw.isascii():
            state = NormalizationState.INVALID_CHARACTER_SET
        elif identifier_class is IdentifierClass.UNKNOWN_IDENTIFIER_CLASS:
            state = NormalizationState.AMBIGUOUS_IDENTIFIER_CLASS
        else:
            candidate = raw.strip(_ASCII_WS)
            if candidate == "":
                state = NormalizationState.EMPTY
            elif identifier_class in {
                IdentifierClass.DEVICE_IDENTIFIER,
                IdentifierClass.BACKUP_IDENTIFIER,
                IdentifierClass.BACKUP_ROOT_NAME,
            }:
                if _HEX40.fullmatch(candidate):
                    syntax = IdentifierSyntax.HEXADECIMAL_40
                    normalized = candidate.lower()
                elif _HEX_PREFIX_SUFFIX.fullmatch(candidate):
                    syntax = IdentifierSyntax.HEXADECIMAL_PREFIX_AND_SUFFIX
                    normalized = candidate.lower()
                else:
                    syntax = IdentifierSyntax.UNSUPPORTED_DEVICE_IDENTIFIER_FORMAT
                    state = NormalizationState.UNSUPPORTED_FORMAT
            elif identifier_class is IdentifierClass.PRODUCT_IDENTIFIER:
                if _PRODUCT_IDENTIFIER.fullmatch(candidate):
                    syntax = IdentifierSyntax.SOURCE_DEFINED_RECOGNIZED
                    normalized = candidate
                else:
                    syntax = IdentifierSyntax.SOURCE_DEFINED_UNRECOGNIZED
                    state = NormalizationState.UNSUPPORTED_FORMAT
            else:
                syntax = IdentifierSyntax.SOURCE_DEFINED_RECOGNIZED
                normalized = candidate
            if normalized is not None:
                state = (
                    NormalizationState.ALREADY_CANONICAL
                    if normalized == raw
                    else NormalizationState.NORMALIZED
                )

    assert state is not None
    typed = _envelope(
        observation,
        scope,
        profile_id=IDENTIFIER_PROFILE_ID,
        state=state,
        normalized=normalized,
        type_id=f"identifier.{identifier_class.value.lower()}",
        limitations=IDENTIFIER_LIMITATIONS,
    )
    return NormalizedMetadataValue(
        observation.tenant_id,
        observation.case_id,
        observation.evidence_source_id,
        observation.source_artifact_id,
        observation.processing_run_id,
        observation.source_file,
        observation.field_name,
        observation.reader_id,
        observation.reader_version,
        raw,
        raw_state,
        normalized,
        state,
        IDENTIFIER_PROFILE_ID,
        IDENTIFIER_PROFILE_VERSION,
        IDENTIFIER_PROFILE_ID,
        syntax,
        identifier_class,
        (),
        typed,
        IDENTIFIER_LIMITATIONS,
    )


def _safe_decimal_integer(text: str) -> int:
    value = 0
    for character in text:
        value = value * 10 + (ord(character) - 48)
    return value


def normalize_product_version(
    observation: MetadataObservation, scope: NormalizationScope
) -> NormalizedMetadataValue:
    _scope_check(observation, scope)
    semantic = _semantic_state(observation)
    raw_state = semantic or NormalizationState.RAW_ONLY
    normalized: str | None = None
    components: tuple[VersionComponent, ...] = ()
    state = semantic
    raw = observation.raw_value

    if semantic is None:
        assert isinstance(raw, str)
        if not raw.isascii():
            state = NormalizationState.INVALID_CHARACTER_SET
        else:
            candidate = raw.strip(_ASCII_WS)
            if candidate == "":
                state = NormalizationState.EMPTY
            elif not _DOTTED_NUMERIC.fullmatch(candidate):
                state = NormalizationState.UNSUPPORTED_FORMAT
            else:
                component_text = candidate.split(".")
                components = tuple(
                    VersionComponent(
                        item,
                        _safe_decimal_integer(item),
                        len(item) > 1 and item.startswith("0"),
                    )
                    for item in component_text
                )
                normalized = candidate
                state = (
                    NormalizationState.ALREADY_CANONICAL
                    if candidate == raw
                    else NormalizationState.NORMALIZED
                )

    assert state is not None
    typed = _envelope(
        observation,
        scope,
        profile_id=PRODUCT_VERSION_PROFILE_ID,
        state=state,
        normalized=normalized,
        type_id="apple.product-version",
        limitations=VERSION_LIMITATIONS,
    )
    return NormalizedMetadataValue(
        observation.tenant_id,
        observation.case_id,
        observation.evidence_source_id,
        observation.source_artifact_id,
        observation.processing_run_id,
        observation.source_file,
        observation.field_name,
        observation.reader_id,
        observation.reader_version,
        raw,
        raw_state,
        normalized,
        state,
        PRODUCT_VERSION_PROFILE_ID,
        PRODUCT_VERSION_PROFILE_VERSION,
        PRODUCT_VERSION_PROFILE_ID,
        None,
        None,
        components,
        typed,
        VERSION_LIMITATIONS,
    )


def compare_identifiers(
    left: NormalizedMetadataValue, right: NormalizedMetadataValue, mode: ComparisonMode
) -> ComparisonResult:
    if mode not in {ComparisonMode.EXACT_RAW_MATCH, ComparisonMode.EXACT_CANONICAL_TEXT_MATCH}:
        return ComparisonResult(
            ComparisonMode.NOT_COMPARABLE,
            ComparisonOutcome.NOT_COMPARABLE,
            left,
            right,
            IDENTIFIER_LIMITATIONS,
        )
    if left.identifier_class is not right.identifier_class:
        return ComparisonResult(
            ComparisonMode.NOT_COMPARABLE,
            ComparisonOutcome.NOT_COMPARABLE,
            left,
            right,
            IDENTIFIER_LIMITATIONS,
        )
    if mode is ComparisonMode.EXACT_RAW_MATCH:
        values = left.raw_value, right.raw_value
    else:
        if left.normalized_value is None or right.normalized_value is None:
            return ComparisonResult(
                ComparisonMode.NOT_COMPARABLE,
                ComparisonOutcome.NOT_COMPARABLE,
                left,
                right,
                IDENTIFIER_LIMITATIONS,
            )
        values = left.normalized_value, right.normalized_value
    return ComparisonResult(
        mode,
        ComparisonOutcome.MATCH if values[0] == values[1] else ComparisonOutcome.DIFFERENT,
        left,
        right,
        IDENTIFIER_LIMITATIONS,
    )


def compare_product_versions(
    left: NormalizedMetadataValue, right: NormalizedMetadataValue, mode: ComparisonMode
) -> ComparisonResult:
    comparable = bool(left.components and right.components)
    if mode is ComparisonMode.EXACT_RAW_MATCH:
        outcome = (
            ComparisonOutcome.MATCH
            if left.raw_value == right.raw_value
            else ComparisonOutcome.DIFFERENT
        )
    elif mode is ComparisonMode.EXACT_CANONICAL_TEXT_MATCH:
        if left.normalized_value is None or right.normalized_value is None:
            outcome = ComparisonOutcome.NOT_COMPARABLE
        else:
            outcome = (
                ComparisonOutcome.MATCH
                if left.normalized_value == right.normalized_value
                else ComparisonOutcome.DIFFERENT
            )
    elif mode in {
        ComparisonMode.EXACT_COMPONENT_SEQUENCE_MATCH,
        ComparisonMode.ORDERED_COMPONENT_COMPARISON,
    }:
        if not comparable:
            outcome = ComparisonOutcome.NOT_COMPARABLE
        elif len(left.components) != len(right.components):
            outcome = ComparisonOutcome.DIFFERENT_COMPONENT_COUNT
        else:
            left_values = tuple(item.numeric_value for item in left.components)
            right_values = tuple(item.numeric_value for item in right.components)
            if mode is ComparisonMode.EXACT_COMPONENT_SEQUENCE_MATCH:
                outcome = (
                    ComparisonOutcome.MATCH
                    if left_values == right_values
                    else ComparisonOutcome.DIFFERENT
                )
            elif left_values < right_values:
                outcome = ComparisonOutcome.LESS_THAN
            elif left_values > right_values:
                outcome = ComparisonOutcome.GREATER_THAN
            else:
                outcome = ComparisonOutcome.EQUAL
    else:
        outcome = ComparisonOutcome.NOT_COMPARABLE
    resolved_mode = (
        ComparisonMode.NOT_COMPARABLE
        if outcome is ComparisonOutcome.NOT_COMPARABLE
        else mode
    )
    return ComparisonResult(resolved_mode, outcome, left, right, VERSION_LIMITATIONS)
