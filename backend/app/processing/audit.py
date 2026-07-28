"""Pipeline audit adapter over the approved append-only taxonomy."""
from uuid import UUID
from app.integrity.domain import AuditEvent,AuditEventType,EvidenceObject
from app.integrity.services import AppendOnlyAuditService
class PipelineAuditRecorder:
 def __init__(self,audit:AppendOnlyAuditService):self.audit=audit
 def started(self,evidence:EvidenceObject,*,actor_id:UUID,correlation_id:UUID)->AuditEvent:
  return self.audit.append(evidence=evidence,event_type=AuditEventType.PARSER_EXECUTION_STARTED,actor_id=actor_id,result="STARTED",correlation_id=correlation_id)
 def completed(self,evidence:EvidenceObject,*,actor_id:UUID,correlation_id:UUID,zero_records:bool)->AuditEvent:
  return self.audit.append(evidence=evidence,event_type=AuditEventType.PARSER_EXECUTION_COMPLETED,actor_id=actor_id,result="COMPLETED_ZERO_RECORDS" if zero_records else "COMPLETED",correlation_id=correlation_id)
 def failed(self,evidence:EvidenceObject,*,actor_id:UUID,correlation_id:UUID,failure_code:str)->AuditEvent:
  if not failure_code.strip():raise ValueError("pipeline_failure_code_required")
  return self.audit.append(evidence=evidence,event_type=AuditEventType.PARSER_EXECUTION_FAILED,actor_id=actor_id,result="FAILED",correlation_id=correlation_id,failure_code=failure_code.strip())
