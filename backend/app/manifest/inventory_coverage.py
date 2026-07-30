"""Immutable factual coverage for candidate Manifest Files-table inventories."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid5

from app.manifest.files_query_v2 import (
    QueryCompletion,
    TerminationReason as QueryTerminationReason,
    V2QueryResult,
)

PROFILE_ID = "manifestdb-inventory-coverage"
PROFILE_VERSION = "1"
SERIALIZATION_PROFILE_ID = "manifestdb-inventory-coverage-canonical-json"
SERIALIZATION_PROFILE_VERSION = "1"
IMPLEMENTATION_ID = "manifestdb-inventory-coverage-observer"
IMPLEMENTATION_VERSION = "1"
_NAMESPACE = UUID("06080000-0000-4000-8000-000000000001")
LIMITATIONS = (
    "Coverage describes only the performed, authorized Manifest Files-table examination.",
    "Manifest-row coverage is not backup, physical-object, artifact, parser, metadata, normalized-record, or user-activity coverage.",
    "No absence, deletion, missing-object, duplicate, orphan, or completeness conclusion is produced.",
    "A complete row query does not establish that all device or backup evidence was examined.",
    "No capability is Supported by this candidate profile.",
)


class RequestedScopeState(str, Enum):
    COMPLETE = "REQUESTED_SCOPE_COMPLETE"
    PARTIAL = "REQUESTED_SCOPE_PARTIAL"
    UNAVAILABLE = "REQUESTED_SCOPE_UNAVAILABLE"
    UNSUPPORTED = "REQUESTED_SCOPE_UNSUPPORTED"
    NOT_EVALUATED = "REQUESTED_SCOPE_NOT_EVALUATED"


class AuthorizedScopeState(str, Enum):
    COMPLETE = "AUTHORIZED_SCOPE_COMPLETE"
    PARTIAL = "AUTHORIZED_SCOPE_PARTIAL"
    DENIED = "AUTHORIZED_SCOPE_DENIED"
    NOT_ESTABLISHED = "AUTHORIZED_SCOPE_NOT_ESTABLISHED"


class ObservationState(str, Enum):
    COMPLETE = "OBSERVATION_COMPLETE"
    PARTIAL = "OBSERVATION_PARTIAL"
    FAILED = "OBSERVATION_FAILED"
    CANCELLED = "OBSERVATION_CANCELLED"
    RESOURCE_TERMINATED = "OBSERVATION_RESOURCE_TERMINATED"
    MUTATION_TERMINATED = "OBSERVATION_MUTATION_TERMINATED"
    INDETERMINATE = "OBSERVATION_INDETERMINATE"


class CoverageTerminationReason(str, Enum):
    COMPLETED = "COMPLETED"
    ROW_CEILING = "ROW_CEILING"
    PAGE_CEILING = "PAGE_CEILING"
    BYTE_CEILING = "BYTE_CEILING"
    MEMORY_ESTIMATE_CEILING = "MEMORY_ESTIMATE_CEILING"
    WALL_CLOCK_CEILING = "WALL_CLOCK_CEILING"
    CANCELLED = "CANCELLED"
    CONCURRENCY_DENIED = "CONCURRENCY_DENIED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    SCHEMA_DENIED = "SCHEMA_DENIED"
    MUTATION_DETECTED = "MUTATION_DETECTED"
    CONTROLLED_COPY_FAILURE = "CONTROLLED_COPY_FAILURE"
    LOCATOR_FAILURE = "LOCATOR_FAILURE"
    SQLITE_FAILURE = "SQLITE_FAILURE"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResourceState(str, Enum):
    NOT_REACHED = "RESOURCE_NOT_REACHED"
    ROW_LIMIT = "RESOURCE_ROW_LIMIT"
    PAGE_LIMIT = "RESOURCE_PAGE_LIMIT"
    BYTE_LIMIT = "RESOURCE_BYTE_LIMIT"
    MEMORY_ESTIMATE_LIMIT = "RESOURCE_MEMORY_ESTIMATE_LIMIT"
    WALL_CLOCK_LIMIT = "RESOURCE_WALL_CLOCK_LIMIT"
    CONCURRENCY_LIMIT = "RESOURCE_CONCURRENCY_LIMIT"
    NOT_APPLICABLE = "RESOURCE_NOT_APPLICABLE"
    INDETERMINATE = "RESOURCE_INDETERMINATE"


class MutationState(str, Enum):
    UNCHANGED = "MUTATION_UNCHANGED"
    CHANGED = "MUTATION_CHANGED"
    INDETERMINATE = "MUTATION_INDETERMINATE"
    NOT_CHECKED = "MUTATION_NOT_CHECKED"


class ProfileCompatibilityState(str, Enum):
    COMPATIBLE = "PROFILES_COMPATIBLE"
    INCOMPATIBLE = "PROFILES_INCOMPATIBLE"
    INDETERMINATE = "PROFILES_INDETERMINATE"


class ComparisonReadiness(str, Enum):
    READY = "COMPARISON_READY"
    PARTIAL = "COMPARISON_PARTIAL"
    NOT_READY = "COMPARISON_NOT_READY"
    INDETERMINATE = "COMPARISON_INDETERMINATE"


class AbsenceEligibility(str, Enum):
    ELIGIBLE = "ABSENCE_ELIGIBLE"
    NOT_ELIGIBLE = "ABSENCE_NOT_ELIGIBLE"
    INDETERMINATE = "ABSENCE_INDETERMINATE"


class PhysicalInventoryState(str, Enum):
    COMPLETE = "PHYSICAL_INVENTORY_COMPLETE"
    PARTIAL = "PHYSICAL_INVENTORY_PARTIAL"
    UNAVAILABLE = "PHYSICAL_INVENTORY_UNAVAILABLE"
    OUTSIDE_SCOPE = "PHYSICAL_INVENTORY_OUTSIDE_SCOPE"
    NOT_EVALUATED = "PHYSICAL_INVENTORY_NOT_EVALUATED"
    INDETERMINATE = "PHYSICAL_INVENTORY_INDETERMINATE"


class CompositionState(str, Enum):
    COMPLETE_LOGICAL_UNIVERSE = "COMPLETE_LOGICAL_UNIVERSE"
    INDETERMINATE = "COMPOSITION_INDETERMINATE"


@dataclass(frozen=True, slots=True, order=True)
class ProfileReference:
    profile_id: str
    profile_version: str

    def __post_init__(self) -> None:
        if not self.profile_id or not self.profile_version:
            raise ValueError("coverage_profile_reference_incomplete")


@dataclass(frozen=True, slots=True)
class ScopeDescriptor:
    universe_id: str
    definition: str
    included_scope: tuple[str, ...]
    excluded_scope: tuple[str, ...]
    unknown_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.universe_id or not self.definition or not self.included_scope:
            raise ValueError("coverage_scope_incomplete")
        for values in (self.included_scope, self.excluded_scope, self.unknown_scope):
            if tuple(sorted(set(values))) != values:
                raise ValueError("coverage_scope_not_canonical")


@dataclass(frozen=True, slots=True)
class InventoryProvenance:
    inventory_request_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    controlled_copy_identity_id: UUID
    source_database_identity_id: UUID
    processing_run_id: UUID
    schema_profile: ProfileReference
    schema_fingerprint_reference: str
    query_profile: ProfileReference
    locator_profile: ProfileReference
    normalization_profiles: tuple[ProfileReference, ...]
    interpretation_profiles: tuple[ProfileReference, ...]
    resource_profile: ProfileReference
    requested_after_locator: int | None
    run_sequence: int
    prior_processing_run_id: UUID | None
    prior_coverage_observation_id: UUID | None
    prior_relationship: str | None
    observed_at: datetime

    def __post_init__(self) -> None:
        identities = (
            self.inventory_request_id, self.tenant_id, self.case_id,
            self.evidence_source_id, self.source_artifact_id,
            self.controlled_copy_identity_id, self.source_database_identity_id,
            self.processing_run_id,
        )
        if any(not isinstance(item, UUID) for item in identities):
            raise ValueError("coverage_provenance_incomplete")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("coverage_time_invalid")
        if not self.schema_fingerprint_reference or self.run_sequence <= 0:
            raise ValueError("coverage_provenance_incomplete")
        if tuple(sorted(set(self.normalization_profiles))) != self.normalization_profiles:
            raise ValueError("coverage_normalization_profiles_not_canonical")
        if tuple(sorted(set(self.interpretation_profiles))) != self.interpretation_profiles:
            raise ValueError("coverage_interpretation_profiles_not_canonical")
        prior = (
            self.prior_processing_run_id,
            self.prior_coverage_observation_id,
            self.prior_relationship,
        )
        if self.run_sequence == 1:
            if any(value is not None for value in prior) or self.requested_after_locator is not None:
                raise ValueError("coverage_initial_run_prior_invalid")
        elif any(value is None for value in prior) or self.requested_after_locator is None:
            raise ValueError("coverage_continuation_prior_incomplete")


@dataclass(frozen=True, slots=True)
class CoverageCount:
    value: int | None
    known: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.known != (self.value is not None):
            raise ValueError("coverage_count_state_mismatch")
        if self.value is not None and self.value < 0:
            raise ValueError("coverage_count_negative")
        if not self.known and not self.reason:
            raise ValueError("coverage_unknown_count_reason_required")


@dataclass(frozen=True, slots=True)
class InventoryCoverageObservation:
    observation_id: UUID
    provenance: InventoryProvenance
    profile_id: str
    profile_version: str
    serialization_profile_id: str
    serialization_profile_version: str
    requested_scope: ScopeDescriptor
    authorized_scope: ScopeDescriptor | None
    examined_scope: ScopeDescriptor | None
    requested_scope_state: RequestedScopeState
    authorized_scope_state: AuthorizedScopeState
    observation_state: ObservationState
    termination_reason: CoverageTerminationReason
    resource_state: ResourceState
    mutation_state: MutationState
    profile_compatibility_state: ProfileCompatibilityState
    comparison_readiness: ComparisonReadiness
    absence_eligibility: AbsenceEligibility
    physical_inventory_state: PhysicalInventoryState
    first_completed_locator: int | None
    last_completed_locator: int | None
    requested_row_ceiling: int
    observed_row_count: CoverageCount
    finalized_observation_count: CoverageCount
    excluded_count: CoverageCount
    continuation_available: bool
    continuation_after_locator: int | None
    excluded_scope: tuple[str, ...]
    unsupported_scope: tuple[str, ...]
    failed_scope: tuple[str, ...]
    unavailable_scope: tuple[str, ...]
    limitation_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    factual_statements: tuple[str, ...]
    implementation_id: str
    implementation_version: str
    limitations: tuple[str, ...] = LIMITATIONS

    def __post_init__(self) -> None:
        if self.profile_id != PROFILE_ID or self.profile_version != PROFILE_VERSION:
            raise ValueError("coverage_profile_invalid")
        if self.requested_row_ceiling <= 0:
            raise ValueError("coverage_row_ceiling_invalid")
        if not self.limitation_ids or tuple(sorted(set(self.limitation_ids))) != self.limitation_ids:
            raise ValueError("coverage_limitations_invalid")
        for values in (
            self.excluded_scope, self.unsupported_scope, self.failed_scope,
            self.unavailable_scope, self.blockers, self.factual_statements,
        ):
            if tuple(sorted(set(values))) != values:
                raise ValueError("coverage_values_not_canonical")
        if self.observation_state is ObservationState.COMPLETE:
            if (
                self.termination_reason is not CoverageTerminationReason.COMPLETED
                or self.continuation_available
                or not self.observed_row_count.known
                or not self.finalized_observation_count.known
            ):
                raise ValueError("coverage_complete_inconsistent")
        if self.continuation_available != (self.continuation_after_locator is not None):
            raise ValueError("coverage_continuation_inconsistent")
        if self.first_completed_locator is None and self.last_completed_locator is not None:
            raise ValueError("coverage_locator_bounds_invalid")
        if (
            self.first_completed_locator is not None
            and self.last_completed_locator is not None
            and self.first_completed_locator > self.last_completed_locator
        ):
            raise ValueError("coverage_locator_bounds_invalid")
        if self.absence_eligibility is AbsenceEligibility.ELIGIBLE and self.blockers:
            raise ValueError("coverage_absence_eligible_with_blockers")

    def canonical_json(self) -> str:
        payload = asdict(self)
        for key in (
            "inventory_request_id", "tenant_id", "case_id",
            "evidence_source_id", "source_artifact_id",
            "controlled_copy_identity_id", "source_database_identity_id",
            "processing_run_id", "prior_processing_run_id",
            "prior_coverage_observation_id",
        ):
            value = payload["provenance"][key]
            payload["provenance"][key] = str(value) if value is not None else None
        payload["provenance"]["observed_at"] = self.provenance.observed_at.isoformat()
        payload["observation_id"] = str(self.observation_id)
        for key in (
            "requested_scope_state", "authorized_scope_state", "observation_state",
            "termination_reason", "resource_state", "mutation_state",
            "profile_compatibility_state", "comparison_readiness",
            "absence_eligibility", "physical_inventory_state",
        ):
            payload[key] = getattr(self, key).value
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class CoverageComposition:
    composition_id: UUID
    state: CompositionState
    component_observation_ids: tuple[UUID, ...]
    processing_run_ids: tuple[UUID, ...]
    rows_observed: int
    first_completed_locator: int | None
    last_completed_locator: int | None
    comparison_readiness: ComparisonReadiness
    absence_eligibility: AbsenceEligibility
    blockers: tuple[str, ...]
    factual_statements: tuple[str, ...]
    limitations: tuple[str, ...] = LIMITATIONS


_TERMINATION_MAP = {
    QueryTerminationReason.COMPLETED: (
        CoverageTerminationReason.COMPLETED, ResourceState.NOT_REACHED,
    ),
    QueryTerminationReason.ROW_LIMIT_REACHED: (
        CoverageTerminationReason.ROW_CEILING, ResourceState.ROW_LIMIT,
    ),
    QueryTerminationReason.PAGE_LIMIT_REACHED: (
        CoverageTerminationReason.PAGE_CEILING, ResourceState.PAGE_LIMIT,
    ),
    QueryTerminationReason.BYTE_LIMIT_REACHED: (
        CoverageTerminationReason.BYTE_CEILING, ResourceState.BYTE_LIMIT,
    ),
    QueryTerminationReason.MEMORY_ESTIMATE_LIMIT_REACHED: (
        CoverageTerminationReason.MEMORY_ESTIMATE_CEILING,
        ResourceState.MEMORY_ESTIMATE_LIMIT,
    ),
    QueryTerminationReason.WALL_CLOCK_LIMIT_REACHED: (
        CoverageTerminationReason.WALL_CLOCK_CEILING,
        ResourceState.WALL_CLOCK_LIMIT,
    ),
    QueryTerminationReason.CALLER_CANCELLED: (
        CoverageTerminationReason.CANCELLED, ResourceState.NOT_REACHED,
    ),
    QueryTerminationReason.CONCURRENCY_LIMIT_REACHED: (
        CoverageTerminationReason.CONCURRENCY_DENIED,
        ResourceState.CONCURRENCY_LIMIT,
    ),
    QueryTerminationReason.AUTHORIZATION_FAILURE: (
        CoverageTerminationReason.AUTHORIZATION_DENIED,
        ResourceState.NOT_APPLICABLE,
    ),
    QueryTerminationReason.SCHEMA_INCOMPATIBLE: (
        CoverageTerminationReason.SCHEMA_DENIED, ResourceState.NOT_APPLICABLE,
    ),
    QueryTerminationReason.CONTROLLED_COPY_FAILURE: (
        CoverageTerminationReason.CONTROLLED_COPY_FAILURE,
        ResourceState.INDETERMINATE,
    ),
    QueryTerminationReason.LOCATOR_FAILURE: (
        CoverageTerminationReason.LOCATOR_FAILURE, ResourceState.NOT_APPLICABLE,
    ),
    QueryTerminationReason.SQLITE_READ_FAILURE: (
        CoverageTerminationReason.SQLITE_FAILURE, ResourceState.INDETERMINATE,
    ),
    QueryTerminationReason.DATABASE_INVALID: (
        CoverageTerminationReason.SQLITE_FAILURE, ResourceState.INDETERMINATE,
    ),
    QueryTerminationReason.DATABASE_CORRUPT: (
        CoverageTerminationReason.SQLITE_FAILURE, ResourceState.INDETERMINATE,
    ),
    QueryTerminationReason.INTERNAL_FAILURE: (
        CoverageTerminationReason.INTERNAL_FAILURE, ResourceState.INDETERMINATE,
    ),
    QueryTerminationReason.SYSTEM_INTERRUPTED: (
        CoverageTerminationReason.INTERNAL_FAILURE, ResourceState.INDETERMINATE,
    ),
    QueryTerminationReason.NOT_APPLICABLE: (
        CoverageTerminationReason.NOT_APPLICABLE, ResourceState.NOT_APPLICABLE,
    ),
}


def observe_v2_inventory_coverage(
    provenance: InventoryProvenance,
    requested_scope: ScopeDescriptor,
    authorized_scope: ScopeDescriptor | None,
    result: V2QueryResult,
    *,
    requested_scope_state: RequestedScopeState,
    authorized_scope_state: AuthorizedScopeState,
    mutation_state: MutationState,
    profile_compatibility_state: ProfileCompatibilityState,
    physical_inventory_state: PhysicalInventoryState,
    requested_row_ceiling: int,
    excluded_scope: tuple[str, ...] = (),
    unsupported_scope: tuple[str, ...] = (),
    failed_scope: tuple[str, ...] = (),
    unavailable_scope: tuple[str, ...] = (),
    required_layers_supported: bool = False,
    comparison_requires_physical_inventory: bool = True,
    required_sources_available: bool = True,
) -> InventoryCoverageObservation:
    context = result.context
    expected_scope = (
        provenance.tenant_id, provenance.case_id, provenance.evidence_source_id,
        provenance.source_artifact_id, provenance.source_database_identity_id,
        provenance.processing_run_id,
    )
    actual_scope = (
        context.tenant_id, context.case_id, context.evidence_source_id,
        context.source_artifact_id, context.database_identity_id,
        context.processing_run_id,
    )
    if expected_scope != actual_scope:
        raise ValueError("coverage_query_scope_mismatch")
    if (
        result.query_profile_id != provenance.query_profile.profile_id
        or result.query_profile_version != provenance.query_profile.profile_version
    ):
        raise ValueError("coverage_query_profile_mismatch")
    if (
        result.resource_profile_id != provenance.resource_profile.profile_id
        or result.resource_profile_version != provenance.resource_profile.profile_version
    ):
        raise ValueError("coverage_resource_profile_mismatch")
    expected_row_scope = (
        provenance.processing_run_id,
        provenance.source_artifact_id,
        provenance.source_database_identity_id,
        provenance.schema_profile.profile_id,
        provenance.schema_profile.profile_version,
        provenance.query_profile.profile_id,
        provenance.query_profile.profile_version,
    )
    if any(
        (
            row.processing_run_id,
            row.source_artifact_id,
            row.database_identity_id,
            row.schema_profile_id,
            row.schema_profile_version,
            row.query_profile_id,
            row.query_profile_version,
        )
        != expected_row_scope
        for row in result.observations
    ):
        raise ValueError("coverage_row_provenance_mismatch")
    if requested_row_ceiling <= 0:
        raise ValueError("coverage_row_ceiling_invalid")

    termination, resource = _TERMINATION_MAP[result.termination_reason]
    if mutation_state is MutationState.CHANGED:
        observation = ObservationState.MUTATION_TERMINATED
        termination = CoverageTerminationReason.MUTATION_DETECTED
    elif result.completion is QueryCompletion.QUERY_COMPLETE:
        observation = ObservationState.COMPLETE
    elif result.termination_reason is QueryTerminationReason.CALLER_CANCELLED:
        observation = ObservationState.CANCELLED
    elif resource in {
        ResourceState.ROW_LIMIT, ResourceState.PAGE_LIMIT,
        ResourceState.BYTE_LIMIT, ResourceState.MEMORY_ESTIMATE_LIMIT,
        ResourceState.WALL_CLOCK_LIMIT,
    }:
        observation = ObservationState.RESOURCE_TERMINATED
    elif result.completion is QueryCompletion.QUERY_PARTIAL:
        observation = ObservationState.PARTIAL
    elif result.completion is QueryCompletion.QUERY_FAILED:
        observation = ObservationState.FAILED
    else:
        observation = ObservationState.INDETERMINATE

    first = (
        result.observations[0].row_locator.locator_value
        if result.observations else None
    )
    last = result.last_completed_locator
    continuation = result.continuation is not None
    blockers: list[str] = []
    if requested_scope_state is not RequestedScopeState.COMPLETE:
        blockers.append("requested_scope_not_complete")
    if authorized_scope_state is not AuthorizedScopeState.COMPLETE:
        blockers.append("authorized_scope_not_complete")
    if observation is not ObservationState.COMPLETE:
        blockers.append("observation_not_complete")
    if termination is not CoverageTerminationReason.COMPLETED:
        blockers.append("processing_not_normally_completed")
    if resource is not ResourceState.NOT_REACHED:
        blockers.append("resource_or_operational_limit_present")
    if mutation_state is not MutationState.UNCHANGED:
        blockers.append("mutation_state_not_unchanged")
    if profile_compatibility_state is not ProfileCompatibilityState.COMPATIBLE:
        blockers.append("profiles_not_compatible")
    if continuation:
        blockers.append("unresolved_continuation")
    if not required_sources_available:
        blockers.append("required_source_unavailable")
    if excluded_scope:
        blockers.append("scope_excluded")
    if unsupported_scope:
        blockers.append("scope_unsupported")
    if failed_scope:
        blockers.append("scope_failed")
    if unavailable_scope:
        blockers.append("scope_unavailable")
    if not required_layers_supported:
        blockers.append("required_parser_or_interpretation_layer_not_supported")
    physical_ready = physical_inventory_state is PhysicalInventoryState.COMPLETE
    if comparison_requires_physical_inventory and not physical_ready:
        blockers.append("required_physical_inventory_not_complete")

    if mutation_state is MutationState.INDETERMINATE or profile_compatibility_state is ProfileCompatibilityState.INDETERMINATE:
        comparison = ComparisonReadiness.INDETERMINATE
        absence = AbsenceEligibility.INDETERMINATE
    elif blockers:
        comparison = (
            ComparisonReadiness.PARTIAL
            if result.rows_completed > 0 and observation is not ObservationState.FAILED
            else ComparisonReadiness.NOT_READY
        )
        absence = AbsenceEligibility.NOT_ELIGIBLE
    else:
        comparison = ComparisonReadiness.READY
        absence = AbsenceEligibility.ELIGIBLE

    statements = [
        "No absence conclusion is permitted."
        if absence is not AbsenceEligibility.ELIGIBLE
        else "All recorded prerequisites for a future approved absence evaluation are satisfied.",
        "This profile does not evaluate physical backup objects.",
    ]
    if observation is ObservationState.COMPLETE:
        statements.append(
            "The authorized Files-table row universe was fully enumerated under the specified query profile."
        )
    elif continuation:
        statements.append(
            "The requested universe was not fully observed; continuation remains available after the recorded locator."
        )
    else:
        statements.append("The requested universe was not fully observed.")
    if observation is ObservationState.RESOURCE_TERMINATED:
        statements.append(
            "Processing terminated after the recorded locator due to the configured resource ceiling."
        )
    if mutation_state is MutationState.CHANGED:
        statements.append("The coverage state is indeterminate because the controlled copy changed.")

    examined_scope = ScopeDescriptor(
        universe_id=f"{requested_scope.universe_id}:examined",
        definition="Finalized Files-table row observations in this processing run.",
        included_scope=("Files rows finalized under the recorded locator bounds",),
        excluded_scope=tuple(sorted(set(excluded_scope))),
        unknown_scope=(
            ("Rows beyond the continuation locator",) if continuation else ()
        ),
    )
    observed_count = CoverageCount(result.rows_completed, True)
    finalized_count = CoverageCount(len(result.observations), True)
    excluded_count = (
        CoverageCount(len(excluded_scope), True)
        if excluded_scope
        else CoverageCount(0, True)
    )
    limitation_ids = tuple(
        sorted((
            "LIMIT-MANIFEST-ROWS-NOT-ARTIFACT-COVERAGE",
            "LIMIT-NO-BACKUP-COMPLETENESS",
            "LIMIT-NO-EVIDENCE-ABSENCE",
            "LIMIT-NO-PHYSICAL-INVENTORY",
            "LIMIT-NO-SUPPORT",
        ))
    )
    identity_text = "|".join((
        str(provenance.inventory_request_id), str(provenance.processing_run_id),
        str(result.query_profile_id), str(result.query_profile_version),
        observation.value, termination.value, str(first), str(last),
        str(result.rows_completed), PROFILE_ID, PROFILE_VERSION,
    ))
    return InventoryCoverageObservation(
        uuid5(_NAMESPACE, identity_text), provenance, PROFILE_ID, PROFILE_VERSION,
        SERIALIZATION_PROFILE_ID, SERIALIZATION_PROFILE_VERSION,
        requested_scope, authorized_scope, examined_scope, requested_scope_state,
        authorized_scope_state, observation, termination, resource,
        mutation_state, profile_compatibility_state, comparison, absence,
        physical_inventory_state, first, last, requested_row_ceiling,
        observed_count, finalized_count, excluded_count, continuation,
        last if continuation else None, tuple(sorted(set(excluded_scope))),
        tuple(sorted(set(unsupported_scope))), tuple(sorted(set(failed_scope))),
        tuple(sorted(set(unavailable_scope))), limitation_ids,
        tuple(sorted(set(blockers))), tuple(sorted(set(statements))),
        IMPLEMENTATION_ID, IMPLEMENTATION_VERSION,
    )


def compose_continuation_coverage(
    observations: tuple[InventoryCoverageObservation, ...],
    *,
    expected_component_count: int,
) -> CoverageComposition:
    if expected_component_count <= 0:
        raise ValueError("coverage_expected_component_count_invalid")
    if not observations:
        raise ValueError("coverage_components_required")
    ordered = tuple(sorted(observations, key=lambda item: item.provenance.run_sequence))
    blockers: list[str] = []
    if len(ordered) != expected_component_count:
        blockers.append("missing_component_run")
    run_ids = tuple(item.provenance.processing_run_id for item in ordered)
    if len(set(run_ids)) != len(run_ids):
        blockers.append("duplicate_component_run")
    sequences = tuple(item.provenance.run_sequence for item in ordered)
    if sequences != tuple(range(1, len(ordered) + 1)):
        blockers.append("component_sequence_gap")

    first = ordered[0]
    scope = (
        first.provenance.tenant_id, first.provenance.case_id,
        first.provenance.evidence_source_id, first.provenance.source_artifact_id,
        first.provenance.controlled_copy_identity_id,
        first.provenance.source_database_identity_id,
    )
    profiles = (
        first.provenance.schema_profile,
        first.provenance.schema_fingerprint_reference,
        first.provenance.query_profile,
        first.provenance.locator_profile,
        first.provenance.normalization_profiles,
        first.provenance.interpretation_profiles,
        first.provenance.resource_profile,
    )
    for item in ordered:
        item_scope = (
            item.provenance.tenant_id, item.provenance.case_id,
            item.provenance.evidence_source_id, item.provenance.source_artifact_id,
            item.provenance.controlled_copy_identity_id,
            item.provenance.source_database_identity_id,
        )
        if item_scope != scope:
            blockers.append("component_scope_or_controlled_copy_mismatch")
        item_profiles = (
            item.provenance.schema_profile,
            item.provenance.schema_fingerprint_reference,
            item.provenance.query_profile,
            item.provenance.locator_profile,
            item.provenance.normalization_profiles,
            item.provenance.interpretation_profiles,
            item.provenance.resource_profile,
        )
        if item_profiles != profiles:
            blockers.append("component_profile_incompatible")
        if item.mutation_state is not MutationState.UNCHANGED:
            blockers.append("component_mutation_not_unchanged")

    for previous, current in zip(ordered, ordered[1:]):
        if (
            not previous.continuation_available
            or previous.last_completed_locator is None
            or current.provenance.requested_after_locator
            != previous.last_completed_locator
            or current.provenance.prior_processing_run_id
            != previous.provenance.processing_run_id
            or current.provenance.prior_coverage_observation_id
            != previous.observation_id
        ):
            blockers.append("locator_continuity_gap_or_overlap")
    if ordered[-1].continuation_available:
        blockers.append("unresolved_final_continuation")
    if ordered[-1].observation_state is not ObservationState.COMPLETE:
        blockers.append("final_component_not_complete")
    if any(not item.observed_row_count.known for item in ordered):
        blockers.append("component_count_unknown")

    unique_blockers = tuple(sorted(set(blockers)))
    complete = not unique_blockers
    state = (
        CompositionState.COMPLETE_LOGICAL_UNIVERSE
        if complete else CompositionState.INDETERMINATE
    )
    statements = (
        (
            "Compatible component runs form one complete logical Files-table row universe.",
            "This combined view does not establish backup, artifact, physical-object, or user-activity completeness.",
            "No absence conclusion is permitted.",
        )
        if complete
        else (
            "Component runs do not establish one complete logical Files-table row universe.",
            "No absence conclusion is permitted.",
        )
    )
    rows = sum(
        item.observed_row_count.value or 0
        for item in ordered if item.observed_row_count.known
    )
    component_ids = tuple(item.observation_id for item in ordered)
    identity_text = "|".join((
        *(str(item) for item in component_ids), state.value,
        str(expected_component_count), PROFILE_ID, PROFILE_VERSION,
    ))
    return CoverageComposition(
        uuid5(_NAMESPACE, identity_text), state, component_ids, run_ids, rows,
        ordered[0].first_completed_locator, ordered[-1].last_completed_locator,
        (
            ComparisonReadiness.READY
            if complete and all(
                item.comparison_readiness is ComparisonReadiness.READY
                for item in ordered
            )
            else ComparisonReadiness.NOT_READY
        ),
        AbsenceEligibility.NOT_ELIGIBLE,
        unique_blockers, tuple(sorted(statements)),
    )
