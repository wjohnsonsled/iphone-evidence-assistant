from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from app.manifest.identifier_normalization import StorageClass, normalize_manifest_fileid, synthetic_source
from app.physical_inventory.inventory import AuthorizedInventoryContext, InventoryResourcePolicy, inventory_backup_root
from app.physical_inventory.resolution import ResolutionOutcome, resolve_manifest_fileid

NOW = datetime(2026, 7, 31, 18, tzinfo=UTC)
uid = lambda n: UUID(f"06030000-0000-4000-8000-{n:012d}")
FILE_ID = "ab" + "1" * 38


def policy(**changes):
    values = dict(max_directory_entries=100, max_regular_files=100, max_directories=100,
        max_path_depth=2, max_pathname_length=300, max_individual_hash_bytes=1000,
        max_total_hash_bytes=2000, max_memory_estimate_bytes=100000,
        max_elapsed_seconds=30, max_concurrent_hash_operations=1, max_unresolved_objects=100)
    values.update(changes)
    return InventoryResourcePolicy(**values)


def context():
    return AuthorizedInventoryContext(uid(1), uid(2), uid(3), uid(5), uid(7),
        (uid(1), uid(2), uid(3), uid(7)), True, True, NOW)


def identifier(value=FILE_ID):
    return normalize_manifest_fileid(synthetic_source(value, StorageClass.TEXT))


def test_exact_single_and_no_match_complete_are_distinct(tmp_path):
    (tmp_path / "ab").mkdir()
    (tmp_path / "ab" / FILE_ID).write_bytes(b"synthetic")
    inventory = inventory_backup_root(tmp_path, context(), policy())
    matched = resolve_manifest_fileid(identifier(), inventory)
    absent = resolve_manifest_fileid(identifier("cd" + "2" * 38), inventory)
    assert matched.outcome is ResolutionOutcome.EXACT_SINGLE_MATCH
    assert len(matched.matched_locator_ids) == 1
    assert absent.outcome is ResolutionOutcome.NO_MATCH_INVENTORY_COMPLETE
    assert "deletion" in " ".join(absent.limitations)


def test_no_match_partial_identifier_invalid_and_scope_mismatch(tmp_path):
    (tmp_path / "ab").mkdir()
    (tmp_path / "unexpected").write_bytes(b"forces a second directory entry")
    partial = inventory_backup_root(tmp_path, context(), policy(max_directory_entries=1))
    assert resolve_manifest_fileid(identifier(), partial).outcome is ResolutionOutcome.NO_MATCH_INVENTORY_PARTIAL
    assert resolve_manifest_fileid(identifier("bad"), partial).outcome is ResolutionOutcome.IDENTIFIER_NOT_COMPARABLE
    wrong = replace(identifier(), source=replace(identifier().source, tenant_id=uid(99)))
    assert resolve_manifest_fileid(wrong, partial).outcome is ResolutionOutcome.SOURCE_SCOPE_MISMATCH


def test_wrong_prefix_name_is_observed_but_unsupported(tmp_path):
    (tmp_path / "cd").mkdir()
    (tmp_path / "cd" / FILE_ID).write_bytes(b"synthetic")
    result = resolve_manifest_fileid(identifier(), inventory_backup_root(tmp_path, context(), policy()))
    assert result.outcome is ResolutionOutcome.PHYSICAL_OBJECT_UNSUPPORTED
    assert result.matched_locator_ids


def test_deterministic_identity_and_no_content_claim(tmp_path):
    inventory = inventory_backup_root(tmp_path, context(), policy())
    first = resolve_manifest_fileid(identifier(), inventory)
    second = resolve_manifest_fileid(identifier(), inventory)
    assert first.observation_id == second.observation_id
    assert first.matched_locator_ids == second.matched_locator_ids
    assert all("support" in " ".join(first.limitations).lower() or first.limitations for _ in [0])
