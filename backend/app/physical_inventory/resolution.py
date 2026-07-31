"""Candidate Manifest fileID to physical-object resolution semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid5

from app.manifest.identifier_normalization import IdentifierObservation
from app.physical_inventory.inventory import (
    InventoryCompletion,
    LayoutClassification,
    PhysicalEntryObservation,
    PhysicalInventoryResult,
)

PROFILE_ID = "manifest-fileid-physical-object-resolution"
PROFILE_VERSION = "1"
_NAMESPACE = UUID("06230000-0000-4000-8000-000000000001")

LIMITATIONS = (
    "This exact mapping is provisional and synthetically characterized, not Apple-authoritative.",
    "A match identifies a filename observation only; it does not prove content meaning, authenticity, extraction success, or artifact support.",
    "No match is not evidence of deletion, absence from the device, tampering, or backup incompleteness.",
)


class ResolutionOutcome(str, Enum):
    EXACT_SINGLE_MATCH = "EXACT_SINGLE_MATCH"
    EXACT_MULTIPLE_MATCHES = "EXACT_MULTIPLE_MATCHES"
    NO_MATCH_INVENTORY_COMPLETE = "NO_MATCH_INVENTORY_COMPLETE"
    NO_MATCH_INVENTORY_PARTIAL = "NO_MATCH_INVENTORY_PARTIAL"
    IDENTIFIER_NOT_COMPARABLE = "IDENTIFIER_NOT_COMPARABLE"
    PHYSICAL_OBJECT_INACCESSIBLE = "PHYSICAL_OBJECT_INACCESSIBLE"
    PHYSICAL_OBJECT_UNSUPPORTED = "PHYSICAL_OBJECT_UNSUPPORTED"
    SOURCE_SCOPE_MISMATCH = "SOURCE_SCOPE_MISMATCH"
    PROFILE_INCOMPATIBLE = "PROFILE_INCOMPATIBLE"
    VALIDATION_FAILED = "VALIDATION_FAILED"


@dataclass(frozen=True, slots=True)
class PhysicalResolutionObservation:
    observation_id: UUID
    outcome: ResolutionOutcome
    identifier_observation_id: UUID
    inventory_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    processing_run_id: UUID
    profile_id: str
    profile_version: str
    canonical_file_id: str | None
    expected_prefix: str | None
    matched_observation_ids: tuple[UUID, ...]
    matched_locator_ids: tuple[UUID, ...]
    inventory_completion: InventoryCompletion
    reason_code: str
    observed_at: datetime
    limitations: tuple[str, ...] = LIMITATIONS


def resolve_manifest_fileid(
    identifier: IdentifierObservation,
    inventory: PhysicalInventoryResult,
) -> PhysicalResolutionObservation:
    source = identifier.source
    canonical = identifier.canonical_representation
    base = dict(
        identifier_observation_id=identifier.observation_id,
        inventory_id=inventory.inventory_id,
        tenant_id=source.tenant_id,
        case_id=source.case_id,
        evidence_source_id=source.evidence_source_id,
        processing_run_id=source.processing_run_id,
        profile_id=PROFILE_ID,
        profile_version=PROFILE_VERSION,
        canonical_file_id=canonical,
        expected_prefix=canonical[:2] if canonical else None,
        inventory_completion=inventory.completion,
        observed_at=datetime.now(timezone.utc),
    )

    def build(outcome: ResolutionOutcome, reason: str,
              matches: tuple[PhysicalEntryObservation, ...] = ()) -> PhysicalResolutionObservation:
        identity = "|".join((str(identifier.observation_id), str(inventory.inventory_id), outcome.value))
        return PhysicalResolutionObservation(
            observation_id=uuid5(_NAMESPACE, identity), outcome=outcome,
            matched_observation_ids=tuple(item.observation_id for item in matches),
            matched_locator_ids=tuple(item.locator.locator_id for item in matches),
            reason_code=reason, **base,
        )

    context = inventory.context
    if (source.tenant_id, source.case_id, source.evidence_source_id, source.processing_run_id) != (
            context.tenant_id, context.case_id, context.evidence_source_id, context.processing_run_id):
        return build(ResolutionOutcome.SOURCE_SCOPE_MISMATCH, "resolution_scope_mismatch")
    if identifier.normalization_profile_id != "manifestdb-fileid-normalization" or identifier.normalization_profile_version != "1":
        return build(ResolutionOutcome.PROFILE_INCOMPATIBLE, "identifier_profile_incompatible")
    if not canonical:
        return build(ResolutionOutcome.IDENTIFIER_NOT_COMPARABLE, "identifier_not_comparable")

    same_name = tuple(item for item in inventory.observations
                      if item.filename.canonical_comparison == canonical)
    eligible = tuple(item for item in same_name
                     if item.eligible_candidate_object and
                     item.layout_classification is LayoutClassification.CANDIDATE_PHYSICAL_OBJECT and
                     item.locator.relative_components[:-1] == (canonical[:2],))
    if len(eligible) == 1:
        return build(ResolutionOutcome.EXACT_SINGLE_MATCH, "exact_single_filename_match", eligible)
    if len(eligible) > 1:
        return build(ResolutionOutcome.EXACT_MULTIPLE_MATCHES, "exact_multiple_filename_matches", eligible)
    if any(not item.accessible for item in same_name):
        return build(ResolutionOutcome.PHYSICAL_OBJECT_INACCESSIBLE, "matching_name_inaccessible", same_name)
    if same_name:
        return build(ResolutionOutcome.PHYSICAL_OBJECT_UNSUPPORTED, "matching_name_not_eligible", same_name)
    if inventory.completion is InventoryCompletion.COMPLETE:
        return build(ResolutionOutcome.NO_MATCH_INVENTORY_COMPLETE, "no_matching_object_observed_complete_inventory")
    if inventory.completion in {InventoryCompletion.PARTIAL, InventoryCompletion.RESOURCE_TERMINATED,
                                InventoryCompletion.CANCELLED, InventoryCompletion.MUTATION_TERMINATED}:
        return build(ResolutionOutcome.NO_MATCH_INVENTORY_PARTIAL, "no_matching_object_observed_partial_inventory")
    return build(ResolutionOutcome.VALIDATION_FAILED, "inventory_not_defensibly_resolvable")
