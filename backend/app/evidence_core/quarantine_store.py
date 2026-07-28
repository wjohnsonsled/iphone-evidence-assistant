"""Separate diagnostic store for non-supported output; no promotion path."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID,uuid4
from app.evidence_core.supported_store import OutputDisposition

@dataclass(frozen=True,slots=True)
class QuarantinedOutput:
 output_id:UUID; disposition:OutputDisposition; tenant_id:UUID; case_id:UUID
 processing_run_id:UUID; parser_id:str; parser_version:str; observed_at:datetime
 diagnostic_payload:tuple[tuple[str,str],...]; limitations:tuple[str,...]
 def __post_init__(self):
  if self.output_id.version!=4 or self.observed_at.tzinfo is None:raise ValueError("quarantine_identity_invalid")
  if self.disposition is OutputDisposition.APPROVED:raise ValueError("approved_output_prohibited_from_quarantine")
  if not self.parser_id.strip() or not self.parser_version.strip() or not self.limitations:raise ValueError("quarantine_metadata_incomplete")

class QuarantinedOutputStore:
 def __init__(self):self._items:tuple[QuarantinedOutput,...]=()
 def append(self,**values:object)->QuarantinedOutput:
  item=QuarantinedOutput(output_id=uuid4(),**values) # type: ignore[arg-type]
  self._items=(*self._items,item);return item
 def list_scoped(self,*,tenant_id:UUID,case_id:UUID)->tuple[QuarantinedOutput,...]:
  return tuple(i for i in self._items if i.tenant_id==tenant_id and i.case_id==case_id)
