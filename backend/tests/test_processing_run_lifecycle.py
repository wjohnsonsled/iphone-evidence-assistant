from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.evidence_core.processing_run import ProcessingRun
from app.processing.lifecycle import ProcessingRunLifecycle, RunState, TERMINAL_STATES


def u(n): return UUID(f"11040000-0000-4000-8000-{n:012d}")
NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)
RUN = ProcessingRun(u(1), u(2), u(3), u(4), "synthetic", NOW, u(5), u(6), u(7), 1)


@pytest.mark.parametrize("terminal", sorted(TERMINAL_STATES, key=lambda item: item.value))
def test_every_terminal_outcome_is_explicit_and_immutable(terminal):
    lifecycle = ProcessingRunLifecycle(RUN, occurred_at=NOW)
    lifecycle.transition(RunState.AUTHORIZED, occurred_at=NOW, reason_code="authorized")
    lifecycle.transition(RunState.RUNNING, occurred_at=NOW, reason_code="started")
    event = lifecycle.transition(terminal, occurred_at=NOW, reason_code="synthetic_result")
    assert event.state is terminal
    assert (event.tenant_id, event.case_id, event.processing_run_id) == (u(2), u(3), u(1))
    with pytest.raises(ValueError, match="transition_denied"):
        lifecycle.transition(RunState.RUNNING, occurred_at=NOW, reason_code="retry")


def test_skipping_authorization_and_empty_reason_fail_closed():
    lifecycle = ProcessingRunLifecycle(RUN, occurred_at=NOW)
    with pytest.raises(ValueError, match="transition_denied"):
        lifecycle.transition(RunState.RUNNING, occurred_at=NOW, reason_code="skip")
    with pytest.raises(ValueError, match="reason_required"):
        lifecycle.transition(RunState.AUTHORIZED, occurred_at=NOW, reason_code=" ")


def test_failure_and_cancel_are_allowed_before_execution():
    for state in (RunState.FAILED, RunState.CANCELLED):
        lifecycle = ProcessingRunLifecycle(RUN, occurred_at=NOW)
        lifecycle.transition(state, occurred_at=NOW, reason_code="preflight_terminal")
        assert lifecycle.state is state
