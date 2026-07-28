"""Candidate supported-evidence core contracts; no capability is Supported."""

from app.evidence_core.processing_run import (
    ProcessingRun,
    ProcessingRunService,
)
from app.evidence_core.source_artifact import SourceArtifact, SourceArtifactService
from app.evidence_core.source_locator import SourceLocator, create_source_locator
from app.evidence_core.parser_identity import ParserIdentity, register_candidate_parser_identity

__all__ = [
    "ProcessingRun", "ProcessingRunService", "SourceArtifact",
    "SourceArtifactService", "SourceLocator", "create_source_locator",
    "ParserIdentity", "register_candidate_parser_identity",
]
