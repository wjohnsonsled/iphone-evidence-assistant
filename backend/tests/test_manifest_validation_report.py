"""Focused DEV-0611 deterministic report-package validation."""

from __future__ import annotations

import copy
import importlib
import inspect
import json
import re
from pathlib import Path

import pytest

from app.manifest.validation_report import (
    CLAIMS,
    DISPOSITION,
    PROFILES,
    REQUIRED_SECTIONS,
    TASKS,
    build_report,
    logical_digest,
    validate_report,
)

ROOT = Path(__file__).parents[2]
CORPUS_PATH = Path(__file__).parent / "fixtures" / "manifest_synthetic" / "corpus-manifest.json"
JSON_PATH = ROOT / "docs" / "06-quality" / "DEV-0611-manifest-synthetic-validation-report.json"
MARKDOWN_PATH = ROOT / "docs" / "06-quality" / "DEV-0611-manifest-synthetic-validation-report.md"
GENERATOR = importlib.import_module("scripts.generate_manifest_validation_report")


def _json():
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def _corpus():
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def _redigest(report):
    report["logical_content_sha256"] = logical_digest(report)
    return report


def test_report_is_valid_and_derived_disposition_is_bounded():
    report = _json()
    result = validate_report(report)
    assert result.valid
    assert report["disposition"] == DISPOSITION
    assert report["implementation_readiness"] == "CANDIDATE_COMPLETE"
    assert report["synthetic_characterization_readiness"] == DISPOSITION
    assert report["apple_produced_characterization_readiness"] == "NOT_STARTED"
    assert report["compatibility_validation_readiness"] == "NOT_EVALUATED"
    assert report["support_validation_readiness"] == "NOT_EVALUATED"
    assert report["production_readiness"] == "NOT_EVALUATED"
    assert report["supported_capability"] == "NOT_AUTHORIZED"


@pytest.mark.parametrize("section", REQUIRED_SECTIONS)
def test_all_forty_authoritative_markdown_sections_exist(section):
    markdown = MARKDOWN_PATH.read_text(encoding="utf-8")
    assert re.search(rf"^## \d+\. {re.escape(section)}$", markdown, re.MULTILINE)


def test_task_inventory_is_exact_ordered_and_traceable():
    report = _json()
    assert [item["task_id"] for item in report["tasks"]] == [item[0] for item in TASKS]
    assert len(report["traceability"]) == len(TASKS) == 12
    for task, link in zip(report["tasks"], report["traceability"]):
        assert link["task"] == task["task_id"]
        assert link["decision"] == task["decision"]
        assert link["implementation"] == task["profile_id"]
        assert all(task[field] for field in ("decision", "acceptance_record", "validation_record"))
        assert task["commit"] == "not recorded" or re.fullmatch(
            r"[0-9a-f]{7}(?:/[0-9a-f]{7})?", task["commit"]
        )


def test_decisions_and_commits_are_supported_by_repository_records():
    decision_log = (ROOT / "docs" / "00-document-control" / "DOC-003-decision-log.md").read_text(encoding="utf-8")
    report = _json()
    for task in report["tasks"]:
        for decision in task["decision"].split("/"):
            assert decision in decision_log
    known_commits = {
        "8b29f16", "c7f7e3e", "74a0175", "6eaee32", "7416db1",
        "4654069", "c1423c6", "2854ecd", "ef3517d", "c8e9684",
        "d23738e", "7a1f2e3", "f615f8b",
    }
    recorded = {
        value
        for task in report["tasks"] if task["commit"] != "not recorded"
        for value in task["commit"].split("/")
    }
    assert recorded == known_commits


def test_profile_inventory_is_exact_ordered_and_preserves_validation_levels():
    report = _json()
    assert [(item["profile_id"], item["profile_version"]) for item in report["profiles"]] == [
        (item[0], item[1]) for item in PROFILES
    ]
    assert len(report["profiles"]) == 17
    for profile in report["profiles"]:
        assert profile["status"] == "CANDIDATE_NOT_SUPPORTED"
        assert profile["synthetic_characterization"] == "CHARACTERIZED"
        assert profile["apple_produced_characterization"] == "NOT_STARTED"
        assert profile["compatibility_validation"] == "NOT_EVALUATED"
        assert profile["support_validation"] == "NOT_EVALUATED"


def test_claims_matrix_is_complete_and_never_supports_a_claim():
    report = _json()
    assert [item["claim"] for item in report["claims_matrix"]] == [item[0] for item in CLAIMS]
    assert len(report["claims_matrix"]) == 18
    for claim in report["claims_matrix"]:
        assert claim["apple_produced_support"] == "NONE"
        assert claim["compatibility_support"] == "NONE"
        assert claim["support_validation"] == "NOT_EVALUATED"
        assert claim["limitation_reference"]


def test_validation_ladder_has_no_automatic_advancement():
    ladder = _json()["validation_ladder"]
    assert [item["level"] for item in ladder] == list(range(1, 7))
    assert ladder[0]["status"] == "COMPLETE_WITH_LIMITATIONS"
    assert all(item["status"] in {"NOT_STARTED", "NOT_EVALUATED", "NOT_AUTHORIZED"} for item in ladder[1:])
    assert all("Separate owner approval" in item["governing_decision_required"] for item in ladder)


def test_validation_dimensions_remain_independent_and_counted():
    results = {item["dimension"]: item for item in _json()["validation_results"]}
    assert len(results) == 16
    assert results["focused validation"]["count"] == 63
    assert results["combined Manifest validation"]["count"] == 385
    assert results["backend regression"]["count"] == 776
    assert results["legacy characterization"]["count"] == 5
    assert results["fixture integrity"]["count"] == 60
    assert results["backend regression"]["accepted_warning"]


def test_corpus_cross_check_uses_committed_registered_facts():
    report = _json()["corpus"]
    corpus = _corpus()
    assert report["corpus_id"] == corpus["corpus_id"]
    assert report["fixture_count"] == len(corpus["fixtures"]) == 60
    assert report["profile_matrix_count"] == len(corpus["profile_matrix"]) == 13
    assert report["synthetic_test_asset_sha256"] == corpus["corpus_manifest_sha256"]
    assert not report["contains_real_or_apple_produced_data"]


def test_generator_is_deterministic_and_matches_both_committed_outputs():
    report = build_report(_corpus())
    assert report == _json()
    assert GENERATOR.render_markdown(report) == MARKDOWN_PATH.read_text(encoding="utf-8")
    expected_json = json.dumps(report, indent=2, sort_keys=True) + "\n"
    assert expected_json == JSON_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        (lambda r: r["required_sections"].pop(), "required_sections_incomplete"),
        (lambda r: r["tasks"].pop(), "task_inventory_incomplete"),
        (lambda r: r["profiles"].pop(), "profile_inventory_incomplete"),
        (lambda r: r["claims_matrix"].pop(), "claims_matrix_incomplete"),
        (lambda r: r["validation_ladder"].pop(), "validation_ladder_incomplete"),
        (lambda r: r["traceability"][0].update({"test": None}), "traceability_gap"),
        (lambda r: r.update({"supported_parser_registry_count": 1}), "support_state_inconsistent"),
        (lambda r: r.update({"supported_normalized_record_count": 1}), "support_state_inconsistent"),
        (lambda r: r.update({"disposition": "SUPPORTED"}), "disposition_invalid"),
        (lambda r: r.update({"limitations": []}), "limitations_incomplete"),
        (lambda r: r.update({"logical_content_sha256": "0" * 64}), "report_digest_mismatch"),
    ),
)
def test_report_validation_fails_closed(mutation, reason):
    report = copy.deepcopy(_json())
    mutation(report)
    if reason != "report_digest_mismatch":
        _redigest(report)
    result = validate_report(report)
    assert not result.valid
    assert reason in result.reason_codes


def test_report_build_rejects_unregistered_or_support_changed_corpus():
    corpus = copy.deepcopy(_corpus())
    corpus["corpus_id"] = "unregistered"
    with pytest.raises(ValueError, match="registered_corpus_identity_mismatch"):
        build_report(corpus)
    corpus = copy.deepcopy(_corpus())
    corpus["corpus_manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="registered_corpus_digest_mismatch"):
        build_report(corpus)
    corpus = copy.deepcopy(_corpus())
    corpus["registry_entry_count"] = 1
    with pytest.raises(ValueError, match="support_state_inconsistent"):
        build_report(corpus)


def test_outputs_contain_no_host_paths_secrets_or_real_data_markers():
    combined = JSON_PATH.read_text(encoding="utf-8") + MARKDOWN_PATH.read_text(encoding="utf-8")
    prohibited = (
        "C:\\Users\\", "/Users/", ".pytest-tmp", "api_key", "password=",
        "BEGIN PRIVATE KEY", "@gmail.com", "@icloud.com", "customer evidence value",
    )
    assert all(value not in combined for value in prohibited)
    assert '"attorney_facing": false' in combined
    assert "No real evidence was processed" in combined


def test_generator_has_fixed_registered_inputs_and_no_network_execution_surface():
    assert not inspect.signature(GENERATOR.main).parameters
    source = inspect.getsource(GENERATOR).casefold()
    prohibited = (
        "argparse", "sys.argv", "input(", "requests", "urllib", "http://",
        "https://", "subprocess", "os.environ", "getenv", "eval(", "exec(",
        "pickle", "marshal", "socket",
    )
    assert all(token not in source for token in prohibited)
    assert GENERATOR.CORPUS_PATH == CORPUS_PATH
    assert GENERATOR.JSON_PATH == JSON_PATH
    assert GENERATOR.MARKDOWN_PATH == MARKDOWN_PATH
