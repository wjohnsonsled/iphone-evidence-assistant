"""DEV-0451 source-inventory tests using synthetic observations only."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.evidence_core.processing_run import ProcessingRun
from app.evidence_core.source_artifact import SourceArtifact
from app.evidence_core.source_inventory import build_source_inventory
from app.evidence_core.source_locator import SourceLocator
from app.security.evidence_source import EvidenceSource


def u(n: int) -> UUID:
    return UUID(f"45010000-0000-4000-8000-{n:012d}")


NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)
SOURCE = EvidenceSource(u(1), u(2), u(3), "synthetic", "synthetic://source", NOW, u(4))
RUN = ProcessingRun(u(5), u(2), u(3), u(1), "inventory", NOW, u(4), u(6), u(7), 1)


def artifact(number: int, family: str = "backup-metadata") -> SourceArtifact:
    return SourceArtifact(u(number), u(2), u(3), u(1), u(5), u(number + 20), family, NOW, u(4), u(7), 1)


def locator(number: int, source_artifact_id: UUID) -> SourceLocator:
    return SourceLocator(
        u(number), u(2), u(3), source_artifact_id, "synthetic-reference",
        f" raw-{number} ", f"raw-{number}", "trim-v1",
    )


def test_inventory_is_deterministic_scoped_and_immutable() -> None:
    first, second = artifact(9, "messages"), artifact(8, "backup-metadata")
    locators = (locator(12, first.source_artifact_id), locator(11, first.source_artifact_id))
    result = build_source_inventory(
        inventory_id=u(10), evidence_source=SOURCE, processing_run=RUN,
        artifacts=(first, second), locators=locators, observed_at=NOW,
    )
    assert [item.artifact_family_key for item in result.items] == ["backup-metadata", "messages"]
    assert result.items[1].locator_ids == (u(11), u(12))
    assert (result.tenant_id, result.case_id, result.evidence_source_id) == (u(2), u(3), u(1))
    assert len(result.limitations) == 3
    with pytest.raises(FrozenInstanceError):
        result.items = ()


def test_zero_observations_is_not_represented_as_a_coverage_conclusion() -> None:
    result = build_source_inventory(
        inventory_id=u(10), evidence_source=SOURCE, processing_run=RUN,
        artifacts=(), locators=(), observed_at=NOW,
    )
    assert result.items == ()
    assert not {"coverage_status", "supported", "complete"} & set(result.__dataclass_fields__)


@pytest.mark.parametrize(
    "artifacts,locators,code",
    [
        ((artifact(8), artifact(8)), (), "duplicate_source_artifact"),
        ((artifact(8),), (locator(11, u(99)),), "orphan_source_locator"),
        ((artifact(8),), (locator(11, artifact(8).source_artifact_id), locator(11, artifact(8).source_artifact_id)), "duplicate_source_locator"),
    ],
)
def test_duplicate_and_orphan_observations_fail_closed(artifacts, locators, code) -> None:
    with pytest.raises(ValueError, match=code):
        build_source_inventory(
            inventory_id=u(10), evidence_source=SOURCE, processing_run=RUN,
            artifacts=artifacts, locators=locators, observed_at=NOW,
        )


def test_cross_scope_observations_fail_closed() -> None:
    wrong = SourceArtifact(u(8), u(2), u(3), u(99), u(5), u(28), "backup-metadata", NOW, u(4), u(7), 1)
    with pytest.raises(ValueError, match="source_artifact_scope_mismatch"):
        build_source_inventory(
            inventory_id=u(10), evidence_source=SOURCE, processing_run=RUN,
            artifacts=(wrong,), locators=(), observed_at=NOW,
        )
