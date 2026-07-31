"""Deterministic candidate-only Manifest synthetic validation report model."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

REPORT_PROFILE_ID = "manifest-synthetic-validation-report"
REPORT_PROFILE_VERSION = "1"
REPORT_SCHEMA_VERSION = "1"
DISPOSITION = "SYNTHETIC_CHARACTERIZATION_ACCEPTED_WITH_LIMITATIONS"
MIGRATION_HEAD = "0005_processing_idempotency"

REQUIRED_SECTIONS = (
    "Document control", "Executive summary", "Purpose", "Scope",
    "Explicit exclusions", "Governing decisions", "Workstream task history",
    "Candidate profile inventory", "Architecture summary",
    "Evidence-integrity controls", "Provenance controls", "Security controls",
    "Resource-governance controls", "Synthetic corpus governance",
    "Synthetic fixture source policy", "Synthetic corpus inventory",
    "Schema coverage matrix", "Profile coverage matrix",
    "Positive scenario coverage", "Negative scenario coverage",
    "Malformed-input coverage", "Resource-limit coverage",
    "Isolation coverage", "Determinism coverage", "Validation results",
    "Accepted warnings", "Migration status",
    "Registry and normalized-record status", "Limitation summary",
    "Unsupported conclusions", "Apple-produced validation status",
    "Compatibility-validation status", "Support-validation status",
    "Risk summary", "Remaining dependencies", "Future validation requirements",
    "Synthetic characterization disposition", "Acceptance criteria",
    "Traceability appendix", "Commit and decision appendix",
)

LIMITATIONS = (
    "Synthetic fixtures do not prove Apple-generated behavior.",
    "Lexical recognition is not cryptographic verification.",
    "Canonical fileID equality is not content identity.",
    "Domain recognition is not proof of application installation or use.",
    "Relative-path normalization is not physical resolution.",
    "Flags observation is not proof of deletion or existence.",
    "Metadata-BLOB syntax recognition is not full semantic interpretation.",
    "Manifest row inventory coverage is not artifact coverage.",
    "Partial coverage cannot support absence.",
    "Reconciliation patterns do not prove missing or orphaned objects without complete comparison universes.",
    "No physical-object inventory was created.",
    "No real evidence or Apple-produced fixture was processed.",
    "No parser was activated and no support status changed.",
    "Supported Parser Registry entries and supported normalized records remain zero.",
)

PROHIBITED_CONCLUSIONS = (
    "Apple-version compatibility", "artifact support", "parser support",
    "backup support", "physical-object existence or absence",
    "duplicate or orphaned physical objects", "user activity completeness",
    "production readiness", "Supported capability",
)

TASKS = (
    ("DEV-0601", "COMPLETE", "DEC-0059", "8b29f16", "apple-manifestdb-schema", "1", "DEV-0601-manifest-schema-profile-acceptance", "QMS record not separate"),
    ("DEV-0602", "COMPLETE", "DEC-0060", "c7f7e3e", "manifestdb-files-query", "1", "DEV-0602-files-query-layer-acceptance", "FOR-012"),
    ("DEV-0602A", "COMPLETE", "DEC-0061/DEC-0062", "74a0175/6eaee32", "manifestdb-files-query", "2", "DEV-0602A-files-query-hardening-acceptance", "QMS-012"),
    ("DEV-0603", "COMPLETE", "DEC-0063/DEC-0064", "7416db1", "manifestdb-fileid-normalization", "1", "DEV-0603-manifest-fileid-normalization-acceptance", "QMS-013"),
    ("DEV-0604", "COMPLETE", "DEC-0065/DEC-0066", "4654069", "manifestdb-domain-grammar", "1", "DEV-0604-manifest-domain-normalization-acceptance", "QMS-014"),
    ("DEV-0605", "COMPLETE", "DEC-0067/DEC-0068", "c1423c6", "manifestdb-relative-path-lexical", "1", "DEV-0605-manifest-relative-path-acceptance", "QMS-015"),
    ("DEV-0606", "COMPLETE", "DEC-0069/DEC-0070", "2854ecd", "manifestdb-flags-observation", "1", "DEV-0606-manifest-flags-observation-acceptance", "QMS-016"),
    ("DEV-0607", "COMPLETE", "DEC-0071/DEC-0072", "ef3517d", "manifestdb-file-bplist-syntax", "1", "DEV-0607-manifest-metadata-blob-acceptance", "QMS-017"),
    ("DEV-0608", "COMPLETE", "DEC-0075/DEC-0076", "c8e9684", "manifestdb-inventory-coverage", "1", "DEV-0608-manifest-inventory-coverage-acceptance", "QMS-019"),
    ("DEV-0609", "COMPLETE", "DEC-0073/DEC-0074", "d23738e/7a1f2e3", "manifestdb-reconciliation-semantics", "1", "DEV-0609-manifest-reconciliation-semantics-acceptance", "QMS-018"),
    ("DEV-0610", "COMPLETE", "DEC-0077/DEC-0078", "f615f8b", "synthetic-characterization-corpus-governance", "1", "DEV-0610-synthetic-manifest-corpus-acceptance", "QMS-020"),
    ("DEV-0611", "COMPLETE", "DEC-0079/DEC-0080", "not recorded", REPORT_PROFILE_ID, REPORT_PROFILE_VERSION, "DEV-0611-acceptance-record", "QMS-021"),
)

PROFILES = (
    ("apple-manifestdb-schema", "1", "DEV-0601", "DEC-0059"),
    ("manifestdb-schema-canonical-json-sha256", "1", "DEV-0601", "DEC-0008/DEC-0059"),
    ("manifestdb-files-query", "1", "DEV-0602", "DEC-0060"),
    ("manifestdb-row-locator", "1", "DEV-0602", "DEC-0060"),
    ("manifestdb-files-query", "2", "DEV-0602A", "DEC-0061/DEC-0062"),
    ("manifestdb-query-resource-controls", "1", "DEV-0602A", "DEC-0061/DEC-0062"),
    ("canonical-identifier-normalization", "1", "DEV-0603", "DEC-0063/DEC-0064"),
    ("manifestdb-fileid-normalization", "1", "DEV-0603", "DEC-0063/DEC-0064"),
    ("manifestdb-domain-grammar", "1", "DEV-0604", "DEC-0065/DEC-0066"),
    ("manifestdb-relative-path-lexical", "1", "DEV-0605", "DEC-0067/DEC-0068"),
    ("manifestdb-flags-observation", "1", "DEV-0606", "DEC-0069/DEC-0070"),
    ("manifestdb-file-bplist-syntax", "1", "DEV-0607", "DEC-0071/DEC-0072"),
    ("manifestdb-reconciliation-semantics", "1", "DEV-0609", "DEC-0073/DEC-0074"),
    ("manifestdb-inventory-coverage", "1", "DEV-0608", "DEC-0075/DEC-0076"),
    ("synthetic-characterization-corpus-governance", "1", "DEV-0610", "DEC-0077/DEC-0078"),
    ("manifest-synthetic-characterization-corpus", "1", "DEV-0610", "DEC-0077/DEC-0078"),
    (REPORT_PROFILE_ID, REPORT_PROFILE_VERSION, "DEV-0611", "DEC-0079"),
)

CLAIMS = (
    ("Manifest schema recognition", "Permitted only for the candidate synthetic schema profile."),
    ("Files-table query behavior", "Permitted only for controlled synthetic query behavior."),
    ("ROWID locator behavior", "Permitted only within one controlled copy and processing run."),
    ("fileID lexical recognition", "Permitted as lexical recognition, not hash verification."),
    ("domain grammar", "Permitted as candidate structural recognition only."),
    ("relative-path normalization", "Permitted as lexical observation, not physical resolution."),
    ("flags observation", "Permitted with every bit meaning unknown."),
    ("metadata-BLOB syntax recognition", "Permitted as bounded syntax recognition without semantic field meaning."),
    ("inventory coverage", "Permitted only for the performed logical Files-row examination."),
    ("reconciliation semantics", "Permitted only as repetition-pattern observation."),
    ("absence eligibility", "Not eligible without every separately approved complete universe and layer."),
    ("duplicate eligibility", "Not established without physical inventory and validated conclusions."),
    ("orphan eligibility", "Not established without physical inventory and validated conclusions."),
    ("physical-object resolution", "Not implemented or evaluated."),
    ("Apple-version compatibility", "Not evaluated."),
    ("artifact support", "Not evaluated."),
    ("parser support", "Not evaluated."),
    ("backup support", "Not evaluated."),
)

VALIDATION_RESULTS = (
    ("focused validation", "PASS", 63, "QMS-021", "not recorded"),
    ("integration validation", "PASS", None, "QMS-021", "not recorded"),
    ("combined Manifest validation", "PASS", 385, "QMS-021", "not recorded"),
    ("backend regression", "PASS_WITH_ACCEPTED_WARNING", 776, "QMS-021", "not recorded"),
    ("legacy characterization", "PASS", 5, "QMS-021", "not recorded"),
    ("compilation", "PASS", None, "QMS-021", "not recorded"),
    ("dependency lock", "PASS", 3, "QMS-020", "f615f8b"),
    ("pip consistency", "PASS", None, "QMS-020", "f615f8b"),
    ("Alembic head", "PASS", 1, "QMS-020", "f615f8b"),
    ("Alembic history", "PASS", 5, "QMS-020", "f615f8b"),
    ("Alembic offline SQL", "PASS", None, "QMS-020", "f615f8b"),
    ("repository hygiene", "PASS", None, "QMS-020", "f615f8b"),
    ("fixture integrity", "PASS", 60, "QMS-020", "f615f8b"),
    ("deterministic regeneration", "PASS", 60, "QMS-020", "f615f8b"),
    ("security review", "PASS_WITH_LIMITATIONS", None, "SEC-001/FOR-021", "f615f8b"),
    ("final diff review", "PASS", None, "QMS-020", "f615f8b"),
)

LADDER = (
    (1, "Synthetic implementation characterization", "COMPLETE_WITH_LIMITATIONS", "Candidate implementation and project-original synthetic corpus characterized.", "Apple-produced behavior and every later gate.", "Candidate synthetic behavior only."),
    (2, "Controlled Apple-produced characterization", "NOT_STARTED", "None.", "Owner-governed lawful fixture package and controlled execution.", "No Apple-produced claim."),
    (3, "Compatibility validation", "NOT_EVALUATED", "None.", "Multi-version Apple-produced matrix and independent review.", "No compatibility claim."),
    (4, "Support validation", "NOT_EVALUATED", "None.", "Complete all-or-nothing artifact/parser validation and owner gate.", "No support claim."),
    (5, "Production readiness review", "NOT_EVALUATED", "None.", "Deployment, capacity, live database, operational and security review.", "No production-readiness claim."),
    (6, "Supported capability", "NOT_AUTHORIZED", "None.", "Explicit traceable owner promotion after all prior gates.", "No Supported claim."),
)


@dataclass(frozen=True, slots=True)
class ReportValidationResult:
    valid: bool
    reason_codes: tuple[str, ...]
    calculated_digest: str


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def logical_digest(report: Mapping[str, object]) -> str:
    material = dict(report)
    material.pop("logical_content_sha256", None)
    return hashlib.sha256(canonical_bytes(material)).hexdigest()


def _task_records() -> list[dict[str, object]]:
    return [
        {
            "task_id": task, "status": status, "decision": decision,
            "commit": commit, "profile_id": profile, "profile_version": version,
            "acceptance_record": acceptance, "validation_record": validation,
            "limitations": list(LIMITATIONS),
        }
        for task, status, decision, commit, profile, version, acceptance, validation in TASKS
    ]


def build_report(corpus: Mapping[str, object]) -> dict[str, object]:
    if corpus.get("corpus_id") != "manifest-synthetic-characterization-corpus":
        raise ValueError("registered_corpus_identity_mismatch")
    if corpus.get("corpus_manifest_sha256") != "159b01df907f56cd7c8f82c1a77cc67e479f6c87e169408b3aec5fcec38655bc":
        raise ValueError("registered_corpus_digest_mismatch")
    if corpus.get("registry_entry_count") != 0 or corpus.get("supported_normalized_record_count") != 0:
        raise ValueError("support_state_inconsistent")
    disposition = (
        DISPOSITION
        if all(item[1] == "COMPLETE" for item in TASKS[:-1])
        and corpus.get("status") == "SYNTHETIC_CHARACTERIZED"
        and LIMITATIONS
        else "INDETERMINATE"
    )
    tasks = _task_records()
    profiles = [
        {
            "profile_id": profile, "profile_version": version, "task_id": task,
            "decision": decision, "status": "CANDIDATE_NOT_SUPPORTED",
            "synthetic_characterization": "CHARACTERIZED",
            "apple_produced_characterization": "NOT_STARTED",
            "compatibility_validation": "NOT_EVALUATED",
            "support_validation": "NOT_EVALUATED",
            "limitations": list(LIMITATIONS),
        }
        for profile, version, task, decision in PROFILES
    ]
    claims = [
        {
            "claim": claim, "repository_support": "CANDIDATE_SYNTHETIC_ONLY",
            "synthetic_support": wording,
            "apple_produced_support": "NONE",
            "compatibility_support": "NONE",
            "support_validation": "NOT_EVALUATED",
            "permitted_wording": wording,
            "prohibited_wording": f"{claim} is Supported or Apple-compatible.",
            "limitation_reference": "DEV-0611 Limitation summary",
        }
        for claim, wording in CLAIMS
    ]
    validations = [
        {
            "dimension": dimension, "status": status, "count": count,
            "source_record": source, "commit_context": commit,
            "accepted_warning": (
                "Accepted third-party TestClient deprecation warning."
                if dimension == "backend regression" else None
            ),
            "limitation": "Synthetic candidate validation only.",
            "recorded_date": "2026-07-30",
        }
        for dimension, status, count, source, commit in VALIDATION_RESULTS
    ]
    traceability = [
        {
            "requirement": f"DEV-0611-R{index:02d}",
            "task": task["task_id"], "decision": task["decision"],
            "implementation": task["profile_id"],
            "test": task["validation_record"],
            "limitation": "DEV-0611 Limitation summary",
            "report_section": "Workstream task history",
        }
        for index, task in enumerate(tasks, start=1)
    ]
    report: dict[str, object] = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "report_profile_id": REPORT_PROFILE_ID,
        "report_profile_version": REPORT_PROFILE_VERSION,
        "report_id": "DEV-0611-MANIFEST-SYNTHETIC-VALIDATION-REPORT",
        "logical_record_date": "2026-07-30",
        "authoritative_representation": "MARKDOWN",
        "audiences": [
            "internal architecture review", "quality-management review",
            "forensic-method review", "security review",
            "future support-gate preparation", "audit preparation",
        ],
        "attorney_facing": False,
        "disposition": disposition,
        "implementation_readiness": "CANDIDATE_COMPLETE",
        "synthetic_characterization_readiness": disposition,
        "apple_produced_characterization_readiness": "NOT_STARTED",
        "compatibility_validation_readiness": "NOT_EVALUATED",
        "support_validation_readiness": "NOT_EVALUATED",
        "production_readiness": "NOT_EVALUATED",
        "supported_capability": "NOT_AUTHORIZED",
        "governing_decisions": [f"DEC-{number:04d}" for number in range(59, 81)],
        "required_sections": list(REQUIRED_SECTIONS),
        "tasks": tasks,
        "profiles": profiles,
        "validation_results": validations,
        "corpus": {
            "corpus_id": corpus["corpus_id"],
            "corpus_version": corpus["corpus_version"],
            "fixture_count": len(corpus["fixtures"]),
            "profile_matrix_count": len(corpus["profile_matrix"]),
            "synthetic_test_asset_sha256": corpus["corpus_manifest_sha256"],
            "source_classification": corpus["origin"],
            "contains_real_or_apple_produced_data": corpus["contains_real_or_apple_produced_data"],
            "fixture_integrity_verified": True,
            "deterministic_regeneration_verified": True,
        },
        "validation_ladder": [
            {
                "level": level, "name": name, "status": status,
                "completed_work": complete, "missing_work": missing,
                "permitted_claims": permitted,
                "governing_decision_required": "Separate owner approval before advancement.",
                "prohibited_claims": "Claims assigned to this or any later uncompleted level.",
            }
            for level, name, status, complete, missing, permitted in LADDER
        ],
        "claims_matrix": claims,
        "limitations": list(LIMITATIONS),
        "unsupported_conclusions": list(PROHIBITED_CONCLUSIONS),
        "accepted_warnings": ["Third-party TestClient/httpx2 deprecation warning."],
        "migration": {"head": MIGRATION_HEAD, "new_migrations": 0},
        "supported_parser_registry_count": 0,
        "supported_normalized_record_count": 0,
        "risks": ["RSK-0031", "RSK-0032", "RSK-0034", "RSK-0035", "RSK-0036", "RSK-0037", "RSK-0038", "RSK-0039", "RSK-0040", "RSK-0041"],
        "future_apple_produced_requirements": [
            "lawful device and account ownership", "documented backup-generation procedure",
            "device model and operating-system version", "Apple backup software and version",
            "encryption state and backup settings", "collection operator and date/time",
            "controlled-copy creation and digests", "custody and minimization",
            "personal-data handling and secure storage", "retention and destruction",
            "distribution limits and source-control prohibition", "schema fingerprints",
            "profile results and known ground truth", "compatibility matrix and failure cases",
            "repeatability and independent review",
        ],
        "traceability": traceability,
        "registered_sources": [
            "DOC-002", "DOC-003", "DOC-004", "ARC-002", "FOR-002",
            "FOR-011 through FOR-021", "SEC-001", "QMS-012 through QMS-020",
            "DEV-009", "DEV-011", "ACCEPTANCE-RECORD-INDEX",
            "manifest-synthetic-characterization-corpus-v1", "local-git-history",
        ],
    }
    report["logical_content_sha256"] = logical_digest(report)
    return report


def validate_report(report: Mapping[str, object]) -> ReportValidationResult:
    reasons: list[str] = []
    if (report.get("report_profile_id"), report.get("report_profile_version")) != (
        REPORT_PROFILE_ID, REPORT_PROFILE_VERSION,
    ):
        reasons.append("report_profile_invalid")
    sections = report.get("required_sections")
    if sections != list(REQUIRED_SECTIONS):
        reasons.append("required_sections_incomplete")
    tasks = report.get("tasks")
    if not isinstance(tasks, list) or [item.get("task_id") for item in tasks] != [item[0] for item in TASKS]:
        reasons.append("task_inventory_incomplete")
    profiles = report.get("profiles")
    if not isinstance(profiles, list) or len(profiles) != len(PROFILES):
        reasons.append("profile_inventory_incomplete")
    claims = report.get("claims_matrix")
    if not isinstance(claims, list) or len(claims) != len(CLAIMS):
        reasons.append("claims_matrix_incomplete")
    ladder = report.get("validation_ladder")
    if not isinstance(ladder, list) or [item.get("level") for item in ladder] != list(range(1, 7)):
        reasons.append("validation_ladder_incomplete")
    traceability = report.get("traceability")
    if (
        not isinstance(traceability, list)
        or len(traceability) != len(TASKS)
        or any(
            not all(item.get(field) for field in (
                "requirement", "task", "decision", "implementation", "test",
                "limitation", "report_section",
            ))
            for item in traceability
        )
    ):
        reasons.append("traceability_gap")
    if report.get("supported_parser_registry_count") != 0 or report.get("supported_normalized_record_count") != 0:
        reasons.append("support_state_inconsistent")
    if report.get("disposition") not in {
        "SYNTHETIC_CHARACTERIZATION_ACCEPTED",
        "SYNTHETIC_CHARACTERIZATION_ACCEPTED_WITH_LIMITATIONS",
        "SYNTHETIC_CHARACTERIZATION_INCOMPLETE",
        "SYNTHETIC_CHARACTERIZATION_REJECTED",
        "INDETERMINATE",
    }:
        reasons.append("disposition_invalid")
    if not report.get("limitations") or not report.get("unsupported_conclusions"):
        reasons.append("limitations_incomplete")
    calculated = logical_digest(report)
    if report.get("logical_content_sha256") != calculated:
        reasons.append("report_digest_mismatch")
    return ReportValidationResult(not reasons, tuple(sorted(set(reasons))), calculated)
