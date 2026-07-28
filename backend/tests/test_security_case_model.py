from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.security.case import SecurityCase, create_case


NOW = datetime(2026, 7, 29, tzinfo=timezone.utc)
ACTOR = UUID("30000000-0000-4000-8000-000000000003")


def test_case_identity_is_stable_immutable_and_tenant_scoped():
    tenant_id = uuid4()
    item = create_case(
        tenant_id=tenant_id,
        name="Synthetic Matter",
        created_by_actor_id=ACTOR,
        created_at=NOW,
    )
    assert item.case_id.version == 4
    assert item.tenant_id == tenant_id
    assert item.created_at == NOW
    with pytest.raises(FrozenInstanceError):
        item.name = "changed"


@pytest.mark.parametrize("name", ["", " padded ", "x" * 256])
def test_case_name_is_nonempty_trimmed_and_bounded(name):
    with pytest.raises(ValueError, match="Case name"):
        create_case(
            tenant_id=uuid4(),
            name=name,
            created_by_actor_id=ACTOR,
            created_at=NOW,
        )


def test_case_rejects_non_v4_naive_time_and_invalid_version():
    with pytest.raises(ValueError, match="UUIDv4"):
        SecurityCase(
            UUID(int=uuid4().int, version=1),
            uuid4(),
            "Matter",
            NOW,
            ACTOR,
        )
    with pytest.raises(ValueError, match="timezone"):
        SecurityCase(uuid4(), uuid4(), "Matter", NOW.replace(tzinfo=None), ACTOR)
    with pytest.raises(ValueError, match="version"):
        SecurityCase(uuid4(), uuid4(), "Matter", NOW, ACTOR, 0)


def test_security_case_orm_is_additive_and_separate_from_legacy_cases():
    import app.models  # noqa: F401

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    assert {"cases", "security_cases"} <= set(inspector.get_table_names())
    foreign_keys = inspector.get_foreign_keys("security_cases")
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["referred_table"] == "security_tenants"
    indexes = {index["name"] for index in inspector.get_indexes("security_cases")}
    assert "ix_security_cases_tenant_name" in indexes
    legacy_columns = {column["name"] for column in inspector.get_columns("cases")}
    assert "tenant_id" not in legacy_columns
