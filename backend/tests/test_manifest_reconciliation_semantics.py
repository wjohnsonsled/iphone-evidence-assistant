from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.manifest.reconciliation_semantics import *

NOW = datetime(2026, 7, 30, tzinfo=timezone.utc)
POLICY = ReconciliationPolicy(100, 100, 10, 100_000, 200_000, 5)


def evaluate(rows, policy=POLICY, **kwargs):
    return evaluate_reconciliation(
        tuple(rows), policy, monotonic=kwargs.pop("monotonic", lambda: 0.0),
        observed_at=NOW, **kwargs
    )


def test_repeated_values_are_separate_patterns_not_duplicate_conclusions():
    rows = (
        synthetic_row(1, raw_file_id="A" * 40, canonical_file_id="a" * 40, domain="HomeDomain", relative_path="x"),
        synthetic_row(2, raw_file_id="A" * 40, canonical_file_id="a" * 40, domain="HomeDomain", relative_path="x"),
    )
    result = evaluate(rows)
    kinds = {pattern.kind for pattern in result.patterns}
    assert kinds == {
        PatternKind.REPEATED_RAW_FILE_ID,
        PatternKind.REPEATED_CANONICAL_FILE_ID,
        PatternKind.REPEATED_DOMAIN_PATH_TUPLE,
    }
    assert result.duplicate_conclusion is ConclusionState.NOT_ESTABLISHED
    assert result.orphan_conclusion is ConclusionState.NOT_ESTABLISHED
    assert result.absence_conclusion is ConclusionState.NOT_ESTABLISHED
    assert not result.physical_inventory_observed
    assert "physical_inventory_not_observed" in result.blockers


def test_repeated_locator_is_distinct_from_repeated_identifier():
    rows = (
        synthetic_row(1, raw_file_id="A", canonical_file_id=None, domain="D1", relative_path="p1"),
        synthetic_row(1, raw_file_id="B", canonical_file_id=None, domain="D2", relative_path="p2"),
    )
    result = evaluate(rows)
    assert tuple(pattern.kind for pattern in result.patterns) == (
        PatternKind.REPEATED_ROW_LOCATOR,
    )


def test_no_repetition_is_zero_patterns_not_absence():
    result = evaluate((
        synthetic_row(1, raw_file_id="A", canonical_file_id=None, domain="D1", relative_path="p1"),
        synthetic_row(2, raw_file_id="B", canonical_file_id=None, domain="D2", relative_path="p2"),
    ))
    assert result.evaluation_state is EvaluationState.ZERO_PATTERNS_OBSERVED
    assert result.patterns == ()
    assert result.absence_conclusion is ConclusionState.NOT_ESTABLISHED


def test_blob_fileid_is_not_silently_textualized():
    result = evaluate((
        synthetic_row(1, raw_file_id=b"\x00\x01", canonical_file_id=None, domain="D1", relative_path="p1"),
        synthetic_row(2, raw_file_id=b"\x00\x01", canonical_file_id=None, domain="D2", relative_path="p2"),
    ))
    assert PatternKind.REPEATED_RAW_FILE_ID not in {item.kind for item in result.patterns}
    assert '"comparison_key":"0001"' not in result.canonical_json()


def test_scope_and_profile_mismatch_fail_closed():
    left = synthetic_row(1, raw_file_id="A", canonical_file_id=None, domain="D", relative_path="p")
    right = synthetic_row(2, raw_file_id="B", canonical_file_id=None, domain="D", relative_path="q", tenant_seed=9)
    with pytest.raises(ValueError, match="reconciliation_scope_mismatch"):
        evaluate((left, right))

    values = {field: getattr(left, field) for field in left.__dataclass_fields__}
    values["path_profile_version"] = "2"
    with pytest.raises(ValueError, match="reconciliation_profile_incompatible"):
        ManifestReferenceObservation(**values)


@pytest.mark.parametrize(
    "policy,code",
    [
        (ReconciliationPolicy(1, 100, 10, 100_000, 200_000, 5), "row_limit"),
        (ReconciliationPolicy(100, 100, 10, 1, 200_000, 5), "projected_bytes_limit"),
        (ReconciliationPolicy(100, 100, 10, 100_000, 1, 5), "memory_estimate_limit"),
        (ReconciliationPolicy(100, 100, 1, 100_000, 200_000, 5), "group_member_limit"),
    ],
)
def test_resource_limits_are_partial_and_never_enable_conclusions(policy, code):
    rows = (
        synthetic_row(1, raw_file_id="A", canonical_file_id="a", domain="D", relative_path="p"),
        synthetic_row(2, raw_file_id="A", canonical_file_id="a", domain="D", relative_path="p"),
    )
    result = evaluate(rows, policy)
    assert result.evaluation_state is EvaluationState.PARTIAL_RESOURCE_LIMIT
    assert code in result.blockers
    assert result.duplicate_conclusion is ConclusionState.NOT_ESTABLISHED
    assert not result.comparison_universe_complete


def test_group_count_limit_cannot_create_conclusion():
    rows = (
        synthetic_row(1, raw_file_id="A", canonical_file_id="a", domain="D", relative_path="p"),
        synthetic_row(2, raw_file_id="A", canonical_file_id="a", domain="D", relative_path="p"),
    )
    result = evaluate(rows, ReconciliationPolicy(100, 1, 10, 100_000, 200_000, 5))
    assert result.evaluation_state is EvaluationState.PARTIAL_RESOURCE_LIMIT
    assert len(result.patterns) == 1
    assert "group_count_limit" in result.blockers


def test_cancellation_and_time_preserve_completed_row_count():
    rows = tuple(
        synthetic_row(i, raw_file_id=str(i), canonical_file_id=None, domain="D", relative_path=str(i))
        for i in range(1, 4)
    )
    calls = 0

    def cancel():
        nonlocal calls
        calls += 1
        return calls > 2

    cancelled = evaluate(rows, cancel=cancel)
    assert cancelled.evaluation_state is EvaluationState.CANCELLED
    assert cancelled.rows_evaluated == 2

    times = iter((0.0, 0.0, 0.0, 6.0))
    timed = evaluate(rows, monotonic=lambda: next(times, 6.0))
    assert timed.evaluation_state is EvaluationState.PARTIAL_RESOURCE_LIMIT
    assert timed.rows_evaluated == 2


def test_policy_and_empty_input_fail_closed():
    with pytest.raises(ValueError, match="reconciliation_rows_required"):
        evaluate(())
    for values in (
        (0, 1, 1, 1, 1, 1), (1, 0, 1, 1, 1, 1),
        (1, 1, 0, 1, 1, 1), (1, 1, 1, 0, 1, 1),
        (1, 1, 1, 1, 0, 1), (1, 1, 1, 1, 1, 0),
    ):
        with pytest.raises(ValueError, match="reconciliation_policy_invalid"):
            ReconciliationPolicy(*values)


def test_deterministic_output_has_no_filesystem_or_support_surface():
    rows = (
        synthetic_row(1, raw_file_id="A", canonical_file_id="a", domain="D", relative_path="p"),
        synthetic_row(2, raw_file_id="A", canonical_file_id="a", domain="D", relative_path="p"),
    )
    assert evaluate(rows).canonical_json() == evaluate(rows).canonical_json()
    module = Path(__import__("app.manifest.reconciliation_semantics", fromlist=["x"]).__file__).read_text(encoding="utf-8").lower()
    for token in ("pathlib", "os.path", "exists(", "open(", "fastapi", "supportedparser"):
        assert token not in module
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry
    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0
