from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.security.identity import (
    Principal,
    PrincipalKind,
    TenantMembership,
    create_membership,
    create_principal,
)


NOW = datetime(2026, 7, 28, 23, 0, tzinfo=timezone.utc)
ACTOR = UUID("30000000-0000-4000-8000-000000000002")


def test_principal_and_membership_are_stable_immutable_and_tenant_scoped():
    principal = create_principal(
        kind=PrincipalKind.USER,
        identity_provider="synthetic-provider",
        external_subject="synthetic-subject",
        created_by_actor_id=ACTOR,
        created_at=NOW,
    )
    tenant_id = uuid4()
    membership = create_membership(
        tenant_id=tenant_id,
        principal_id=principal.principal_id,
        role_key="synthetic-reviewer",
        created_by_actor_id=ACTOR,
        created_at=NOW,
    )
    assert principal.principal_id.version == membership.membership_id.version == 4
    assert membership.tenant_id == tenant_id
    assert membership.principal_id == principal.principal_id
    assert membership.role_key == "synthetic-reviewer"
    with pytest.raises(FrozenInstanceError):
        membership.role_key = "changed"


def test_principal_kind_is_closed():
    assert {kind.value for kind in PrincipalKind} == {"USER", "SERVICE"}


@pytest.mark.parametrize(
    ("provider", "subject"),
    [("", "subject"), (" padded ", "subject"), ("provider", ""), ("provider", "x" * 256)],
)
def test_principal_external_identity_is_required_and_bounded(provider, subject):
    with pytest.raises(ValueError):
        create_principal(
            kind=PrincipalKind.USER,
            identity_provider=provider,
            external_subject=subject,
            created_by_actor_id=ACTOR,
            created_at=NOW,
        )


@pytest.mark.parametrize("role", ["", "-bad", "bad-", "UPPER", "has space", "x" * 129])
def test_role_key_is_canonical_but_has_no_permission_semantics(role):
    with pytest.raises(ValueError, match="Role key"):
        create_membership(
            tenant_id=uuid4(),
            principal_id=uuid4(),
            role_key=role,
            created_by_actor_id=ACTOR,
            created_at=NOW,
        )


def test_identity_contracts_reject_naive_time_and_invalid_version():
    with pytest.raises(ValueError, match="timezone"):
        Principal(
            uuid4(),
            PrincipalKind.USER,
            "provider",
            "subject",
            NOW.replace(tzinfo=None),
            ACTOR,
        )
    with pytest.raises(ValueError, match="version"):
        TenantMembership(uuid4(), uuid4(), uuid4(), "role", NOW, ACTOR, 0)


def test_additive_orm_contract_has_scoped_keys_and_foreign_keys():
    import app.models  # noqa: F401

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    assert {"security_principals", "security_tenant_memberships"} <= set(
        inspector.get_table_names()
    )
    foreign_targets = {
        foreign["referred_table"]
        for foreign in inspector.get_foreign_keys("security_tenant_memberships")
    }
    assert foreign_targets == {"security_tenants", "security_principals"}
    unique_sets = {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints(
            "security_tenant_memberships"
        )
    }
    assert ("tenant_id", "principal_id", "role_key") in unique_sets
