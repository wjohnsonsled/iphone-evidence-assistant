from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.fixture_preflight.validator import PreflightOutcome, canonical_digest, validate_preflight

ROOT=Path(__file__).parent/"fixtures"/"controlled_apple_fixture_preparation"
def load(): return (json.loads((ROOT/"example-package-manifest.json").read_text()),json.loads((ROOT/"example-ground-truth.json").read_text()))
def redigest(p,g):
    p["package_digest"]=canonical_digest(p,"package_digest"); g["record_digest"]=canonical_digest(g,"record_digest")

def test_complete_plan_is_deterministic_and_ready_only_for_owner_authorization():
    p,g=load(); first=validate_preflight(p,g); second=validate_preflight(p,g)
    assert first==second
    assert first.outcome is PreflightOutcome.READY_FOR_OWNER_VALIDATION_AUTHORIZATION
    assert canonical_digest(p,"package_digest")==p["package_digest"]

@pytest.mark.parametrize("mutation,code,outcome",[
 (lambda p,g:p.pop("package_id"),"missing_package_field:package_id",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(device_ownership_basis=""),"empty_package_field:device_ownership_basis",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(os_version=""),"empty_package_field:os_version",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(apple_software_version=""),"empty_package_field:apple_software_version",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(encryption_state="ENCRYPTED"),"encrypted_fixture_outside_mvp",PreflightOutcome.REJECTED),
 (lambda p,g:g.update(events=[]),"ground_truth_absent",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(custody_events=[]),"custody_incomplete",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(minimization_attestations=[]),"minimization_incomplete",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(distribution_restriction="PUBLIC"),"distribution_prohibited",PreflightOutcome.REJECTED),
 (lambda p,g:p.update(git_inclusion_requested=True),"git_inclusion_requested",PreflightOutcome.REJECTED),
 (lambda p,g:p.update(controlled_package_location="C:\\fixture"),"absolute_host_path:controlled_package_location",PreflightOutcome.REJECTED),
 (lambda p,g:p.update(backup_creation_end="2026-08-04T09:00:00-04:00"),"backup_timestamps_inconsistent",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(package_digest="0"*64),"package_digest_invalid",PreflightOutcome.NOT_READY),
 (lambda p,g:g.update(record_digest="0"*64),"ground_truth_digest_invalid",PreflightOutcome.NOT_READY),
 (lambda p,g:g["events"].append(deepcopy(g["events"][0])),"duplicate_event_id",PreflightOutcome.NOT_READY),
 (lambda p,g:g["events"][0].update(event_type="HEALTH"),"event_type_unsupported",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(profile_matrix=[]),"profile_matrix_incomplete",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(fixture_classification="CUSTOMER_EVIDENCE"),"fixture_classification_prohibited",PreflightOutcome.REJECTED),
 (lambda p,g:p.update(fixture_classification="REAL_EVIDENCE"),"fixture_classification_prohibited",PreflightOutcome.REJECTED),
 (lambda p,g:p.update(account_control_basis=""),"empty_package_field:account_control_basis",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(retention_classification=""),"empty_package_field:retention_classification",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(destruction_requirement=""),"empty_package_field:destruction_requirement",PreflightOutcome.NOT_READY),
 (lambda p,g:p.update(validation_boundary=""),"validation_boundary_missing",PreflightOutcome.REJECTED),
 (lambda p,g:p.update(operator="password=secret"),"secret_material_detected",PreflightOutcome.REJECTED),
])
def test_fail_closed_matrix(mutation,code,outcome):
    p,g=load(); mutation(p,g)
    if code not in {"package_digest_invalid", "ground_truth_digest_invalid"}:
        redigest(p,g)
    result=validate_preflight(p,g)
    assert result.outcome is outcome and code in result.observations

def test_module_has_no_backup_parser_or_processing_dependency():
    source=(Path(__file__).parents[1]/"app"/"fixture_preflight"/"validator.py").read_text()
    assert "sqlite3" not in source and "app.manifest" not in source and "physical_inventory" not in source
