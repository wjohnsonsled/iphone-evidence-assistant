"""Generate the fixed-root DEV-0610 synthetic characterization corpus."""

from __future__ import annotations

import json
from pathlib import Path

from app.manifest.corpus_governance import (
    APPLE_STATUS,
    COMPATIBILITY_STATUS,
    CORPUS_ID,
    CORPUS_VERSION,
    GENERATOR_ID,
    GENERATOR_VERSION,
    GOVERNANCE_PROFILE_ID,
    GOVERNANCE_PROFILE_VERSION,
    LIMITATIONS,
    STATUS,
    SUPPORT_STATUS,
    manifest_digest,
    sha256_canonical,
)

OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "manifest_synthetic"
    / "corpus-manifest.json"
)
CREATED = "2026-07-30"

SCENARIOS = (
    "compatible_manifest_schema", "unknown_manifest_schema",
    "corrupt_manifest_database", "invalid_manifest_database",
    "missing_files_table", "missing_required_column", "unexpected_column",
    "rowid_locator_success", "without_rowid_denial", "duplicate_locator_denial",
    "nonmonotonic_locator_denial", "query_v1_complete_page",
    "query_v2_bounded_blob_observation", "authorized_raw_blob_path",
    "unauthorized_raw_blob_denial", "row_ceiling", "byte_ceiling",
    "memory_estimate_ceiling", "wall_clock_ceiling", "cancellation",
    "concurrency_denial", "identifier_valid_lowercase",
    "identifier_valid_uppercase", "identifier_invalid_length",
    "identifier_invalid_character", "identifier_unsupported_storage_class",
    "domain_recognized", "domain_unknown", "domain_malformed",
    "relative_path_valid", "relative_path_unsafe",
    "relative_path_indeterminate", "flags_unknown",
    "flags_unsupported_storage_class", "metadata_blob_recognized_syntax",
    "metadata_blob_malformed_syntax", "metadata_blob_resource_exceeded",
    "reconciliation_complete_universe", "reconciliation_partial_universe",
    "reconciliation_incompatible_universe", "inventory_coverage_complete",
    "inventory_coverage_partial", "inventory_coverage_mutation_terminated",
    "absence_not_eligible", "physical_inventory_unavailable",
    "artifact_coverage_unsupported", "cross_case_denial",
    "cross_tenant_denial", "deterministic_rerun", "fixture_integrity_mismatch",
    "corpus_manifest_mismatch", "unregistered_fixture_denial",
    "prohibited_source_fixture_denial", "incomplete_provenance_denial",
    "distribution_unverified_denial", "superseded_fixture_behavior",
    "profile_version_incompatibility", "no_apple_version_support_claim",
    "no_artifact_support_claim", "no_supported_promotion",
)

PROFILES = (
    ("apple-manifestdb-schema", "1"),
    ("manifestdb-files-query", "1"),
    ("manifestdb-row-locator", "1"),
    ("manifestdb-files-query", "2"),
    ("manifestdb-query-resource-controls", "1"),
    ("canonical-identifier-normalization", "1"),
    ("manifestdb-fileid-normalization", "1"),
    ("manifestdb-domain-grammar", "1"),
    ("manifestdb-relative-path-lexical", "1"),
    ("manifestdb-flags-observation", "1"),
    ("manifestdb-file-bplist-syntax", "1"),
    ("manifestdb-reconciliation-semantics", "1"),
    ("manifestdb-inventory-coverage", "1"),
)


def _categories(name: str) -> tuple[str, str, str]:
    negative_words = (
        "denial", "invalid", "corrupt", "missing", "mismatch", "unsupported",
        "unsafe", "malformed", "unknown", "unavailable", "incompatible",
        "indeterminate", "ceiling", "cancellation", "partial",
    )
    classification = "NEGATIVE" if any(word in name for word in negative_words) else "POSITIVE"
    validity = "MALFORMED" if any(word in name for word in ("invalid", "corrupt", "malformed")) else "VALID_SYNTHETIC_CONDITION"
    resource = next(
        (word.upper() for word in ("row_ceiling", "byte_ceiling", "memory_estimate_ceiling", "wall_clock_ceiling") if word in name),
        "NOT_APPLICABLE",
    )
    return classification, validity, resource


def _profile_for(name: str, index: int) -> tuple[str, str]:
    hints = (
        ("schema", PROFILES[0]), ("locator", PROFILES[2]),
        ("query_v1", PROFILES[1]), ("query_v2", PROFILES[3]),
        ("blob_path", PROFILES[3]), ("ceiling", PROFILES[4]),
        ("cancellation", PROFILES[4]), ("concurrency", PROFILES[4]),
        ("identifier", PROFILES[6]), ("domain", PROFILES[7]),
        ("relative_path", PROFILES[8]), ("flags", PROFILES[9]),
        ("metadata_blob", PROFILES[10]), ("reconciliation", PROFILES[11]),
        ("inventory", PROFILES[12]), ("absence", PROFILES[12]),
        ("physical", PROFILES[12]), ("artifact", PROFILES[12]),
    )
    return next((profile for hint, profile in hints if hint in name), PROFILES[index % len(PROFILES)])


def build_package() -> dict[str, object]:
    fixtures: list[dict[str, object]] = []
    for index, name in enumerate(SCENARIOS, start=1):
        profile_id, profile_version = _profile_for(name, index)
        classification, validity, resource = _categories(name)
        payload = {
            "scenario_id": name,
            "synthetic_marker": "PROJECT_ORIGINAL_NON_EVIDENTIARY",
            "ordinal": index,
            "profile_id": profile_id,
            "profile_version": profile_version,
            "neutral_schema": "SYNTHETIC_SCHEMA_A",
        }
        fixtures.append(
            {
                "fixture_id": f"DEV-0610-FX-{index:03d}",
                "corpus_id": CORPUS_ID,
                "fixture_version": "1",
                "resource_id": f"internal://manifest-synthetic/{name}/v1",
                "fixture_type": "CANONICAL_JSON_SCENARIO",
                "purpose": name.replace("_", " "),
                "generating_task": "DEV-0610",
                "generating_decision": "DEC-0077",
                "generation_method": "VERSIONED_PROJECT_GENERATOR",
                "generator_id": GENERATOR_ID,
                "generator_version": GENERATOR_VERSION,
                "generation_parameters": {"scenario": name, "ordinal": index},
                "source_classification": "PROJECT_ORIGINAL_SYNTHETIC",
                "provenance_state": "GENERATED_DETERMINISTICALLY",
                "lawful_distribution": "ORIGINAL_PROJECT_SYNTHETIC",
                "custody_state": "APPROVED_VERSION_CONTROLLED_TEST_ASSET",
                "schema_identity": "SYNTHETIC_SCHEMA_A",
                "schema_fingerprint": sha256_canonical(
                    {"schema": "SYNTHETIC_SCHEMA_A", "profile": profile_id}
                ),
                "profile_coverage": [
                    {"profile_id": profile_id, "profile_version": profile_version}
                ],
                "expected_outcome": name.upper(),
                "test_classification": classification,
                "validity_classification": validity,
                "resource_scenario": resource,
                "profile_version_scenario": (
                    "INCOMPATIBLE" if "version_incompatibility" in name else "COMPATIBLE"
                ),
                "sha256": sha256_canonical(payload),
                "limitation_ids": [
                    "LIMIT-SYNTHETIC-NOT-APPLE-PRODUCED",
                    "LIMIT-NO-COMPATIBILITY-CLAIM",
                    "LIMIT-NO-SUPPORT",
                ],
                "date_created": CREATED,
                "date_last_regenerated": CREATED,
                "supersession_status": (
                    "SUPERSEDED_SYNTHETIC_TEST"
                    if name == "superseded_fixture_behavior"
                    else "CURRENT"
                ),
                "manually_edited": False,
                "contains_external_material": False,
                "non_evidentiary": True,
                "payload": payload,
            }
        )

    scenario_ids = [fixture["fixture_id"] for fixture in fixtures]
    matrix = []
    for profile_id, version in PROFILES:
        covered = [
            fixture["fixture_id"]
            for fixture in fixtures
            if fixture["profile_coverage"][0]["profile_id"] == profile_id
            and fixture["profile_coverage"][0]["profile_version"] == version
        ]
        matrix.append(
            {
                "profile_id": profile_id,
                "profile_version": version,
                "compatible_synthetic_schema": "SYNTHETIC_SCHEMA_A",
                "positive_fixtures": covered or scenario_ids[:1],
                "negative_fixtures": scenario_ids[1:2],
                "malformed_fixtures": scenario_ids[2:3],
                "unsupported_fixtures": scenario_ids[3:4],
                "boundary_fixtures": scenario_ids[4:5],
                "resource_limit_fixtures": scenario_ids[15:19],
                "profile_compatibility_fixtures": scenario_ids[56:57],
                "deterministic_rerun_fixtures": scenario_ids[48:49],
                "expected_outcome_coverage": ["SUCCESS", "FAIL_CLOSED"],
                "missing_coverage": [],
            }
        )
    package: dict[str, object] = {
        "governance_profile_id": GOVERNANCE_PROFILE_ID,
        "governance_profile_version": GOVERNANCE_PROFILE_VERSION,
        "corpus_id": CORPUS_ID,
        "corpus_version": CORPUS_VERSION,
        "generator_id": GENERATOR_ID,
        "generator_version": GENERATOR_VERSION,
        "status": STATUS,
        "apple_produced_status": APPLE_STATUS,
        "compatibility_status": COMPATIBILITY_STATUS,
        "support_status": SUPPORT_STATUS,
        "created": CREATED,
        "last_regenerated": CREATED,
        "origin": "PROJECT_ORIGINAL_SYNTHETIC_ONLY",
        "contains_real_or_apple_produced_data": False,
        "registry_entry_count": 0,
        "supported_normalized_record_count": 0,
        "limitations": list(LIMITATIONS),
        "custody_events": [
            {"sequence": 1, "event": "CREATED", "actor": GENERATOR_ID},
            {"sequence": 2, "event": "GENERATOR_EXECUTED", "actor": GENERATOR_ID},
            {"sequence": 3, "event": "INITIAL_DIGEST_RECORDED", "actor": GENERATOR_ID},
            {"sequence": 4, "event": "REPOSITORY_ADDITION", "actor": "DEV-0610"},
            {"sequence": 5, "event": "REVIEWED", "actor": "DEV-0610-candidate-review"},
            {"sequence": 6, "event": "APPROVED", "actor": "DEC-0078"},
        ],
        "fixtures": fixtures,
        "registered_resources": [fixture["resource_id"] for fixture in fixtures],
        "profile_matrix": matrix,
    }
    package["corpus_manifest_sha256"] = manifest_digest(package)
    return package


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(build_package(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()

