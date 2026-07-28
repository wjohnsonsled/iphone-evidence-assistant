"""Candidate supported-processing infrastructure; no parser is Supported."""

from app.processing.executor import ExecutionOutcome, SupportedParserExecutor
from app.processing.lifecycle import (
    ProcessingRunLifecycle, RunState, RunStateObservation, TERMINAL_STATES,
)
from app.processing.coverage_aggregation import CoverageAggregate, aggregate_coverage

__all__ = [
    "ExecutionOutcome", "SupportedParserExecutor", "ProcessingRunLifecycle",
    "RunState", "RunStateObservation", "TERMINAL_STATES",
    "CoverageAggregate", "aggregate_coverage",
]
