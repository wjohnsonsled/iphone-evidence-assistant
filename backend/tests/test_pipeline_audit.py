from datetime import datetime,timezone
from uuid import uuid4
import pytest
from app.integrity.domain import AuditEventType,register_evidence
from app.integrity.services import AppendOnlyAuditService
from app.processing.audit import PipelineAuditRecorder
def evidence():
 return register_evidence(tenant_id=uuid4(),case_id=uuid4(),evidence_source_id=uuid4(),evidence_kind="SOURCE",source_type="SYNTHETIC",source_locator="synthetic",logical_identifier="synthetic",intake_method="SYNTHETIC_TEST",registered_at=datetime(2026,7,28,tzinfo=timezone.utc),registered_by_actor_id=uuid4())
def test_pipeline_events_are_closed_scoped_ordered_and_failure_aware():
 item,actor,correlation=evidence(),uuid4(),uuid4();audit=AppendOnlyAuditService();recorder=PipelineAuditRecorder(audit)
 recorder.started(item,actor_id=actor,correlation_id=correlation)
 recorder.completed(item,actor_id=actor,correlation_id=correlation,zero_records=True)
 recorder.failed(item,actor_id=actor,correlation_id=correlation,failure_code="synthetic_failure")
 assert [e.event_type for e in audit.events]==[AuditEventType.PARSER_EXECUTION_STARTED,AuditEventType.PARSER_EXECUTION_COMPLETED,AuditEventType.PARSER_EXECUTION_FAILED]
 assert [e.sequence for e in audit.events]==[1,2,3] and audit.events[1].result=="COMPLETED_ZERO_RECORDS"
 assert audit.events[2].failure_code=="synthetic_failure" and all(e.evidence_uuid==item.evidence_uuid for e in audit.events)
def test_blank_failure_code_fails_before_append():
 audit=AppendOnlyAuditService()
 with pytest.raises(ValueError,match="required"):PipelineAuditRecorder(audit).failed(evidence(),actor_id=uuid4(),correlation_id=uuid4(),failure_code=" ")
 assert audit.events==()
