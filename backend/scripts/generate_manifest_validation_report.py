"""Generate fixed-path DEV-0611 JSON and authoritative Markdown reports."""

from __future__ import annotations

import json
from pathlib import Path

from app.manifest.validation_report import REQUIRED_SECTIONS, build_report

BACKEND = Path(__file__).resolve().parents[1]
REPOSITORY = BACKEND.parent
CORPUS_PATH = BACKEND / "tests" / "fixtures" / "manifest_synthetic" / "corpus-manifest.json"
JSON_PATH = REPOSITORY / "docs" / "06-quality" / "DEV-0611-manifest-synthetic-validation-report.json"
MARKDOWN_PATH = REPOSITORY / "docs" / "06-quality" / "DEV-0611-manifest-synthetic-validation-report.md"


def _table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *["| " + " | ".join("not recorded" if value is None else str(value) for value in row) + " |" for row in rows],
    ]


def render_markdown(report: dict[str, object]) -> str:
    content: dict[str, list[str]] = {
        section: ["No additional evaluated result; the governing limitation remains explicit."]
        for section in REQUIRED_SECTIONS
    }
    content["Document control"] = [
        f"- Report: `{report['report_id']}`",
        f"- Profile: `{report['report_profile_id']}` version `{report['report_profile_version']}`",
        f"- Logical-content SHA-256: `{report['logical_content_sha256']}`",
        "- Authority: DEC-0079",
        "- Authoritative representation: this Markdown report",
    ]
    content["Executive summary"] = [
        f"Disposition: `{report['disposition']}`.",
        "Candidate implementation and project-original synthetic characterization are complete with the limitations below.",
        "Apple-produced characterization, compatibility validation, support validation, production readiness, and Supported capability remain not started, not evaluated, or unauthorized.",
        "No real evidence was processed; registry entries and supported normalized records remain zero.",
    ]
    content["Purpose"] = ["Internal architecture, quality, forensic-method, security, audit, and future support-gate preparation."]
    content["Scope"] = ["Repository-controlled DEV-0601 through DEV-0610 implementation and synthetic characterization records, plus this DEV-0611 package."]
    content["Explicit exclusions"] = [f"- {item}" for item in report["unsupported_conclusions"]]
    content["Governing decisions"] = [", ".join(f"`{item}`" for item in report["governing_decisions"])]
    content["Workstream task history"] = _table(
        ("Task", "Status", "Decision", "Commit", "Profile", "Acceptance", "Validation"),
        [(item["task_id"], item["status"], item["decision"], item["commit"], f"{item['profile_id']} v{item['profile_version']}", item["acceptance_record"], item["validation_record"]) for item in report["tasks"]],
    )
    content["Candidate profile inventory"] = _table(
        ("Profile", "Version", "Task", "Decision", "Synthetic", "Apple-produced", "Compatibility", "Support"),
        [(item["profile_id"], item["profile_version"], item["task_id"], item["decision"], item["synthetic_characterization"], item["apple_produced_characterization"], item["compatibility_validation"], item["support_validation"]) for item in report["profiles"]],
    )
    content["Architecture summary"] = ["Candidate modules remain isolated from production composition, persistence, APIs, supported storage, and parser activation. See ARC-002."]
    content["Evidence-integrity controls"] = ["Source immutability and controlled-copy boundaries remain governing; this package contains no source evidence. Report and corpus digests protect test/report assets only."]
    content["Provenance controls"] = ["Every task/profile/claim traces to decisions, acceptance/validation records, commits where recorded, limitations, and report sections."]
    content["Security controls"] = ["Fixed registered inputs only; no arbitrary paths, backup crawling, network, secrets, dynamic code, unsafe deserialization, or evidence access."]
    content["Resource-governance controls"] = ["Row, page, byte, deterministic memory-estimate, wall-clock, cancellation, concurrency, authorization, schema, mutation, and SQLite outcomes were synthetically characterized."]
    content["Synthetic corpus governance"] = [f"Corpus `{report['corpus']['corpus_id']}` v{report['corpus']['corpus_version']} is governed by FOR-021."]
    content["Synthetic fixture source policy"] = [f"Source: `{report['corpus']['source_classification']}`; real/Apple-produced content: `{report['corpus']['contains_real_or_apple_produced_data']}`."]
    content["Synthetic corpus inventory"] = [
        f"- Fixtures: {report['corpus']['fixture_count']}",
        f"- Profile matrix entries: {report['corpus']['profile_matrix_count']}",
        f"- Synthetic test-asset integrity digest: `{report['corpus']['synthetic_test_asset_sha256']}`",
    ]
    content["Schema coverage matrix"] = ["QMS-020 and the v1 corpus matrix cover compatible, unknown, missing, unexpected, invalid, corrupt, locator, mutation, fingerprint, and unsupported synthetic schema conditions."]
    content["Profile coverage matrix"] = ["All 13 DEV-0610 matrix entries and the broader 17-entry workstream profile inventory are accounted for. See the JSON `profiles` and committed corpus `profile_matrix`."]
    content["Positive scenario coverage"] = ["Recognized schema/query/locator/normalization/syntax and complete-coverage synthetic paths are registered."]
    content["Negative scenario coverage"] = ["Denial, unsupported, unavailable, mismatch, isolation, mutation, missing, and prohibited-source paths are registered."]
    content["Malformed-input coverage"] = ["Malformed SQLite, identifier, domain, BLOB, manifest, provenance, custody, and distribution inputs fail closed."]
    content["Resource-limit coverage"] = ["Row, byte, deterministic memory-estimate, wall-clock, cancellation, and concurrency cases are registered."]
    content["Isolation coverage"] = ["Cross-tenant, cross-case, cross-source/copy/run, authorization, and unregistered-input denials are covered."]
    content["Determinism coverage"] = ["Fixture regeneration, canonical JSON, corpus manifest, observation/report serialization, and digest verification are deterministic."]
    content["Validation results"] = _table(
        ("Dimension", "Status", "Count", "Source", "Commit", "Warning"),
        [(item["dimension"], item["status"], item["count"], item["source_record"], item["commit_context"], item["accepted_warning"]) for item in report["validation_results"]],
    )
    content["Accepted warnings"] = [f"- {item}" for item in report["accepted_warnings"]]
    content["Migration status"] = [f"Head remains `{report['migration']['head']}`; new migrations: {report['migration']['new_migrations']}."]
    content["Registry and normalized-record status"] = [f"Supported Parser Registry entries: {report['supported_parser_registry_count']}; supported normalized records: {report['supported_normalized_record_count']}."]
    content["Limitation summary"] = [f"- {item}" for item in report["limitations"]]
    content["Unsupported conclusions"] = [f"- {item}: not evaluated or not authorized." for item in report["unsupported_conclusions"]]
    content["Apple-produced validation status"] = ["`NOT_STARTED`. No Apple-produced fixture was acquired, generated, or processed."]
    content["Compatibility-validation status"] = ["`NOT_EVALUATED`. Synthetic behavior cannot establish Apple/device/software compatibility."]
    content["Support-validation status"] = ["`NOT_EVALUATED`. No parser, artifact, input, backup, workflow, or capability is Supported."]
    content["Risk summary"] = [", ".join(f"`{item}`" for item in report["risks"])]
    content["Remaining dependencies"] = ["A separately owner-governed Apple-produced characterization package is required before compatibility or support validation."]
    content["Future validation requirements"] = [f"- {item}" for item in report["future_apple_produced_requirements"]]
    content["Synthetic characterization disposition"] = [
        f"`{report['disposition']}` applies only to implementation and synthetic characterization.",
        *[f"- {item}" for item in report["limitations"]],
    ]
    content["Acceptance criteria"] = ["All DEV-0611 criteria are validated by QMS-021 and the focused report test suite; this statement becomes final only with the completion record."]
    content["Traceability appendix"] = _table(
        ("Requirement", "Task", "Decision", "Implementation", "Test", "Limitation", "Section"),
        [(item["requirement"], item["task"], item["decision"], item["implementation"], item["test"], item["limitation"], item["report_section"]) for item in report["traceability"]],
    )
    content["Commit and decision appendix"] = _table(
        ("Task", "Decision", "Commit"),
        [(item["task_id"], item["decision"], item["commit"]) for item in report["tasks"]],
    )
    lines = ["# DEV-0611 — Manifest Synthetic Validation Report", ""]
    for number, section in enumerate(REQUIRED_SECTIONS, start=1):
        lines.extend((f"## {number}. {section}", "", *content[section], ""))
        if section == "Support-validation status":
            lines.extend(("### Claims matrix", "", *_table(
                ("Claim", "Repository", "Synthetic", "Apple", "Compatibility", "Support", "Permitted wording", "Prohibited wording"),
                [(item["claim"], item["repository_support"], item["synthetic_support"], item["apple_produced_support"], item["compatibility_support"], item["support_validation"], item["permitted_wording"], item["prohibited_wording"]) for item in report["claims_matrix"]],
            ), ""))
        if section == "Future validation requirements":
            lines.extend(("### Validation ladder", "", *_table(
                ("Level", "Name", "Status", "Completed", "Missing", "Permitted", "Decision required"),
                [(item["level"], item["name"], item["status"], item["completed_work"], item["missing_work"], item["permitted_claims"], item["governing_decision_required"]) for item in report["validation_ladder"]],
            ), ""))
    return "\n".join(lines)


def main() -> None:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    report = build_report(corpus)
    JSON_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    MARKDOWN_PATH.write_text(render_markdown(report), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

