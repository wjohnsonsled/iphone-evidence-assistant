"""Separate physical-inventory coverage and conservative reconciliation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid5

from app.physical_inventory.inventory import InventoryCompletion, PhysicalInventoryResult
from app.physical_inventory.resolution import PhysicalResolutionObservation, ResolutionOutcome

PROFILE_ID = "physical-inventory-coverage"
PROFILE_VERSION = "1"
_NAMESPACE = UUID("06240000-0000-4000-8000-000000000001")


class ConclusionState(str, Enum):
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    FACTUAL_COUNT_ONLY = "FACTUAL_COUNT_ONLY"


@dataclass(frozen=True, slots=True)
class PhysicalCoverageObservation:
    observation_id: UUID
    inventory_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    processing_run_id: UUID
    profile_id: str
    profile_version: str
    inventory_completion: InventoryCompletion
    physical_entries_observed: int
    candidate_objects_observed: int
    inaccessible_objects: int
    unsupported_objects: int
    resolution_counts: tuple[tuple[str, int], ...]
    complete_no_match_count: int
    partial_no_match_count: int
    absence_conclusion: ConclusionState
    deletion_conclusion: ConclusionState
    duplicate_conclusion: ConclusionState
    orphan_conclusion: ConclusionState
    observed_at: datetime
    limitations: tuple[str, ...]


def observe_physical_coverage(
    inventory: PhysicalInventoryResult,
    resolutions: tuple[PhysicalResolutionObservation, ...],
) -> PhysicalCoverageObservation:
    for item in resolutions:
        if (item.inventory_id != inventory.inventory_id or
                (item.tenant_id, item.case_id, item.evidence_source_id, item.processing_run_id) !=
                (inventory.context.tenant_id, inventory.context.case_id,
                 inventory.context.evidence_source_id, inventory.context.processing_run_id)):
            raise ValueError("physical_coverage_scope_mismatch")
    counts = Counter(item.outcome.value for item in resolutions)
    identity = uuid5(_NAMESPACE, f"{inventory.inventory_id}|{len(resolutions)}|{sorted(counts.items())}")
    return PhysicalCoverageObservation(
        identity, inventory.inventory_id, inventory.context.tenant_id,
        inventory.context.case_id, inventory.context.evidence_source_id,
        inventory.context.processing_run_id, PROFILE_ID, PROFILE_VERSION,
        inventory.completion, inventory.entries_observed,
        inventory.candidate_objects_observed, inventory.inaccessible_objects,
        inventory.unsupported_objects, tuple(sorted(counts.items())),
        counts[ResolutionOutcome.NO_MATCH_INVENTORY_COMPLETE.value],
        counts[ResolutionOutcome.NO_MATCH_INVENTORY_PARTIAL.value],
        ConclusionState.NOT_ESTABLISHED, ConclusionState.NOT_ESTABLISHED,
        ConclusionState.NOT_ESTABLISHED, ConclusionState.NOT_ESTABLISHED,
        datetime.now(timezone.utc),
        (
            "Physical coverage is separate from Manifest row and parser coverage.",
            "Counts describe only observations made within the governed inventory universe.",
            "No-match, repeated names, or unmatched objects do not establish absence, deletion, duplication, orphan status, tampering, or backup completeness.",
            "No capability or artifact is Supported.",
        ),
    )
