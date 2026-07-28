"""Timestamp provenance envelopes; no timestamp interpretation algorithms."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from app.evidence_core.typed_value import TypedRepresentation

class TimestampCategory(str, Enum):
    ABSOLUTE_INSTANT="ABSOLUTE_INSTANT"; OFFSET_DATE_TIME="OFFSET_DATE_TIME"; ZONED_DATE_TIME="ZONED_DATE_TIME"
    LOCAL_DATE_TIME="LOCAL_DATE_TIME"; DATE_ONLY="DATE_ONLY"; TIME_ONLY="TIME_ONLY"
    NUMERIC_EPOCH_VALUE="NUMERIC_EPOCH_VALUE"; UNKNOWN_TIMESTAMP_FORM="UNKNOWN_TIMESTAMP_FORM"
    UNREPRESENTABLE_TIMESTAMP="UNREPRESENTABLE_TIMESTAMP"
class TimestampPrecision(str, Enum):
    YEAR="YEAR"; MONTH="MONTH"; DAY="DAY"; HOUR="HOUR"; MINUTE="MINUTE"; SECOND="SECOND"
    MILLISECOND="MILLISECOND"; MICROSECOND="MICROSECOND"; NANOSECOND="NANOSECOND"
    SOURCE_DEFINED="SOURCE_DEFINED"; UNKNOWN="UNKNOWN"
class TimezoneSource(str, Enum):
    EXPLICIT_OFFSET_IN_VALUE="EXPLICIT_OFFSET_IN_VALUE"; EXPLICIT_ZONE_IDENTIFIER_IN_VALUE="EXPLICIT_ZONE_IDENTIFIER_IN_VALUE"
    ARTIFACT_FIELD="ARTIFACT_FIELD"; ARTIFACT_METADATA="ARTIFACT_METADATA"; APPLICATION_CONFIGURATION="APPLICATION_CONFIGURATION"
    DEVICE_CONFIGURATION="DEVICE_CONFIGURATION"; BACKUP_METADATA="BACKUP_METADATA"; PROCESSING_CONFIGURATION="PROCESSING_CONFIGURATION"
    CASE_SUPPLIED_CONTEXT="CASE_SUPPLIED_CONTEXT"; ARTIFACT_PROFILE_RULE="ARTIFACT_PROFILE_RULE"
    INFERRED_WITH_DOCUMENTED_BASIS="INFERRED_WITH_DOCUMENTED_BASIS"; UNKNOWN="UNKNOWN"; NOT_APPLICABLE="NOT_APPLICABLE"
class InterpretationStatus(str, Enum):
    NOT_ATTEMPTED="NOT_ATTEMPTED"; INTERPRETED="INTERPRETED"; PARTIALLY_INTERPRETED="PARTIALLY_INTERPRETED"
    AMBIGUOUS="AMBIGUOUS"; INVALID="INVALID"; UNSUPPORTED="UNSUPPORTED"; UNREPRESENTABLE="UNREPRESENTABLE"
class LocalTimeStatus(str, Enum):
    UNAMBIGUOUS_LOCAL_TIME="UNAMBIGUOUS_LOCAL_TIME"; AMBIGUOUS_LOCAL_TIME="AMBIGUOUS_LOCAL_TIME"
    NONEXISTENT_LOCAL_TIME="NONEXISTENT_LOCAL_TIME"; LOCAL_TIME_STATUS_UNKNOWN="LOCAL_TIME_STATUS_UNKNOWN"; NOT_APPLICABLE="NOT_APPLICABLE"
class ConversionStatus(str, Enum):
    NOT_REQUESTED="NOT_REQUESTED"; NOT_APPLICABLE="NOT_APPLICABLE"; NOT_ATTEMPTED="NOT_ATTEMPTED"; CONVERTED="CONVERTED"
    CONVERTED_WITH_LIMITATIONS="CONVERTED_WITH_LIMITATIONS"; AMBIGUOUS_SOURCE_TIME="AMBIGUOUS_SOURCE_TIME"
    NONEXISTENT_SOURCE_TIME="NONEXISTENT_SOURCE_TIME"; MISSING_TIMEZONE_CONTEXT="MISSING_TIMEZONE_CONTEXT"
    UNSUPPORTED_SOURCE_FORMAT="UNSUPPORTED_SOURCE_FORMAT"; INVALID_SOURCE_VALUE="INVALID_SOURCE_VALUE"; OUT_OF_RANGE="OUT_OF_RANGE"
    PRECISION_LOSS_PROHIBITED="PRECISION_LOSS_PROHIBITED"; CONVERSION_FAILED="CONVERSION_FAILED"

@dataclass(frozen=True, slots=True)
class TimezoneContext:
    source: TimezoneSource
    utc_offset: str | None = None
    zone_identifier: str | None = None
    ruleset_id: str | None = None
    ruleset_version: str | None = None
    derived: bool = False
    inference_method_id: str | None = None
    inference_method_version: str | None = None
    basis_reference: str | None = None
    processing_run_id: UUID | None = None
    limitations: tuple[str, ...] = ()
    def __post_init__(self):
        if self.source is TimezoneSource.INFERRED_WITH_DOCUMENTED_BASIS and not all((self.inference_method_id,self.inference_method_version,self.basis_reference,self.processing_run_id,self.limitations)):
            raise ValueError("inferred_timezone_requires_complete_basis")
        if self.source is TimezoneSource.NOT_APPLICABLE and any((self.utc_offset,self.zone_identifier,self.ruleset_id,self.ruleset_version)):
            raise ValueError("not_applicable_timezone_contains_value")

@dataclass(frozen=True, slots=True)
class NumericEpochMetadata:
    original_numeric_value: str; serialization_profile: str; epoch_id: str; unit_id: str
    signedness: str | None; scale: str | None; interpretation_method_id: str
    interpretation_method_version: str; limitations: tuple[str, ...]
    def __post_init__(self):
        if not all((self.original_numeric_value,self.serialization_profile,self.epoch_id,self.unit_id,self.interpretation_method_id,self.interpretation_method_version,self.limitations)):
            raise ValueError("numeric_epoch_metadata_incomplete")

@dataclass(frozen=True, slots=True)
class TimestampObservation:
    observation_id: UUID; source_artifact_id: UUID; source_locator_id: UUID | None
    processing_run_id: UUID; parser_identity_id: UUID | None; observed_at: datetime
    raw: TypedRepresentation; category: TimestampCategory; precision: TimestampPrecision
    precision_reference: str | None; timezone: TimezoneContext
    interpretation_status: InterpretationStatus; local_time_status: LocalTimeStatus
    numeric_epoch: NumericEpochMetadata | None; limitations: tuple[str, ...]
    def __post_init__(self):
        if self.observation_id.version != 4 or self.observed_at.tzinfo is None: raise ValueError("timestamp_observation_invalid")
        if self.precision is TimestampPrecision.SOURCE_DEFINED and not self.precision_reference: raise ValueError("source_precision_reference_required")
        if (self.category is TimestampCategory.NUMERIC_EPOCH_VALUE) != (self.numeric_epoch is not None): raise ValueError("numeric_epoch_metadata_mismatch")
        if not self.limitations: raise ValueError("timestamp_limitations_required")

@dataclass(frozen=True, slots=True)
class TimestampConversion:
    conversion_id: UUID; source_observation_id: UUID; processing_run_id: UUID
    parser_identity_id: UUID | None; method_id: str; method_version: str
    converted_at: datetime; result: TypedRepresentation | None
    result_precision: TimestampPrecision | None; timezone: TimezoneContext
    status: ConversionStatus; failure_code: str | None; limitations: tuple[str, ...]
    def __post_init__(self):
        converted={ConversionStatus.CONVERTED,ConversionStatus.CONVERTED_WITH_LIMITATIONS}
        if self.conversion_id.version != 4 or self.converted_at.tzinfo is None: raise ValueError("conversion_identity_invalid")
        if (self.status in converted) != (self.result is not None and self.result_precision is not None): raise ValueError("conversion_result_status_mismatch")
        failed=self.status in {ConversionStatus.CONVERSION_FAILED,ConversionStatus.INVALID_SOURCE_VALUE,ConversionStatus.OUT_OF_RANGE,ConversionStatus.PRECISION_LOSS_PROHIBITED}
        if failed and not self.failure_code: raise ValueError("conversion_failure_code_required")
        if not self.limitations: raise ValueError("conversion_limitations_required")

def observe_timestamp(**values: object)->TimestampObservation:
    return TimestampObservation(observation_id=uuid4(),**values)  # type: ignore[arg-type]
