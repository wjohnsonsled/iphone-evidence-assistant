"""Validate fixture-plan metadata without accessing a backup or running parsers."""
from __future__ import annotations
import hashlib, json, re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import PurePath
from typing import Any

PACKAGE_FIELDS = frozenset({"package_id","package_version","fixture_classification","owner_authorization","device_ownership_basis","account_control_basis","device_model","os_version","host_os","apple_software_version","backup_type","encryption_state","backup_creation_start","backup_creation_end","timezone_context","operator","backup_root_identity","controlled_package_location","source_hash_observations","controlled_copy_identity","package_digest","ground_truth_record_reference","custody_record_reference","minimization_record","retention_classification","destruction_requirement","distribution_restriction","profile_matrix","limitations","approvals","validation_boundary"})
EVENT_FIELDS = frozenset({"event_id","event_type","action_performed","expected_source_artifact","expected_logical_record","expected_participant","expected_direction","expected_timestamp","timestamp_source","timestamp_precision","expected_content","expected_attachment_identity","execution_status","independent_confirmation_method","known_limitations","validation_disposition"})
EVENT_TYPES = frozenset({"SMS","IMESSAGE","MESSAGE_THREAD","PARTICIPANT","GROUP_CONVERSATION","MESSAGE_ATTACHMENT","INCOMING_CALL","OUTGOING_CALL","MISSED_CALL","CONTACT","BACKUP_METADATA","DEVICE_METADATA"})
REQUIRED_PROFILES = tuple(f"STEP-{n:02d}" for n in range(1,21))
REQUIRED_CUSTODY = frozenset({"PACKAGE_CREATION","BACKUP_COMPLETION","INITIAL_REGISTRATION","SOURCE_HASH","TRANSFER","RECEIPT","CONTROLLED_COPY_CREATION","VERIFICATION","VALIDATION_RUN","TEMPORARY_WORKING_COPY","CLEANUP","ARCHIVE","DESTRUCTION"})
REQUIRED_MINIMIZATION = frozenset({"OWNER_CONTROLLED_TEST_ACCOUNTS","NO_CLIENT_DATA","NO_CONFIDENTIAL_BUSINESS_DATA","NO_REAL_SECRETS","MINIMUM_ARTIFACTS","PRE_BACKUP_REVIEW","PRE_TRANSFER_REVIEW","RESTRICTED_STORAGE"})
_ABS = re.compile(r"^(?:[A-Za-z]:[\\/]|/|\\\\)")
_SECRET = re.compile(r"(?i)(password|api[_-]?key|access[_-]?token|private[_-]?key)\s*[:=]\s*\S+")

class PreflightOutcome(str, Enum):
    READY_FOR_OWNER_VALIDATION_AUTHORIZATION="READY_FOR_OWNER_VALIDATION_AUTHORIZATION"
    NOT_READY="NOT_READY"
    REJECTED="REJECTED"
    INDETERMINATE="INDETERMINATE"

@dataclass(frozen=True, slots=True)
class PreflightResult:
    outcome: PreflightOutcome
    observations: tuple[str,...]
    limitations: tuple[str,...] = ("Readiness does not authorize backup access or processing.","One fixture cannot establish compatibility or support.")

def canonical_digest(value: dict[str,Any], digest_field: str) -> str:
    payload={k:v for k,v in value.items() if k != digest_field}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def _time(value: Any) -> datetime | None:
    try:
        result=datetime.fromisoformat(value)
        return result if result.tzinfo and result.utcoffset() is not None else None
    except (TypeError,ValueError): return None

def validate_preflight(package: dict[str,Any], ground_truth: dict[str,Any]) -> PreflightResult:
    errors=[]; rejected=[]
    missing=sorted(PACKAGE_FIELDS-set(package)); errors += [f"missing_package_field:{x}" for x in missing]
    for key in ("package_id","owner_authorization","device_ownership_basis","account_control_basis","device_model","os_version","host_os","apple_software_version","retention_classification","destruction_requirement","validation_boundary"):
        if key in package and not str(package[key]).strip(): errors.append(f"empty_package_field:{key}")
    if package.get("fixture_classification") != "CONTROLLED_APPLE_PRODUCED_TEST_FIXTURE": rejected.append("fixture_classification_prohibited")
    if package.get("backup_type") != "APPLE_LOCAL_BACKUP": rejected.append("backup_type_prohibited")
    if package.get("encryption_state") != "UNENCRYPTED": rejected.append("encrypted_fixture_outside_mvp")
    if package.get("distribution_restriction") != "RESTRICTED_OUTSIDE_GIT": rejected.append("distribution_prohibited")
    if package.get("git_inclusion_requested") is True: rejected.append("git_inclusion_requested")
    if package.get("validation_boundary") != "OWNER_AUTHORIZATION_REQUIRED_BEFORE_PROCESSING": rejected.append("validation_boundary_missing")
    for key in ("backup_root_identity","controlled_package_location","ground_truth_record_reference","custody_record_reference"):
        if _ABS.match(str(package.get(key,""))): rejected.append(f"absolute_host_path:{key}")
    start,end=_time(package.get("backup_creation_start")),_time(package.get("backup_creation_end"))
    if not start or not end or start > end: errors.append("backup_timestamps_inconsistent")
    if canonical_digest(package,"package_digest") != package.get("package_digest"): errors.append("package_digest_invalid")
    if ground_truth.get("fixture_package_id") != package.get("package_id"): errors.append("ground_truth_package_mismatch")
    events=ground_truth.get("events")
    if not isinstance(events,list) or not events: errors.append("ground_truth_absent"); events=[]
    ids=[]
    for event in events:
        errors += [f"missing_event_field:{x}" for x in sorted(EVENT_FIELDS-set(event))]
        ids.append(event.get("event_id"))
        if event.get("event_type") not in EVENT_TYPES: errors.append("event_type_unsupported")
    if len(ids) != len(set(ids)): errors.append("duplicate_event_id")
    if canonical_digest(ground_truth,"record_digest") != ground_truth.get("record_digest"): errors.append("ground_truth_digest_invalid")
    custody=set(package.get("custody_events",[])); minimization=set(package.get("minimization_attestations",[]))
    if not REQUIRED_CUSTODY <= custody: errors.append("custody_incomplete")
    if not REQUIRED_MINIMIZATION <= minimization: errors.append("minimization_incomplete")
    if not set(REQUIRED_PROFILES) <= set(package.get("profile_matrix",[])): errors.append("profile_matrix_incomplete")
    serialized=json.dumps([package,ground_truth],sort_keys=True,default=str)
    if _SECRET.search(serialized): rejected.append("secret_material_detected")
    if rejected: return PreflightResult(PreflightOutcome.REJECTED,tuple(sorted(set(rejected+errors))))
    if errors: return PreflightResult(PreflightOutcome.NOT_READY,tuple(sorted(set(errors))))
    return PreflightResult(PreflightOutcome.READY_FOR_OWNER_VALIDATION_AUTHORIZATION,("metadata_preflight_complete",))
