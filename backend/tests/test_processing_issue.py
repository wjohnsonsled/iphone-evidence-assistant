from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.evidence_core.processing_issue import *
def u(n):return UUID(f"49000000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def base(**x):
 d=dict(issue_code="validation.schema-rejected",category=IssueCategory.VALIDATION,severity=IssueSeverity.ERROR,recoverability=Recoverability.INDETERMINATE,description="Schema validation did not complete.",processing_stage="validation",affected_scope="candidate source artifact",remediation_guidance="Review the governed validation record.",processing_run_id=u(1),source_artifact_id=u(2),parser_identity_id=None,coverage_observation_id=u(3),omission_observation_id=None,typed_value_observation_id=None,timestamp_observation_id=None,observed_at=NOW,limitation_references=("DEV-0409",),limitations=("Processing diagnosis only.",));return d|x
def test_all_vocabularies():
 assert len(IssueCategory)==15 and len(IssueSeverity)==4 and len(Recoverability)==4
def test_issue_is_immutable_and_provenance_complete():
 i=record_issue(**base()); assert i.issue_id.version==4 and i.processing_run_id==u(1)
 with pytest.raises(FrozenInstanceError):i.description="changed"
@pytest.mark.parametrize("text",["Traceback: bad","password=abc","C:\\client\\file.db","/Users/client/evidence","access token abc","line one\nline two"])
def test_unsafe_diagnostics_rejected(text):
 with pytest.raises(ValueError):record_issue(**base(description=text))
def test_sensitive_fields_do_not_exist():
 fields=set(ProcessingIssue.__dataclass_fields__)
 assert not {"raw_exception","stack_trace","filesystem_path","credential","token","evidence_content","customer_id"} & fields
def test_partial_links_coverage_omission_and_issues():
 p=record_partial_processing(processing_run_id=u(1),source_artifact_id=u(2),parser_identity_id=None,completed_scope=("rows 1-2",),incomplete_scope=("rows 3-4",),unresolved_scope=("row 5",),coverage_observation_ids=(u(3),),omission_observation_ids=(u(4),),contributing_issue_ids=(u(5),),observed_at=NOW,limitations=("Synthetic scope only.",))
 assert p.coverage_observation_ids==(u(3),) and p.omission_observation_ids==(u(4),)
@pytest.mark.parametrize("change",[{"limitations":()},{"limitation_references":()},{"description":" secret "},{"issue_code":"Bad Code"}])
def test_invalid_issue_combinations(change):
 with pytest.raises(ValueError):record_issue(**base(**change))
