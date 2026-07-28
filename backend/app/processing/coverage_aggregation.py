"""Deterministic aggregation of factual processing coverage observations."""
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from app.evidence_core.processing_coverage import CountObservation,CountStatus,CoverageStatus,ProcessingCoverageObservation

@dataclass(frozen=True,slots=True)
class CoverageAggregate:
 processing_run_id:UUID; observation_ids:tuple[UUID,...]
 statuses:tuple[tuple[CoverageStatus,int],...]
 examined:CountObservation; emitted:CountObservation; excluded:CountObservation
 rejected:CountObservation; failed:CountObservation; indeterminate:CountObservation
 limitations:tuple[str,...]=("Aggregate describes processing observations only; it does not establish evidentiary completeness.",)

def aggregate_coverage(processing_run_id:UUID,observations:tuple[ProcessingCoverageObservation,...])->CoverageAggregate:
 ids=set()
 for observation in observations:
  if observation.processing_run_id!=processing_run_id:raise ValueError("coverage_run_scope_mismatch")
  if observation.observation_id in ids:raise ValueError("duplicate_coverage_observation")
  ids.add(observation.observation_id)
 def total(field):
  values=[getattr(item,field) for item in observations]
  if any(value.status is not CountStatus.KNOWN for value in values):return CountObservation(CountStatus.UNKNOWN,None)
  return CountObservation(CountStatus.KNOWN,sum(value.value for value in values))
 statuses=tuple((status,sum(item.status is status for item in observations)) for status in CoverageStatus if any(item.status is status for item in observations))
 return CoverageAggregate(processing_run_id,tuple(sorted(ids,key=str)),statuses,*(total(name) for name in ("examined","emitted","excluded","rejected","failed","indeterminate")))
