"""Entity normalization and linking logic."""

from evidence_engine._legacy import (
    add_entity_link,
    link_entities_for_normalized_event,
    normalize_domain_entity,
    normalize_email_entity,
    normalize_file_entity,
    normalize_phone_entity,
)

__all__ = [
    "add_entity_link",
    "link_entities_for_normalized_event",
    "normalize_domain_entity",
    "normalize_email_entity",
    "normalize_file_entity",
    "normalize_phone_entity",
]
