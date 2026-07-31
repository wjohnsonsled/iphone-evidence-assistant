from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from app.manifest.identifier_normalization import StorageClass, normalize_manifest_fileid, synthetic_source
from app.physical_inventory.coverage import ConclusionState, observe_physical_coverage
from app.physical_inventory.inventory import AuthorizedInventoryContext, InventoryResourcePolicy, inventory_backup_root
from app.physical_inventory.resolution import ResolutionOutcome, resolve_manifest_fileid

uid = lambda n: UUID(f"06030000-0000-4000-8000-{n:012d}")
NOW = datetime(2026, 7, 31, 18, tzinfo=UTC)
FILE_ID = "ab" + "1" * 38


def fixture(root: Path):
    (root / "ab").mkdir()
    (root / "ab" / FILE_ID).write_bytes(b"synthetic")
    ctx = AuthorizedInventoryContext(uid(1), uid(2), uid(3), uid(5), uid(7),
        (uid(1), uid(2), uid(3), uid(7)), True, True, NOW)
    policy = InventoryResourcePolicy(100, 100, 100, 2, 300, 1000, 2000, 100000, 30, 1, 100)
    return inventory_backup_root(root, ctx, policy)


def ident(value):
    return normalize_manifest_fileid(synthetic_source(value, StorageClass.TEXT))


def test_physical_coverage_is_separate_factual_and_fail_closed(tmp_path):
    inventory = fixture(tmp_path)
    resolutions = (resolve_manifest_fileid(ident(FILE_ID), inventory),
                   resolve_manifest_fileid(ident("cd" + "2" * 38), inventory))
    coverage = observe_physical_coverage(inventory, resolutions)
    assert coverage.candidate_objects_observed == 1
    assert coverage.complete_no_match_count == 1
    assert dict(coverage.resolution_counts)[ResolutionOutcome.EXACT_SINGLE_MATCH.value] == 1
    assert {coverage.absence_conclusion, coverage.deletion_conclusion,
            coverage.duplicate_conclusion, coverage.orphan_conclusion} == {ConclusionState.NOT_ESTABLISHED}
    assert "Manifest" in coverage.limitations[0]


def test_scope_mismatch_is_rejected_and_identity_is_deterministic(tmp_path):
    inventory = fixture(tmp_path)
    item = resolve_manifest_fileid(ident(FILE_ID), inventory)
    first = observe_physical_coverage(inventory, (item,))
    second = observe_physical_coverage(inventory, (item,))
    assert first.observation_id == second.observation_id
    with pytest.raises(ValueError, match="physical_coverage_scope_mismatch"):
        observe_physical_coverage(inventory, (replace(item, tenant_id=uid(99)),))
