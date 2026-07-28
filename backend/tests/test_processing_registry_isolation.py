"""DEV-1102 static and runtime registry-isolation checks."""

from __future__ import annotations

import ast
from pathlib import Path

from app.support.registry import create_supported_registry


BACKEND = Path(__file__).parents[1]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_supported_registry_tree_has_no_legacy_or_service_imports() -> None:
    for path in (BACKEND / "app" / "support").glob("*.py"):
        imports = imported_modules(path)
        assert not any(
            name.startswith(("app.legacy", "app.services", "evidence_engine"))
            for name in imports
        )


def test_legacy_plugin_access_remains_confined_to_legacy_processing_service() -> None:
    matches = []
    for path in (BACKEND / "app").rglob("*.py"):
        if "evidence_engine._legacy" in path.read_text(encoding="utf-8"):
            matches.append(path.relative_to(BACKEND).as_posix())
    assert matches == ["app/services/case_processing.py"]


def test_production_supported_registry_remains_empty() -> None:
    assert create_supported_registry().entries == ()
