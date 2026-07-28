"""Fail-closed cancellation and cleanup coordination."""
from collections.abc import Callable
from datetime import datetime
from app.processing.lifecycle import ProcessingRunLifecycle,RunState
class CancellationCoordinator:
 def cancel(self,lifecycle:ProcessingRunLifecycle,*,cleanup:Callable[[],None],occurred_at:datetime):
  if lifecycle.state in {RunState.COMPLETED,RunState.COMPLETED_ZERO_RECORDS,RunState.PARTIAL,RunState.FAILED,RunState.CANCELLED}:raise ValueError("processing_run_transition_denied")
  try:cleanup()
  except Exception:
   return lifecycle.transition(RunState.FAILED,occurred_at=occurred_at,reason_code="cancellation_cleanup_failed")
  return lifecycle.transition(RunState.CANCELLED,occurred_at=occurred_at,reason_code="cancellation_cleanup_succeeded")
