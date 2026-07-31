import hashlib, json
from pathlib import Path

ROOT = Path(__file__).parent / "fixtures" / "physical_inventory_synthetic"


def test_corpus_is_versioned_deterministic_project_original_and_complete():
    document = json.loads((ROOT / "corpus-manifest.json").read_text(encoding="utf-8"))
    assert document["corpus_version"] == "1"
    assert document["source_basis"] == "PROJECT_ORIGINAL_SYNTHETIC"
    assert document["apple_produced"] is False
    assert document["support_effect"] == "NONE"
    assert document["scenario_count"] == len(document["scenarios"]) == 50
    assert len({item["scenario_id"] for item in document["scenarios"]}) == 50
    for item in document["scenarios"]:
        digest = item.pop("sha256")
        canonical = json.dumps(item, sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(canonical).hexdigest() == digest


def test_corpus_covers_every_governed_behavior_family():
    document = json.loads((ROOT / "corpus-manifest.json").read_text(encoding="utf-8"))
    categories = {item["category"] for item in document["scenarios"]}
    assert {"exact_match", "complete_no_match", "partial_no_match", "invalid_name",
            "wrong_prefix", "unsupported_object", "inaccessible", "resource_limit",
            "cancellation", "scope_mismatch", "hash_success", "hash_mutation",
            "hash_limit", "multiple_match", "determinism", "provenance",
            "coverage_separation", "absence_prohibited", "support_prohibited"} <= categories
