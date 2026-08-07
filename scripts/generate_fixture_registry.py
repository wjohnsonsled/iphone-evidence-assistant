"""Generate authoritative registry, human projection, and current pointer."""
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"backend"))
from app.fixture_preflight.registry import registry_digest

fixture={
 "package_id":"CAF-2026-001","package_version":"1","classification":"CONTROLLED_APPLE_PRODUCED_TEST_FIXTURE",
 "lifecycle_status":"PREPARATION_COMPLETE","preparation_status":"CONTROLLED_APPLE_FIXTURE_PREPARATION_COMPLETE",
 "apple_produced_characterization_status":"NOT_STARTED","compatibility_validation_status":"NOT_EVALUATED",
 "support_validation_status":"NOT_EVALUATED","production_readiness_status":"NOT_EVALUATED","supported_capability_status":"UNAUTHORIZED",
 "owner_authorization_reference":"OWNER-AUTH-2026-08-07-CAF-2026-001-REGISTRATION","governing_work_package":"WP-0630",
 "governing_decisions":["DEC-0088","DEC-0089"],"owner_checklist_reference":"docs/operations/OWNER-001-controlled-apple-fixture-checklist.md",
 "sop_reference":"docs/operations/SOP-001-controlled-apple-fixture-generation.md","package_manifest_reference":"docs/schemas/controlled-apple-fixture-package-v1.schema.json",
 "ground_truth_reference":"docs/operations/TPL-001-ground-truth-event-plan.md","custody_record_reference":"docs/operations/TPL-002-fixture-custody-record.md",
 "minimization_record_reference":"docs/operations/TPL-003-fixture-minimization-checklist.md","retention_destruction_record_reference":"docs/operations/TPL-004-retention-destruction-record.md",
 "validation_matrix_reference":"docs/operations/TPL-005-apple-fixture-validation-matrix.md","storage_reference_id":"CAF-2026-001-SECURE-STORE",
 "storage_status":"NOT_YET_ASSIGNED","secured_external_storage_reference_policy":"NON_SENSITIVE_ID_ONLY_PROTECTED_MAPPING_NOT_IN_GIT",
 "source_control_policy":"RAW_FIXTURE_PROHIBITED","permitted_processing_status":"NOT_AUTHORIZED","fixture_generated":False,"preflight_passed":False,
 "restrictions":["Fixture has not been generated.","No backup has been opened or processed.","Future raw fixture must remain outside Git.","Processing requires separate owner authorization naming CAF-2026-001."],
 "limitations":["Package documentation preparation is complete only.","One fixture cannot establish compatibility or support."],
 "current_owner_action":"CREATE_CONTROLLED_APPLE_PRODUCED_FIXTURE","created_at":"2026-08-07","last_updated_at":"2026-08-07",
 "supersedes":None,"superseded_by":None,"retirement_status":"ACTIVE","package_id_reusable":False
}
registry={"registry_id":"controlled-apple-fixture-registry","registry_version":"1","registry_classification":"CONTROLLED_INTERNAL_VALIDATION_METADATA",
 "logical_digest_algorithm":"SHA-256","logical_digest_canonicalization_profile":"canonical-json-sorted-keys-no-whitespace-excluding-logical-digest",
 "logical_digest_canonicalization_version":"1","fixtures":[fixture],"limitations":["Registry digest protects document consistency only; it is not an evidence hash or Apple authenticity proof.","Registry presence does not authorize processing or support."]}
registry["logical_digest"]=registry_digest(registry)
ops=ROOT/"docs"/"operations"
(ops/"FIXTURE_REGISTRY.json").write_text(json.dumps(registry,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
(ops/"CURRENT_FIXTURE.json").write_text(json.dumps({"package_id":"CAF-2026-001","package_version":"1","registry_reference":"docs/operations/FIXTURE_REGISTRY.json","current_owner_action":"CREATE_CONTROLLED_APPLE_PRODUCED_FIXTURE","processing_authorized":False,"last_updated_at":"2026-08-07"},indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
md=f'''# Controlled Apple Fixture Registry

The JSON registry is authoritative. Package IDs use `CAF-YYYY-NNN`: uppercase
Controlled Apple Fixture prefix, assignment year, and unreused zero-padded sequence.

## Current fixtures

| Package ID | Classification | Lifecycle | Fixture generated | Preflight passed | Processing authorized | Apple-produced characterization | Compatibility validation | Support validation | Supported capability | Raw fixture in Git |
|---|---|---|---|---|---|---|---|---|---|---|
| CAF-2026-001 | Controlled Apple-produced test fixture | PREPARATION_COMPLETE | No | No | No | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED | UNAUTHORIZED | Prohibited |

## Validation dimensions and lifecycle

Preparation, Apple-produced characterization, compatibility validation, support
validation, production readiness, and Supported capability are independent.
Closed lifecycle values are: PLANNED, PREPARATION_IN_PROGRESS,
PREPARATION_COMPLETE, FIXTURE_GENERATED, PREFLIGHT_PENDING, PREFLIGHT_FAILED,
READY_FOR_OWNER_VALIDATION_AUTHORIZATION, PROCESSING_AUTHORIZED,
CHARACTERIZATION_IN_PROGRESS, CHARACTERIZATION_COMPLETE, VALIDATION_REJECTED,
ARCHIVED, RETIRED, DESTROYED.

## Restrictions and next action

Raw fixture bytes, sensitive device/account identifiers, secrets, and protected
storage mappings are prohibited from Git. CAF-2026-001 has not been generated;
no backup has been opened or processed. Owner follows OWNER-001 and SOP-001 to
create the fixture, then separately authorizes processing by exact package ID.

Logical digest: `{registry['logical_digest']}` (`SHA-256`, canonical profile v1).
'''
(ops/"FIXTURE_REGISTRY.md").write_text(md,encoding="utf-8",newline="\n")
