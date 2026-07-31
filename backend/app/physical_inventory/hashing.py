"""Root-confined SHA-256 observations for inventoried candidate objects."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable
from uuid import UUID, uuid4

from app.integrity.domain import EvidenceObject
from app.integrity.services import HashRegistry
from app.physical_inventory.inventory import (
    InventoryResourcePolicy,
    LayoutClassification,
    PhysicalEntryObservation,
)


class PhysicalHashStatus(str, Enum):
    SUCCESS = "SUCCESS"
    OBJECT_INELIGIBLE = "OBJECT_INELIGIBLE"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    RESOURCE_TERMINATED = "RESOURCE_TERMINATED"
    CANCELLED = "CANCELLED"
    SOURCE_UNSTABLE = "SOURCE_UNSTABLE"
    OPERATIONAL_FAILURE = "OPERATIONAL_FAILURE"


@dataclass(slots=True)
class HashBudget:
    bytes_consumed: int = 0


@dataclass(frozen=True, slots=True)
class PhysicalHashObservation:
    observation_id: UUID
    status: PhysicalHashStatus
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    controlled_source_id: UUID
    processing_run_id: UUID
    locator_id: UUID
    locator_profile_id: str
    algorithm: str
    digest: str | None
    bytes_hashed: int
    pre_stat: tuple[int, int, int, int] | None
    post_stat: tuple[int, int, int, int] | None
    integrity_hash_observation_id: UUID | None
    observed_at: datetime
    reason_code: str
    limitations: tuple[str, ...] = (
        "A digest identifies observed bytes only; it does not establish authenticity, artifact meaning, compatibility, or support.",
        "Mutation checks compare available filesystem metadata and cannot prove the source was stable before or after this bounded observation.",
    )


def _snapshot(value: os.stat_result) -> tuple[int, int, int, int]:
    return (value.st_size, value.st_mtime_ns, value.st_dev, value.st_ino)


def hash_inventory_object(
    root: Path,
    entry: PhysicalEntryObservation,
    evidence: EvidenceObject,
    registry: HashRegistry,
    policy: InventoryResourcePolicy,
    budget: HashBudget,
    *,
    actor_id: UUID,
    correlation_id: UUID,
    cancelled: Callable[[], bool] = lambda: False,
) -> PhysicalHashObservation:
    """Hash one previously inventoried object through the common integrity registry."""
    common = dict(
        observation_id=uuid4(), tenant_id=entry.tenant_id, case_id=entry.case_id,
        evidence_source_id=entry.evidence_source_id,
        controlled_source_id=entry.controlled_source_id,
        processing_run_id=entry.processing_run_id, locator_id=entry.locator.locator_id,
        locator_profile_id=f"{entry.locator.profile_id}@{entry.locator.profile_version}",
        algorithm="SHA-256", observed_at=datetime.now(timezone.utc),
    )
    def result(status: PhysicalHashStatus, reason: str, *, before=None, after=None,
               digest=None, count=0, hash_id=None) -> PhysicalHashObservation:
        return PhysicalHashObservation(**common, status=status, digest=digest,
            bytes_hashed=count, pre_stat=before, post_stat=after,
            integrity_hash_observation_id=hash_id, reason_code=reason)

    if cancelled():
        return result(PhysicalHashStatus.CANCELLED, "hash_cancelled")
    if (not entry.eligible_candidate_object or
            entry.layout_classification is not LayoutClassification.CANDIDATE_PHYSICAL_OBJECT):
        return result(PhysicalHashStatus.OBJECT_INELIGIBLE, "object_not_eligible")
    if (entry.tenant_id, entry.case_id, entry.evidence_source_id) != (
            evidence.tenant_id, evidence.case_id, evidence.evidence_source_id):
        return result(PhysicalHashStatus.SCOPE_MISMATCH, "evidence_scope_mismatch")
    try:
        root_resolved = root.resolve(strict=True)
        path = root_resolved.joinpath(*entry.locator.relative_components)
        resolved = path.resolve(strict=True)
        if resolved.parent.parent != root_resolved:
            return result(PhysicalHashStatus.SCOPE_MISMATCH, "locator_escaped_root")
        before = _snapshot(path.stat(follow_symlinks=False))
        if before[0] > policy.max_individual_hash_bytes:
            return result(PhysicalHashStatus.RESOURCE_TERMINATED, "individual_hash_limit_exceeded", before=before)
        if budget.bytes_consumed + before[0] > policy.max_total_hash_bytes:
            return result(PhysicalHashStatus.RESOURCE_TERMINATED, "aggregate_hash_limit_exceeded", before=before)
        observed = registry.compute(path, evidence, purpose="physical_object_inventory",
            role="candidate_physical_backup_object", actor_id=actor_id,
            correlation_id=correlation_id, component_version="1.0.0")
        after = _snapshot(path.stat(follow_symlinks=False))
    except OSError:
        return result(PhysicalHashStatus.OPERATIONAL_FAILURE, "hash_operational_failure")
    inventory_snapshot = (entry.size_bytes, entry.modified_time_ns, entry.object_identity)
    # Windows may report a zero/unstable inode through DirEntry while the file
    # handle reports a usable identity. Size and nanosecond mtime remain the
    # portable inventory-to-hash checkpoint; pre/post hashing also compares
    # device/inode when the platform supplies them consistently.
    current_snapshot = (before[0], before[1], entry.object_identity)
    if (observed.failure_code == "source_unstable" or before != after or
            inventory_snapshot != current_snapshot):
        return result(PhysicalHashStatus.SOURCE_UNSTABLE, "source_unstable",
                      before=before, after=after, count=observed.byte_length,
                      hash_id=observed.observation_id)
    if not observed.success:
        return result(PhysicalHashStatus.OPERATIONAL_FAILURE, "hash_operational_failure",
                      before=before, after=after, count=observed.byte_length,
                      hash_id=observed.observation_id)
    budget.bytes_consumed += observed.byte_length
    return result(PhysicalHashStatus.SUCCESS, "sha256_observed", before=before,
                  after=after, digest=observed.digest, count=observed.byte_length,
                  hash_id=observed.observation_id)
