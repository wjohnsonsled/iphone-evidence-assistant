"""Candidate supported-evidence core contracts; no capability is Supported."""

from app.evidence_core.processing_run import (
    ProcessingRun,
    ProcessingRunService,
)
from app.evidence_core.source_artifact import SourceArtifact, SourceArtifactService
from app.evidence_core.source_locator import SourceLocator, create_source_locator
from app.evidence_core.parser_identity import ParserIdentity, register_candidate_parser_identity
from app.evidence_core.schema_fingerprint import SchemaFingerprintObservation, record_schema_fingerprint
from app.evidence_core.typed_value import (
    TypedRepresentation, TypedValueObservation, ValueState,
    ValueTransformation, observe_typed_value, representation,
)
from app.evidence_core.timestamp_provenance import (
    ConversionStatus, InterpretationStatus, LocalTimeStatus, NumericEpochMetadata,
    TimestampCategory, TimestampConversion, TimestampObservation,
    TimestampPrecision, TimezoneContext, TimezoneSource, observe_timestamp,
)
from app.evidence_core.processing_coverage import (
    AuthorizationState, CountObservation, CountStatus, CoverageStatus,
    ExecutionState, OmissionCategory, OmissionObservation,
    ProcessingCoverageObservation, ReconciliationStatus,
    ResourceLimitObservation, count, observe_coverage,
)
from app.evidence_core.processing_issue import (
    IssueCategory, IssueSeverity, PartialProcessingObservation, ProcessingIssue,
    Recoverability, record_issue, record_partial_processing,
)
from app.evidence_core.supported_store import (
    AdmissionAuthorization, AdmissionDecision, AdmissionDenied,
    AdmissionOutcome, OutputDisposition, SupportedEvidenceStore,
    SupportedNormalizedRecord, SupportedRecordCandidate,
)

__all__ = [
    "ProcessingRun", "ProcessingRunService", "SourceArtifact",
    "SourceArtifactService", "SourceLocator", "create_source_locator",
    "ParserIdentity", "register_candidate_parser_identity",
    "SchemaFingerprintObservation", "record_schema_fingerprint",
    "TypedRepresentation", "TypedValueObservation", "ValueState",
    "ValueTransformation", "observe_typed_value", "representation",
    "ConversionStatus", "InterpretationStatus", "LocalTimeStatus",
    "NumericEpochMetadata", "TimestampCategory", "TimestampConversion",
    "TimestampObservation", "TimestampPrecision", "TimezoneContext",
    "TimezoneSource", "observe_timestamp",
    "AuthorizationState", "CountObservation", "CountStatus", "CoverageStatus",
    "ExecutionState", "OmissionCategory", "OmissionObservation",
    "ProcessingCoverageObservation", "ReconciliationStatus",
    "ResourceLimitObservation", "count", "observe_coverage",
    "IssueCategory", "IssueSeverity", "PartialProcessingObservation",
    "ProcessingIssue", "Recoverability", "record_issue",
    "record_partial_processing",
    "AdmissionAuthorization", "AdmissionDecision", "AdmissionDenied",
    "AdmissionOutcome", "OutputDisposition", "SupportedEvidenceStore",
    "SupportedNormalizedRecord", "SupportedRecordCandidate",
]
