"""Correlation, activity scoring, and relationship analysis."""

from evidence_engine._legacy import (
    build_correlation_clusters,
    build_entity_correlations,
    build_scored_buckets,
    correlation_event_score,
    derive_relationships_from_normalized_events,
    domain_from_url,
    event_contact,
    event_weight,
    extract_entities,
    is_attachment,
    is_communication,
    relationship_edges,
)

__all__ = [
    "build_correlation_clusters",
    "build_entity_correlations",
    "build_scored_buckets",
    "correlation_event_score",
    "derive_relationships_from_normalized_events",
    "domain_from_url",
    "event_contact",
    "event_weight",
    "extract_entities",
    "is_attachment",
    "is_communication",
    "relationship_edges",
]
