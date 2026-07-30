"""DEV-0610 governed synthetic Manifest corpus validation."""

from __future__ import annotations

import copy
import importlib
import inspect
import json
from pathlib import Path

import pytest

from app.manifest import (
    corpus_governance,
    domain_normalization,
    files_query,
    files_query_v2,
    flags_observation,
    identifier_normalization,
    inventory_coverage,
    metadata_blob,
    reconciliation_semantics,
    relative_path_normalization,
    schema_profile,
)
from app.manifest.corpus_governance import manifest_digest, validate_corpus

CORPUS_PATH = (
    Path(__file__).parent / "fixtures" / "manifest_synthetic" / "corpus-manifest.json"
)
GENERATOR = importlib.import_module("scripts.generate_manifest_synthetic_corpus")


def _load():
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def _redigest(package):
    package["corpus_manifest_sha256"] = manifest_digest(package)
    return package


def test_corpus_is_valid_complete_and_synthetic_only():
    package = _load()
    result = validate_corpus(package)
    assert result.valid
    assert result.fixture_count == result.verified_fixture_count == 60
    assert len(package["profile_matrix"]) == 13
    assert package["contains_real_or_apple_produced_data"] is False
    assert package["origin"] == "PROJECT_ORIGINAL_SYNTHETIC_ONLY"
    assert package["registry_entry_count"] == 0
    assert package["supported_normalized_record_count"] == 0


@pytest.mark.parametrize("fixture_index", range(60))
def test_every_fixture_has_complete_governed_provenance(fixture_index):
    fixture = _load()["fixtures"][fixture_index]
    assert corpus_governance.REQUIRED_FIXTURE_FIELDS <= fixture.keys()
    assert fixture["source_classification"] == "PROJECT_ORIGINAL_SYNTHETIC"
    assert fixture["provenance_state"] == "GENERATED_DETERMINISTICALLY"
    assert fixture["lawful_distribution"] == "ORIGINAL_PROJECT_SYNTHETIC"
    assert fixture["contains_external_material"] is False
    assert fixture["non_evidentiary"] is True
    assert fixture["manually_edited"] is False
    assert fixture["sha256"] == corpus_governance.sha256_canonical(fixture["payload"])


def test_required_sixty_scenarios_are_exact_and_unique():
    package = _load()
    observed = tuple(item["payload"]["scenario_id"] for item in package["fixtures"])
    assert observed == GENERATOR.SCENARIOS
    assert len(observed) == len(set(observed)) == 60


def test_generator_is_deterministic_and_matches_committed_bytes():
    first = GENERATOR.build_package()
    second = GENERATOR.build_package()
    assert first == second == _load()
    expected = json.dumps(first, indent=2, sort_keys=True) + "\n"
    assert CORPUS_PATH.read_text(encoding="utf-8") == expected


def test_profile_matrix_matches_approved_candidate_profile_constants():
    actual = {
        (entry["profile_id"], entry["profile_version"])
        for entry in _load()["profile_matrix"]
    }
    expected = {
        (schema_profile.PROFILE_ID, schema_profile.PROFILE_VERSION),
        (files_query.QUERY_PROFILE_ID, files_query.QUERY_PROFILE_VERSION),
        (files_query.LOCATOR_PROFILE_ID, files_query.LOCATOR_PROFILE_VERSION),
        (files_query_v2.QUERY_PROFILE_ID, files_query_v2.QUERY_PROFILE_VERSION),
        (files_query_v2.RESOURCE_PROFILE_ID, files_query_v2.RESOURCE_PROFILE_VERSION),
        (identifier_normalization.FRAMEWORK_ID, identifier_normalization.FRAMEWORK_VERSION),
        (identifier_normalization.PROFILE_ID, identifier_normalization.PROFILE_VERSION),
        (domain_normalization.PROFILE_ID, domain_normalization.PROFILE_VERSION),
        (relative_path_normalization.PROFILE_ID, relative_path_normalization.PROFILE_VERSION),
        (flags_observation.PROFILE_ID, flags_observation.PROFILE_VERSION),
        (metadata_blob.PROFILE_ID, metadata_blob.PROFILE_VERSION),
        (reconciliation_semantics.PROFILE_ID, reconciliation_semantics.PROFILE_VERSION),
        (inventory_coverage.PROFILE_ID, inventory_coverage.PROFILE_VERSION),
    }
    assert actual == expected
    assert all(not entry["missing_coverage"] for entry in _load()["profile_matrix"])


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        (lambda p: p["fixtures"][0]["payload"].update({"ordinal": 999}), "fixture_integrity_mismatch"),
        (lambda p: p.update({"corpus_manifest_sha256": "0" * 64}), "corpus_manifest_mismatch"),
        (lambda p: p["fixtures"].pop(), "registered_fixture_missing"),
        (lambda p: p["registered_resources"].pop(), "fixture_unregistered"),
        (lambda p: p["fixtures"][0].update({"source_classification": "REAL_APPLE_BACKUP"}), "fixture_source_prohibited"),
        (lambda p: p["fixtures"][0].pop("generation_method"), "fixture_provenance_incomplete"),
        (lambda p: p["fixtures"][0].update({"lawful_distribution": "DISTRIBUTION_UNVERIFIED"}), "fixture_distribution_unacceptable"),
        (lambda p: p["fixtures"][0].update({"provenance_state": "PROVENANCE_INDETERMINATE"}), "fixture_provenance_unacceptable"),
        (lambda p: p["fixtures"][0].update({"custody_state": "CREATED"}), "fixture_custody_incomplete"),
        (lambda p: p["custody_events"].pop(), "custody_incomplete"),
        (lambda p: p["profile_matrix"][0].update({"missing_coverage": ["malformed"]}), "profile_matrix_incomplete"),
        (lambda p: p.update({"generator_id": "unknown"}), "generator_unknown"),
        (lambda p: p.update({"governance_profile_version": "999"}), "governance_profile_version_incompatible"),
    ),
)
def test_fail_closed_manifest_mutations(mutation, reason):
    package = copy.deepcopy(_load())
    mutation(package)
    if reason not in {"corpus_manifest_mismatch", "fixture_integrity_mismatch"}:
        _redigest(package)
    result = validate_corpus(package)
    assert not result.valid
    assert reason in result.reason_codes


def test_superseded_fixture_remains_registered_and_auditable():
    fixture = next(
        item for item in _load()["fixtures"]
        if item["payload"]["scenario_id"] == "superseded_fixture_behavior"
    )
    assert fixture["supersession_status"] == "SUPERSEDED_SYNTHETIC_TEST"
    assert fixture["resource_id"] in _load()["registered_resources"]


def test_generator_has_no_caller_supplied_path_network_or_execution_surface():
    assert not inspect.signature(GENERATOR.main).parameters
    source = inspect.getsource(GENERATOR).casefold()
    prohibited = (
        "argparse", "sys.argv", "input(", "requests", "urllib", "http://",
        "https://", "subprocess", "os.environ", "getenv", "eval(", "exec(",
        "pickle", "marshal", "socket",
    )
    assert all(token not in source for token in prohibited)
    assert GENERATOR.OUTPUT == CORPUS_PATH


def test_no_apple_version_compatibility_or_support_claims():
    text = CORPUS_PATH.read_text(encoding="utf-8").casefold()
    prohibited = (
        "tested on ios", "compatible with ios", "supports iphone",
        "supports apple devices", "supports itunes", "compatibility_validated",
        '"support_status": "supported"', '"apple_produced_status": "apple_produced_characterized"',
    )
    assert all(claim not in text for claim in prohibited)
    assert '"apple_produced_status": "apple_produced_not_started"' in text
    assert '"compatibility_status": "compatibility_not_evaluated"' in text
    assert '"support_status": "support_not_evaluated"' in text

