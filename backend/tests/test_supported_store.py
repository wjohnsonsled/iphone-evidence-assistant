from datetime import date,datetime,timezone
from uuid import UUID
import pytest
from app.evidence_core.processing_coverage import *
from app.evidence_core.supported_store import *
from app.support.domain import ProcessingResultStatus
from app.support.registry import ApprovedParserEntry,CurrentSupportStatus,ParserDisposition,SupportedParserRegistry,create_supported_registry
def u(n):return UUID(f"50000000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def coverage():
 return observe_coverage(status=CoverageStatus.COMPLETE_WITH_RECORDS,authorization_state=AuthorizationState.AUTHORIZED,execution_state=ExecutionState.COMPLETED,processing_run_id=u(5),source_artifact_id=u(4),source_locator_id=u(6),parser_identity_id=u(7),parser_contract_version="v1",processing_profile_reference="synthetic",observed_at=NOW,examined=count(1),emitted=count(1),excluded=count(0),rejected=count(0),failed=count(0),indeterminate=count(0),reconciliation_status=ReconciliationStatus.RECONCILED,reconciliation_profile_reference="one-to-one",omissions=(),reason_code=None,description=None,governing_reference="DEV-0410",limitations=("Synthetic only.",))
def candidate(**x):
 d=dict(candidate_id=u(1),tenant_id=u(2),case_id=u(3),evidence_source_id=u(20),source_artifact_id=u(4),processing_run_id=u(5),parser_identity_id=u(7),parser_id="synthetic.parser",parser_version="1",parser_contract_version="v1",artifact_family="synthetic",schema_profile="synthetic-v1",schema_fingerprint_observation_id=u(8),source_locator_id=u(6),raw_value_observation_id=u(9),normalized_value_observation_id=None,transformation_provenance_complete=True,timestamp_observation_id=None,timestamp_provenance_complete=True,coverage=coverage(),integrity_approval_id=u(10),support_promotion_reference="DEC-SYNTHETIC",limitations=("Synthetic only.",),processing_result=ProcessingResultStatus.SUPPORTED_COMPLETE,disposition=OutputDisposition.APPROVED);return SupportedRecordCandidate(**(d|x))
def registry():
 e=ApprovedParserEntry("SYN","synthetic","synthetic.parser","1",("synthetic-v1",),"DEC-SYNTHETIC","QMS-SYNTHETIC",("AC-SYNTHETIC",),date(2026,1,1),CurrentSupportStatus.SUPPORTED)
 r=SupportedParserRegistry("synthetic-test",(e,),instance_id=u(11))
 p=r.authorize(artifact_id="SYN",parser_id="synthetic.parser",parser_version="1",schema_profile="synthetic-v1",disposition=ParserDisposition.APPROVED,on_date=date(2026,7,28))
 a=AdmissionAuthorization(p,u(2),u(3),u(4),u(5),"supported-record.admit","DEC-SYNTHETIC")
 return r,a
def test_default_empty_registry_denies_and_stays_empty():
 s=SupportedEvidenceStore(create_supported_registry())
 with pytest.raises(AdmissionDenied,match="REGISTRY_EMPTY"):s.admit(candidate(),None,occurred_at=NOW)
 assert s.count==0
def test_isolated_exact_synthetic_authorization_admits():
 r,a=registry();s=SupportedEvidenceStore(r);record=s.admit(candidate(),a,occurred_at=NOW)
 assert s.get(tenant_id=u(2),case_id=u(3),record_id=record.record_id)==record
def test_cross_scope_query_is_non_enumerating():
 r,a=registry();s=SupportedEvidenceStore(r);record=s.admit(candidate(),a,occurred_at=NOW)
 with pytest.raises(AdmissionDenied,match="RESOURCE_NOT_AVAILABLE"):s.get(tenant_id=u(99),case_id=u(3),record_id=record.record_id)
@pytest.mark.parametrize("change,code",[
 ({"disposition":OutputDisposition.CANDIDATE},"CANDIDATE_OUTPUT_PROHIBITED"),
 ({"processing_result":ProcessingResultStatus.FAILED},"PROCESSING_RESULT_NOT_SUPPORTED_SUCCESS"),
 ({"support_promotion_reference":None},"AUTHORIZATION_SCOPE_MISMATCH"),
 ({"raw_value_observation_id":None},"RAW_VALUE_MISSING"),
 ({"limitations":()},"LIMITATIONS_MISSING"),
 ({"unresolved_fatal_issue_ids":(u(30),)},"UNRESOLVED_FATAL_ISSUE")])
def test_fail_closed_admission(change,code):
 r,a=registry();s=SupportedEvidenceStore(r)
 with pytest.raises(AdmissionDenied,match=code):s.admit(candidate(**change),a,occurred_at=NOW)
def test_store_has_no_update_or_delete_api():
 assert not {"update","delete"} & set(dir(SupportedEvidenceStore))
