"""Immutable safe processing diagnostics without evidentiary conclusions."""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

class IssueCategory(str,Enum):
 AUTHORIZATION="AUTHORIZATION"; ACCESS="ACCESS"; VALIDATION="VALIDATION"; RESOURCE_LIMIT="RESOURCE_LIMIT"; INTEGRITY="INTEGRITY"; PROVENANCE="PROVENANCE"; PARSING="PARSING"; NORMALIZATION="NORMALIZATION"; SERIALIZATION="SERIALIZATION"; STORAGE="STORAGE"; CONFIGURATION="CONFIGURATION"; CLEANUP="CLEANUP"; SYSTEM="SYSTEM"; INTERNAL="INTERNAL"; UNKNOWN="UNKNOWN"
class IssueSeverity(str,Enum):
 INFORMATIONAL="INFORMATIONAL"; WARNING="WARNING"; ERROR="ERROR"; FATAL="FATAL"
class Recoverability(str,Enum):
 RECOVERABLE="RECOVERABLE"; NON_RECOVERABLE="NON_RECOVERABLE"; INDETERMINATE="INDETERMINATE"; NOT_APPLICABLE="NOT_APPLICABLE"

_CODE=re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
_UNSAFE=re.compile(r"(?i)(traceback|password|passwd|api[_ -]?key|access[_ -]?token|secret|bearer\s|[a-z]:\\|/users/|/home/|\\\\)")
def _safe(value:str,field:str,maximum:int)->None:
 if not value or value!=value.strip() or len(value)>maximum or "\n" in value or "\r" in value or _UNSAFE.search(value): raise ValueError(f"unsafe_{field}")

@dataclass(frozen=True,slots=True)
class ProcessingIssue:
 issue_id:UUID; issue_code:str; category:IssueCategory; severity:IssueSeverity; recoverability:Recoverability
 description:str; processing_stage:str; affected_scope:str; remediation_guidance:str|None
 processing_run_id:UUID; source_artifact_id:UUID; parser_identity_id:UUID|None
 coverage_observation_id:UUID|None; omission_observation_id:UUID|None
 typed_value_observation_id:UUID|None; timestamp_observation_id:UUID|None
 observed_at:datetime; limitation_references:tuple[str,...]; limitations:tuple[str,...]
 supersedes_issue_id:UUID|None=None
 def __post_init__(self):
  if self.issue_id.version!=4 or self.observed_at.tzinfo is None: raise ValueError("issue_identity_invalid")
  if not _CODE.fullmatch(self.issue_code): raise ValueError("issue_code_invalid")
  for value,field,maximum in ((self.description,"description",512),(self.processing_stage,"stage",128),(self.affected_scope,"scope",255)):
   _safe(value,field,maximum)
  if self.remediation_guidance is not None:_safe(self.remediation_guidance,"remediation",512)
  if not self.limitations or not self.limitation_references or any(not v.strip() for v in self.limitations+self.limitation_references): raise ValueError("issue_limitations_required")

@dataclass(frozen=True,slots=True)
class PartialProcessingObservation:
 partial_id:UUID; processing_run_id:UUID; source_artifact_id:UUID; parser_identity_id:UUID|None
 completed_scope:tuple[str,...]; incomplete_scope:tuple[str,...]; unresolved_scope:tuple[str,...]
 coverage_observation_ids:tuple[UUID,...]; omission_observation_ids:tuple[UUID,...]
 contributing_issue_ids:tuple[UUID,...]; observed_at:datetime; limitations:tuple[str,...]
 def __post_init__(self):
  if self.partial_id.version!=4 or self.observed_at.tzinfo is None: raise ValueError("partial_identity_invalid")
  if not self.completed_scope or not self.incomplete_scope or not self.unresolved_scope: raise ValueError("partial_scope_required")
  if not self.coverage_observation_ids or not self.contributing_issue_ids or not self.limitations: raise ValueError("partial_relationships_required")
  if any(not v.strip() for v in self.completed_scope+self.incomplete_scope+self.unresolved_scope+self.limitations): raise ValueError("partial_text_invalid")

def record_issue(**values:object)->ProcessingIssue:return ProcessingIssue(issue_id=uuid4(),**values) # type: ignore[arg-type]
def record_partial_processing(**values:object)->PartialProcessingObservation:return PartialProcessingObservation(partial_id=uuid4(),**values) # type: ignore[arg-type]
