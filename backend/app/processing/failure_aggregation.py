"""Safe deterministic aggregation of processing issue observations."""
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from app.evidence_core.processing_issue import IssueCategory,IssueSeverity,PartialProcessingObservation,ProcessingIssue

@dataclass(frozen=True,slots=True)
class FailureAggregate:
 processing_run_id:UUID; issue_ids:tuple[UUID,...]; partial_observation_ids:tuple[UUID,...]
 categories:tuple[tuple[IssueCategory,int],...]; severities:tuple[tuple[IssueSeverity,int],...]
 fatal_issue_ids:tuple[UUID,...]
 limitations:tuple[str,...]=("Aggregate contains safe processing diagnostics only; it makes no evidentiary conclusion.",)

def aggregate_failures(processing_run_id:UUID,issues:tuple[ProcessingIssue,...],partials:tuple[PartialProcessingObservation,...])->FailureAggregate:
 issue_ids=set()
 for issue in issues:
  if issue.processing_run_id!=processing_run_id:raise ValueError("issue_run_scope_mismatch")
  if issue.issue_id in issue_ids:raise ValueError("duplicate_processing_issue")
  issue_ids.add(issue.issue_id)
 partial_ids=set()
 for partial in partials:
  if partial.processing_run_id!=processing_run_id:raise ValueError("partial_run_scope_mismatch")
  if partial.partial_id in partial_ids:raise ValueError("duplicate_partial_observation")
  if not set(partial.contributing_issue_ids).issubset(issue_ids):raise ValueError("partial_issue_reference_missing")
  partial_ids.add(partial.partial_id)
 categories=tuple((value,sum(item.category is value for item in issues)) for value in IssueCategory if any(item.category is value for item in issues))
 severities=tuple((value,sum(item.severity is value for item in issues)) for value in IssueSeverity if any(item.severity is value for item in issues))
 fatal=tuple(sorted((item.issue_id for item in issues if item.severity is IssueSeverity.FATAL),key=str))
 return FailureAggregate(processing_run_id,tuple(sorted(issue_ids,key=str)),tuple(sorted(partial_ids,key=str)),categories,severities,fatal)
