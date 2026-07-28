"""Exact projection of registered inventory and processing coverage facts."""
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from app.evidence_core.processing_coverage import CoverageStatus,ProcessingCoverageObservation
from app.evidence_core.source_inventory import SourceInventory

LIMITATIONS=(
 "Coverage describes the registered measurable set only, not all evidence on a backup or device.",
 "Missing inventory or processing observations cannot be interpreted as evidence absence.",
 "Unsupported processing is not a successful zero-record result.",
)
@dataclass(frozen=True,slots=True)
class ArtifactCoverageEntry:
 source_artifact_id:UUID; artifact_family_key:str; coverage_observation_id:UUID
 status:CoverageStatus; processing_run_id:UUID
@dataclass(frozen=True,slots=True)
class ArtifactCoverageReport:
 processing_run_id:UUID; measurable_set_name:str; denominator:int
 entries:tuple[ArtifactCoverageEntry,...]; status_counts:tuple[tuple[CoverageStatus,int],...]
 limitations:tuple[str,...]=LIMITATIONS
def build_artifact_coverage(*,inventory:SourceInventory,observations:tuple[ProcessingCoverageObservation,...],measurable_set_name:str)->ArtifactCoverageReport:
 if not measurable_set_name.strip():raise ValueError("measurable_set_name_required")
 by_artifact={}
 for observation in observations:
  if observation.processing_run_id!=inventory.processing_run_id:raise ValueError("coverage_run_scope_mismatch")
  if observation.source_artifact_id in by_artifact:raise ValueError("duplicate_artifact_coverage")
  by_artifact[observation.source_artifact_id]=observation
 inventory_ids={item.source_artifact_id for item in inventory.items}
 if set(by_artifact)!=inventory_ids:raise ValueError("inventory_coverage_set_mismatch")
 entries=tuple(ArtifactCoverageEntry(item.source_artifact_id,item.artifact_family_key,by_artifact[item.source_artifact_id].observation_id,by_artifact[item.source_artifact_id].status,inventory.processing_run_id) for item in inventory.items)
 counts=tuple((status,sum(entry.status is status for entry in entries)) for status in CoverageStatus if any(entry.status is status for entry in entries))
 return ArtifactCoverageReport(inventory.processing_run_id,measurable_set_name.strip(),len(entries),entries,counts)
