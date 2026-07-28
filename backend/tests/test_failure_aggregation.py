from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.evidence_core.processing_issue import *
from app.processing.failure_aggregation import aggregate_failures
def u(n):return UUID(f"11060000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def issue(n,severity):
 return ProcessingIssue(u(n),f"failure.{n}",IssueCategory.PARSING,severity,Recoverability.INDETERMINATE,"Synthetic failure.","parse","synthetic scope",None,u(1),u(2),None,None,None,None,None,NOW,("DEV-1106",),("Synthetic.",))
def partial(issue_id):
 return PartialProcessingObservation(u(9),u(1),u(2),None,("completed",),("incomplete",),("unknown",),(u(20),),(),(issue_id,),NOW,("Synthetic.",))
def test_safe_deterministic_aggregation():
 warning,fatal=issue(4,IssueSeverity.WARNING),issue(3,IssueSeverity.FATAL)
 result=aggregate_failures(u(1),(warning,fatal),(partial(fatal.issue_id),))
 assert result.issue_ids==(u(3),u(4)) and result.fatal_issue_ids==(u(3),)
 assert result.severities==((IssueSeverity.WARNING,1),(IssueSeverity.FATAL,1))
 assert not {"descriptions","evidence_conclusion"} & set(result.__dataclass_fields__)
def test_scope_duplicates_and_broken_partial_fail_closed():
 item=issue(3,IssueSeverity.ERROR)
 with pytest.raises(ValueError,match="duplicate"):aggregate_failures(u(1),(item,item),())
 with pytest.raises(ValueError,match="scope"):aggregate_failures(u(99),(item,),())
 with pytest.raises(ValueError,match="reference_missing"):aggregate_failures(u(1),(item,),(partial(u(88)),))
