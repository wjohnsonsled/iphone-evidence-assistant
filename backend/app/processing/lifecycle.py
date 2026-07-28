"""Immutable processing-run lifecycle observations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.evidence_core.processing_run import ProcessingRun


class RunState(str, Enum):
    REQUESTED = "REQUESTED"
    AUTHORIZED = "AUTHORIZED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_ZERO_RECORDS = "COMPLETED_ZERO_RECORDS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL_STATES = frozenset({
    RunState.COMPLETED, RunState.COMPLETED_ZERO_RECORDS, RunState.PARTIAL,
    RunState.FAILED, RunState.CANCELLED,
})
TRANSITIONS = {
    RunState.REQUESTED: frozenset({RunState.AUTHORIZED, RunState.FAILED, RunState.CANCELLED}),
    RunState.AUTHORIZED: frozenset({RunState.RUNNING, RunState.FAILED, RunState.CANCELLED}),
    RunState.RUNNING: TERMINAL_STATES,
}


@dataclass(frozen=True, slots=True)
class RunStateObservation:
    observation_id: UUID
    tenant_id: UUID
    case_id: UUID
    processing_run_id: UUID
    prior_state: RunState | None
    state: RunState
    occurred_at: datetime
    reason_code: str


class ProcessingRunLifecycle:
    def __init__(self, run: ProcessingRun, *, occurred_at: datetime) -> None:
        self._run = run
        self._events = (
            self._event(None, RunState.REQUESTED, occurred_at, "run_requested"),
        )

    @property
    def state(self) -> RunState:
        return self._events[-1].state

    @property
    def events(self) -> tuple[RunStateObservation, ...]:
        return self._events

    def transition(self, state: RunState, *, occurred_at: datetime, reason_code: str) -> RunStateObservation:
        if state not in TRANSITIONS.get(self.state, frozenset()):
            raise ValueError("processing_run_transition_denied")
        if not reason_code.strip():
            raise ValueError("processing_run_reason_required")
        event = self._event(self.state, state, occurred_at, reason_code.strip())
        self._events = (*self._events, event)
        return event

    def _event(self, prior, state, occurred_at, reason):
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("processing_run_time_must_be_timezone_aware")
        return RunStateObservation(
            uuid4(), self._run.tenant_id, self._run.case_id,
            self._run.processing_run_id, prior, state, occurred_at, reason,
        )
