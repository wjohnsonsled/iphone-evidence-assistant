"""Versioned idempotency and immutable forensic rerun contracts."""
from __future__ import annotations
import hashlib,json,threading
from dataclasses import asdict,dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID,uuid4

PROFILE_ID="processing-request-canonical-json-sha256";PROFILE_VERSION="1"
class RequestStatus(str,Enum):
 CLAIMED="CLAIMED";ACCEPTED="ACCEPTED";EXECUTION_PENDING="EXECUTION_PENDING";EXECUTION_STARTED="EXECUTION_STARTED";COMPLETED="COMPLETED";FAILED_BEFORE_EXECUTION="FAILED_BEFORE_EXECUTION";CANCELLED_BEFORE_EXECUTION="CANCELLED_BEFORE_EXECUTION";EXPIRED="EXPIRED";REJECTED="REJECTED";FAILED="FAILED";PARTIAL="PARTIAL";CANCELLED="CANCELLED"
class RelationshipType(str,Enum):
 RETRY_OF="RETRY_OF";RERUN_OF="RERUN_OF";SUPERSEDES_PROCESSING_RESULT="SUPERSEDES_PROCESSING_RESULT";REPLACES_INVALID_ATTEMPT="REPLACES_INVALID_ATTEMPT";CONTINUES_AFTER_INTERRUPTION="CONTINUES_AFTER_INTERRUPTION";REPROCESSING_WITH_NEW_PROFILE="REPROCESSING_WITH_NEW_PROFILE";REPROCESSING_WITH_NEW_PARSER_VERSION="REPROCESSING_WITH_NEW_PARSER_VERSION";REPROCESSING_WITH_CHANGED_INPUTS="REPROCESSING_WITH_CHANGED_INPUTS"
@dataclass(frozen=True,slots=True)
class RequestInputs:
 tenant_id:UUID;case_id:UUID;evidence_source_id:UUID;source_artifact_id:UUID;parser_id:str;parser_version:str;parser_contract_version:str;artifact_family:str;schema_profile_id:str;processing_profile_id:str;processing_profile_version:str;operation:str;controlled_input_digest:str;authorization_reference:str;idempotency_profile_id:str=PROFILE_ID;idempotency_profile_version:str=PROFILE_VERSION
 def __post_init__(self):
  strings=(self.parser_id,self.parser_version,self.parser_contract_version,self.artifact_family,self.schema_profile_id,self.processing_profile_id,self.processing_profile_version,self.operation,self.authorization_reference,self.idempotency_profile_id,self.idempotency_profile_version)
  if any(not value.strip() for value in strings):raise ValueError("idempotency_input_required")
  if len(self.controlled_input_digest)!=64 or any(c not in "0123456789abcdef" for c in self.controlled_input_digest):raise ValueError("controlled_input_digest_invalid")
@dataclass(frozen=True,slots=True)
class KeyObservation:
 profile_id:str;profile_version:str;canonical_input_description:str;canonical_input_digest:str;algorithm_id:str;algorithm_version:str;idempotency_key:str;generated_at:datetime;limitations:tuple[str,...]
@dataclass(frozen=True,slots=True)
class LogicalRequest:
 request_id:UUID;inputs:RequestInputs;key:KeyObservation;created_at:datetime;status:RequestStatus;run_ids:tuple[UUID,...];limitations:tuple[str,...]
@dataclass(frozen=True,slots=True)
class ExecutionAttempt:
 run_id:UUID;request_id:UUID;attempt_number:int;started_at:datetime;status:RequestStatus;prior_run_id:UUID|None;reason_code:str|None;limitations:tuple[str,...]
@dataclass(frozen=True,slots=True)
class RunRelationship:
 relationship_id:UUID;prior_run_id:UUID;current_run_id:UUID;relationship_type:RelationshipType;reason_code:str;explanation:str;authorization_reference:str;occurred_at:datetime;limitations:tuple[str,...]
@dataclass(frozen=True,slots=True)
class ClaimResult:
 code:str;request:LogicalRequest;run:ExecutionAttempt|None
def generate_key(inputs:RequestInputs,*,generated_at:datetime)->KeyObservation:
 if generated_at.tzinfo is None:raise ValueError("idempotency_time_required")
 payload={k:(str(v) if isinstance(v,UUID) else v) for k,v in asdict(inputs).items()}
 encoded=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
 digest=hashlib.sha256(encoded).hexdigest()
 return KeyObservation(inputs.idempotency_profile_id,inputs.idempotency_profile_version,"RequestInputs fields in sorted canonical JSON",digest,"SHA-256","1",digest,generated_at,("Key does not imply parser or artifact support.",))
class InMemoryAtomicRequestRepository:
 """Synthetic adapter; atomic claim models required relational uniqueness."""
 def __init__(self):self._lock=threading.Lock();self._requests={};self._attempts={};self._relationships=();self._history=()
 def claim(self,inputs,now):
  key=generate_key(inputs,generated_at=now)
  with self._lock:
   existing=self._requests.get(key.idempotency_key)
   if existing and existing.status is not RequestStatus.EXPIRED:return False,existing
   request=LogicalRequest(uuid4(),inputs,key,now,RequestStatus.ACCEPTED,(),("Candidate infrastructure only.",))
   if existing:self._history=(*self._history,existing)
   self._requests[key.idempotency_key]=request;return True,request
 def replace(self,request):
  with self._lock:self._requests[request.key.idempotency_key]=request
 def attempts(self,request_id):return tuple(a for a in self._attempts.values() if a.request_id==request_id)
 def add_attempt(self,attempt):
  with self._lock:
   if attempt.run_id in self._attempts:raise ValueError("run_identity_reused")
   self._attempts[attempt.run_id]=attempt
 def add_relationship(self,relationship):
  if relationship.prior_run_id==relationship.current_run_id:raise ValueError("relationship_cycle")
  self._relationships=(*self._relationships,relationship)
 @property
 def relationships(self):return self._relationships
class IdempotencyService:
 def __init__(self,repository):self.repository=repository
 def submit(self,inputs,*,now):
  created,request=self.repository.claim(inputs,now)
  if created:return ClaimResult("IDEMPOTENCY_CLAIM_CREATED",request,None)
  attempts=self.repository.attempts(request.request_id);run=attempts[-1] if attempts else None
  code="DUPLICATE_REQUEST_PENDING" if run is None else ("DUPLICATE_REQUEST_RUNNING" if run.status is RequestStatus.EXECUTION_STARTED else ("DUPLICATE_REQUEST_COMPLETED" if run.status is RequestStatus.COMPLETED else "EXPLICIT_RETRY_REQUIRED"))
  return ClaimResult(code,request,run)
 def start(self,request,*,now,prior=None,relationship=None,reason=None):
  if prior and (relationship is None or not reason):raise ValueError("prior_run_relationship_required")
  attempts=self.repository.attempts(request.request_id)
  run=ExecutionAttempt(uuid4(),request.request_id,len(attempts)+1,now,RequestStatus.EXECUTION_STARTED,prior.run_id if prior else None,reason,("No checkpoint resumption or output merging.",))
  self.repository.add_attempt(run)
  updated=LogicalRequest(request.request_id,request.inputs,request.key,request.created_at,RequestStatus.EXECUTION_STARTED,(*request.run_ids,run.run_id),request.limitations);self.repository.replace(updated)
  if prior:
   self.repository.add_relationship(RunRelationship(uuid4(),prior.run_id,run.run_id,relationship,reason,"Explicit forensic retry or rerun.",request.inputs.authorization_reference,now,("Prior outcome remains immutable.",)))
  return run
 def finish(self,request,run,*,status):
  if status not in {RequestStatus.COMPLETED,RequestStatus.FAILED,RequestStatus.PARTIAL,RequestStatus.CANCELLED}:raise ValueError("terminal_status_required")
  finished=ExecutionAttempt(run.run_id,run.request_id,run.attempt_number,run.started_at,status,run.prior_run_id,run.reason_code,run.limitations);self.repository._attempts[run.run_id]=finished
  self.repository.replace(LogicalRequest(request.request_id,request.inputs,request.key,request.created_at,status,request.run_ids,request.limitations));return finished
 def retry(self,request,prior,*,now,reason):
  if prior.status not in {RequestStatus.FAILED,RequestStatus.PARTIAL,RequestStatus.CANCELLED}:raise ValueError("retry_not_authorized")
  return self.start(request,now=now,prior=prior,relationship=RelationshipType.RETRY_OF,reason=reason)
 def rerun(self,request,prior,*,now,reason):
  if prior.status is not RequestStatus.COMPLETED:raise ValueError("rerun_not_authorized")
  return self.start(request,now=now,prior=prior,relationship=RelationshipType.RERUN_OF,reason=reason)
 def expire(self,request):
  expired=LogicalRequest(request.request_id,request.inputs,request.key,request.created_at,RequestStatus.EXPIRED,request.run_ids,request.limitations);self.repository.replace(expired);return expired
