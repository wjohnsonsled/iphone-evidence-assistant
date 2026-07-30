"""Synthetic validation corpus for candidate Manifest inventory coverage."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.manifest.files_query import FilesQueryContext, LocatorConfidence, RowLocator
from app.manifest.files_query_v2 import (
    QueryCompletion,
    TerminationReason,
    V2ContinuationToken,
    V2QueryResult,
    V2RowObservation,
)
from app.manifest.inventory_coverage import (
    AbsenceEligibility,
    AuthorizedScopeState,
    CompositionState,
    CoverageTerminationReason,
    InventoryProvenance,
    MutationState,
    ObservationState,
    PhysicalInventoryState,
    ProfileCompatibilityState,
    ProfileReference,
    RequestedScopeState,
    ResourceState,
    ScopeDescriptor,
    compose_continuation_coverage,
    observe_v2_inventory_coverage,
)

NOW = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
IDS = tuple(UUID(int=index) for index in range(1, 20))
QUERY = ProfileReference("manifestdb-files-query-v2", "2")
LOCATOR = ProfileReference("manifestdb-row-locator", "1")
SCHEMA = ProfileReference("manifestdb-files-schema", "1")
RESOURCE = ProfileReference("manifestdb-files-query-resource-policy", "1")
REQUESTED = ScopeDescriptor(
    "manifest-files-rows",
    "Rows in the controlled Manifest.db Files table.",
    ("Files rows",),
    (),
)
AUTHORIZED = ScopeDescriptor(
    "authorized-manifest-files-rows",
    "Authorized rows in the controlled Manifest.db Files table.",
    ("Files rows",),
    (),
)


def _context(run_id: UUID = IDS[7], *, tenant: UUID = IDS[1], case: UUID = IDS[2]):
    return FilesQueryContext(
        tenant,
        case,
        IDS[3],
        IDS[4],
        IDS[6],
        run_id,
        (tenant, case, IDS[3], run_id),
        NOW,
    )


def _row(locator: int, run_id: UUID = IDS[7]) -> V2RowObservation:
    return V2RowObservation(
        run_id,
        IDS[4],
        IDS[6],
        SCHEMA.profile_id,
        SCHEMA.profile_version,
        QUERY.profile_id,
        QUERY.profile_version,
        RowLocator(
            "ROW_LOCATOR_V1",
            locator,
            "1",
            LocatorConfidence.SQLITE_ROWID_CONTROLLED_RUN,
            "Files",
            run_id,
        ),
        (),
        NOW,
        "synthetic-reader",
        "1",
    )


def _result(
    termination: TerminationReason = TerminationReason.COMPLETED,
    *,
    completion: QueryCompletion = QueryCompletion.QUERY_COMPLETE,
    locators: tuple[int, ...] = (1, 2),
    continuation: bool = False,
    run_id: UUID = IDS[7],
    tenant: UUID = IDS[1],
    case: UUID = IDS[2],
) -> V2QueryResult:
    context = _context(run_id, tenant=tenant, case=case)
    token = (
        V2ContinuationToken(
            locators[-1],
            QUERY.profile_id,
            QUERY.profile_version,
            tenant,
            case,
            IDS[3],
            IDS[4],
            IDS[6],
            run_id,
        )
        if continuation and locators
        else None
    )
    return V2QueryResult(
        completion,
        termination,
        context,
        QUERY.profile_id,
        QUERY.profile_version,
        RESOURCE.profile_id,
        RESOURCE.profile_version,
        tuple(_row(value, run_id) for value in locators),
        len(locators),
        len(locators),
        locators[-1] if locators else None,
        token,
        None,
        100,
        200,
        NOW,
        NOW,
        0.0,
        termination.value.lower(),
    )


def _provenance(
    *,
    run_id: UUID = IDS[7],
    sequence: int = 1,
    after: int | None = None,
    prior_run: UUID | None = None,
    prior_observation: UUID | None = None,
    tenant: UUID = IDS[1],
    case: UUID = IDS[2],
    copy: UUID = IDS[5],
    resource: ProfileReference = RESOURCE,
) -> InventoryProvenance:
    return InventoryProvenance(
        IDS[0],
        tenant,
        case,
        IDS[3],
        IDS[4],
        copy,
        IDS[6],
        run_id,
        SCHEMA,
        "sha256:synthetic-schema",
        QUERY,
        LOCATOR,
        (),
        (),
        resource,
        after,
        sequence,
        prior_run,
        prior_observation,
        "CONTINUES_AFTER_LOCATOR" if sequence > 1 else None,
        NOW,
    )


def _observe(
    result: V2QueryResult | None = None,
    provenance: InventoryProvenance | None = None,
    **overrides,
):
    arguments = {
        "requested_scope_state": RequestedScopeState.COMPLETE,
        "authorized_scope_state": AuthorizedScopeState.COMPLETE,
        "mutation_state": MutationState.UNCHANGED,
        "profile_compatibility_state": ProfileCompatibilityState.COMPATIBLE,
        "physical_inventory_state": PhysicalInventoryState.UNAVAILABLE,
        "requested_row_ceiling": 100,
    }
    arguments.update(overrides)
    return observe_v2_inventory_coverage(
        provenance or _provenance(),
        REQUESTED,
        AUTHORIZED,
        result or _result(),
        **arguments,
    )


def test_completed_authorized_row_universe_is_factual_and_fail_closed():
    observation = _observe()
    assert observation.observation_state is ObservationState.COMPLETE
    assert observation.termination_reason is CoverageTerminationReason.COMPLETED
    assert observation.observed_row_count.value == 2
    assert observation.absence_eligibility is AbsenceEligibility.NOT_ELIGIBLE
    assert "required_physical_inventory_not_complete" in observation.blockers
    assert "required_parser_or_interpretation_layer_not_supported" in observation.blockers


@pytest.mark.parametrize(
    ("reason", "resource"),
    (
        (TerminationReason.ROW_LIMIT_REACHED, ResourceState.ROW_LIMIT),
        (TerminationReason.BYTE_LIMIT_REACHED, ResourceState.BYTE_LIMIT),
        (TerminationReason.MEMORY_ESTIMATE_LIMIT_REACHED, ResourceState.MEMORY_ESTIMATE_LIMIT),
        (TerminationReason.WALL_CLOCK_LIMIT_REACHED, ResourceState.WALL_CLOCK_LIMIT),
        (TerminationReason.PAGE_LIMIT_REACHED, ResourceState.PAGE_LIMIT),
    ),
)
def test_resource_termination_preserves_partial_rows(reason, resource):
    observation = _observe(
        _result(reason, completion=QueryCompletion.QUERY_PARTIAL, continuation=True)
    )
    assert observation.observation_state is ObservationState.RESOURCE_TERMINATED
    assert observation.resource_state is resource
    assert observation.last_completed_locator == 2
    assert observation.continuation_available
    assert observation.absence_eligibility is AbsenceEligibility.NOT_ELIGIBLE


@pytest.mark.parametrize(
    ("reason", "completion", "state"),
    (
        (TerminationReason.CALLER_CANCELLED, QueryCompletion.QUERY_PARTIAL, ObservationState.CANCELLED),
        (TerminationReason.CONCURRENCY_LIMIT_REACHED, QueryCompletion.QUERY_FAILED, ObservationState.FAILED),
        (TerminationReason.AUTHORIZATION_FAILURE, QueryCompletion.QUERY_FAILED, ObservationState.FAILED),
        (TerminationReason.SCHEMA_INCOMPATIBLE, QueryCompletion.QUERY_FAILED, ObservationState.FAILED),
        (TerminationReason.SQLITE_READ_FAILURE, QueryCompletion.QUERY_FAILED, ObservationState.FAILED),
        (TerminationReason.INTERNAL_FAILURE, QueryCompletion.QUERY_FAILED, ObservationState.FAILED),
    ),
)
def test_operational_end_states_remain_distinct(reason, completion, state):
    observation = _observe(_result(reason, completion=completion, locators=()))
    assert observation.observation_state is state
    assert observation.absence_eligibility is AbsenceEligibility.NOT_ELIGIBLE
    assert "processing_not_normally_completed" in observation.blockers


def test_mutation_terminates_fail_closed():
    observation = _observe(mutation_state=MutationState.CHANGED)
    assert observation.observation_state is ObservationState.MUTATION_TERMINATED
    assert observation.termination_reason is CoverageTerminationReason.MUTATION_DETECTED
    assert observation.absence_eligibility is AbsenceEligibility.NOT_ELIGIBLE


def _continued(first, *, locators=(3, 5), run_id=IDS[8], **changes):
    provenance = _provenance(
        run_id=run_id,
        sequence=2,
        after=first.last_completed_locator,
        prior_run=first.provenance.processing_run_id,
        prior_observation=first.observation_id,
        **changes,
    )
    return _observe(_result(run_id=run_id, locators=locators), provenance)


def test_perfect_locator_continuation_composes_without_assuming_rowid_adjacency():
    first = _observe(
        _result(
            TerminationReason.ROW_LIMIT_REACHED,
            completion=QueryCompletion.QUERY_PARTIAL,
            continuation=True,
        )
    )
    second = _continued(first)
    composition = compose_continuation_coverage((second, first), expected_component_count=2)
    assert composition.state is CompositionState.COMPLETE_LOGICAL_UNIVERSE
    assert composition.rows_observed == 4
    assert composition.absence_eligibility is AbsenceEligibility.NOT_ELIGIBLE


@pytest.mark.parametrize(
    ("kind", "expected"),
    (
        ("gap", "locator_continuity_gap_or_overlap"),
        ("overlap", "locator_continuity_gap_or_overlap"),
        ("profile", "component_profile_incompatible"),
        ("copy", "component_scope_or_controlled_copy_mismatch"),
        ("resource", "component_profile_incompatible"),
    ),
)
def test_incompatible_continuations_fail_closed(kind, expected):
    first = _observe(
        _result(
            TerminationReason.ROW_LIMIT_REACHED,
            completion=QueryCompletion.QUERY_PARTIAL,
            continuation=True,
        )
    )
    second = _continued(first)
    if kind == "gap":
        second = replace(second, provenance=replace(second.provenance, requested_after_locator=99))
    elif kind == "overlap":
        second = replace(second, provenance=replace(second.provenance, requested_after_locator=1))
    elif kind == "profile":
        second = replace(
            second,
            provenance=replace(
                second.provenance,
                normalization_profiles=(ProfileReference("changed", "1"),),
            ),
        )
    elif kind == "copy":
        second = replace(second, provenance=replace(second.provenance, controlled_copy_identity_id=IDS[9]))
    else:
        second = replace(
            second,
            provenance=replace(
                second.provenance,
                resource_profile=ProfileReference("changed-resource", "1"),
            ),
        )
    composition = compose_continuation_coverage((first, second), expected_component_count=2)
    assert composition.state is CompositionState.INDETERMINATE
    assert expected in composition.blockers


def test_missing_duplicate_and_unresolved_components_are_detected():
    first = _observe(
        _result(
            TerminationReason.ROW_LIMIT_REACHED,
            completion=QueryCompletion.QUERY_PARTIAL,
            continuation=True,
        )
    )
    assert "missing_component_run" in compose_continuation_coverage(
        (first,), expected_component_count=2
    ).blockers
    assert "duplicate_component_run" in compose_continuation_coverage(
        (first, first), expected_component_count=2
    ).blockers
    assert "unresolved_final_continuation" in compose_continuation_coverage(
        (first,), expected_component_count=1
    ).blockers


@pytest.mark.parametrize(
    ("overrides", "blocker"),
    (
        ({"physical_inventory_state": PhysicalInventoryState.UNAVAILABLE}, "required_physical_inventory_not_complete"),
        ({"physical_inventory_state": PhysicalInventoryState.OUTSIDE_SCOPE}, "required_physical_inventory_not_complete"),
        ({"required_layers_supported": False}, "required_parser_or_interpretation_layer_not_supported"),
        ({"excluded_scope": ("excluded-domain",)}, "scope_excluded"),
        ({"unavailable_scope": ("unknown-domain",)}, "scope_unavailable"),
        ({"required_sources_available": False}, "required_source_unavailable"),
        ({"requested_scope_state": RequestedScopeState.UNAVAILABLE}, "requested_scope_not_complete"),
        ({"requested_scope_state": RequestedScopeState.UNSUPPORTED}, "requested_scope_not_complete"),
        ({"authorized_scope_state": AuthorizedScopeState.DENIED}, "authorized_scope_not_complete"),
    ),
)
def test_absence_prerequisites_are_independently_fail_closed(overrides, blocker):
    observation = _observe(**overrides)
    assert blocker in observation.blockers
    assert observation.absence_eligibility is AbsenceEligibility.NOT_ELIGIBLE


def test_indeterminate_mutation_and_profiles_remain_indeterminate():
    assert _observe(
        mutation_state=MutationState.INDETERMINATE
    ).absence_eligibility is AbsenceEligibility.INDETERMINATE
    assert _observe(
        profile_compatibility_state=ProfileCompatibilityState.INDETERMINATE
    ).absence_eligibility is AbsenceEligibility.INDETERMINATE


def test_equivalent_inputs_serialize_deterministically_without_paths_or_blobs():
    first = _observe()
    second = _observe()
    assert first.observation_id == second.observation_id
    assert first.canonical_json() == second.canonical_json()
    serialized = first.canonical_json()
    assert ".pytest-tmp" not in serialized
    assert "\\\\" not in serialized
    assert "raw_blob" not in serialized


@pytest.mark.parametrize(("tenant", "case"), ((IDS[10], IDS[2]), (IDS[1], IDS[10])))
def test_cross_tenant_or_case_result_is_rejected(tenant, case):
    with pytest.raises(ValueError, match="coverage_query_scope_mismatch"):
        _observe(_result(tenant=tenant, case=case))


def test_missing_provenance_is_rejected():
    with pytest.raises(ValueError, match="coverage_provenance_incomplete"):
        replace(_provenance(), schema_fingerprint_reference="")


def test_query_profile_mismatch_is_rejected():
    bad = replace(_result(), query_profile_version="unexpected")
    with pytest.raises(ValueError, match="coverage_query_profile_mismatch"):
        _observe(bad)


def test_resource_profile_mismatch_is_rejected():
    bad = replace(_result(), resource_profile_version="unexpected")
    with pytest.raises(ValueError, match="coverage_resource_profile_mismatch"):
        _observe(bad)


def test_row_provenance_mismatch_is_rejected():
    result = _result()
    bad_row = replace(result.observations[0], source_artifact_id=IDS[10])
    with pytest.raises(ValueError, match="coverage_row_provenance_mismatch"):
        _observe(replace(result, observations=(bad_row, result.observations[1])))


def test_successful_zero_row_universe_is_distinct_from_failure():
    observation = _observe(_result(locators=()))
    assert observation.observation_state is ObservationState.COMPLETE
    assert observation.observed_row_count.value == 0
    assert observation.first_completed_locator is None
    assert observation.last_completed_locator is None


def test_known_excluded_scope_is_counted_and_preserved():
    observation = _observe(excluded_scope=("excluded-domain",))
    assert observation.excluded_count.known
    assert observation.excluded_count.value == 1
    assert observation.excluded_scope == ("excluded-domain",)


def test_no_prohibited_evidentiary_or_support_conclusions():
    text = " ".join(_observe().factual_statements).casefold()
    prohibited = (
        "backup is complete",
        "artifact is absent",
        "no files are missing",
        "parser is supported",
        "user activity is complete",
        "everything was examined",
        "physical object exists",
    )
    assert all(phrase not in text for phrase in prohibited)
    assert "no absence conclusion is permitted" in text
    assert "does not evaluate physical backup objects" in text


def test_registry_and_supported_store_zero_do_not_change_row_coverage():
    registry_count = 0
    supported_normalized_record_count = 0
    observation = _observe(required_layers_supported=registry_count > 0)
    assert registry_count == supported_normalized_record_count == 0
    assert observation.observation_state is ObservationState.COMPLETE
    assert observation.absence_eligibility is AbsenceEligibility.NOT_ELIGIBLE
