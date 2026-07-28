import json
from datetime import datetime, timezone
from pathlib import Path
import plistlib
from uuid import UUID

from app.discovery.apple_backup import *
from app.discovery.metadata_coverage import build_metadata_coverage
from app.discovery.metadata_normalization import *


CORPUS_PATH = Path(__file__).parent / "fixtures" / "apple_metadata" / "corpus.json"
NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)


def u(n: int) -> UUID:
    return UUID(f"05080000-0000-4000-8000-{n:012d}")


def load_corpus():
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def materialize(case, root: Path):
    root.mkdir()
    (root / "Manifest.db").write_bytes(b"SQLite format 3\x00")
    omitted = set(case.get("omit_files", ()))
    for name, value in case["files"].items():
        assert name in {"Info.plist", "Manifest.plist", "Status.plist"}
        if name not in omitted:
            with (root / name).open("wb") as stream:
                plistlib.dump(value, stream, sort_keys=True)
    for name, encoded in case.get("raw_files", {}).items():
        assert name in {"Info.plist", "Manifest.plist", "Status.plist"}
        (root / name).write_bytes(bytes.fromhex(encoded))


def context(root: Path):
    return DiscoveryContext(
        u(1), u(2), u(3), u(4), u(5),
        {name: u(10 + index) for index, name in enumerate(TARGETS)},
        root.parent, root, True, (u(1), u(2), u(3)),
    )


def normalized(result):
    scope = NormalizationScope(u(1), u(2), u(3), u(4), u(99), NOW)
    output = []
    for item in result.observations:
        if item.field_name == "Product Version":
            output.append(normalize_product_version(item, scope))
        elif item.field_name in {"Target Identifier", "Unique Identifier"}:
            output.append(normalize_identifier(item, IdentifierClass.DEVICE_IDENTIFIER, scope))
    return tuple(output)


def test_corpus_manifest_is_synthetic_stable_and_complete():
    corpus = load_corpus()
    assert corpus["origin"] == "SYNTHETIC_ONLY"
    assert (corpus["corpus_id"], corpus["corpus_version"]) == (
        "synthetic-apple-metadata-corpus", "1"
    )
    ids = [case["case_id"] for case in corpus["cases"]]
    assert len(ids) == len(set(ids)) == 6
    assert all(case["expected"]["coverage_denominator"] == 6 for case in corpus["cases"])
    assert "client" not in CORPUS_PATH.read_text(encoding="utf-8").lower()


def test_every_synthetic_case_matches_declared_candidate_observations(tmp_path):
    for index, case in enumerate(load_corpus()["cases"]):
        root = tmp_path / f"case-{index}"
        materialize(case, root)
        result = discover(context(root), at=NOW)
        values = normalized(result)
        report = build_metadata_coverage(result, values)
        assert report.denominator == case["expected"]["coverage_denominator"]

        encryption = next(
            item for item in result.observations if item.field_name == "IsEncrypted"
        )
        assert encryption.raw_value is case["expected"]["encryption"]

        product = next(
            (item for item in values if item.source_field == "Product Version"), None
        )
        if product is not None:
            assert product.state.value == case["expected"]["product_state"]


def test_materialization_is_root_confined_and_deterministic(tmp_path):
    case = load_corpus()["cases"][0]
    first, second = tmp_path / "first", tmp_path / "second"
    materialize(case, first)
    materialize(case, second)
    assert sorted(path.name for path in first.iterdir()) == sorted(
        path.name for path in second.iterdir()
    )
    for name in TARGETS:
        assert (first / name).read_bytes() == (second / name).read_bytes()
    assert all(path.parent == first for path in first.iterdir())


def test_corpus_does_not_activate_support():
    from app.evidence_core.supported_store import SupportedEvidenceStore
    from app.support.registry import create_supported_registry

    registry = create_supported_registry()
    assert registry.entries == ()
    assert SupportedEvidenceStore(registry).count == 0
