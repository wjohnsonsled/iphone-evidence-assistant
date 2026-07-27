"""Candidate parser contract and deterministic conformance harness."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from app.integrity.domain import IntegrityState, ProvenanceValidationReport


class ParserRegistryState(str, Enum):
    QUARANTINED = "QUARANTINED"
    EXPERIMENTAL = "EXPERIMENTAL"
    CANDIDATE = "CANDIDATE"
    SUPPORTED = "SUPPORTED"
    DEPRECATED = "DEPRECATED"
    DISABLED = "DISABLED"


@dataclass(frozen=True, slots=True)
class ControlledParseContext:
    controlled_input_id: str
    schema_profile: str
    integrity_state: IntegrityState
    provenance_report: ProvenanceValidationReport
    source_writable: bool = False
    legacy_source: bool = False


@dataclass(frozen=True, slots=True)
class ParserResult:
    success: bool
    records_examined: int
    records_emitted: int
    records_excluded: int
    records_rejected: int
    records_failed: int
    records_indeterminate: int
    unsupported_variants: int
    provenance_complete: bool
    omissions: tuple[str, ...]
    failures: tuple[str, ...]
    limitations: tuple[str, ...]
    raw_records: tuple[dict[str, Any], ...] = ()
    normalized_records: tuple[dict[str, Any], ...] = ()


@runtime_checkable
class EvidenceParser(Protocol):
    parser_id: str
    parser_version: str
    artifact_family: str
    registry_state: ParserRegistryState

    def declared_schema_profiles(self) -> tuple[str, ...]: ...
    def validate(self, context: ControlledParseContext) -> ParserResult: ...
    def parse(self, context: ControlledParseContext) -> ParserResult: ...
    def report_coverage(self, context: ControlledParseContext) -> ParserResult: ...
    def report_limitations(self, context: ControlledParseContext) -> tuple[str, ...]: ...
    def self_test(self) -> ParserResult: ...


@dataclass(frozen=True, slots=True)
class ConformanceReport:
    conforming: bool
    failures: tuple[str, ...]
    parser_id: str
    parser_version: str
    support_effect: str = "NONE_CANDIDATE_ONLY"


class IntegrityPolicy:
    def evaluate(self, context: ControlledParseContext, parser: EvidenceParser) -> tuple[bool, tuple[str, ...]]:
        failures = []
        if context.integrity_state is not IntegrityState.VERIFIED:
            failures.append("integrity_not_verified")
        if not context.provenance_report.valid:
            failures.append("provenance_invalid")
        if context.source_writable:
            failures.append("source_write_capability")
        if context.legacy_source:
            failures.append("legacy_input")
        if context.schema_profile not in parser.declared_schema_profiles():
            failures.append("schema_profile_not_declared")
        if parser.registry_state is not ParserRegistryState.CANDIDATE:
            failures.append("registry_state_not_candidate")
        return not failures, tuple(failures)


class ParserConformanceHarness:
    def __init__(self, policy: IntegrityPolicy | None = None) -> None:
        self.policy = policy or IntegrityPolicy()

    def evaluate(self, parser: EvidenceParser, context: ControlledParseContext) -> ConformanceReport:
        failures = []
        for attr in ("parser_id", "parser_version", "artifact_family"):
            if not isinstance(getattr(parser, attr, None), str) or not getattr(parser, attr).strip():
                failures.append(f"missing_{attr}")
        profiles = parser.declared_schema_profiles()
        if not profiles or any(not profile.strip() for profile in profiles):
            failures.append("missing_schema_profiles")
        permitted, policy_failures = self.policy.evaluate(context, parser)
        failures.extend(policy_failures)
        if permitted:
            validation = parser.validate(context)
            parsed = parser.parse(context)
            coverage = parser.report_coverage(context)
            self_test = parser.self_test()
            limitations = parser.report_limitations(context)
            if not validation.success:
                failures.append("validation_failed")
            if not parsed.provenance_complete:
                failures.append("provenance_missing")
            if parsed.records_examined != parsed.records_emitted + parsed.records_excluded + parsed.records_rejected + parsed.records_failed + parsed.records_indeterminate:
                failures.append("coverage_not_reconciled")
            if coverage.records_examined != parsed.records_examined:
                failures.append("coverage_report_mismatch")
            if parsed.omissions and not coverage.omissions:
                failures.append("silent_omission")
            if not limitations:
                failures.append("limitations_missing")
            if not self_test.success or not self_test.provenance_complete:
                failures.append("self_test_failed")
        return ConformanceReport(not failures, tuple(sorted(set(failures))), getattr(parser, "parser_id", ""), getattr(parser, "parser_version", ""))
