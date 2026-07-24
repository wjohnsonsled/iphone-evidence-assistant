"""Deterministic tests for the DEV-0101 composition boundary."""

from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from app.legacy.main import create_legacy_app
from app.main import create_app


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent


def test_default_application_exposes_health_only() -> None:
    app = create_app()
    paths = set(app.openapi()["paths"])

    assert paths == {"/api/v1/health"}

    client = TestClient(app)
    assert client.get("/api/v1/cases").status_code == 404
    assert (
        client.post(
            "/api/v1/cases/00000000-0000-0000-0000-000000000000/process",
            json={"backup_path": "synthetic"},
        ).status_code
        == 404
    )


def test_supported_composition_has_no_legacy_imports() -> None:
    forbidden_modules = {
        "app.api.cases",
        "app.api.evidence",
        "app.legacy",
        "app.services.case_processing",
        "evidence_engine._legacy",
    }

    for relative_path in ("app/main.py", "app/api/router.py"):
        path = BACKEND_ROOT / relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = _imported_modules(tree)
        forbidden = {
            module
            for module in imported
            if any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden_modules)
        }
        assert forbidden == set(), f"{relative_path} imports forbidden modules: {sorted(forbidden)}"


def test_legacy_application_is_explicit_and_warns_that_it_is_unsupported() -> None:
    app = create_legacy_app()
    paths = set(app.openapi()["paths"])

    assert {
        "/api/v1/health",
        "/api/v1/cases",
        "/api/v1/cases/{case_id}",
        "/api/v1/cases/{case_id}/process",
        "/api/v1/cases/{case_id}/summary",
        "/api/v1/cases/{case_id}/evidence",
        "/api/v1/cases/{case_id}/evidence/{evidence_id}",
    }.issubset(paths)
    assert "legacy" in app.title.lower()
    assert "unsupported" in app.description.lower()


def test_gitignore_is_conflict_free_and_excludes_sensitive_material() -> None:
    content = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
    lines = {line.strip() for line in content.splitlines()}

    assert not any(marker in content for marker in ("<<<<<<<", "=======", ">>>>>>>", "Set-Content", "@'"))
    assert {
        ".env",
        ".env.*",
        "dev-evidence/",
        "evidence/",
        "uploads/",
        "*.db",
        "*.db-wal",
        "*.db-shm",
        "*.db-journal",
        "*.zip",
        ".venv/",
        "outputs/",
    }.issubset(lines)


def _imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            modules.update(f"{node.module}.{alias.name}" for alias in node.names)
    return modules
