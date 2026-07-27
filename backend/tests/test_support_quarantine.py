"""DEV-0304 deterministic support-status and quarantine tests."""

from __future__ import annotations

import ast
from dataclasses import replace
from datetime import date
from pathlib import Path
from uuid import UUID

import pytest

from app.support import (
    ApprovedParserEntry,
    ArtifactLifecycleStatus,
    ParserAuthorization,
    ParserDisposition,
    ParserQuarantinedError,
    ProcessingResultStatus,
    SupportedOutputGate,
    SupportedParserRegistry,
    create_supported_registry,
)

BACKEND = Path(__file__).parents[1]


def entry() -> ApprovedParserEntry:
    return ApprovedParserEntry(
        "SYN-001",
        "synthetic_test_only",
        "synthetic.parser",
        "1.0.0",
        ("SCHEMA_B", "SCHEMA_A"),
        "SYNTHETIC-VALIDATION",
        "SYNTHETIC-OWNER-APPROVAL",
        date(2026, 1, 1),
    )


def authorized() -> tuple[SupportedParserRegistry, ParserAuthorization]:
    registry = SupportedParserRegistry(
        "synthetic-v1",
        (entry(),),
        instance_id=UUID("00000000-0000-0000-0000-000000000304"),
    )
    authorization = registry.authorize(
        artifact_id="SYN-001",
        parser_id="synthetic.parser",
        parser_version="1.0.0",
        schema_profile="SCHEMA_A",
        disposition=ParserDisposition.APPROVED,
        on_date=date(2026, 7, 27),
    )
    return registry, authorization


def test_closed_status_vocabularies_are_exact_and_separate():
    assert {item.value for item in ArtifactLifecycleStatus} == {
        "CANDIDATE", "IN_DEVELOPMENT", "VALIDATION_PENDING", "DEPRECATED"
    }
    assert {item.value for item in ProcessingResultStatus} == {
        "SUPPORTED_COMPLETE", "SUPPORTED_NO_RECORDS", "UNSUPPORTED",
        "INACCESSIBLE", "CORRUPTED", "FAILED", "EXCLUDED",
    }
    assert not ({item.value for item in ArtifactLifecycleStatus} & {item.value for item in ProcessingResultStatus})


def test_default_registry_is_empty_and_support_module_has_no_legacy_imports():
    registry = create_supported_registry()
    assert registry.entries == ()
    for path in (BACKEND / "app" / "support").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not any(name.startswith(("evidence_engine", "app.legacy")) for name in imports)


@pytest.mark.parametrize("disposition", [item for item in ParserDisposition if item is not ParserDisposition.APPROVED])
def test_every_nonapproved_disposition_is_quarantined(disposition):
    with pytest.raises(ParserQuarantinedError, match="parser_disposition"):
        create_supported_registry().authorize(
            artifact_id="SYN-001",
            parser_id="synthetic.parser",
            parser_version="1.0.0",
            schema_profile="SCHEMA_A",
            disposition=disposition,
            on_date=date(2026, 7, 27),
        )


def test_unknown_identity_profile_dates_and_duplicates_fail_closed():
    valid = entry()
    with pytest.raises(ValueError, match="duplicate"):
        SupportedParserRegistry("v1", (valid, valid))
    registry = SupportedParserRegistry("v1", (valid,))
    base = dict(
        artifact_id=valid.artifact_id, parser_id=valid.parser_id,
        parser_version=valid.parser_version, schema_profile="SCHEMA_A",
        disposition=ParserDisposition.APPROVED, on_date=date(2026, 7, 27),
    )
    for changed, code in (
        ({"parser_version": "2"}, "not_in"),
        ({"schema_profile": "UNKNOWN"}, "not_approved"),
        ({"on_date": date(2025, 1, 1)}, "not_effective"),
    ):
        with pytest.raises(ParserQuarantinedError, match=code):
            registry.authorize(**(base | changed))


@pytest.mark.parametrize(
    "change,code",
    [
        ({"approval_record": ""}, "approval_record_required"),
        ({"validation_reference": ""}, "validation_reference_required"),
        ({"schema_profiles": ()}, "schema_profiles_required"),
        ({"retirement_date": date(2025, 1, 1)}, "retirement_precedes"),
    ],
)
def test_registry_entry_requires_complete_approval_metadata(change, code):
    with pytest.raises(ValueError, match=code):
        replace(entry(), **change)


def admission_args(**changes):
    base = dict(
        status=ProcessingResultStatus.SUPPORTED_COMPLETE,
        records=({"raw": "synthetic"},),
        records_examined=1,
        records_emitted=1,
        records_excluded=0,
        records_rejected=0,
        records_failed=0,
        records_indeterminate=0,
        provenance_complete=True,
    )
    return base | changes


def test_output_gate_admits_only_exact_registry_authorization_and_complete_output():
    registry, authorization = authorized()
    gate = SupportedOutputGate(registry)
    result = gate.admit(authorization, **admission_args())
    assert result.records == ({"raw": "synthetic"},)

    other = SupportedParserRegistry("synthetic-v1", (entry(),))
    other_authorization = other.authorize(
        artifact_id="SYN-001",
        parser_id="synthetic.parser",
        parser_version="1.0.0",
        schema_profile="SCHEMA_A",
        disposition=ParserDisposition.APPROVED,
        on_date=date(2026, 7, 27),
    )
    assert other is not registry
    with pytest.raises(ParserQuarantinedError, match="authorization_not_issued"):
        gate.admit(other_authorization, **admission_args())


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"status": ProcessingResultStatus.FAILED}, "status_not_supported"),
        ({"provenance_complete": False}, "provenance_incomplete"),
        ({"records_examined": 2}, "coverage_not_reconciled"),
        ({"records": ()}, "coverage_not_reconciled"),
    ],
)
def test_output_gate_rejects_failure_provenance_and_coverage(changes, code):
    registry, authorization = authorized()
    with pytest.raises(ParserQuarantinedError, match=code):
        SupportedOutputGate(registry).admit(authorization, **admission_args(**changes))


def test_zero_records_is_distinct_and_cannot_mask_failure_or_records():
    registry, authorization = authorized()
    gate = SupportedOutputGate(registry)
    zero = admission_args(
        status=ProcessingResultStatus.SUPPORTED_NO_RECORDS,
        records=(),
        records_examined=0,
        records_emitted=0,
    )
    assert gate.admit(authorization, **zero).records == ()
    with pytest.raises(ParserQuarantinedError, match="no_records_status_contains_records"):
        gate.admit(
            authorization,
            **admission_args(status=ProcessingResultStatus.SUPPORTED_NO_RECORDS),
        )
    with pytest.raises(ParserQuarantinedError, match="status_not_supported"):
        gate.admit(
            authorization,
            **admission_args(
                status=ProcessingResultStatus.FAILED,
                records=(),
                records_examined=0,
                records_emitted=0,
            ),
        )
