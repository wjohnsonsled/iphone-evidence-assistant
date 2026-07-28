from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.evidence_core.processing_run import ProcessingRun
from app.processing.cancellation import CancellationCoordinator
from app.processing.lifecycle import ProcessingRunLifecycle,RunState
def u(n):return UUID(f"11080000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
RUN=ProcessingRun(u(1),u(2),u(3),u(4),"synthetic",NOW,u(5),u(6),u(7),1)
def test_cleanup_precedes_cancelled_terminal_state():
 lifecycle=ProcessingRunLifecycle(RUN,occurred_at=NOW);calls=[]
 event=CancellationCoordinator().cancel(lifecycle,cleanup=lambda:calls.append("cleaned"),occurred_at=NOW)
 assert calls==["cleaned"] and event.state is RunState.CANCELLED
def test_cleanup_failure_is_explicit_failed_not_cancelled():
 lifecycle=ProcessingRunLifecycle(RUN,occurred_at=NOW)
 def fail():raise OSError("sensitive")
 event=CancellationCoordinator().cancel(lifecycle,cleanup=fail,occurred_at=NOW)
 assert event.state is RunState.FAILED and event.reason_code=="cancellation_cleanup_failed"
 assert "sensitive" not in repr(event)
def test_terminal_run_cannot_be_cancelled_or_cleaned_again():
 lifecycle=ProcessingRunLifecycle(RUN,occurred_at=NOW);lifecycle.transition(RunState.CANCELLED,occurred_at=NOW,reason_code="done");calls=[]
 with pytest.raises(ValueError,match="transition_denied"):CancellationCoordinator().cancel(lifecycle,cleanup=lambda:calls.append(1),occurred_at=NOW)
 assert calls==[]
