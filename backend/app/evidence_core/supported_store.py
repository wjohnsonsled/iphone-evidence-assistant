"""Candidate supported-store admission boundary; default registry admits nothing."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4
from app.evidence_core.processing_coverage import AuthorizationState, CoverageStatus, ExecutionState, ProcessingCoverageObservation, ReconciliationStatus
from app.support.domain import ProcessingResultStatus, SUPPORTED_SUCCESS_STATUSES
from app.support.registry import ParserAuthorization, ParserDisposition, SupportedParserRegistry

class OutputDisposition(str,Enum):
 APPROVED="APPROVED"; CANDIDATE="CANDIDATE"; EXPERIMENTAL="EXPERIMENTAL"; LEGACY="LEGACY"
class AdmissionOutcome(str,Enum):
 ADMITTED="ADMITTED"; DENIED="DENIED"
class AdmissionDenied(PermissionError):
 def __init__(self,code:str):self.code=code;super().__init__(code)
@dataclass(frozen=True,slots=True)
class AdmissionAuthorization:
 parser_authorization:ParserAuthorization; tenant_id:UUID; case_id:UUID
 source_artifact_id:UUID; processing_run_id:UUID; operation:str
 support_promotion_reference:str

@dataclass(frozen=True,slots=True)
class SupportedRecordCandidate:
 candidate_id:UUID; tenant_id:UUID; case_id:UUID; evidence_source_id:UUID
 source_artifact_id:UUID; processing_run_id:UUID; parser_identity_id:UUID
 parser_id:str; parser_version:str; parser_contract_version:str; artifact_family:str
 schema_profile:str; schema_fingerprint_observation_id:UUID|None; source_locator_id:UUID|None
 raw_value_observation_id:UUID|None; normalized_value_observation_id:UUID|None
 transformation_provenance_complete:bool; timestamp_observation_id:UUID|None
 timestamp_provenance_complete:bool; coverage:ProcessingCoverageObservation
 integrity_approval_id:UUID|None; support_promotion_reference:str|None
 limitations:tuple[str,...]; processing_result:ProcessingResultStatus
 disposition:OutputDisposition; unresolved_fatal_issue_ids:tuple[UUID,...]=()

@dataclass(frozen=True,slots=True)
class SupportedNormalizedRecord:
 record_id:UUID; candidate:SupportedRecordCandidate; admitted_at:datetime; admission_decision_id:UUID
 supersedes_record_id:UUID|None=None

@dataclass(frozen=True,slots=True)
class AdmissionDecision:
 decision_id:UUID; outcome:AdmissionOutcome; code:str; occurred_at:datetime
 tenant_id:UUID; case_id:UUID; candidate_id:UUID; admitted_record_id:UUID|None
 limitations:tuple[str,...]

class SupportedEvidenceStore:
 def __init__(self,registry:SupportedParserRegistry):self._registry=registry;self._records:tuple[SupportedNormalizedRecord,...]=();self._decisions:tuple[AdmissionDecision,...]=()
 @property
 def count(self)->int:return len(self._records)
 def admit(self,c:SupportedRecordCandidate,auth:AdmissionAuthorization|None,*,occurred_at:datetime)->SupportedNormalizedRecord:
  code=self._validate(c,auth)
  if code:self._deny(c,code,occurred_at)
  decision_id,record_id=uuid4(),uuid4()
  record=SupportedNormalizedRecord(record_id,c,occurred_at,decision_id)
  self._records=(*self._records,record)
  self._decisions=(*self._decisions,AdmissionDecision(decision_id,AdmissionOutcome.ADMITTED,"ADMITTED",occurred_at,c.tenant_id,c.case_id,c.candidate_id,record_id,c.limitations))
  return record
 def _validate(self,c,auth):
  if not self._registry.entries:return "REGISTRY_EMPTY"
  if c.disposition is not OutputDisposition.APPROVED:return f"{c.disposition.value}_OUTPUT_PROHIBITED"
  if auth is None:return "AUTHORIZATION_MISSING"
  if not self._registry.issued(auth.parser_authorization):return "AUTHORIZATION_SCOPE_MISMATCH"
  if (auth.tenant_id,auth.case_id,auth.source_artifact_id,auth.processing_run_id,auth.operation,auth.support_promotion_reference)!=(c.tenant_id,c.case_id,c.source_artifact_id,c.processing_run_id,"supported-record.admit",c.support_promotion_reference):return "AUTHORIZATION_SCOPE_MISMATCH"
  e=auth.parser_authorization.entry
  if (c.parser_id,c.parser_version)!=(e.parser_id,e.parser_version):return "PARSER_IDENTITY_MISMATCH"
  if c.artifact_family!=e.artifact_family or c.schema_profile!=auth.parser_authorization.schema_profile:return "AUTHORIZATION_SCOPE_MISMATCH"
  if c.processing_result not in SUPPORTED_SUCCESS_STATUSES:return "PROCESSING_RESULT_NOT_SUPPORTED_SUCCESS"
  cov=c.coverage
  if cov.status not in {CoverageStatus.COMPLETE_WITH_RECORDS,CoverageStatus.COMPLETE_ZERO_RECORDS}:return "COVERAGE_NOT_COMPLETE"
  if cov.reconciliation_status is not ReconciliationStatus.RECONCILED:return "COVERAGE_NOT_RECONCILED"
  if cov.authorization_state is not AuthorizationState.AUTHORIZED or cov.execution_state is not ExecutionState.COMPLETED:return "COVERAGE_NOT_COMPLETE"
  if (cov.processing_run_id,cov.source_artifact_id)!=(c.processing_run_id,c.source_artifact_id):return "SOURCE_SCOPE_MISMATCH"
  if c.unresolved_fatal_issue_ids:return "UNRESOLVED_FATAL_ISSUE"
  for value,code in ((c.integrity_approval_id,"INTEGRITY_APPROVAL_MISSING"),(c.support_promotion_reference,"SUPPORT_PROMOTION_MISSING"),(c.schema_fingerprint_observation_id,"SCHEMA_FINGERPRINT_MISSING"),(c.source_locator_id,"SOURCE_LOCATOR_MISSING"),(c.raw_value_observation_id,"RAW_VALUE_MISSING")):
   if not value:return code
  if c.normalized_value_observation_id and not c.transformation_provenance_complete:return "PROVENANCE_INCOMPLETE"
  if c.timestamp_observation_id and not c.timestamp_provenance_complete:return "TIMESTAMP_PROVENANCE_INCOMPLETE"
  if not c.limitations:return "LIMITATIONS_MISSING"
  return None
 def _deny(self,c,code,at):
  self._decisions=(*self._decisions,AdmissionDecision(uuid4(),AdmissionOutcome.DENIED,code,at,c.tenant_id,c.case_id,c.candidate_id,None,c.limitations))
  raise AdmissionDenied(code)
 def get(self,*,tenant_id:UUID,case_id:UUID,record_id:UUID)->SupportedNormalizedRecord:
  match=next((r for r in self._records if r.candidate.tenant_id==tenant_id and r.candidate.case_id==case_id and r.record_id==record_id),None)
  if match is None:raise AdmissionDenied("RESOURCE_NOT_AVAILABLE")
  return match
 def supersede(self,*,old_record_id:UUID,new_record:SupportedNormalizedRecord,reason:str)->SupportedNormalizedRecord:
  if old_record_id==new_record.record_id or not reason.strip():raise AdmissionDenied("SUPERSESSION_INVALID")
  seen={new_record.record_id};cursor=old_record_id
  while cursor:
   if cursor in seen:raise AdmissionDenied("SUPERSESSION_CYCLE")
   seen.add(cursor);item=next((r for r in self._records if r.record_id==cursor),None);cursor=item.supersedes_record_id if item else None
  corrected=SupportedNormalizedRecord(new_record.record_id,new_record.candidate,new_record.admitted_at,new_record.admission_decision_id,old_record_id)
  self._records=tuple(corrected if r.record_id==new_record.record_id else r for r in self._records);return corrected
