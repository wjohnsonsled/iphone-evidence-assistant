from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.security.tenant import Tenant, create_tenant


NOW = datetime(2026, 7, 28, 22, 0, tzinfo=timezone.utc)
ACTOR = UUID("30000000-0000-4000-8000-000000000001")
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_tenant_identity_is_stable_immutable_and_content_independent():
    first = create_tenant(
        slug="synthetic-one",
        display_name="Synthetic One",
        created_by_actor_id=ACTOR,
        created_at=NOW,
    )
    second = create_tenant(
        slug="synthetic-two",
        display_name="Synthetic Two",
        created_by_actor_id=ACTOR,
        created_at=NOW,
    )
    assert first.tenant_id.version == 4
    assert first.tenant_id != second.tenant_id
    assert first.created_at == NOW
    assert first.created_by_actor_id == ACTOR
    with pytest.raises(FrozenInstanceError):
        first.slug = "changed"


@pytest.mark.parametrize(
    "slug",
    ["", "-start", "end-", "UPPER", "space value", "a" * 64, "under_score"],
)
def test_tenant_slug_rejects_noncanonical_values(slug):
    with pytest.raises(ValueError, match="slug"):
        create_tenant(
            slug=slug,
            display_name="Synthetic",
            created_by_actor_id=ACTOR,
            created_at=NOW,
        )


@pytest.mark.parametrize("name", ["", " padded ", "a" * 256])
def test_tenant_display_name_is_nonempty_trimmed_and_bounded(name):
    with pytest.raises(ValueError, match="display name"):
        create_tenant(
            slug="synthetic",
            display_name=name,
            created_by_actor_id=ACTOR,
            created_at=NOW,
        )


def test_tenant_rejects_non_v4_naive_time_and_invalid_version():
    with pytest.raises(ValueError, match="UUIDv4"):
        Tenant(UUID(int=uuid4().int, version=1), "synthetic", "Synthetic", NOW, ACTOR)
    with pytest.raises(ValueError, match="timezone"):
        Tenant(uuid4(), "synthetic", "Synthetic", NOW.replace(tzinfo=None), ACTOR)
    with pytest.raises(ValueError, match="version"):
        Tenant(uuid4(), "synthetic", "Synthetic", NOW, ACTOR, version=0)


def test_additive_tenant_metadata_contract_preserves_existing_tables():
    import app.models  # noqa: F401

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "security_tenants" in tables
    assert {"cases", "integrity_evidence_objects"} <= tables
    columns = {column["name"]: column for column in inspector.get_columns("security_tenants")}
    assert set(columns) == {
        "id",
        "slug",
        "display_name",
        "created_at",
        "created_by_actor_id",
        "version",
    }
    assert all(not column["nullable"] for column in columns.values())
    unique_columns = {
        tuple(item["column_names"])
        for item in (
            inspector.get_unique_constraints("security_tenants")
            + inspector.get_indexes("security_tenants")
        )
        if item.get("unique", True)
    }
    assert ("slug",) in unique_columns


def test_tenant_boundary_has_no_legacy_api_or_evidence_imports():
    paths = [
        BACKEND_ROOT / "app" / "security" / "tenant.py",
        BACKEND_ROOT / "app" / "models" / "tenant.py",
    ]
    imports = set()
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    assert not any(
        name.startswith(("evidence_engine", "app.legacy", "app.api", "app.intake"))
        for name in imports
    )
