"""Closed artifact lifecycle and processing-result vocabularies."""

from enum import Enum


class ArtifactLifecycleStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    IN_DEVELOPMENT = "IN_DEVELOPMENT"
    VALIDATION_PENDING = "VALIDATION_PENDING"
    DEPRECATED = "DEPRECATED"


class ProcessingResultStatus(str, Enum):
    SUPPORTED_COMPLETE = "SUPPORTED_COMPLETE"
    SUPPORTED_NO_RECORDS = "SUPPORTED_NO_RECORDS"
    UNSUPPORTED = "UNSUPPORTED"
    INACCESSIBLE = "INACCESSIBLE"
    CORRUPTED = "CORRUPTED"
    FAILED = "FAILED"
    EXCLUDED = "EXCLUDED"


SUPPORTED_SUCCESS_STATUSES = frozenset(
    {
        ProcessingResultStatus.SUPPORTED_COMPLETE,
        ProcessingResultStatus.SUPPORTED_NO_RECORDS,
    }
)
