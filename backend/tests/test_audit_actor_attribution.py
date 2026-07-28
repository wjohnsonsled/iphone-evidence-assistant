from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.integrity.domain import AuditEventType, register_evidence
from app.integrity.services import AppendOnlyAuditService
from app.security.audit_attribution import TenantAuditService, create_audit_actor
from app.security.identity import PrincipalKind, create_membership, create_principal


NOW = datetime(2026, 7, 29, 2, 0, tzinfo=timezone.utc)


def _actor(tenant_id):
    creator = uuid4()
    principal = create_principal(
        kind=PrincipalKind.USER,
        identity_provider="synthetic",
        external_subject=str(uuid4()),
        created_by_actor_id=creator,
        created_at=NOW,
    )
    membership = create_membership(
        tenant_id=tenant_id,
        principal_id=principal.principal_id,
        role_key="synthetic-role",
        created_by_actor_id=creator,
        created_at=NOW,
    )
    return principal, membership, create_audit_actor(principal, membership)


def _evidence(tenant_id):
    return register_evidence(
        tenant_id=tenant_id,
        case_id=uuid4(),
        evidence_source_id=uuid4(),
        evidence_kind="SOURCE",
        source_type="SYNTHETIC",
        source_locator="source",
        logical_identifier="synthetic",
        intake_method="SYNTHETIC_TEST",
        registered_at=NOW,
        registered_by_actor_id=uuid4(),
    )


def test_attributed_event_uses_principal_and_preserves_typed_fields():
    tenant_id, correlation_id = uuid4(), uuid4()
    principal, membership, actor = _actor(tenant_id)
    audit = AppendOnlyAuditService()
    event = TenantAuditService(audit).append(
        evidence=_evidence(tenant_id),
        actor=actor,
        event_type=AuditEventType.EVIDENCE_VALIDATION_FAILED,
        result="FAILED",
        correlation_id=correlation_id,
        failure_code="synthetic_failure",
    )
    assert event.actor_id == principal.principal_id
    assert actor.membership_id == membership.membership_id
    assert event.correlation_id == correlation_id
    assert event.event_type is AuditEventType.EVIDENCE_VALIDATION_FAILED
    assert event.failure_code == "synthetic_failure"
    with pytest.raises(FrozenInstanceError):
        actor.role_key = "changed"


def test_mismatched_principal_membership_is_rejected():
    tenant_id = uuid4()
    principal, _, _ = _actor(tenant_id)
    _, foreign_membership, _ = _actor(tenant_id)
    with pytest.raises(PermissionError, match="principal"):
        create_audit_actor(principal, foreign_membership)


def test_cross_tenant_attribution_fails_without_appending():
    source_tenant, target_tenant = uuid4(), uuid4()
    _, _, actor = _actor(source_tenant)
    audit = AppendOnlyAuditService()
    with pytest.raises(PermissionError, match="Cross-tenant"):
        TenantAuditService(audit).append(
            evidence=_evidence(target_tenant),
            actor=actor,
            event_type=AuditEventType.EVIDENCE_VALIDATION_STARTED,
            result="STARTED",
            correlation_id=uuid4(),
        )
    assert audit.events == ()
