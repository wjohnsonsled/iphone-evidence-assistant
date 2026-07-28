from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.evidence_core.source_artifact import SourceArtifact
from app.evidence_core.source_locator import SourceLocator, create_source_locator


def u(n: int) -> UUID:
    return UUID(f"42000000-0000-4000-8000-{n:012d}")


ARTIFACT = SourceArtifact(
    u(1), u(2), u(3), u(4), u(5), u(6), "backup-metadata",
    datetime(2026, 7, 28, tzinfo=timezone.utc), u(7), u(8), 1,
)


def test_locator_has_stable_identity_and_preserves_raw_separately() -> None:
    locator = create_source_locator(
        artifact=ARTIFACT, locator_kind="plist-key",
        raw_value=" Device Name ", normalized_value="Device Name",
        normalization_method="trim-v1",
    )
    assert locator.locator_id.version == 4
    assert locator.raw_value == " Device Name "
    assert locator.normalized_value == "Device Name"
    assert locator.source_artifact_id == u(1)
    with pytest.raises(FrozenInstanceError):
        locator.raw_value = "changed"


@pytest.mark.parametrize("raw, normalized", [("", "x"), ("x", ""), ("a\x00b", "x")])
def test_invalid_values_fail_closed(raw: str, normalized: str) -> None:
    with pytest.raises(ValueError):
        SourceLocator(u(9), u(2), u(3), u(1), "plist-key", raw, normalized, "identity-v1")


def test_contract_has_no_filesystem_or_support_semantics() -> None:
    fields = set(SourceLocator.__dataclass_fields__)
    assert not {"path_exists", "supported", "filesystem_path"} & fields
