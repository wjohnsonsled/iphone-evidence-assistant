"""Fail-closed executor for exactly registry-authorized parser calls."""

from __future__ import annotations

from dataclasses import dataclass

from app.integrity.domain import IntegrityState
from app.integrity.parser_contract import ControlledParseContext, EvidenceParser
from app.support.domain import ProcessingResultStatus
from app.support.registry import ParserAuthorization, SupportedParserRegistry


@dataclass(frozen=True, slots=True)
class ExecutionOutcome:
    status: ProcessingResultStatus
    records: tuple[dict, ...]
    failure_codes: tuple[str, ...]
    limitations: tuple[str, ...]


class SupportedParserExecutor:
    """Execute only after exact authorization and controlled-input checks."""

    def __init__(self, registry: SupportedParserRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        *,
        parser: EvidenceParser,
        context: ControlledParseContext,
        authorization: ParserAuthorization,
    ) -> ExecutionOutcome:
        denial = self._preflight(parser, context, authorization)
        if denial:
            return self._failed(denial)
        try:
            validation = parser.validate(context)
            if not validation.success:
                return self._failed("parser_validation_failed", validation.limitations)
            parsed = parser.parse(context)
            limitations = tuple(parser.report_limitations(context))
        except Exception:
            return self._failed("parser_execution_failed")
        if not parsed.success:
            return self._failed("parser_result_failed", parsed.limitations)
        if not parsed.provenance_complete:
            return self._failed("provenance_incomplete", parsed.limitations)
        total = (
            parsed.records_emitted + parsed.records_excluded + parsed.records_rejected
            + parsed.records_failed + parsed.records_indeterminate
        )
        if parsed.records_examined != total or len(parsed.normalized_records) != parsed.records_emitted:
            return self._failed("coverage_not_reconciled", parsed.limitations)
        if not limitations:
            return self._failed("limitations_missing")
        if parsed.records_examined == 0:
            if parsed.records_emitted or parsed.normalized_records:
                return self._failed("zero_result_contains_records", limitations)
            status = ProcessingResultStatus.SUPPORTED_NO_RECORDS
        else:
            status = ProcessingResultStatus.SUPPORTED_COMPLETE
        return ExecutionOutcome(status, parsed.normalized_records, (), limitations)

    def _preflight(self, parser, context, authorization) -> str | None:
        if not self._registry.issued(authorization):
            return "registry_authorization_invalid"
        entry = authorization.entry
        if (parser.parser_id, parser.parser_version, parser.artifact_family) != (
            entry.parser_id, entry.parser_version, entry.artifact_family
        ):
            return "parser_identity_mismatch"
        if context.schema_profile != authorization.schema_profile:
            return "schema_profile_mismatch"
        if context.integrity_state is not IntegrityState.VERIFIED:
            return "integrity_not_verified"
        if not context.provenance_report.valid:
            return "provenance_invalid"
        if context.source_writable:
            return "source_write_capability"
        if context.legacy_source:
            return "legacy_input"
        return None

    @staticmethod
    def _failed(code: str, limitations: tuple[str, ...] = ()) -> ExecutionOutcome:
        return ExecutionOutcome(ProcessingResultStatus.FAILED, (), (code,), tuple(limitations))
