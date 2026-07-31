"""Generate deterministic project-original DEV-0625 scenario metadata."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

CATEGORIES = (
    "exact_match", "complete_no_match", "partial_no_match", "invalid_name",
    "wrong_prefix", "unexpected_directory", "unsupported_object", "inaccessible",
    "resource_limit", "cancellation", "scope_mismatch", "hash_success",
    "hash_mutation", "hash_limit", "multiple_match", "determinism",
    "provenance", "coverage_separation", "absence_prohibited", "support_prohibited",
)

scenarios = []
for index in range(50):
    category = CATEGORIES[index % len(CATEGORIES)]
    payload = {
        "scenario_id": f"PHY-{index + 1:03d}",
        "category": category,
        "synthetic_only": True,
        "file_id": f"{index % 256:02x}" + f"{index:038x}"[-38:],
        "expected_claim_boundary": "CANDIDATE_OBSERVATION_ONLY",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["sha256"] = hashlib.sha256(canonical).hexdigest()
    scenarios.append(payload)
document = {
    "corpus_id": "physical-inventory-synthetic-corpus",
    "corpus_version": "1",
    "generator": "generate_corpus.py",
    "scenario_count": len(scenarios),
    "source_basis": "PROJECT_ORIGINAL_SYNTHETIC",
    "apple_produced": False,
    "support_effect": "NONE",
    "scenarios": scenarios,
}
Path(__file__).with_name("corpus-manifest.json").write_text(
    json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
)
