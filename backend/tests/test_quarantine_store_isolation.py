from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.evidence_core.quarantine_store import QuarantinedOutputStore
from app.evidence_core.supported_store import OutputDisposition,SupportedEvidenceStore
from app.support.registry import create_supported_registry
def u(n):return UUID(f"51000000-0000-4000-8000-{n:012d}")
def values(disposition):
 return dict(disposition=disposition,tenant_id=u(1),case_id=u(2),processing_run_id=u(3),parser_id="synthetic.legacy",parser_version="0",observed_at=datetime(2026,7,28,tzinfo=timezone.utc),diagnostic_payload=(("result","synthetic"),),limitations=("Not supported evidence.",))
@pytest.mark.parametrize("d",[OutputDisposition.CANDIDATE,OutputDisposition.EXPERIMENTAL,OutputDisposition.LEGACY])
def test_non_supported_outputs_remain_in_separate_store(d):
 q=QuarantinedOutputStore();q.append(**values(d))
 assert len(q.list_scoped(tenant_id=u(1),case_id=u(2)))==1
 assert SupportedEvidenceStore(create_supported_registry()).count==0
def test_approved_output_cannot_enter_quarantine():
 with pytest.raises(ValueError):QuarantinedOutputStore().append(**values(OutputDisposition.APPROVED))
def test_no_transfer_promotion_or_broad_list_api():
 assert not {"transfer","promote","admit","list_all"} & set(dir(QuarantinedOutputStore))
def test_cross_tenant_scope_returns_nothing_without_disclosure():
 q=QuarantinedOutputStore();q.append(**values(OutputDisposition.LEGACY))
 assert q.list_scoped(tenant_id=u(9),case_id=u(2))==()
