from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from app.integrity.domain import register_evidence
from app.integrity.services import AppendOnlyAuditService, HashRegistry
from app.physical_inventory.hashing import HashBudget, PhysicalHashStatus, hash_inventory_object
from app.physical_inventory.inventory import AuthorizedInventoryContext, InventoryResourcePolicy, inventory_backup_root

IDS = tuple(UUID(int=value) for value in range(1, 9))
NOW = datetime(2026, 7, 31, 14, tzinfo=UTC)


def setup(root: Path, content=b"synthetic bytes"):
    (root / "ab").mkdir()
    (root / "ab" / ("ab" + "1" * 38)).write_bytes(content)
    context = AuthorizedInventoryContext(IDS[0], IDS[1], IDS[2], IDS[3], IDS[4],
        (IDS[0], IDS[1], IDS[2], IDS[4]), True, True, NOW)
    policy = InventoryResourcePolicy(100, 100, 100, 2, 300, 1024, 2048, 100000, 30, 1, 100)
    entry = next(item for item in inventory_backup_root(root, context, policy).observations
                 if item.eligible_candidate_object)
    evidence = register_evidence(tenant_id=IDS[0], case_id=IDS[1], evidence_source_id=IDS[2],
        evidence_kind="CONTROLLED", source_type="SYNTHETIC", source_locator="fixture",
        logical_identifier="physical", intake_method="SYNTHETIC_TEST",
        registered_by_actor_id=IDS[5], registered_at=NOW, processing_run_id=IDS[4])
    return entry, evidence, policy


def test_hash_is_streaming_registry_observation_with_complete_provenance(tmp_path):
    entry, evidence, policy = setup(tmp_path)
    audit = AppendOnlyAuditService()
    budget = HashBudget()
    result = hash_inventory_object(tmp_path, entry, evidence, HashRegistry(audit), policy,
        budget, actor_id=IDS[5], correlation_id=IDS[6])
    assert result.status is PhysicalHashStatus.SUCCESS
    assert result.digest == "a3b16b6e44c6ea47c8f2531f402530e414091de3769594c3db04ddedd3165bc5"
    assert result.bytes_hashed == budget.bytes_consumed == 15
    assert result.pre_stat == result.post_stat
    assert result.integrity_hash_observation_id is not None
    assert result.processing_run_id == IDS[4]
    assert len(audit.events) == 1


def test_limits_cancellation_scope_and_inventory_mutation_fail_closed(tmp_path):
    entry, evidence, policy = setup(tmp_path)
    registry = HashRegistry(AppendOnlyAuditService())
    cancelled = hash_inventory_object(tmp_path, entry, evidence, registry, policy, HashBudget(),
        actor_id=IDS[5], correlation_id=IDS[6], cancelled=lambda: True)
    assert cancelled.status is PhysicalHashStatus.CANCELLED
    limited = hash_inventory_object(tmp_path, entry, evidence, registry, policy, HashBudget(2040),
        actor_id=IDS[5], correlation_id=IDS[6])
    assert limited.status is PhysicalHashStatus.RESOURCE_TERMINATED
    path = tmp_path / "ab" / ("ab" + "1" * 38)
    path.write_bytes(b"changed after inventory")
    unstable = hash_inventory_object(tmp_path, entry, evidence, registry, policy, HashBudget(),
        actor_id=IDS[5], correlation_id=IDS[6])
    assert unstable.status is PhysicalHashStatus.SOURCE_UNSTABLE


def test_ineligible_and_cross_tenant_objects_are_not_read(tmp_path):
    entry, evidence, policy = setup(tmp_path)
    registry = HashRegistry(AppendOnlyAuditService())
    wrong = register_evidence(tenant_id=IDS[7], case_id=IDS[1], evidence_source_id=IDS[2],
        evidence_kind="CONTROLLED", source_type="SYNTHETIC", source_locator="fixture",
        logical_identifier="wrong", intake_method="SYNTHETIC_TEST",
        registered_by_actor_id=IDS[5], registered_at=NOW)
    result = hash_inventory_object(tmp_path, entry, wrong, registry, policy, HashBudget(),
        actor_id=IDS[5], correlation_id=IDS[6])
    assert result.status is PhysicalHashStatus.SCOPE_MISMATCH
    assert not registry.observations
