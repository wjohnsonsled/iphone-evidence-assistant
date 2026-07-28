from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.evidence_source import EvidenceSourceModel
from app.models.security_case import SecurityCaseModel
from app.models.tenant import TenantModel
from app.security.case import create_case
from app.security.evidence_source import EvidenceSource, register_evidence_source


NOW = datetime(2026, 7, 29, 1, 0, tzinfo=timezone.utc)
ACTOR = UUID("30000000-0000-4000-8000-000000000004")


def test_factory_derives_tenant_and_case_and_preserves_registration():
    case = create_case(
        tenant_id=uuid4(),
        name="Synthetic",
        created_by_actor_id=ACTOR,
        created_at=NOW,
    )
    source = register_evidence_source(
        case=case,
        source_type="synthetic_candidate",
        source_locator="candidate/source",
        registered_by_actor_id=ACTOR,
        registered_at=NOW,
    )
    assert source.evidence_source_id.version == 4
    assert (source.tenant_id, source.case_id) == (case.tenant_id, case.case_id)
    assert source.registered_at == NOW
    with pytest.raises(FrozenInstanceError):
        source.source_type = "changed"


@pytest.mark.parametrize(
    ("source_type", "locator"),
    [("", "source"), (" padded ", "source"), ("type", ""), ("type", "x" * 2049)],
)
def test_source_identity_fields_are_required_and_bounded(source_type, locator):
    case = create_case(
        tenant_id=uuid4(),
        name="Synthetic",
        created_by_actor_id=ACTOR,
        created_at=NOW,
    )
    with pytest.raises(ValueError):
        register_evidence_source(
            case=case,
            source_type=source_type,
            source_locator=locator,
            registered_by_actor_id=ACTOR,
            registered_at=NOW,
        )


def test_source_rejects_naive_time_and_invalid_version():
    with pytest.raises(ValueError, match="timezone"):
        EvidenceSource(
            uuid4(), uuid4(), uuid4(), "type", "source",
            NOW.replace(tzinfo=None), ACTOR,
        )
    with pytest.raises(ValueError, match="version"):
        EvidenceSource(uuid4(), uuid4(), uuid4(), "type", "source", NOW, ACTOR, 0)


def test_relational_boundary_rejects_cross_tenant_case_link():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    tenant_one, tenant_two, case_id = uuid4(), uuid4(), uuid4()
    with Session(engine) as session:
        session.add_all(
            [
                TenantModel(id=tenant_one, slug="one", display_name="One", created_at=NOW, created_by_actor_id=ACTOR, version=1),
                TenantModel(id=tenant_two, slug="two", display_name="Two", created_at=NOW, created_by_actor_id=ACTOR, version=1),
            ]
        )
        session.commit()
        session.add(
            SecurityCaseModel(id=case_id, tenant_id=tenant_one, name="Matter", created_at=NOW, created_by_actor_id=ACTOR, version=1)
        )
        session.commit()
        session.add(
            EvidenceSourceModel(
                tenant_id=tenant_two,
                case_id=case_id,
                source_type="synthetic",
                source_locator="source",
                registered_at=NOW,
                registered_by_actor_id=ACTOR,
                version=1,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_evidence_source_metadata_has_composite_case_tenant_foreign_key():
    import app.models  # noqa: F401

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    foreign_keys = inspect(engine).get_foreign_keys("security_evidence_sources")
    assert any(
        foreign["referred_table"] == "security_cases"
        and foreign["constrained_columns"] == ["case_id", "tenant_id"]
        for foreign in foreign_keys
    )
