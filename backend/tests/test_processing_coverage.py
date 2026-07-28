from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.evidence_core.processing_coverage import *
def u(n):return UUID(f"48000000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def base(**x):
 d=dict(status=CoverageStatus.COMPLETE_WITH_RECORDS,authorization_state=AuthorizationState.AUTHORIZED,execution_state=ExecutionState.COMPLETED,processing_run_id=u(1),source_artifact_id=u(2),source_locator_id=None,parser_identity_id=None,parser_contract_version=None,processing_profile_reference="synthetic-v1",observed_at=NOW,examined=count(1),emitted=count(1),excluded=count(0),rejected=count(0),failed=count(0),indeterminate=count(0),reconciliation_status=ReconciliationStatus.RECONCILED,reconciliation_profile_reference="one-to-one-v1",omissions=(),reason_code=None,description=None,governing_reference="DEV-0408",limitations=("Processing facts only.",),resource_limit=None);return d|x
def test_vocabularies_complete():
 assert len(CoverageStatus)==13 and len(AuthorizationState)==4 and len(ExecutionState)==6 and len(ReconciliationStatus)==5 and len(OmissionCategory)==12
def test_complete_records_and_zero_are_distinct():
 assert observe_coverage(**base()).status is CoverageStatus.COMPLETE_WITH_RECORDS
 z=observe_coverage(**base(status=CoverageStatus.COMPLETE_ZERO_RECORDS,examined=count(0),emitted=count(0)))
 assert z.emitted.value==0
@pytest.mark.parametrize("change",[{"authorization_state":AuthorizationState.NOT_AUTHORIZED},{"execution_state":ExecutionState.NOT_STARTED},{"emitted":CountObservation(CountStatus.UNKNOWN,None)},{"reconciliation_status":ReconciliationStatus.NOT_RECONCILED},{"status":CoverageStatus.COMPLETE_ZERO_RECORDS}])
def test_invalid_complete_combinations_rejected(change):
 with pytest.raises(ValueError):observe_coverage(**base(**change))
def test_known_zero_unknown_and_failure_unavailable_distinct():
 assert len({count(0),CountObservation(CountStatus.UNKNOWN,None),CountObservation(CountStatus.UNAVAILABLE_DUE_TO_FAILURE,None)})==3
def test_not_authorized_and_source_absent_are_not_zero():
 a=observe_coverage(**base(status=CoverageStatus.NOT_AUTHORIZED,authorization_state=AuthorizationState.NOT_AUTHORIZED,execution_state=ExecutionState.NOT_STARTED,reconciliation_status=ReconciliationStatus.RECONCILIATION_NOT_ATTEMPTED,reason_code="denied",description="Not authorized."))
 s=observe_coverage(**base(status=CoverageStatus.SOURCE_ABSENT,execution_state=ExecutionState.NOT_STARTED,reconciliation_status=ReconciliationStatus.RECONCILIATION_NOT_ATTEMPTED,reason_code="absent",description="Source absent."))
 assert a.status is not s.status
def test_resource_limit_requires_metadata():
 with pytest.raises(ValueError):observe_coverage(**base(status=CoverageStatus.RESOURCE_LIMIT_EXCEEDED,execution_state=ExecutionState.STOPPED,reconciliation_status=ReconciliationStatus.RECONCILIATION_INDETERMINATE,reason_code="limit",description="Limit exceeded."))
def test_partial_cannot_masquerade_as_complete():
 with pytest.raises(ValueError):observe_coverage(**base(status=CoverageStatus.PARTIAL,reason_code="partial",description="Incomplete."))
def test_omission_is_processing_fact_only():
 o=OmissionObservation(u(3),OmissionCategory.SOURCE_ABSENT,"synthetic source","absent","DEV-0408",u(1),u(2),None,False,CountObservation(CountStatus.UNKNOWN,None),("Not device absence.",),NOW)
 assert not {"deletion","spoliation","concealment"} & set(o.__dataclass_fields__)
