from datetime import datetime, timezone
from pathlib import Path
import plistlib
from uuid import UUID

import pytest

from app.discovery.apple_backup import *
from app.discovery.metadata_coverage import *
from app.discovery.metadata_normalization import *


def u(n: int) -> UUID:
    return UUID(f"05070000-0000-4000-8000-{n:012d}")


NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)


def context(root: Path) -> DiscoveryContext:
    return DiscoveryContext(
        u(1), u(2), u(3), u(4), u(5),
        {name: u(10 + index) for index, name in enumerate(TARGETS)},
        root.parent, root, True, (u(1), u(2), u(3)),
    )


def fixture(root: Path, *, omit_field: str | None = None) -> DiscoveryResult:
    root.mkdir()
    (root / "Manifest.db").write_bytes(b"SQLite format 3\x00")
    values = {
        "Info.plist": {
            "Product Version": "17.0",
            "Target Identifier": "A" * 40,
            "Unique Identifier": "B" * 40,
        },
        "Manifest.plist": {"IsEncrypted": False},
        "Status.plist": {"SnapshotState": "finished"},
    }
    for value in values.values():
        value.pop(omit_field, None)
    for name, value in values.items():
        with (root / name).open("wb") as stream:
            plistlib.dump(value, stream)
    return discover(context(root), at=NOW)


def normalize_supported(result: DiscoveryResult):
    scope = NormalizationScope(u(1), u(2), u(3), u(4), u(99), NOW)
    output = []
    classes = {
        "Target Identifier": IdentifierClass.DEVICE_IDENTIFIER,
        "Unique Identifier": IdentifierClass.DEVICE_IDENTIFIER,
    }
    for observation in result.observations:
        if observation.field_name == "Product Version":
            output.append(normalize_product_version(observation, scope))
        elif observation.field_name in classes:
            output.append(normalize_identifier(observation, classes[observation.field_name], scope))
    return tuple(output)


def test_complete_report_has_exact_denominator_order_scope_and_limitations(tmp_path):
    result = fixture(tmp_path / "backup")
    report = build_metadata_coverage(result, normalize_supported(result))
    assert report.denominator == 6 and len(report.entries) == 6
    assert tuple((item.source_file, item.source_field) for item in report.entries) == MEASURABLE_SET
    assert report.entries[0].state is MetadataCoverageState.OBSERVED_RAW_ONLY
    assert sum(count for _, count in report.state_counts) == report.denominator
    assert (report.tenant_id, report.case_id, report.evidence_source_id, report.processing_run_id) == (u(1), u(2), u(3), u(4))
    assert all(report.limitations)


def test_missing_field_source_absence_and_raw_only_are_distinct(tmp_path):
    missing_field = fixture(tmp_path / "field", omit_field="Unique Identifier")
    field_report = build_metadata_coverage(missing_field, normalize_supported(missing_field))
    unique = next(item for item in field_report.entries if item.source_field == "Unique Identifier")
    assert unique.state is MetadataCoverageState.FIELD_MISSING

    absent_root = tmp_path / "absent"
    absent = fixture(absent_root)
    (absent_root / "Status.plist").unlink()
    absent = discover(context(absent_root), at=NOW)
    absent_report = build_metadata_coverage(absent, normalize_supported(absent))
    status = next(item for item in absent_report.entries if item.source_file == "Status.plist")
    assert status.state is MetadataCoverageState.SOURCE_ABSENT
    encrypted = next(item for item in absent_report.entries if item.source_field == "IsEncrypted")
    assert encrypted.state is MetadataCoverageState.OBSERVED_RAW_ONLY


def test_unsupported_and_malformed_remain_distinct(tmp_path):
    root = tmp_path / "bad"
    result = fixture(root)
    with (root / "Info.plist").open("wb") as stream:
        plistlib.dump({"Product Version": ["17"], "Target Identifier": "A" * 40, "Unique Identifier": "B" * 40}, stream)
    result = discover(context(root), at=NOW)
    report = build_metadata_coverage(result, normalize_supported(result))
    product = next(item for item in report.entries if item.source_field == "Product Version")
    assert product.state is MetadataCoverageState.VALUE_UNSUPPORTED

    (root / "Status.plist").write_bytes(b"not a plist")
    result = discover(context(root), at=NOW)
    report = build_metadata_coverage(result, normalize_supported(result))
    status = next(item for item in report.entries if item.source_file == "Status.plist")
    assert status.state is MetadataCoverageState.SOURCE_MALFORMED


def test_duplicate_extra_and_cross_scope_normalization_fail_closed(tmp_path):
    result = fixture(tmp_path / "backup")
    normalized = normalize_supported(result)
    with pytest.raises(ValueError, match="duplicate"):
        build_metadata_coverage(result, normalized + (normalized[0],))
    wrong = normalized[0]
    changed = NormalizedMetadataValue(
        u(999), wrong.case_id, wrong.evidence_source_id, wrong.source_artifact_id,
        wrong.processing_run_id, wrong.source_file, wrong.source_field, wrong.reader_id,
        wrong.reader_version, wrong.raw_value, wrong.raw_state, wrong.normalized_value,
        wrong.state, wrong.profile_id, wrong.profile_version, wrong.transformation_method,
        wrong.syntax, wrong.identifier_class, wrong.components, wrong.typed_value, wrong.limitations,
    )
    with pytest.raises(PermissionError, match="scope"):
        build_metadata_coverage(result, (changed,))


def test_output_is_deterministic_and_has_no_support_surface(tmp_path):
    result = fixture(tmp_path / "backup")
    normalized = normalize_supported(result)
    first = build_metadata_coverage(result, normalized)
    second = build_metadata_coverage(result, normalized)
    assert first == second
    assert not {"supported", "compatible", "complete_device"} & set(first.__dataclass_fields__)
    from app.support.registry import create_supported_registry
    from app.evidence_core.supported_store import SupportedEvidenceStore
    registry = create_supported_registry()
    assert registry.entries == () and SupportedEvidenceStore(registry).count == 0
