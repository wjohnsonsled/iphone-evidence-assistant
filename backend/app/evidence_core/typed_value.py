"""Lossless typed-value envelopes with separate derived normalization."""

from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

_KEY = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")


class ValueState(str, Enum):
    VALUE = "VALUE"
    NULL = "NULL"
    MISSING = "MISSING"
    EMPTY = "EMPTY"
    FALSE = "FALSE"
    ZERO = "ZERO"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"
    UNREPRESENTABLE = "UNREPRESENTABLE"


@dataclass(frozen=True, slots=True)
class TypedRepresentation:
    representation_id: UUID
    state: ValueState
    type_id: str
    serialization_profile_id: str
    serialization_profile_version: str
    serialized_value: str | None
    failure_code: str | None = None

    def __post_init__(self) -> None:
        if self.representation_id.version != 4:
            raise ValueError("representation_id_invalid")
        if not _KEY.fullmatch(self.type_id) or not _KEY.fullmatch(self.serialization_profile_id):
            raise ValueError("representation_type_or_profile_invalid")
        if not self.serialization_profile_version.strip():
            raise ValueError("serialization_profile_version_invalid")
        no_value = {ValueState.NULL, ValueState.MISSING, ValueState.UNKNOWN, ValueState.UNSUPPORTED, ValueState.UNREPRESENTABLE}
        if self.state in no_value and self.serialized_value is not None:
            raise ValueError("semantic_state_must_not_contain_value")
        if self.state not in no_value and self.serialized_value is None:
            raise ValueError("present_state_requires_serialized_value")
        failed = self.state in {ValueState.UNSUPPORTED, ValueState.UNREPRESENTABLE}
        if failed != (self.failure_code is not None):
            raise ValueError("explicit_failure_code_required_only_for_failed_state")


@dataclass(frozen=True, slots=True)
class ValueTransformation:
    transformation_id: UUID
    method_id: str
    method_version: str
    processing_run_id: UUID
    parser_identity_id: UUID | None
    transformed_at: datetime
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.transformation_id.version != 4 or not _KEY.fullmatch(self.method_id):
            raise ValueError("transformation_identity_invalid")
        if not self.method_version.strip():
            raise ValueError("transformation_version_invalid")
        if self.transformed_at.tzinfo is None or self.transformed_at.utcoffset() is None:
            raise ValueError("transformation_time_invalid")
        if not self.limitations or any(not item.strip() for item in self.limitations):
            raise ValueError("transformation_limitations_required")


@dataclass(frozen=True, slots=True)
class TypedValueObservation:
    observation_id: UUID
    source_artifact_id: UUID
    processing_run_id: UUID
    parser_identity_id: UUID | None
    observed_at: datetime
    raw: TypedRepresentation
    normalized: TypedRepresentation | None = None
    transformation: ValueTransformation | None = None

    def __post_init__(self) -> None:
        if self.observation_id.version != 4:
            raise ValueError("observation_id_invalid")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observation_time_invalid")
        if (self.normalized is None) != (self.transformation is None):
            raise ValueError("normalized_value_requires_complete_transformation")
        if self.transformation and self.transformation.processing_run_id != self.processing_run_id:
            raise ValueError("transformation_run_mismatch")
        if self.transformation and self.transformation.parser_identity_id != self.parser_identity_id:
            raise ValueError("transformation_parser_mismatch")
        if self.normalized and self.normalized.representation_id == self.raw.representation_id:
            raise ValueError("raw_and_normalized_must_be_independently_addressable")


def representation(**values: object) -> TypedRepresentation:
    return TypedRepresentation(representation_id=uuid4(), **values)  # type: ignore[arg-type]


def observe_typed_value(**values: object) -> TypedValueObservation:
    return TypedValueObservation(observation_id=uuid4(), **values)  # type: ignore[arg-type]
