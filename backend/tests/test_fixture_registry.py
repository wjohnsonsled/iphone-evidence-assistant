from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.fixture_preflight.registry import ID_PATTERN,RegistryOutcome,registry_digest,validate_current_pointer,validate_markdown,validate_registry

ROOT=Path(__file__).parents[2]
def load(): return json.loads((ROOT/"docs/operations/FIXTURE_REGISTRY.json").read_text())
def redigest(value): value["logical_digest"]=registry_digest(value)

def test_caf_2026_001_registry_pointer_markdown_and_digest_are_valid():
    registry=load(); item=registry["fixtures"][0]
    pointer=json.loads((ROOT/"docs/operations/CURRENT_FIXTURE.json").read_text())
    markdown=(ROOT/"docs/operations/FIXTURE_REGISTRY.md").read_text()
    assert validate_registry(registry).outcome is RegistryOutcome.VALID
    assert validate_current_pointer(pointer,registry).outcome is RegistryOutcome.VALID
    assert validate_markdown(markdown,registry).outcome is RegistryOutcome.VALID
    assert item["package_id"]=="CAF-2026-001" and item["lifecycle_status"]=="PREPARATION_COMPLETE"
    assert item["fixture_generated"] is False and item["permitted_processing_status"]=="NOT_AUTHORIZED"
    assert registry_digest(registry)==registry["logical_digest"]

@pytest.mark.parametrize("value",["XYZ-2026-001","CAF-26-001","CAF-2026-1","caf-2026-001","CAF 2026 001"])
def test_invalid_package_identifiers_are_rejected(value): assert not ID_PATTERN.fullmatch(value)
def test_valid_future_sequential_identifier(): assert ID_PATTERN.fullmatch("CAF-2026-002")

@pytest.mark.parametrize("mutation,code",[
 (lambda r:r["fixtures"].append(deepcopy(r["fixtures"][0])),"duplicate_package_id"),
 (lambda r:r["fixtures"][0].pop("compatibility_validation_status"),"missing_status_dimension"),
 (lambda r:r["fixtures"][0].update(lifecycle_status="SUPPORTED"),"lifecycle_invalid"),
 (lambda r:r["fixtures"][0].update(lifecycle_status="FIXTURE_GENERATED",fixture_generated=False),"generation_state_impossible"),
 (lambda r:r["fixtures"][0].update(fixture_generated=True),"generated_fixture_records_missing"),
 (lambda r:r["fixtures"][0].update(permitted_processing_status="AUTHORIZED",lifecycle_status="PROCESSING_AUTHORIZED"),"processing_without_preflight_authorization"),
 (lambda r:r["fixtures"][0].update(supported_capability_status="SUPPORTED"),"support_without_promotion"),
 (lambda r:r["fixtures"][0].update(owner_checklist_reference="C:\\records\\owner.md"),"absolute_reference"),
 (lambda r:r["fixtures"][0].update(udid="a"*40),"prohibited_registry_field"),
 (lambda r:r["fixtures"][0].update(raw_fixture_path="fixture/Manifest.db"),"prohibited_registry_field"),
 (lambda r:r["fixtures"][0].update(retirement_status="RETIRED",package_id_reusable=True),"retired_id_reuse_possible"),
])
def test_registry_fail_closed_matrix(mutation,code):
    value=load(); mutation(value); redigest(value); result=validate_registry(value)
    assert result.outcome is RegistryOutcome.INVALID and any(code in x for x in result.observations)

def test_missing_and_incorrect_digest_fail():
    value=load(); value.pop("logical_digest"); assert validate_registry(value).outcome is RegistryOutcome.INVALID
    value=load(); value["logical_digest"]="0"*64; assert "registry_digest_invalid" in validate_registry(value).observations

def test_markdown_and_pointer_mismatch_fail_closed():
    value=load(); md=(ROOT/"docs/operations/FIXTURE_REGISTRY.md").read_text().replace("CAF-2026-001","CAF-2026-999")
    assert validate_markdown(md,value).outcome is RegistryOutcome.INVALID
    pointer=json.loads((ROOT/"docs/operations/CURRENT_FIXTURE.json").read_text()); pointer["package_id"]="CAF-2026-999"
    assert validate_current_pointer(pointer,value).outcome is RegistryOutcome.INVALID
    pointer["package_id"]="CAF-2026-001"; pointer["processing_authorized"]=True
    assert validate_current_pointer(pointer,value).outcome is RegistryOutcome.INVALID

def test_deterministic_serialization_no_secrets_raw_fixture_or_processing_dependencies():
    first=load(); second=load(); assert registry_digest(first)==registry_digest(second)
    serialized=json.dumps(first).lower(); assert "password" not in serialized and "manifest.db" not in serialized and "backup_path" not in serialized
    source=(ROOT/"backend/app/fixture_preflight/registry.py").read_text()
    assert "sqlite3" not in source and "app.manifest" not in source and "physical_inventory" not in source
