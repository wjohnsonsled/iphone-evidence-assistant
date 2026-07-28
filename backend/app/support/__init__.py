"""Supported-path registry boundary; the production registry is empty."""

from app.support.domain import (
    ArtifactLifecycleStatus,
    ProcessingResultStatus,
)
from app.support.registry import (
    ApprovedParserEntry,
    CurrentSupportStatus,
    OutputAdmission,
    ParserAuthorization,
    ParserDisposition,
    ParserQuarantinedError,
    SupportedOutputGate,
    SupportedParserRegistry,
    create_supported_registry,
)

__all__ = [
    "ApprovedParserEntry",
    "CurrentSupportStatus",
    "ArtifactLifecycleStatus",
    "OutputAdmission",
    "ParserAuthorization",
    "ParserDisposition",
    "ParserQuarantinedError",
    "ProcessingResultStatus",
    "SupportedOutputGate",
    "SupportedParserRegistry",
    "create_supported_registry",
]
