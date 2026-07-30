"""Candidate-only Manifest repetition and reconciliation semantics."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable
from uuid import UUID, uuid5

PROFILE_ID = "manifestdb-reconciliation-semantics"
PROFILE_VERSION = "1"
_NAMESPACE = UUID("06090000-0000-4000-8000-000000000001")
LIMITATIONS = (
    "Repeated Manifest values are pattern observations, not duplicate-file or duplicate-content conclusions.",
    "No physical-object inventory or resolution was performed.",
    "Orphan, missing-object, and absence conclusions are not established.",
    "Partial, unavailable, resource-terminated, or incompatible universes remain indeterminate.",
    "No capability is Supported by this candidate profile.",
)


class PatternKind(str, Enum):
    REPEATED_ROW_LOCATOR = "REPEATED_ROW_LOCATOR"
    REPEATED_RAW_FILE_ID = "REPEATED_RAW_FILE_ID"
    REPEATED_CANONICAL_FILE_ID = "REPEATED_CANONICAL_FILE_ID"
    REPEATED_DOMAIN_PATH_TUPLE = "REPEATED_DOMAIN_PATH_TUPLE"


class EvaluationState(str, Enum):
    COMPLETE_PATTERN_OBSERVATION = "COMPLETE_PATTERN_OBSERVATION"
    ZERO_PATTERNS_OBSERVED = "ZERO_PATTERNS_OBSERVED"
    PARTIAL_RESOURCE_LIMIT = "PARTIAL_RESOURCE_LIMIT"
    CANCELLED = "CANCELLED"
    INDETERMINATE = "INDETERMINATE"


class ConclusionState(str, Enum):
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


@dataclass(frozen=True, slots=True)
class ReconciliationPolicy:
    max_rows: int
    max_groups: int
    max_group_members: int
    max_projected_bytes: int
    max_memory_estimate: int
    max_wall_seconds: float

    def __post_init__(self) -> None:
        integers = (
            self.max_rows, self.max_groups, self.max_group_members,
            self.max_projected_bytes, self.max_memory_estimate,
        )
        if any(type(value) is not int or value <= 0 for value in integers):
            raise ValueError("reconciliation_policy_invalid")
        if type(self.max_wall_seconds) not in {int, float} or self.max_wall_seconds <= 0:
            raise ValueError("reconciliation_policy_invalid")


@dataclass(frozen=True, slots=True)
class ManifestReferenceObservation:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    controlled_copy_identity_id: UUID
    database_identity_id: UUID
    processing_run_id: UUID
    row_locator: int
    query_profile_id: str
    query_profile_version: str
    locator_profile_id: str
    locator_profile_version: str
    raw_file_id: str | bytes | None
    canonical_file_id: str | None
    file_id_profile_id: str
    file_id_profile_version: str
    domain: str | None
    domain_profile_id: str
    domain_profile_version: str
    relative_path: str | None
    path_profile_id: str
    path_profile_version: str
    observed_at: datetime

    def __post_init__(self) -> None:
        identities = (
            self.tenant_id, self.case_id, self.evidence_source_id,
            self.source_artifact_id, self.controlled_copy_identity_id,
            self.database_identity_id, self.processing_run_id,
        )
        if any(not isinstance(item, UUID) for item in identities):
            raise ValueError("reconciliation_provenance_incomplete")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("reconciliation_time_invalid")
        expected = (
            ("manifestdb-files-query", {"1", "2"}, self.query_profile_id, self.query_profile_version),
            ("manifestdb-row-locator", {"1"}, self.locator_profile_id, self.locator_profile_version),
            ("manifestdb-fileid-normalization", {"1"}, self.file_id_profile_id, self.file_id_profile_version),
            ("manifestdb-domain-grammar", {"1"}, self.domain_profile_id, self.domain_profile_version),
            ("manifestdb-relative-path-lexical", {"1"}, self.path_profile_id, self.path_profile_version),
        )
        if any(actual_id != profile_id or actual_version not in versions for profile_id, versions, actual_id, actual_version in expected):
            raise ValueError("reconciliation_profile_incompatible")


@dataclass(frozen=True, slots=True)
class PatternObservation:
    kind: PatternKind
    comparison_key: str
    row_locators: tuple[int, ...]
    member_count: int
    limitation: str


@dataclass(frozen=True, slots=True)
class ReconciliationObservation:
    observation_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    processing_run_id: UUID
    profile_id: str
    profile_version: str
    evaluation_state: EvaluationState
    rows_supplied: int
    rows_evaluated: int
    patterns: tuple[PatternObservation, ...]
    duplicate_conclusion: ConclusionState
    orphan_conclusion: ConclusionState
    missing_object_conclusion: ConclusionState
    absence_conclusion: ConclusionState
    physical_inventory_observed: bool
    comparison_universe_complete: bool
    blockers: tuple[str, ...]
    projected_bytes: int
    memory_estimate: int
    observed_at: datetime
    limitations: tuple[str, ...] = LIMITATIONS

    def canonical_json(self) -> str:
        payload = asdict(self)
        for key in (
            "observation_id", "tenant_id", "case_id", "evidence_source_id",
            "source_artifact_id", "processing_run_id",
        ):
            payload[key] = str(payload[key])
        payload["evaluation_state"] = self.evaluation_state.value
        for key in (
            "duplicate_conclusion", "orphan_conclusion",
            "missing_object_conclusion", "absence_conclusion",
        ):
            payload[key] = getattr(self, key).value
        payload["patterns"] = [
            {**asdict(pattern), "kind": pattern.kind.value} for pattern in self.patterns
        ]
        payload["observed_at"] = self.observed_at.isoformat()
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def evaluate_reconciliation(
    rows: tuple[ManifestReferenceObservation, ...],
    policy: ReconciliationPolicy,
    *,
    cancel: Callable[[], bool] = lambda: False,
    monotonic: Callable[[], float],
    observed_at: datetime,
) -> ReconciliationObservation:
    if not rows:
        raise ValueError("reconciliation_rows_required")
    scope = (
        rows[0].tenant_id, rows[0].case_id, rows[0].evidence_source_id,
        rows[0].source_artifact_id, rows[0].processing_run_id,
    )
    if any(
        (row.tenant_id, row.case_id, row.evidence_source_id, row.source_artifact_id, row.processing_run_id) != scope
        for row in rows
    ):
        raise ValueError("reconciliation_scope_mismatch")
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("reconciliation_time_invalid")

    started = monotonic()
    groups: dict[tuple[PatternKind, str], list[int]] = {}
    projected = memory = evaluated = 0
    state = EvaluationState.COMPLETE_PATTERN_OBSERVATION
    blocker: str | None = None
    for row in rows:
        if cancel():
            state, blocker = EvaluationState.CANCELLED, "evaluation_cancelled"
            break
        if monotonic() - started >= policy.max_wall_seconds:
            state, blocker = EvaluationState.PARTIAL_RESOURCE_LIMIT, "wall_time_limit"
            break
        # Raw BLOB bytes remain non-serializable and are not transformed into
        # an invented text identifier. Canonical comparison, when available,
        # remains separately profile-qualified.
        raw = row.raw_file_id if isinstance(row.raw_file_id, str) else None
        keys = (
            (PatternKind.REPEATED_ROW_LOCATOR, str(row.row_locator)),
            (PatternKind.REPEATED_RAW_FILE_ID, raw),
            (PatternKind.REPEATED_CANONICAL_FILE_ID, row.canonical_file_id),
            (
                PatternKind.REPEATED_DOMAIN_PATH_TUPLE,
                None if row.domain is None or row.relative_path is None else f"{row.domain}\u0000{row.relative_path}",
            ),
        )
        row_bytes = sum(len(value.encode("utf-8")) for _, value in keys if value is not None)
        next_projected = projected + row_bytes
        next_memory = memory + 128 + row_bytes
        if evaluated >= policy.max_rows:
            state, blocker = EvaluationState.PARTIAL_RESOURCE_LIMIT, "row_limit"
            break
        if next_projected > policy.max_projected_bytes:
            state, blocker = EvaluationState.PARTIAL_RESOURCE_LIMIT, "projected_bytes_limit"
            break
        if next_memory > policy.max_memory_estimate:
            state, blocker = EvaluationState.PARTIAL_RESOURCE_LIMIT, "memory_estimate_limit"
            break
        active_keys = tuple((kind, key) for kind, key in keys if key is not None)
        if any(
            len(groups.get((kind, key), ())) >= policy.max_group_members
            for kind, key in active_keys
        ):
            state, blocker = EvaluationState.PARTIAL_RESOURCE_LIMIT, "group_member_limit"
            break
        for kind, key in active_keys:
            groups.setdefault((kind, key), []).append(row.row_locator)
        if blocker:
            break
        projected, memory, evaluated = next_projected, next_memory, evaluated + 1

    patterns = tuple(
        PatternObservation(
            kind, key, tuple(locators), len(locators),
            "Repeated values are lexical/source-row patterns only; no duplicate or physical identity is established.",
        )
        for (kind, key), locators in sorted(groups.items(), key=lambda item: (item[0][0].value, item[0][1]))
        if len(locators) > 1
    )
    if len(patterns) > policy.max_groups:
        patterns = patterns[:policy.max_groups]
        state, blocker = EvaluationState.PARTIAL_RESOURCE_LIMIT, "group_count_limit"
    elif state is EvaluationState.COMPLETE_PATTERN_OBSERVATION and not patterns:
        state = EvaluationState.ZERO_PATTERNS_OBSERVED

    blockers = (
        "physical_inventory_not_observed",
        "comparison_universe_not_complete",
        "physical_resolution_not_authorized",
        "support_not_approved",
    ) + ((blocker,) if blocker else ())
    stable = uuid5(_NAMESPACE, "|".join((
        *(str(value) for value in scope), str(len(rows)), str(evaluated),
        state.value, PROFILE_ID, PROFILE_VERSION,
    )))
    return ReconciliationObservation(
        stable, *scope, PROFILE_ID, PROFILE_VERSION, state, len(rows), evaluated,
        patterns, ConclusionState.NOT_ESTABLISHED, ConclusionState.NOT_ESTABLISHED,
        ConclusionState.NOT_ESTABLISHED, ConclusionState.NOT_ESTABLISHED,
        False, False, blockers, projected, memory, observed_at,
    )


def synthetic_row(
    row_locator: int,
    *,
    raw_file_id: str | bytes | None,
    canonical_file_id: str | None,
    domain: str | None,
    relative_path: str | None,
    tenant_seed: int = 1,
) -> ManifestReferenceObservation:
    def uid(n: int) -> UUID:
        return UUID(f"06090000-0000-4000-8000-{n:012d}")
    return ManifestReferenceObservation(
        uid(tenant_seed), uid(2), uid(3), uid(4), uid(5), uid(6), uid(7),
        row_locator, "manifestdb-files-query", "2", "manifestdb-row-locator",
        "1", raw_file_id, canonical_file_id, "manifestdb-fileid-normalization",
        "1", domain, "manifestdb-domain-grammar", "1", relative_path,
        "manifestdb-relative-path-lexical", "1",
        datetime(2026, 7, 30, tzinfo=timezone.utc),
    )
