"""Candidate Manifest.db schema-only infrastructure."""

from app.manifest.schema_profile import (
    CompatibilityOutcome,
    MANIFEST_SCHEMA_PROFILE,
    validate_controlled_manifest_schema,
)

__all__ = (
    "CompatibilityOutcome",
    "MANIFEST_SCHEMA_PROFILE",
    "validate_controlled_manifest_schema",
)
