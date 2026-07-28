from datetime import date,datetime,timezone
from uuid import UUID
from app.evidence_core.processing_coverage import *
from app.evidence_core.processing_run import ProcessingRun
from app.integrity.domain import IntegrityState,ProvenanceValidationReport,register_evidence
from app.integrity.parser_contract import ControlledParseContext,ParserRegistryState,ParserResult
from app.integrity.services import AppendOnlyAuditService
from app.processing import *
from app.support import ApprovedParserEntry,CurrentSupportStatus,ParserDisposition,SupportedParserRegistry,create_supported_registry
from app.support.domain import ProcessingResultStatus
def u(n):return UUID(f"11100000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
class ZeroParser:
 parser_id="synthetic.parser";parser_version="1";artifact_family="synthetic";registry_state=ParserRegistryState.CANDIDATE
 def declared_schema_profiles(self):return ("schema-v1",)
 def _result(self):return ParserResult(True,0,0,0,0,0,0,0,True,(),(),("Synthetic.",),(),())
 def validate(self,c):return self._result()
 def parse(self,c):return self._result()
 def report_coverage(self,c):return self._result()
 def report_limitations(self,c):return ("Synthetic.",)
 def self_test(self):return self._result()
def registry():
 entry=ApprovedParserEntry("SYN","synthetic","synthetic.parser","1",("schema-v1",),"DEC-SYN","QMS-SYN",("AC-SYN",),date(2026,1,1),CurrentSupportStatus.SUPPORTED)
 r=SupportedParserRegistry("synthetic",(entry,),instance_id=u(1))
 return r,r.authorize(artifact_id="SYN",parser_id="synthetic.parser",parser_version="1",schema_profile="schema-v1",disposition=ParserDisposition.APPROVED,on_date=date(2026,7,28))
def test_candidate_pipeline_preserves_identity_zero_coverage_audit_and_prior_history():
 inputs=RequestInputs(u(2),u(3),u(4),u(5),"synthetic.parser","1","contract-v1","synthetic","schema-v1","process-v1","1","parse","a"*64,"AUTH")
 repo=InMemoryAtomicRequestRepository();idem=IdempotencyService(repo);claim=idem.submit(inputs,now=NOW);attempt=idem.start(claim.request,now=NOW)
 run=ProcessingRun(attempt.run_id,u(2),u(3),u(4),"synthetic",NOW,u(6),u(7),u(8),1);life=ProcessingRunLifecycle(run,occurred_at=NOW);life.transition(RunState.AUTHORIZED,occurred_at=NOW,reason_code="authorized");life.transition(RunState.RUNNING,occurred_at=NOW,reason_code="started")
 r,auth=registry();outcome=SupportedParserExecutor(r).execute(parser=ZeroParser(),context=ControlledParseContext("copy","schema-v1",IntegrityState.VERIFIED,ProvenanceValidationReport(True)),authorization=auth)
 assert outcome.status is ProcessingResultStatus.SUPPORTED_NO_RECORDS
 life.transition(RunState.COMPLETED_ZERO_RECORDS,occurred_at=NOW,reason_code="zero");finished=idem.finish(claim.request,attempt,status=RequestStatus.COMPLETED)
 coverage=ProcessingCoverageObservation(u(9),CoverageStatus.COMPLETE_ZERO_RECORDS,AuthorizationState.AUTHORIZED,ExecutionState.COMPLETED,attempt.run_id,u(5),None,None,"contract-v1","process-v1",NOW,count(0),count(0),count(0),count(0),count(0),count(0),ReconciliationStatus.RECONCILED,"v1",(),None,None,"DEV-1110",("Synthetic.",))
 assert aggregate_coverage(attempt.run_id,(coverage,)).emitted.value==0
 assert aggregate_failures(attempt.run_id,(),()).issue_ids==()
 evidence=register_evidence(tenant_id=u(2),case_id=u(3),evidence_source_id=u(4),evidence_kind="SOURCE",source_type="SYNTHETIC",source_locator="synthetic",logical_identifier="synthetic",intake_method="SYNTHETIC",registered_at=NOW,registered_by_actor_id=u(6));audit=AppendOnlyAuditService();rec=PipelineAuditRecorder(audit);rec.started(evidence,actor_id=u(6),correlation_id=u(7));rec.completed(evidence,actor_id=u(6),correlation_id=u(7),zero_records=True)
 assert finished.run_id==attempt.run_id and [e.result for e in audit.events]==["STARTED","COMPLETED_ZERO_RECORDS"]
 assert idem.submit(inputs,now=NOW).code=="DUPLICATE_REQUEST_COMPLETED"
def test_production_empty_registry_denies_before_parser_execution_and_stores_nothing():
 _,auth=registry();parser=ZeroParser();parser.parse=lambda c:(_ for _ in ()).throw(AssertionError("must not execute"))
 outcome=SupportedParserExecutor(create_supported_registry()).execute(parser=parser,context=ControlledParseContext("copy","schema-v1",IntegrityState.VERIFIED,ProvenanceValidationReport(True)),authorization=auth)
 assert outcome.failure_codes==("registry_authorization_invalid",)
