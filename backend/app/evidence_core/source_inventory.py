"""Deterministic inventory of registered source observations only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.evidence_core.processing_run import ProcessingRun
from app.evidence_core.source_artifact import SourceArtifact
from app.evidence_core.source_locator import SourceLocator
from app.security.evidence_source import EvidenceSource


INVENTORY_LIMITATIONS = (
    "Inventory contains registered observations only; it does not establish source completeness.",
    "An absent inventory item does not establish absence, deletion, concealment, or destruction.",
    "Inventory membership does not establish parser, artifact, input, or workflow support.",
)


@dataclass(frozen=True, slots=True)
class SourceInventoryItem:
    source_artifact_id: UUID
    evidence_uuid: UUID
    artifact_family_key: str
    locator_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class SourceInventory:
    inventory_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    processing_run_id: UUID
    observed_at: datetime
    items: tuple[SourceInventoryItem, ...]
    limitations: tuple[str, ...] = INVENTORY_LIMITATIONS
    version: int = 1

    def __post_init__(self) -> None:
        if self.inventory_id.version != 4:
            raise ValueError("inventory_id_must_be_uuid4")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at_must_be_timezone_aware")
        if self.version < 1:
            raise ValueError("inventory_version_must_be_positive")
        if not self.limitations or any(not value.strip() for value in self.limitations):
            raise ValueError("inventory_limitations_required")


def build_source_inventory(
    *,
    inventory_id: UUID,
    evidence_source: EvidenceSource,
    processing_run: ProcessingRun,
    artifacts: tuple[SourceArtifact, ...],
    locators: tuple[SourceLocator, ...],
    observed_at: datetime,
) -> SourceInventory:
    """Build a scoped snapshot without reading or interpreting evidence."""

    scope = (evidence_source.tenant_id, evidence_source.case_id, evidence_source.evidence_source_id)
    run_scope = (processing_run.tenant_id, processing_run.case_id, processing_run.evidence_source_id)
    if run_scope != scope:
        raise ValueError("processing_run_scope_mismatch")

    artifact_by_id: dict[UUID, SourceArtifact] = {}
    for artifact in artifacts:
        artifact_scope = (artifact.tenant_id, artifact.case_id, artifact.evidence_source_id)
        if artifact_scope != scope or artifact.processing_run_id != processing_run.processing_run_id:
            raise ValueError("source_artifact_scope_mismatch")
        if artifact.source_artifact_id in artifact_by_id:
            raise ValueError("duplicate_source_artifact")
        artifact_by_id[artifact.source_artifact_id] = artifact

    locator_ids: set[UUID] = set()
    by_artifact: dict[UUID, list[UUID]] = {key: [] for key in artifact_by_id}
    for locator in locators:
        if locator.locator_id in locator_ids:
            raise ValueError("duplicate_source_locator")
        locator_ids.add(locator.locator_id)
        if (locator.tenant_id, locator.case_id) != scope[:2]:
            raise ValueError("source_locator_scope_mismatch")
        if locator.source_artifact_id not in artifact_by_id:
            raise ValueError("orphan_source_locator")
        by_artifact[locator.source_artifact_id].append(locator.locator_id)

    items = tuple(
        SourceInventoryItem(
            artifact.source_artifact_id,
            artifact.evidence_uuid,
            artifact.artifact_family_key,
            tuple(sorted(by_artifact[artifact.source_artifact_id], key=str)),
        )
        for artifact in sorted(
            artifact_by_id.values(),
            key=lambda value: (value.artifact_family_key, str(value.source_artifact_id)),
        )
    )
    return SourceInventory(
        inventory_id, scope[0], scope[1], scope[2], processing_run.processing_run_id,
        observed_at, items,
    )
