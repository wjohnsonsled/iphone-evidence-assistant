"""Event normalization logic."""

from evidence_engine._legacy import (
    build_coverage_lookup,
    coverage_status_for_event,
    normalize_event,
    normalized_category_and_type,
    normalized_event_id,
    source_database_from_event,
)

__all__ = [
    "build_coverage_lookup",
    "coverage_status_for_event",
    "normalize_event",
    "normalized_category_and_type",
    "normalized_event_id",
    "source_database_from_event",
]
