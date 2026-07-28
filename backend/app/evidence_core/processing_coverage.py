"""Processing coverage facts; never device-level or legal conclusions."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

class CoverageStatus(str,Enum):
 COMPLETE_WITH_RECORDS="COMPLETE_WITH_RECORDS"; COMPLETE_ZERO_RECORDS="COMPLETE_ZERO_RECORDS"; NOT_AUTHORIZED="NOT_AUTHORIZED"; NOT_EXECUTED="NOT_EXECUTED"; SOURCE_ABSENT="SOURCE_ABSENT"; UNSUPPORTED="UNSUPPORTED"; INACCESSIBLE="INACCESSIBLE"; EXCLUDED="EXCLUDED"; VALIDATION_FAILED="VALIDATION_FAILED"; RESOURCE_LIMIT_EXCEEDED="RESOURCE_LIMIT_EXCEEDED"; CORRUPTED="CORRUPTED"; FAILED="FAILED"; PARTIAL="PARTIAL"
class AuthorizationState(str,Enum):
 AUTHORIZED="AUTHORIZED"; NOT_AUTHORIZED="NOT_AUTHORIZED"; AUTHORIZATION_UNKNOWN="AUTHORIZATION_UNKNOWN"; NOT_APPLICABLE="NOT_APPLICABLE"
class ExecutionState(str,Enum):
 NOT_STARTED="NOT_STARTED"; STARTED="STARTED"; COMPLETED="COMPLETED"; STOPPED="STOPPED"; FAILED="FAILED"; EXECUTION_UNKNOWN="EXECUTION_UNKNOWN"
class CountStatus(str,Enum):
 KNOWN="KNOWN"; UNKNOWN="UNKNOWN"; NOT_APPLICABLE="NOT_APPLICABLE"; UNAVAILABLE_DUE_TO_FAILURE="UNAVAILABLE_DUE_TO_FAILURE"
class ReconciliationStatus(str,Enum):
 RECONCILED="RECONCILED"; NOT_RECONCILED="NOT_RECONCILED"; RECONCILIATION_NOT_ATTEMPTED="RECONCILIATION_NOT_ATTEMPTED"; RECONCILIATION_NOT_APPLICABLE="RECONCILIATION_NOT_APPLICABLE"; RECONCILIATION_INDETERMINATE="RECONCILIATION_INDETERMINATE"
class OmissionCategory(str,Enum):
 NOT_AUTHORIZED="NOT_AUTHORIZED"; NOT_EXECUTED="NOT_EXECUTED"; SOURCE_ABSENT="SOURCE_ABSENT"; UNSUPPORTED="UNSUPPORTED"; INACCESSIBLE="INACCESSIBLE"; SCOPE_EXCLUDED="SCOPE_EXCLUDED"; POLICY_EXCLUDED="POLICY_EXCLUDED"; VALIDATION_REJECTED="VALIDATION_REJECTED"; RESOURCE_LIMIT="RESOURCE_LIMIT"; PROCESSING_FAILURE="PROCESSING_FAILURE"; PARTIAL_PROCESSING="PARTIAL_PROCESSING"; INDETERMINATE="INDETERMINATE"

@dataclass(frozen=True,slots=True)
class CountObservation:
 status: CountStatus; value: int|None
 def __post_init__(self):
  if (self.status is CountStatus.KNOWN)!=(self.value is not None): raise ValueError("count_status_value_mismatch")
  if self.value is not None and self.value<0: raise ValueError("count_negative")

@dataclass(frozen=True,slots=True)
class ResourceLimitObservation:
 resource_type:str; configured_limit:int; observed_quantity:int|None; enforcement_point:str; failure_code:str; limitations:tuple[str,...]
 def __post_init__(self):
  if self.configured_limit<=0 or not all((self.resource_type,self.enforcement_point,self.failure_code,self.limitations)): raise ValueError("resource_limit_metadata_incomplete")

@dataclass(frozen=True,slots=True)
class OmissionObservation:
 omission_id:UUID; category:OmissionCategory; subject:str; reason_code:str; governing_reference:str
 processing_run_id:UUID; source_artifact_id:UUID; parser_identity_id:UUID|None; intentional:bool
 omitted_count:CountObservation; limitations:tuple[str,...]; observed_at:datetime
 def __post_init__(self):
  if self.omission_id.version!=4 or self.observed_at.tzinfo is None: raise ValueError("omission_identity_invalid")
  if not all((self.subject,self.reason_code,self.governing_reference,self.limitations)): raise ValueError("omission_metadata_incomplete")

@dataclass(frozen=True,slots=True)
class ProcessingCoverageObservation:
 observation_id:UUID; status:CoverageStatus; authorization_state:AuthorizationState; execution_state:ExecutionState
 processing_run_id:UUID; source_artifact_id:UUID; source_locator_id:UUID|None; parser_identity_id:UUID|None
 parser_contract_version:str|None; processing_profile_reference:str; observed_at:datetime
 examined:CountObservation; emitted:CountObservation; excluded:CountObservation; rejected:CountObservation
 failed:CountObservation; indeterminate:CountObservation; reconciliation_status:ReconciliationStatus
 reconciliation_profile_reference:str|None; omissions:tuple[OmissionObservation,...]
 reason_code:str|None; description:str|None; governing_reference:str; limitations:tuple[str,...]
 resource_limit:ResourceLimitObservation|None=None
 def __post_init__(self):
  if self.observation_id.version!=4 or self.observed_at.tzinfo is None: raise ValueError("coverage_identity_invalid")
  if not self.processing_profile_reference or not self.governing_reference or not self.limitations: raise ValueError("coverage_metadata_incomplete")
  complete=self.status in {CoverageStatus.COMPLETE_WITH_RECORDS,CoverageStatus.COMPLETE_ZERO_RECORDS}
  counts=(self.examined,self.emitted,self.excluded,self.rejected,self.failed,self.indeterminate)
  if complete:
   if self.authorization_state is not AuthorizationState.AUTHORIZED or self.execution_state is not ExecutionState.COMPLETED: raise ValueError("complete_requires_authorized_completed_execution")
   if any(c.status is not CountStatus.KNOWN for c in counts) or self.reconciliation_status is not ReconciliationStatus.RECONCILED: raise ValueError("complete_requires_known_reconciled_counts")
   if self.examined.value != sum(c.value for c in counts[1:]): raise ValueError("complete_counts_not_reconciled")
   if (self.status is CoverageStatus.COMPLETE_WITH_RECORDS)!=(self.emitted.value>0): raise ValueError("complete_emission_status_mismatch")
  if self.status is CoverageStatus.NOT_AUTHORIZED and self.authorization_state is not AuthorizationState.NOT_AUTHORIZED: raise ValueError("authorization_status_mismatch")
  if self.status is CoverageStatus.NOT_EXECUTED and self.execution_state is not ExecutionState.NOT_STARTED: raise ValueError("execution_status_mismatch")
  if self.status is CoverageStatus.PARTIAL and self.execution_state is ExecutionState.COMPLETED and self.reconciliation_status is ReconciliationStatus.RECONCILED: raise ValueError("partial_cannot_be_complete_and_reconciled")
  unsuccessful=not complete
  if unsuccessful and not all((self.reason_code,self.description)): raise ValueError("noncomplete_reason_required")
  if (self.status is CoverageStatus.RESOURCE_LIMIT_EXCEEDED)!=(self.resource_limit is not None): raise ValueError("resource_limit_metadata_mismatch")

def count(value:int)->CountObservation:return CountObservation(CountStatus.KNOWN,value)
def observe_coverage(**values:object)->ProcessingCoverageObservation:return ProcessingCoverageObservation(observation_id=uuid4(),**values) # type: ignore[arg-type]
