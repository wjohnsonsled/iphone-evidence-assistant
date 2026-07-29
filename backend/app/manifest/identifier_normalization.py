"""Profile-driven, lossless identifier normalization for controlled observations."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid5

from app.manifest.files_query import (
    ColumnValueState,
    FilesQueryContext,
    FilesRowObservation,
)
from app.manifest.files_query_v2 import (
    RowValueState,
    V2RowObservation,
)

FRAMEWORK_ID = "canonical-identifier-normalization"
FRAMEWORK_VERSION = "1"
PROFILE_ID = "manifestdb-fileid-normalization"
PROFILE_VERSION = "1"
IMPLEMENTATION_ID = "manifestdb-fileid-normalizer"
IMPLEMENTATION_VERSION = "1"
SOURCE_TABLE = "Files"
SOURCE_COLUMN = "fileID"
_NAMESPACE = UUID("06030000-0000-4000-8000-000000000001")
_ASCII_WHITESPACE = frozenset(" \t\r\n\v\f")
_HEX = frozenset("0123456789abcdefABCDEF")
MAX_POLICY_COUNTER = 2_147_483_647

LIMITATIONS = (
    "Lexical recognition is not hash verification or cryptographic integrity.",
    "Normalization is not physical backup-object resolution or proof of existence.",
    "Canonical equality is not content, object, artifact, or source-row identity.",
    "Repeated fileID observations are not duplicate-file or orphan conclusions.",
    "Absence, completeness, tampering, and corruption have not been evaluated.",
    "Candidate infrastructure is not Apple, parser, artifact, workflow, or support approval.",
)


class IdentifierClass(str, Enum):
    MANIFEST_FILE_ID = "MANIFEST_FILE_ID"
    SOURCE_DEFINED_IDENTIFIER = "SOURCE_DEFINED_IDENTIFIER"
    UNKNOWN_IDENTIFIER_CLASS = "UNKNOWN_IDENTIFIER_CLASS"


class StorageClass(str, Enum):
    NULL = "NULL"
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"
    BLOB = "BLOB"


class SyntaxResult(str, Enum):
    FILEID_RECOGNIZED_40_HEX = "FILEID_RECOGNIZED_40_HEX"
    FILEID_SYNTAX_NOT_RECOGNIZED = "FILEID_SYNTAX_NOT_RECOGNIZED"
    NOT_EVALUATED = "NOT_EVALUATED"


class NormalizationOutcome(str, Enum):
    FILEID_RECOGNIZED_CANONICAL = "FILEID_RECOGNIZED_CANONICAL"
    FILEID_RECOGNIZED_NORMALIZED = "FILEID_RECOGNIZED_NORMALIZED"
    FILEID_NULL = "FILEID_NULL"
    FILEID_EMPTY_TEXT = "FILEID_EMPTY_TEXT"
    FILEID_EMPTY_BLOB = "FILEID_EMPTY_BLOB"
    FILEID_INVALID_LENGTH = "FILEID_INVALID_LENGTH"
    FILEID_INVALID_CHARACTER = "FILEID_INVALID_CHARACTER"
    FILEID_NON_ASCII_TEXT = "FILEID_NON_ASCII_TEXT"
    FILEID_TEXT_WITH_WHITESPACE = "FILEID_TEXT_WITH_WHITESPACE"
    FILEID_UNSUPPORTED_TEXT_SYNTAX = "FILEID_UNSUPPORTED_TEXT_SYNTAX"
    FILEID_BLOB_ASCII_RECOGNIZED = "FILEID_BLOB_ASCII_RECOGNIZED"
    FILEID_BLOB_ASCII_UNRECOGNIZED = "FILEID_BLOB_ASCII_UNRECOGNIZED"
    FILEID_BLOB_NON_ASCII = "FILEID_BLOB_NON_ASCII"
    FILEID_UNSUPPORTED_STORAGE_CLASS = "FILEID_UNSUPPORTED_STORAGE_CLASS"
    FILEID_SOURCE_VALUE_UNAVAILABLE = "FILEID_SOURCE_VALUE_UNAVAILABLE"
    FILEID_READ_FAILURE = "FILEID_READ_FAILURE"
    FILEID_NOT_EVALUATED = "FILEID_NOT_EVALUATED"
    FILEID_INDETERMINATE = "FILEID_INDETERMINATE"


class TransformationType(str, Enum):
    NONE = "NONE"
    STRICT_ASCII_BLOB_DECODE = "STRICT_ASCII_BLOB_DECODE"
    ASCII_HEX_CASE_CANONICALIZATION = "ASCII_HEX_CASE_CANONICALIZATION"


class TransformationState(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ComparisonMode(str, Enum):
    EXACT_RAW = "EXACT_RAW"
    EXACT_CANONICAL = "EXACT_CANONICAL"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class ComparisonOutcome(str, Enum):
    EQUAL = "EQUAL"
    DIFFERENT = "DIFFERENT"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class ComparisonEligibility(str, Enum):
    RAW_AND_CANONICAL = "RAW_AND_CANONICAL"
    RAW_ONLY = "RAW_ONLY"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True, slots=True)
class IdentifierProfile:
    profile_id: str
    profile_version: str
    identifier_class: IdentifierClass
    accepted_storage_classes: tuple[StorageClass, ...]
    permitted_transformations: tuple[TransformationType, ...]
    comparison_modes: tuple[ComparisonMode, ...]
    canonical_description: str
    limitations: tuple[str, ...]


MANIFEST_FILEID_PROFILE = IdentifierProfile(
    PROFILE_ID,
    PROFILE_VERSION,
    IdentifierClass.MANIFEST_FILE_ID,
    (StorageClass.TEXT, StorageClass.BLOB),
    (
        TransformationType.NONE,
        TransformationType.STRICT_ASCII_BLOB_DECODE,
        TransformationType.ASCII_HEX_CASE_CANONICALIZATION,
    ),
    (ComparisonMode.EXACT_RAW, ComparisonMode.EXACT_CANONICAL),
    "Exactly 40 lowercase ASCII hexadecimal characters after exact lexical recognition.",
    LIMITATIONS,
)


@dataclass(frozen=True, slots=True)
class IdentifierSourceObservation:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    controlled_copy_identity_id: UUID
    manifest_database_identity_id: UUID
    processing_run_id: UUID
    source_table: str
    source_column: str
    row_locator: int
    locator_profile_id: str
    locator_profile_version: str
    query_profile_id: str
    query_profile_version: str
    storage_class: StorageClass
    upstream_value_state: str
    raw_value: str | int | float | bytes | None
    blob_authorized: bool
    observed_at: datetime
    synthetic_fixture: bool = False

    def __post_init__(self) -> None:
        identities = (
            self.tenant_id,
            self.case_id,
            self.evidence_source_id,
            self.source_artifact_id,
            self.controlled_copy_identity_id,
            self.manifest_database_identity_id,
            self.processing_run_id,
        )
        if any(not isinstance(identity, UUID) for identity in identities):
            raise ValueError("identifier_source_provenance_incomplete")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("identifier_source_time_invalid")
        if self.source_table != SOURCE_TABLE or self.source_column != SOURCE_COLUMN:
            raise ValueError("identifier_source_not_manifest_fileid")
        if self.query_profile_id != "manifestdb-files-query":
            raise ValueError("identifier_query_profile_unapproved")
        if self.query_profile_version not in {"1", "2"}:
            raise ValueError("identifier_query_version_unapproved")
        if (
            self.locator_profile_id != "manifestdb-row-locator"
            or self.locator_profile_version != "1"
        ):
            raise ValueError("identifier_locator_profile_unapproved")
        if self.storage_class is StorageClass.BLOB and isinstance(self.raw_value, bytes):
            if not self.blob_authorized:
                raise ValueError("identifier_blob_not_authorized")
        expected = {
            StorageClass.NULL: type(None),
            StorageClass.INTEGER: int,
            StorageClass.REAL: float,
            StorageClass.TEXT: str,
            StorageClass.BLOB: bytes,
        }[self.storage_class]
        if self.raw_value is not None and not isinstance(self.raw_value, expected):
            raise ValueError("identifier_storage_value_mismatch")


@dataclass(frozen=True, slots=True)
class TransformationRecord:
    transformation_type: TransformationType
    sequence_number: int
    input_representation_reference: str
    output_representation_reference: str
    deterministic_parameters: tuple[str, ...]
    profile_version: str
    implementation_version: str
    state: TransformationState


@dataclass(frozen=True, slots=True)
class IdentifierObservation:
    observation_id: UUID
    source: IdentifierSourceObservation
    identifier_class: IdentifierClass
    syntax_profile_id: str
    syntax_profile_version: str
    normalization_profile_id: str
    normalization_profile_version: str
    syntax_result: SyntaxResult
    normalization_result: NormalizationOutcome
    canonical_representation: str | None
    decoded_blob_text: str | None
    raw_byte_length: int | None
    raw_character_length: int | None
    transformations: tuple[TransformationRecord, ...]
    comparison_eligibility: ComparisonEligibility
    implementation_id: str
    implementation_version: str
    observed_at: datetime
    limitations: tuple[str, ...]
    prior_observation_id: UUID | None = None

    def canonical_json(self) -> str:
        source = asdict(self.source)
        source["tenant_id"] = str(self.source.tenant_id)
        source["case_id"] = str(self.source.case_id)
        source["evidence_source_id"] = str(self.source.evidence_source_id)
        source["source_artifact_id"] = str(self.source.source_artifact_id)
        source["controlled_copy_identity_id"] = str(
            self.source.controlled_copy_identity_id
        )
        source["manifest_database_identity_id"] = str(
            self.source.manifest_database_identity_id
        )
        source["processing_run_id"] = str(self.source.processing_run_id)
        source["storage_class"] = self.source.storage_class.value
        source["observed_at"] = self.source.observed_at.isoformat()
        if isinstance(self.source.raw_value, bytes):
            source["raw_value"] = {
                "representation": "BOUNDED_BLOB_NOT_SERIALIZED",
                "byte_length": len(self.source.raw_value),
            }
        payload = {
            "observation_id": str(self.observation_id),
            "source": source,
            "identifier_class": self.identifier_class.value,
            "syntax_profile_id": self.syntax_profile_id,
            "syntax_profile_version": self.syntax_profile_version,
            "normalization_profile_id": self.normalization_profile_id,
            "normalization_profile_version": self.normalization_profile_version,
            "syntax_result": self.syntax_result.value,
            "normalization_result": self.normalization_result.value,
            "canonical_representation": self.canonical_representation,
            "decoded_blob_text": self.decoded_blob_text,
            "raw_byte_length": self.raw_byte_length,
            "raw_character_length": self.raw_character_length,
            "transformations": [
                {
                    **asdict(item),
                    "transformation_type": item.transformation_type.value,
                    "state": item.state.value,
                }
                for item in self.transformations
            ],
            "comparison_eligibility": self.comparison_eligibility.value,
            "implementation_id": self.implementation_id,
            "implementation_version": self.implementation_version,
            "observed_at": self.observed_at.isoformat(),
            "limitations": list(self.limitations),
            "prior_observation_id": (
                str(self.prior_observation_id)
                if self.prior_observation_id is not None
                else None
            ),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class IdentifierComparison:
    mode: ComparisonMode
    outcome: ComparisonOutcome
    left_observation_id: UUID
    right_observation_id: UUID
    raw_storage_class_equal: bool | None
    reason_code: str
    limitations: tuple[str, ...] = LIMITATIONS


@dataclass(frozen=True, slots=True)
class BatchResourcePolicy:
    max_observations: int
    max_comparisons: int
    max_projected_bytes: int
    max_memory_estimate_bytes: int
    max_wall_clock_seconds: float

    def __post_init__(self) -> None:
        values = (
            self.max_observations,
            self.max_comparisons,
            self.max_projected_bytes,
            self.max_memory_estimate_bytes,
            self.max_wall_clock_seconds,
        )
        if any(isinstance(value, bool) or value <= 0 for value in values):
            raise ValueError("identifier_resource_policy_invalid")
        if any(
            value > MAX_POLICY_COUNTER
            for value in (
                self.max_observations,
                self.max_comparisons,
                self.max_projected_bytes,
                self.max_memory_estimate_bytes,
            )
        ):
            raise ValueError("identifier_resource_policy_excessive")


@dataclass(frozen=True, slots=True)
class BatchNormalizationResult:
    observations: tuple[IdentifierObservation, ...]
    inputs_attempted: int
    termination_reason: str
    projected_bytes: int
    deterministic_memory_estimate: int
    continuation_index: int | None
    limitations: tuple[str, ...] = LIMITATIONS


@dataclass(frozen=True, slots=True)
class BatchComparisonResult:
    comparisons: tuple[IdentifierComparison, ...]
    pairs_attempted: int
    termination_reason: str
    projected_bytes: int
    deterministic_memory_estimate: int
    continuation_index: int | None
    limitations: tuple[str, ...] = LIMITATIONS


def _storage_from_v1(name: str) -> StorageClass:
    return {
        "NoneType": StorageClass.NULL,
        "int": StorageClass.INTEGER,
        "float": StorageClass.REAL,
        "str": StorageClass.TEXT,
        "bytes": StorageClass.BLOB,
    }[name]


def source_from_v1(
    row: FilesRowObservation,
    context: FilesQueryContext,
    controlled_copy_identity_id: UUID,
) -> IdentifierSourceObservation:
    if (
        (
            context.tenant_id,
            context.case_id,
            context.evidence_source_id,
            context.processing_run_id,
        )
        != context.authorized_scope
        or
        row.processing_run_id != context.processing_run_id
        or row.source_artifact_id != context.source_artifact_id
        or row.database_identity_id != context.database_identity_id
        or row.row_locator.processing_run_id != context.processing_run_id
    ):
        raise ValueError("identifier_v1_scope_mismatch")
    value = next(
        (item for item in row.projected_values if item.column_name == SOURCE_COLUMN),
        None,
    )
    if value is None:
        raise ValueError("identifier_fileid_not_projected")
    return IdentifierSourceObservation(
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.source_artifact_id,
        controlled_copy_identity_id,
        context.database_identity_id,
        context.processing_run_id,
        SOURCE_TABLE,
        SOURCE_COLUMN,
        row.row_locator.locator_value,
        "manifestdb-row-locator",
        row.row_locator.locator_version,
        row.query_profile_id,
        row.query_profile_version,
        _storage_from_v1(value.observed_sqlite_type),
        value.state.value,
        value.raw_value,
        isinstance(value.raw_value, bytes),
        row.queried_at,
    )


def source_from_v2(
    row: V2RowObservation,
    context: FilesQueryContext,
    controlled_copy_identity_id: UUID,
    *,
    blob_authorized: bool = False,
) -> IdentifierSourceObservation:
    if (
        (
            context.tenant_id,
            context.case_id,
            context.evidence_source_id,
            context.processing_run_id,
        )
        != context.authorized_scope
        or
        row.processing_run_id != context.processing_run_id
        or row.source_artifact_id != context.source_artifact_id
        or row.database_identity_id != context.database_identity_id
        or row.row_locator.processing_run_id != context.processing_run_id
    ):
        raise ValueError("identifier_v2_scope_mismatch")
    value = next(
        (item for item in row.projected_values if item.column_name == SOURCE_COLUMN),
        None,
    )
    if value is None:
        raise ValueError("identifier_fileid_not_projected")
    storage = StorageClass(value.observed_storage_class)
    return IdentifierSourceObservation(
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.source_artifact_id,
        controlled_copy_identity_id,
        context.database_identity_id,
        context.processing_run_id,
        SOURCE_TABLE,
        SOURCE_COLUMN,
        row.row_locator.locator_value,
        "manifestdb-row-locator",
        row.row_locator.locator_version,
        row.query_profile_id,
        row.query_profile_version,
        storage,
        value.state.value,
        value.raw_value,
        blob_authorized,
        row.observed_at,
    )


def synthetic_source(
    raw_value: str | int | float | bytes | None,
    storage_class: StorageClass,
    *,
    upstream_value_state: str = "VALUE_PRESENT",
    blob_authorized: bool = False,
    seed: int = 1,
    tenant_id: UUID | None = None,
    case_id: UUID | None = None,
) -> IdentifierSourceObservation:
    """Explicit synthetic-only harness; production adapters never call this."""

    def uid(n: int) -> UUID:
        return UUID(f"06030000-0000-4000-8000-{n:012d}")

    return IdentifierSourceObservation(
        tenant_id or uid(1),
        case_id or uid(2),
        uid(3),
        uid(4),
        uid(5),
        uid(6),
        uid(7),
        SOURCE_TABLE,
        SOURCE_COLUMN,
        seed,
        "manifestdb-row-locator",
        "1",
        "manifestdb-files-query",
        "2",
        storage_class,
        upstream_value_state,
        raw_value,
        blob_authorized,
        datetime(2026, 7, 28, tzinfo=timezone.utc),
        True,
    )


def _transform(
    kind: TransformationType,
    sequence: int,
    input_ref: str,
    output_ref: str,
    *parameters: str,
) -> TransformationRecord:
    if kind not in MANIFEST_FILEID_PROFILE.permitted_transformations:
        raise ValueError("identifier_transformation_not_permitted")
    return TransformationRecord(
        kind,
        sequence,
        input_ref,
        output_ref,
        tuple(parameters),
        PROFILE_VERSION,
        IMPLEMENTATION_VERSION,
        TransformationState.SUCCEEDED,
    )


def _text_outcome(text: str) -> tuple[NormalizationOutcome, SyntaxResult, str | None]:
    if text == "":
        return NormalizationOutcome.FILEID_EMPTY_TEXT, SyntaxResult.FILEID_SYNTAX_NOT_RECOGNIZED, None
    if not text.isascii():
        return NormalizationOutcome.FILEID_NON_ASCII_TEXT, SyntaxResult.FILEID_SYNTAX_NOT_RECOGNIZED, None
    if any(character in _ASCII_WHITESPACE for character in text):
        return NormalizationOutcome.FILEID_TEXT_WITH_WHITESPACE, SyntaxResult.FILEID_SYNTAX_NOT_RECOGNIZED, None
    if text.startswith("0x") or text.startswith("{") or "-" in text or text.endswith("}"):
        return NormalizationOutcome.FILEID_UNSUPPORTED_TEXT_SYNTAX, SyntaxResult.FILEID_SYNTAX_NOT_RECOGNIZED, None
    if len(text) != 40:
        return NormalizationOutcome.FILEID_INVALID_LENGTH, SyntaxResult.FILEID_SYNTAX_NOT_RECOGNIZED, None
    if any(character not in _HEX for character in text):
        return NormalizationOutcome.FILEID_INVALID_CHARACTER, SyntaxResult.FILEID_SYNTAX_NOT_RECOGNIZED, None
    canonical = text.lower()
    outcome = (
        NormalizationOutcome.FILEID_RECOGNIZED_CANONICAL
        if canonical == text
        else NormalizationOutcome.FILEID_RECOGNIZED_NORMALIZED
    )
    return outcome, SyntaxResult.FILEID_RECOGNIZED_40_HEX, canonical


def _stable_id(source: IdentifierSourceObservation) -> UUID:
    raw = (
        source.raw_value.hex()
        if isinstance(source.raw_value, bytes)
        else repr(source.raw_value)
    )
    name = "|".join(
        (
            str(source.tenant_id),
            str(source.case_id),
            str(source.evidence_source_id),
            str(source.source_artifact_id),
            str(source.controlled_copy_identity_id),
            str(source.processing_run_id),
            str(source.row_locator),
            source.query_profile_version,
            source.storage_class.value,
            raw,
            PROFILE_ID,
            PROFILE_VERSION,
        )
    )
    return uuid5(_NAMESPACE, name)


def normalize_manifest_fileid(
    source: IdentifierSourceObservation,
    *,
    prior_observation_id: UUID | None = None,
) -> IdentifierObservation:
    storage = source.storage_class
    raw = source.raw_value
    outcome = NormalizationOutcome.FILEID_INDETERMINATE
    syntax = SyntaxResult.NOT_EVALUATED
    canonical: str | None = None
    decoded: str | None = None
    transformations: list[TransformationRecord] = []
    byte_length: int | None = None
    character_length: int | None = None

    state = source.upstream_value_state
    if state in {"READ_FAILURE", "FILEID_READ_FAILURE"}:
        outcome = NormalizationOutcome.FILEID_READ_FAILURE
    elif state in {"NOT_PROJECTED", "NOT_AVAILABLE", "FILEID_SOURCE_VALUE_UNAVAILABLE"}:
        outcome = NormalizationOutcome.FILEID_SOURCE_VALUE_UNAVAILABLE
    elif state in {"NOT_EVALUATED", "FILEID_NOT_EVALUATED"}:
        outcome = NormalizationOutcome.FILEID_NOT_EVALUATED
    elif state in {"INDETERMINATE", "FILEID_INDETERMINATE"}:
        outcome = NormalizationOutcome.FILEID_INDETERMINATE
    elif storage is StorageClass.NULL:
        outcome = NormalizationOutcome.FILEID_NULL
    elif storage in {StorageClass.INTEGER, StorageClass.REAL}:
        outcome = NormalizationOutcome.FILEID_UNSUPPORTED_STORAGE_CLASS
    elif storage is StorageClass.TEXT:
        if not isinstance(raw, str):
            outcome = NormalizationOutcome.FILEID_INDETERMINATE
        else:
            character_length = len(raw)
            byte_length = len(raw.encode("utf-8"))
            outcome, syntax, canonical = _text_outcome(raw)
            if canonical is not None:
                transformations.append(
                    _transform(
                        (
                            TransformationType.NONE
                            if canonical == raw
                            else TransformationType.ASCII_HEX_CASE_CANONICALIZATION
                        ),
                        1,
                        "raw",
                        "canonical",
                        "ASCII",
                        "lowercase",
                    )
                )
    elif storage is StorageClass.BLOB:
        if not isinstance(raw, bytes) or not source.blob_authorized:
            outcome = NormalizationOutcome.FILEID_SOURCE_VALUE_UNAVAILABLE
        else:
            byte_length = len(raw)
            if len(raw) == 0:
                outcome = NormalizationOutcome.FILEID_EMPTY_BLOB
            elif any(byte > 0x7F for byte in raw):
                outcome = NormalizationOutcome.FILEID_BLOB_NON_ASCII
            else:
                decoded = raw.decode("ascii", errors="strict")
                transformations.append(
                    _transform(
                        TransformationType.STRICT_ASCII_BLOB_DECODE,
                        1,
                        "raw_blob",
                        "decoded_text",
                        "encoding=ASCII",
                        "errors=strict",
                    )
                )
                character_length = len(decoded)
                text_outcome, syntax, canonical = _text_outcome(decoded)
                if canonical is None:
                    outcome = NormalizationOutcome.FILEID_BLOB_ASCII_UNRECOGNIZED
                else:
                    outcome = NormalizationOutcome.FILEID_BLOB_ASCII_RECOGNIZED
                    if canonical != decoded:
                        transformations.append(
                            _transform(
                                TransformationType.ASCII_HEX_CASE_CANONICALIZATION,
                                2,
                                "decoded_text",
                                "canonical",
                                "ASCII",
                                "lowercase",
                            )
                        )
    eligibility = (
        ComparisonEligibility.RAW_AND_CANONICAL
        if canonical is not None
        else ComparisonEligibility.NOT_COMPARABLE
    )
    return IdentifierObservation(
        _stable_id(source),
        source,
        IdentifierClass.MANIFEST_FILE_ID,
        PROFILE_ID,
        PROFILE_VERSION,
        PROFILE_ID,
        PROFILE_VERSION,
        syntax,
        outcome,
        canonical,
        decoded,
        byte_length,
        character_length,
        tuple(transformations),
        eligibility,
        IMPLEMENTATION_ID,
        IMPLEMENTATION_VERSION,
        source.observed_at,
        LIMITATIONS,
        prior_observation_id,
    )


def compare_identifiers(
    left: IdentifierObservation,
    right: IdentifierObservation,
    mode: ComparisonMode,
) -> IdentifierComparison:
    same_scope = (
        left.source.tenant_id == right.source.tenant_id
        and left.source.case_id == right.source.case_id
    )
    same_profile = (
        left.normalization_profile_id == right.normalization_profile_id
        and left.normalization_profile_version == right.normalization_profile_version
        == PROFILE_VERSION
    )
    if not same_scope:
        return IdentifierComparison(
            ComparisonMode.NOT_COMPARABLE,
            ComparisonOutcome.NOT_COMPARABLE,
            left.observation_id,
            right.observation_id,
            None,
            "identifier_comparison_scope_denied",
        )
    if mode is ComparisonMode.EXACT_RAW:
        if (
            left.comparison_eligibility is ComparisonEligibility.NOT_COMPARABLE
            or right.comparison_eligibility is ComparisonEligibility.NOT_COMPARABLE
            or left.source.storage_class is not right.source.storage_class
        ):
            return IdentifierComparison(
                ComparisonMode.NOT_COMPARABLE,
                ComparisonOutcome.NOT_COMPARABLE,
                left.observation_id,
                right.observation_id,
                False,
                "identifier_raw_not_comparable",
            )
        equal = left.source.raw_value == right.source.raw_value
        return IdentifierComparison(
            mode,
            ComparisonOutcome.EQUAL if equal else ComparisonOutcome.DIFFERENT,
            left.observation_id,
            right.observation_id,
            True,
            "identifier_raw_equal" if equal else "identifier_raw_different",
        )
    if (
        mode is not ComparisonMode.EXACT_CANONICAL
        or not same_profile
        or left.canonical_representation is None
        or right.canonical_representation is None
    ):
        return IdentifierComparison(
            ComparisonMode.NOT_COMPARABLE,
            ComparisonOutcome.NOT_COMPARABLE,
            left.observation_id,
            right.observation_id,
            None,
            "identifier_canonical_not_comparable",
        )
    equal = left.canonical_representation == right.canonical_representation
    return IdentifierComparison(
        mode,
        ComparisonOutcome.EQUAL if equal else ComparisonOutcome.DIFFERENT,
        left.observation_id,
        right.observation_id,
        None,
        "identifier_canonical_equal" if equal else "identifier_canonical_different",
    )


def normalize_batch(
    sources: Iterable[IdentifierSourceObservation],
    policy: BatchResourcePolicy,
    *,
    cancelled: Callable[[], bool] = lambda: False,
    monotonic_clock: Callable[[], float] = time.monotonic,
) -> BatchNormalizationResult:
    start = monotonic_clock()
    completed: list[IdentifierObservation] = []
    attempted = 0
    projected = 0
    memory = 128
    termination = "COMPLETED"
    continuation: int | None = None
    for index, source in enumerate(sources):
        if cancelled():
            termination, continuation = "CANCELLED", index
            break
        if monotonic_clock() - start >= policy.max_wall_clock_seconds:
            termination, continuation = "WALL_CLOCK_LIMIT_REACHED", index
            break
        if len(completed) >= policy.max_observations:
            termination, continuation = "OBSERVATION_LIMIT_REACHED", index
            break
        attempted += 1
        raw_bytes = (
            len(source.raw_value)
            if isinstance(source.raw_value, bytes)
            else (
                len(source.raw_value.encode("utf-8"))
                if isinstance(source.raw_value, str)
                else (8 if isinstance(source.raw_value, (int, float)) else 0)
            )
        )
        next_projected = projected + raw_bytes
        next_memory = memory + raw_bytes + 512
        if next_projected > policy.max_projected_bytes:
            termination, continuation = "BYTE_LIMIT_REACHED", index
            break
        if next_memory > policy.max_memory_estimate_bytes:
            termination, continuation = "MEMORY_ESTIMATE_LIMIT_REACHED", index
            break
        completed.append(normalize_manifest_fileid(source))
        projected, memory = next_projected, next_memory
    return BatchNormalizationResult(
        tuple(completed),
        attempted,
        termination,
        projected,
        memory,
        continuation,
    )


def _observation_size(observation: IdentifierObservation) -> int:
    raw = observation.source.raw_value
    raw_size = (
        len(raw)
        if isinstance(raw, bytes)
        else (
            len(raw.encode("utf-8"))
            if isinstance(raw, str)
            else (8 if isinstance(raw, (int, float)) else 0)
        )
    )
    canonical_size = (
        len(observation.canonical_representation.encode("ascii"))
        if observation.canonical_representation is not None
        else 0
    )
    return raw_size + canonical_size + 64


def compare_explicit_pairs(
    pairs: Iterable[
        tuple[IdentifierObservation, IdentifierObservation, ComparisonMode]
    ],
    policy: BatchResourcePolicy,
    *,
    cancelled: Callable[[], bool] = lambda: False,
    monotonic_clock: Callable[[], float] = time.monotonic,
) -> BatchComparisonResult:
    start = monotonic_clock()
    completed: list[IdentifierComparison] = []
    attempted = 0
    projected = 0
    memory = 128
    termination = "COMPLETED"
    continuation: int | None = None
    for index, (left, right, mode) in enumerate(pairs):
        if cancelled():
            termination, continuation = "CANCELLED", index
            break
        if monotonic_clock() - start >= policy.max_wall_clock_seconds:
            termination, continuation = "WALL_CLOCK_LIMIT_REACHED", index
            break
        if len(completed) >= policy.max_comparisons:
            termination, continuation = "COMPARISON_LIMIT_REACHED", index
            break
        attempted += 1
        pair_bytes = _observation_size(left) + _observation_size(right)
        next_projected = projected + pair_bytes
        next_memory = memory + pair_bytes + 256
        if next_projected > policy.max_projected_bytes:
            termination, continuation = "BYTE_LIMIT_REACHED", index
            break
        if next_memory > policy.max_memory_estimate_bytes:
            termination, continuation = "MEMORY_ESTIMATE_LIMIT_REACHED", index
            break
        completed.append(compare_identifiers(left, right, mode))
        projected, memory = next_projected, next_memory
    return BatchComparisonResult(
        tuple(completed),
        attempted,
        termination,
        projected,
        memory,
        continuation,
    )


def compare_against_bounded_set(
    subject: IdentifierObservation,
    candidates: Iterable[IdentifierObservation],
    mode: ComparisonMode,
    policy: BatchResourcePolicy,
    *,
    cancelled: Callable[[], bool] = lambda: False,
    monotonic_clock: Callable[[], float] = time.monotonic,
) -> BatchComparisonResult:
    """Compare one subject to caller-supplied candidates; never creates all-pairs work."""

    explicit_pairs = ((subject, candidate, mode) for candidate in candidates)
    return compare_explicit_pairs(
        explicit_pairs,
        policy,
        cancelled=cancelled,
        monotonic_clock=monotonic_clock,
    )
