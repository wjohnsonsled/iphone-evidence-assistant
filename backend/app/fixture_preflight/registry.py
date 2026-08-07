"""Deterministic, data-only controlled Apple fixture registry validation."""
from __future__ import annotations
import hashlib, json, re
from dataclasses import dataclass
from enum import Enum
from typing import Any

ID_PATTERN=re.compile(r"^CAF-[0-9]{4}-[0-9]{3}$")
LIFECYCLE=frozenset({"PLANNED","PREPARATION_IN_PROGRESS","PREPARATION_COMPLETE","FIXTURE_GENERATED","PREFLIGHT_PENDING","PREFLIGHT_FAILED","READY_FOR_OWNER_VALIDATION_AUTHORIZATION","PROCESSING_AUTHORIZED","CHARACTERIZATION_IN_PROGRESS","CHARACTERIZATION_COMPLETE","VALIDATION_REJECTED","ARCHIVED","RETIRED","DESTROYED"})
REQUIRED_DIMENSIONS=frozenset({"preparation_status","apple_produced_characterization_status","compatibility_validation_status","support_validation_status","production_readiness_status","supported_capability_status"})
REQUIRED_REFS=frozenset({"owner_checklist_reference","sop_reference","package_manifest_reference","ground_truth_reference","custody_record_reference","minimization_record_reference","retention_destruction_record_reference","validation_matrix_reference"})
_ABS=re.compile(r"^(?:[A-Za-z]:[\\/]|/|\\\\)")
_UDID=re.compile(r"(?i)^[0-9a-f]{40}$|^[0-9a-f]{8}-[0-9a-f]{16}$")

class RegistryOutcome(str,Enum): VALID="VALID"; INVALID="INVALID"
@dataclass(frozen=True,slots=True)
class RegistryValidation:
    outcome: RegistryOutcome
    observations: tuple[str,...]

def canonical_registry_payload(registry:dict[str,Any])->bytes:
    payload={k:v for k,v in registry.items() if k!="logical_digest"}
    return json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def registry_digest(registry:dict[str,Any])->str:
    return hashlib.sha256(canonical_registry_payload(registry)).hexdigest()

def validate_registry(registry:dict[str,Any])->RegistryValidation:
    errors=[]
    for key in ("registry_id","registry_version","registry_classification","logical_digest_algorithm","logical_digest_canonicalization_profile","logical_digest_canonicalization_version","logical_digest","fixtures","limitations"):
        if key not in registry: errors.append(f"missing_registry_field:{key}")
    if registry.get("registry_id")!="controlled-apple-fixture-registry" or registry.get("registry_version")!="1": errors.append("registry_profile_invalid")
    if registry.get("logical_digest_algorithm")!="SHA-256": errors.append("registry_digest_algorithm_invalid")
    if registry.get("logical_digest")!=registry_digest(registry): errors.append("registry_digest_invalid")
    fixtures=registry.get("fixtures",[])
    ids=[x.get("package_id") for x in fixtures if isinstance(x,dict)]
    if len(ids)!=len(set(ids)): errors.append("duplicate_package_id")
    for item in fixtures:
        pid=item.get("package_id","")
        if not ID_PATTERN.fullmatch(pid): errors.append(f"package_id_invalid:{pid}")
        if item.get("lifecycle_status") not in LIFECYCLE: errors.append(f"lifecycle_invalid:{pid}")
        for key in REQUIRED_DIMENSIONS:
            if key not in item: errors.append(f"missing_status_dimension:{pid}:{key}")
        for key in REQUIRED_REFS:
            value=item.get(key,"")
            if not value: errors.append(f"missing_reference:{pid}:{key}")
            elif _ABS.match(value): errors.append(f"absolute_reference:{pid}:{key}")
        if item.get("fixture_generated") is False and item.get("lifecycle_status") not in {"PLANNED","PREPARATION_IN_PROGRESS","PREPARATION_COMPLETE"}: errors.append(f"generation_state_impossible:{pid}")
        if item.get("fixture_generated") is True and (not item.get("generation_record_reference") or not item.get("source_registration_reference")): errors.append(f"generated_fixture_records_missing:{pid}")
        if item.get("permitted_processing_status")=="AUTHORIZED" and item.get("lifecycle_status") not in {"PROCESSING_AUTHORIZED","CHARACTERIZATION_IN_PROGRESS","CHARACTERIZATION_COMPLETE"}: errors.append(f"processing_without_readiness:{pid}")
        if item.get("permitted_processing_status")=="AUTHORIZED" and (item.get("preflight_passed") is not True or not item.get("processing_authorization_reference")): errors.append(f"processing_without_preflight_authorization:{pid}")
        if item.get("supported_capability_status")!="UNAUTHORIZED" and not item.get("support_promotion_decision_id"): errors.append(f"support_without_promotion:{pid}")
        if item.get("source_control_policy")!="RAW_FIXTURE_PROHIBITED": errors.append(f"raw_fixture_policy_invalid:{pid}")
        if item.get("retirement_status") not in {"ACTIVE","RETIRED","DESTROYED"}: errors.append(f"retirement_status_invalid:{pid}")
        if item.get("retirement_status")!="ACTIVE" and item.get("package_id_reusable") is not False: errors.append(f"retired_id_reuse_possible:{pid}")
        serialized=json.dumps(item,sort_keys=True)
        if any(_UDID.fullmatch(str(v)) for v in item.values() if isinstance(v,str)): errors.append(f"sensitive_identifier:{pid}")
        if any(key.lower() in {"udid","serial_number","phone_number","account_name","password","secret","raw_fixture_path","backup_path"} for key in item): errors.append(f"prohibited_registry_field:{pid}")
        if re.search(r"(?i)(Manifest\.db|Info\.plist|[A-Za-z]:\\|/Users/|backup[/\\])",serialized): errors.append(f"raw_backup_reference:{pid}")
    return RegistryValidation(RegistryOutcome.INVALID if errors else RegistryOutcome.VALID,tuple(sorted(set(errors))))

def validate_current_pointer(pointer:dict[str,Any],registry:dict[str,Any])->RegistryValidation:
    ids={x.get("package_id") for x in registry.get("fixtures",[])}; errors=[]
    if pointer.get("package_id") not in ids: errors.append("current_fixture_unknown")
    if pointer.get("processing_authorized") is not False: errors.append("current_fixture_authorization_invalid")
    if _ABS.match(str(pointer.get("registry_reference",""))): errors.append("current_fixture_absolute_reference")
    return RegistryValidation(RegistryOutcome.INVALID if errors else RegistryOutcome.VALID,tuple(errors))

def validate_markdown(markdown:str,registry:dict[str,Any])->RegistryValidation:
    errors=[]
    for item in registry.get("fixtures",[]):
        for expected in (item["package_id"],item["lifecycle_status"],item["supported_capability_status"]):
            if expected not in markdown: errors.append(f"markdown_registry_mismatch:{item['package_id']}:{expected}")
    return RegistryValidation(RegistryOutcome.INVALID if errors else RegistryOutcome.VALID,tuple(errors))
