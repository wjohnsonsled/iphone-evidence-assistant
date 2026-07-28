from dataclasses import replace
from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.evidence_core.processing_coverage import *
from app.processing.coverage_aggregation import aggregate_coverage
def u(n):return UUID(f"11050000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def observation(identity,status=CoverageStatus.COMPLETE_WITH_RECORDS):
 return ProcessingCoverageObservation(u(identity),status,AuthorizationState.AUTHORIZED,ExecutionState.COMPLETED,u(1),u(identity+20),None,u(3),"v1","synthetic",NOW,count(1),count(1),count(0),count(0),count(0),count(0),ReconciliationStatus.RECONCILED,"v1",(),None,None,"DEV-1105",("Synthetic.",))
def test_aggregate_is_deterministic_and_factual_only():
 result=aggregate_coverage(u(1),(observation(2),observation(1)))
 assert result.observation_ids==(u(1),u(2)) and result.examined.value==2 and result.emitted.value==2
 assert result.statuses==((CoverageStatus.COMPLETE_WITH_RECORDS,2),)
 assert not {"coverage_percentage","complete_device","conclusion"} & set(result.__dataclass_fields__)
def test_unknown_count_propagates_without_guessing():
 item=replace(observation(1),status=CoverageStatus.FAILED,execution_state=ExecutionState.FAILED,examined=CountObservation(CountStatus.UNAVAILABLE_DUE_TO_FAILURE,None),emitted=CountObservation(CountStatus.UNAVAILABLE_DUE_TO_FAILURE,None),excluded=CountObservation(CountStatus.UNAVAILABLE_DUE_TO_FAILURE,None),rejected=CountObservation(CountStatus.UNAVAILABLE_DUE_TO_FAILURE,None),failed=CountObservation(CountStatus.UNAVAILABLE_DUE_TO_FAILURE,None),indeterminate=CountObservation(CountStatus.UNAVAILABLE_DUE_TO_FAILURE,None),reconciliation_status=ReconciliationStatus.NOT_RECONCILED,reconciliation_profile_reference=None,reason_code="failed",description="Synthetic failure.")
 assert aggregate_coverage(u(1),(item,)).examined.status is CountStatus.UNKNOWN
def test_cross_run_and_duplicates_fail_closed():
 item=observation(1)
 with pytest.raises(ValueError,match="duplicate"):aggregate_coverage(u(1),(item,item))
 with pytest.raises(ValueError,match="scope"):aggregate_coverage(u(99),(item,))
