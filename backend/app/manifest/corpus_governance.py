"""Pure validation for the candidate synthetic Manifest characterization corpus."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

GOVERNANCE_PROFILE_ID = "synthetic-characterization-corpus-governance"
GOVERNANCE_PROFILE_VERSION = "1"
CORPUS_ID = "manifest-synthetic-characterization-corpus"
CORPUS_VERSION = "1"
GENERATOR_ID = "dev-0610-manifest-synthetic-corpus-generator"
GENERATOR_VERSION = "1"
STATUS = "SYNTHETIC_CHARACTERIZED"
APPLE_STATUS = "APPLE_PRODUCED_NOT_STARTED"
COMPATIBILITY_STATUS = "COMPATIBILITY_NOT_EVALUATED"
SUPPORT_STATUS = "SUPPORT_NOT_EVALUATED"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

LIMITATIONS = (
    "Synthetic characterization is not Apple-produced validation.",
    "Synthetic characterization is not compatibility or support validation.",
    "Fixture SHA-256 values protect test assets and are not evidence hashes.",
    "No Apple, parser, artifact, input, workflow, production, or Supported claim is established.",
)


class ProvenanceState(str, Enum):
    GENERATED_DETERMINISTICALLY = "GENERATED_DETERMINISTICALLY"
    GENERATED_MANUALLY_SYNTHETIC = "GENERATED_MANUALLY_SYNTHETIC"
    DERIVED_FROM_APPROVED_SYNTHETIC_FIXTURE = "DERIVED_FROM_APPROVED_SYNTHETIC_FIXTURE"
    REGENERATED_FROM_APPROVED_GENERATOR = "REGENERATED_FROM_APPROVED_GENERATOR"
    PROVENANCE_INCOMPLETE = "PROVENANCE_INCOMPLETE"
    PROVENANCE_DISALLOWED = "PROVENANCE_DISALLOWED"
    PROVENANCE_INDETERMINATE = "PROVENANCE_INDETERMINATE"


class DistributionClass(str, Enum):
    ORIGINAL_PROJECT_SYNTHETIC = "ORIGINAL_PROJECT_SYNTHETIC"
    OPEN_SPECIFICATION_DERIVED_SYNTHETIC = "OPEN_SPECIFICATION_DERIVED_SYNTHETIC"
    APPROVED_LICENSED_SYNTHETIC = "APPROVED_LICENSED_SYNTHETIC"
    INTERNAL_NON_DISTRIBUTABLE_SYNTHETIC = "INTERNAL_NON_DISTRIBUTABLE_SYNTHETIC"
    DISTRIBUTION_UNVERIFIED = "DISTRIBUTION_UNVERIFIED"
    DISTRIBUTION_PROHIBITED = "DISTRIBUTION_PROHIBITED"


ACCEPTED_PROVENANCE = frozenset(
    {
        ProvenanceState.GENERATED_DETERMINISTICALLY.value,
        ProvenanceState.GENERATED_MANUALLY_SYNTHETIC.value,
        ProvenanceState.DERIVED_FROM_APPROVED_SYNTHETIC_FIXTURE.value,
        ProvenanceState.REGENERATED_FROM_APPROVED_GENERATOR.value,
    }
)
COMMITTABLE_DISTRIBUTION = frozenset(
    {
        DistributionClass.ORIGINAL_PROJECT_SYNTHETIC.value,
        DistributionClass.OPEN_SPECIFICATION_DERIVED_SYNTHETIC.value,
        DistributionClass.APPROVED_LICENSED_SYNTHETIC.value,
    }
)
PROHIBITED_SOURCE_CLASSES = frozenset(
    {
        "REAL_APPLE_BACKUP",
        "SANITIZED_REAL_BACKUP",
        "CUSTOMER_EVIDENCE",
        "DEVICE_DATA",
        "PUBLIC_PERSONAL_DATA",
        "UNCERTAIN_PROVENANCE",
        "VENDOR_SAMPLE_UNVERIFIED",
    }
)

REQUIRED_FIXTURE_FIELDS = frozenset(
    {
        "fixture_id",
        "corpus_id",
        "fixture_version",
        "resource_id",
        "fixture_type",
        "purpose",
        "generating_task",
        "generating_decision",
        "generation_method",
        "generator_id",
        "generator_version",
        "generation_parameters",
        "source_classification",
        "provenance_state",
        "lawful_distribution",
        "custody_state",
        "schema_identity",
        "schema_fingerprint",
        "profile_coverage",
        "expected_outcome",
        "test_classification",
        "validity_classification",
        "resource_scenario",
        "profile_version_scenario",
        "sha256",
        "limitation_ids",
        "date_created",
        "date_last_regenerated",
        "supersession_status",
        "manually_edited",
        "contains_external_material",
        "non_evidentiary",
        "payload",
    }
)
REQUIRED_MATRIX_FIELDS = frozenset(
    {
        "profile_id",
        "profile_version",
        "compatible_synthetic_schema",
        "positive_fixtures",
        "negative_fixtures",
        "malformed_fixtures",
        "unsupported_fixtures",
        "boundary_fixtures",
        "resource_limit_fixtures",
        "profile_compatibility_fixtures",
        "deterministic_rerun_fixtures",
        "expected_outcome_coverage",
        "missing_coverage",
    }
)
REQUIRED_CUSTODY_EVENTS = (
    "CREATED",
    "GENERATOR_EXECUTED",
    "INITIAL_DIGEST_RECORDED",
    "REPOSITORY_ADDITION",
    "REVIEWED",
    "APPROVED",
)


@dataclass(frozen=True, slots=True)
class CorpusValidationResult:
    valid: bool
    reason_codes: tuple[str, ...]
    fixture_count: int
    verified_fixture_count: int
    calculated_manifest_sha256: str | None


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_canonical(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def manifest_digest(package: Mapping[str, object]) -> str:
    material = dict(package)
    material.pop("corpus_manifest_sha256", None)
    return sha256_canonical(material)


def validate_corpus(package: Mapping[str, object]) -> CorpusValidationResult:
    """Validate untrusted manifest data without filesystem or code execution."""

    reasons: list[str] = []
    if package.get("governance_profile_id") != GOVERNANCE_PROFILE_ID:
        reasons.append("governance_profile_unknown")
    if package.get("governance_profile_version") != GOVERNANCE_PROFILE_VERSION:
        reasons.append("governance_profile_version_incompatible")
    if (package.get("corpus_id"), package.get("corpus_version")) != (
        CORPUS_ID,
        CORPUS_VERSION,
    ):
        reasons.append("corpus_identity_invalid")
    if package.get("generator_id") != GENERATOR_ID:
        reasons.append("generator_unknown")
    if package.get("generator_version") != GENERATOR_VERSION:
        reasons.append("generator_version_incompatible")
    if package.get("status") != STATUS:
        reasons.append("synthetic_status_invalid")
    if package.get("apple_produced_status") != APPLE_STATUS:
        reasons.append("apple_status_invalid")
    if package.get("compatibility_status") != COMPATIBILITY_STATUS:
        reasons.append("compatibility_status_invalid")
    if package.get("support_status") != SUPPORT_STATUS:
        reasons.append("support_status_invalid")

    fixtures = package.get("fixtures")
    if not isinstance(fixtures, list):
        fixtures = []
        reasons.append("fixtures_invalid")
    registered = package.get("registered_resources")
    if not isinstance(registered, list):
        registered = []
        reasons.append("registered_resources_invalid")
    ids: list[str] = []
    resources: list[str] = []
    verified = 0
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            reasons.append("fixture_invalid")
            continue
        missing = REQUIRED_FIXTURE_FIELDS.difference(fixture)
        if missing:
            reasons.append("fixture_provenance_incomplete")
            continue
        fixture_id = fixture["fixture_id"]
        resource_id = fixture["resource_id"]
        if not isinstance(fixture_id, str) or not isinstance(resource_id, str):
            reasons.append("fixture_identity_invalid")
            continue
        ids.append(fixture_id)
        resources.append(resource_id)
        if fixture["corpus_id"] != CORPUS_ID:
            reasons.append("fixture_corpus_mismatch")
        if fixture["source_classification"] in PROHIBITED_SOURCE_CLASSES:
            reasons.append("fixture_source_prohibited")
        if fixture["source_classification"] != "PROJECT_ORIGINAL_SYNTHETIC":
            reasons.append("fixture_source_not_authorized")
        if fixture["provenance_state"] not in ACCEPTED_PROVENANCE:
            reasons.append("fixture_provenance_unacceptable")
        if fixture["lawful_distribution"] not in COMMITTABLE_DISTRIBUTION:
            reasons.append("fixture_distribution_unacceptable")
        if fixture["custody_state"] != "APPROVED_VERSION_CONTROLLED_TEST_ASSET":
            reasons.append("fixture_custody_incomplete")
        if fixture["contains_external_material"] is not False:
            reasons.append("fixture_external_material_present")
        if fixture["non_evidentiary"] is not True:
            reasons.append("fixture_not_marked_non_evidentiary")
        digest = fixture["sha256"]
        if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
            reasons.append("fixture_digest_invalid")
        elif digest != sha256_canonical(fixture["payload"]):
            reasons.append("fixture_integrity_mismatch")
        else:
            verified += 1

    if len(ids) != len(set(ids)):
        reasons.append("duplicate_fixture_id")
    if len(resources) != len(set(resources)):
        reasons.append("duplicate_resource_id")
    if set(registered) - set(resources):
        reasons.append("registered_fixture_missing")
    if set(resources) - set(registered):
        reasons.append("fixture_unregistered")
    if len(registered) != len(set(registered)):
        reasons.append("duplicate_registered_resource")

    custody = package.get("custody_events")
    if not isinstance(custody, list):
        reasons.append("custody_invalid")
    else:
        sequence = tuple(event.get("sequence") for event in custody if isinstance(event, dict))
        events = tuple(event.get("event") for event in custody if isinstance(event, dict))
        if sequence != tuple(range(1, len(custody) + 1)) or events != REQUIRED_CUSTODY_EVENTS:
            reasons.append("custody_incomplete")

    profiles = package.get("profile_matrix")
    if not isinstance(profiles, list) or not profiles:
        reasons.append("profile_matrix_missing")
    else:
        for profile in profiles:
            if (
                not isinstance(profile, dict)
                or REQUIRED_MATRIX_FIELDS.difference(profile)
                or profile.get("missing_coverage")
            ):
                reasons.append("profile_matrix_incomplete")
                break
            fixture_references = {
                reference
                for key, value in profile.items()
                if key.endswith("_fixtures") and isinstance(value, list)
                for reference in value
            }
            if not fixture_references.issubset(set(ids)):
                reasons.append("profile_matrix_fixture_unregistered")
                break

    recorded = package.get("corpus_manifest_sha256")
    calculated = manifest_digest(package)
    if not isinstance(recorded, str) or not SHA256_PATTERN.fullmatch(recorded):
        reasons.append("corpus_manifest_digest_invalid")
    elif recorded != calculated:
        reasons.append("corpus_manifest_mismatch")

    canonical_reasons = tuple(sorted(set(reasons)))
    return CorpusValidationResult(
        not canonical_reasons,
        canonical_reasons,
        len(fixtures),
        verified,
        calculated,
    )
