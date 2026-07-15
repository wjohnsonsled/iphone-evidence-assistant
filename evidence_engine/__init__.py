"""Reusable forensic evidence engine package.

The package exposes the former ``window_investigator.py`` implementation as
testable modules while preserving the original command-line behavior.
"""

from evidence_engine.models import (
    AppCoverageRecord,
    CaseContext,
    CoverageRecord,
    Event,
    NormalizedEvent,
    Relationship,
)

__all__ = [
    "AppCoverageRecord",
    "CaseContext",
    "CoverageRecord",
    "Event",
    "NormalizedEvent",
    "Relationship",
]
