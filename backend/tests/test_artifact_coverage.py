from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.coverage.artifact_coverage import build_artifact_coverage
from app.evidence_core.processing_coverage import *
from app.evidence_core.source_inventory import SourceInventory,SourceInventoryItem
def u(n):return UUID(f"04520000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
INV=SourceInventory(u(1),u(2),u(3),u(4),u(5),NOW,(SourceInventoryItem(u(6),u(7),"messages",()),))
def coverage(status=CoverageStatus.COMPLETE_ZERO_RECORDS,run=u(5),artifact=u(6)):
 complete=status is CoverageStatus.COMPLETE_ZERO_RECORDS
 return ProcessingCoverageObservation(u(8),status,AuthorizationState.AUTHORIZED if complete else AuthorizationState.NOT_APPLICABLE,ExecutionState.COMPLETED if complete else ExecutionState.NOT_STARTED,run,artifact,None,None,None,"synthetic",NOW,count(0) if complete else CountObservation(CountStatus.UNKNOWN,None),count(0) if complete else CountObservation(CountStatus.UNKNOWN,None),count(0) if complete else CountObservation(CountStatus.UNKNOWN,None),count(0) if complete else CountObservation(CountStatus.UNKNOWN,None),count(0) if complete else CountObservation(CountStatus.UNKNOWN,None),count(0) if complete else CountObservation(CountStatus.UNKNOWN,None),ReconciliationStatus.RECONCILED if complete else ReconciliationStatus.RECONCILIATION_NOT_ATTEMPTED,"v1" if complete else None,(),"unsupported" if not complete else None,"Synthetic." if not complete else None,"DEV-0452",("Synthetic.",))
def test_exact_measurable_set_and_zero_are_preserved():
 report=build_artifact_coverage(inventory=INV,observations=(coverage(),),measurable_set_name="registered artifacts")
 assert report.denominator==1 and report.entries[0].status is CoverageStatus.COMPLETE_ZERO_RECORDS
 assert report.status_counts==((CoverageStatus.COMPLETE_ZERO_RECORDS,1),)
 assert not {"percentage","device_complete","evidence_gap"} & set(report.__dataclass_fields__)
def test_unsupported_is_not_zero():
 report=build_artifact_coverage(inventory=INV,observations=(coverage(CoverageStatus.UNSUPPORTED),),measurable_set_name="registered artifacts")
 assert report.entries[0].status is CoverageStatus.UNSUPPORTED
def test_missing_duplicate_cross_run_and_extra_fail_closed():
 with pytest.raises(ValueError,match="set_mismatch"):build_artifact_coverage(inventory=INV,observations=(),measurable_set_name="x")
 item=coverage()
 with pytest.raises(ValueError,match="duplicate"):build_artifact_coverage(inventory=INV,observations=(item,item),measurable_set_name="x")
 with pytest.raises(ValueError,match="scope"):build_artifact_coverage(inventory=INV,observations=(coverage(run=u(99)),),measurable_set_name="x")
 with pytest.raises(ValueError,match="set_mismatch"):build_artifact_coverage(inventory=INV,observations=(coverage(artifact=u(99)),),measurable_set_name="x")
