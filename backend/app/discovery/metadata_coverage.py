"""Factual coverage projection for the candidate Apple metadata measurable set."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.discovery.apple_backup import (
    DiscoveryResult,
    DiscoveryState,
    MetadataObservation,
    ValueState,
)
from app.discovery.metadata_normalization import (
    NormalizationState,
    NormalizedMetadataValue,
)

COVERAGE_PROFILE_ID = "apple-backup-metadata-coverage"
COVERAGE_PROFILE_VERSION = "1"
MEASURABLE_SET = (
    (".", None),
    ("Info.plist", "Product Version"),
    ("Info.plist", "Target Identifier"),
    ("Info.plist", "Unique Identifier"),
    ("Manifest.plist", "IsEncrypted"),
    ("Status.plist", "SnapshotState"),
)
LIMITATIONS = (
    "Coverage describes only the six-item candidate metadata measurable set.",
    "It does not establish completeness of the backup, device, or evidence.",
    "Missing metadata does not prove deletion, concealment, destruction, or absence from the device.",
    "Coverage does not establish Apple compatibility, parser support, artifact support, or support status.",
)


class MetadataCoverageState(str, Enum):
    OBSERVED_NORMALIZED = "OBSERVED_NORMALIZED"
    OBSERVED_RAW_ONLY = "OBSERVED_RAW_ONLY"
    FIELD_MISSING = "FIELD_MISSING"
    SOURCE_ABSENT = "SOURCE_ABSENT"
    SOURCE_INACCESSIBLE = "SOURCE_INACCESSIBLE"
    SOURCE_INVALID_TYPE = "SOURCE_INVALID_TYPE"
    SOURCE_MALFORMED = "SOURCE_MALFORMED"
    VALUE_UNSUPPORTED = "VALUE_UNSUPPORTED"
    DISCOVERY_FAILED = "DISCOVERY_FAILED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class MetadataCoverageEntry:
    source_file: str
    source_field: str | None
    source_artifact_id: UUID
    state: MetadataCoverageState
    observation_index: int | None
    normalization_profile_reference: str | None
    reason_code: str


@dataclass(frozen=True, slots=True)
class MetadataCoverageReport:
    profile_id: str
    profile_version: str
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    processing_run_id: UUID
    measurable_set_name: str
    denominator: int
    entries: tuple[MetadataCoverageEntry, ...]
    state_counts: tuple[tuple[MetadataCoverageState, int], ...]
    limitations: tuple[str, ...] = LIMITATIONS


def _artifact_state(result: DiscoveryResult, source_file: str) -> tuple[UUID, MetadataCoverageState, str]:
    if source_file == ".":
        return (
            result.context.backup_root_artifact_id,
            MetadataCoverageState.INDETERMINATE,
            "root_observation_missing",
        )
    artifact = next(item for item in result.artifacts if item.source_file == source_file)
    if artifact.failure_code == "plist_malformed":
        return (
            artifact.source_artifact_id,
            MetadataCoverageState.SOURCE_MALFORMED,
            "metadata_source_malformed",
        )
    mapping = {
        DiscoveryState.ABSENT: (MetadataCoverageState.SOURCE_ABSENT, "metadata_source_absent"),
        DiscoveryState.PRESENT_INACCESSIBLE: (
            MetadataCoverageState.SOURCE_INACCESSIBLE,
            "metadata_source_inaccessible",
        ),
        DiscoveryState.PRESENT_INVALID_TYPE: (
            MetadataCoverageState.SOURCE_INVALID_TYPE,
            "metadata_source_invalid_type",
        ),
        DiscoveryState.DISCOVERY_FAILED: (
            MetadataCoverageState.DISCOVERY_FAILED,
            "metadata_discovery_failed",
        ),
    }
    state, reason = mapping.get(
        artifact.state, (MetadataCoverageState.INDETERMINATE, "metadata_observation_missing")
    )
    return artifact.source_artifact_id, state, reason


def build_metadata_coverage(
    result: DiscoveryResult,
    normalized: tuple[NormalizedMetadataValue, ...],
) -> MetadataCoverageReport:
    context = result.context
    normalized_by_key: dict[tuple[str, str | None], NormalizedMetadataValue] = {}
    for item in normalized:
        scope = (
            item.tenant_id,
            item.case_id,
            item.evidence_source_id,
            item.processing_run_id,
        )
        expected = (
            context.tenant_id,
            context.case_id,
            context.evidence_source_id,
            context.processing_run_id,
        )
        if scope != expected:
            raise PermissionError("metadata_coverage_scope_mismatch")
        key = (item.source_file, item.source_field)
        if key not in MEASURABLE_SET:
            raise ValueError("metadata_coverage_unexpected_normalization")
        if key in normalized_by_key:
            raise ValueError("metadata_coverage_duplicate_normalization")
        normalized_by_key[key] = item

    observation_by_key: dict[tuple[str, str | None], tuple[int, MetadataObservation]] = {}
    for index, observation in enumerate(result.observations):
        key = (observation.source_file, observation.field_name)
        if key not in MEASURABLE_SET:
            continue
        if key in observation_by_key:
            raise ValueError("metadata_coverage_duplicate_observation")
        observation_by_key[key] = (index, observation)

    entries: list[MetadataCoverageEntry] = []
    for key in MEASURABLE_SET:
        source_file, source_field = key
        indexed_observation = observation_by_key.get(key)
        normalized_item = normalized_by_key.get(key)
        if indexed_observation is None:
            artifact_id, state, reason = _artifact_state(result, source_file)
            entries.append(
                MetadataCoverageEntry(source_file, source_field, artifact_id, state, None, None, reason)
            )
            continue
        index, observation = indexed_observation
        if observation.value_state is ValueState.MISSING:
            state, reason = MetadataCoverageState.FIELD_MISSING, "metadata_field_missing"
        elif observation.value_state is ValueState.MALFORMED:
            state, reason = MetadataCoverageState.SOURCE_MALFORMED, "metadata_source_malformed"
        elif observation.value_state is ValueState.UNSUPPORTED:
            state, reason = MetadataCoverageState.VALUE_UNSUPPORTED, "metadata_value_unsupported"
        elif normalized_item is None:
            state, reason = MetadataCoverageState.OBSERVED_RAW_ONLY, "normalization_not_supplied"
        elif normalized_item.state in {
            NormalizationState.NORMALIZED,
            NormalizationState.ALREADY_CANONICAL,
        }:
            state, reason = MetadataCoverageState.OBSERVED_NORMALIZED, "metadata_value_normalized"
        else:
            state, reason = MetadataCoverageState.OBSERVED_RAW_ONLY, normalized_item.state.value.lower()
        entries.append(
            MetadataCoverageEntry(
                source_file,
                source_field,
                observation.source_artifact_id,
                state,
                index,
                (
                    f"{normalized_item.profile_id}:v{normalized_item.profile_version}"
                    if normalized_item
                    else None
                ),
                reason,
            )
        )

    counts = tuple(
        (state, sum(entry.state is state for entry in entries))
        for state in MetadataCoverageState
        if any(entry.state is state for entry in entries)
    )
    return MetadataCoverageReport(
        COVERAGE_PROFILE_ID,
        COVERAGE_PROFILE_VERSION,
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.processing_run_id,
        "candidate-apple-backup-metadata-v1",
        len(MEASURABLE_SET),
        tuple(entries),
        counts,
    )
