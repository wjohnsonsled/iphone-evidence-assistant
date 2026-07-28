"""DEV-1103 fail-closed executor tests with synthetic parser metadata."""

from datetime import date
from uuid import UUID

from app.integrity.domain import IntegrityState, ProvenanceValidationReport
from app.integrity.parser_contract import ControlledParseContext, ParserRegistryState, ParserResult
from app.processing.executor import SupportedParserExecutor
from app.support.domain import ProcessingResultStatus
from app.support.registry import (
    ApprovedParserEntry, CurrentSupportStatus, ParserDisposition,
    SupportedParserRegistry, create_supported_registry,
)


def result(*, examined=1, emitted=1, success=True, provenance=True):
    records = tuple({"value": n} for n in range(emitted))
    return ParserResult(success, examined, emitted, 0, 0, 0, 0, 0, provenance, (), (), ("Synthetic only.",), records, records)


class Parser:
    parser_id = "synthetic.parser"
    parser_version = "1"
    artifact_family = "synthetic"
    registry_state = ParserRegistryState.CANDIDATE

    def __init__(self, parsed=None):
        self.calls = []
        self.parsed = parsed or result()

    def declared_schema_profiles(self): return ("synthetic-v1",)
    def validate(self, context): self.calls.append("validate"); return result()
    def parse(self, context): self.calls.append("parse"); return self.parsed
    def report_coverage(self, context): return self.parsed
    def report_limitations(self, context): self.calls.append("limitations"); return ("Synthetic only.",)
    def self_test(self): return result()


def registry_and_auth():
    entry = ApprovedParserEntry(
        "SYN", "synthetic", "synthetic.parser", "1", ("synthetic-v1",),
        "DEC-SYNTHETIC", "QMS-SYNTHETIC", ("AC-SYNTHETIC",),
        date(2026, 1, 1), CurrentSupportStatus.SUPPORTED,
    )
    registry = SupportedParserRegistry(
        "synthetic", (entry,),
        instance_id=UUID("11030000-0000-4000-8000-000000000001"),
    )
    auth = registry.authorize(
        artifact_id="SYN", parser_id="synthetic.parser", parser_version="1",
        schema_profile="synthetic-v1", disposition=ParserDisposition.APPROVED,
        on_date=date(2026, 7, 28),
    )
    return registry, auth


def context(**changes):
    values = dict(
        controlled_input_id="synthetic-copy", schema_profile="synthetic-v1",
        integrity_state=IntegrityState.VERIFIED,
        provenance_report=ProvenanceValidationReport(True),
    )
    return ControlledParseContext(**(values | changes))


def test_empty_production_registry_denies_before_parser_call():
    synthetic_registry, auth = registry_and_auth()
    parser = Parser()
    outcome = SupportedParserExecutor(create_supported_registry()).execute(
        parser=parser, context=context(), authorization=auth,
    )
    assert outcome.failure_codes == ("registry_authorization_invalid",)
    assert parser.calls == []


def test_authorized_execution_validates_before_parse():
    registry, auth = registry_and_auth()
    parser = Parser()
    outcome = SupportedParserExecutor(registry).execute(
        parser=parser, context=context(), authorization=auth,
    )
    assert outcome.status is ProcessingResultStatus.SUPPORTED_COMPLETE
    assert parser.calls == ["validate", "parse", "limitations"]


def test_zero_records_is_distinct_success():
    registry, auth = registry_and_auth()
    outcome = SupportedParserExecutor(registry).execute(
        parser=Parser(result(examined=0, emitted=0)), context=context(), authorization=auth,
    )
    assert outcome.status is ProcessingResultStatus.SUPPORTED_NO_RECORDS
    assert outcome.records == ()


def test_integrity_and_identity_denials_do_not_call_parser():
    registry, auth = registry_and_auth()
    for parser, controlled, code in (
        (Parser(), context(source_writable=True), "source_write_capability"),
        (Parser(), context(legacy_source=True), "legacy_input"),
        (Parser(), context(integrity_state=IntegrityState.MISMATCH), "integrity_not_verified"),
    ):
        outcome = SupportedParserExecutor(registry).execute(
            parser=parser, context=controlled, authorization=auth,
        )
        assert outcome.failure_codes == (code,)
        assert parser.calls == []
    parser = Parser()
    parser.parser_version = "2"
    assert SupportedParserExecutor(registry).execute(
        parser=parser, context=context(), authorization=auth,
    ).failure_codes == ("parser_identity_mismatch",)


def test_exception_and_incomplete_results_are_safe_failures():
    registry, auth = registry_and_auth()
    parser = Parser()
    parser.parse = lambda _: (_ for _ in ()).throw(RuntimeError("sensitive"))
    outcome = SupportedParserExecutor(registry).execute(
        parser=parser, context=context(), authorization=auth,
    )
    assert outcome.failure_codes == ("parser_execution_failed",)
    assert "sensitive" not in repr(outcome)
    bad = Parser(result(examined=2, emitted=1))
    assert SupportedParserExecutor(registry).execute(
        parser=bad, context=context(), authorization=auth,
    ).failure_codes == ("coverage_not_reconciled",)
