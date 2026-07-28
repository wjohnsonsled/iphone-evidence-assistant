"""Adversarial tenant-isolation checks across supported-boundary services."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.integrity.domain import AuditEventType, register_evidence
from app.integrity.services import AppendOnlyAuditService
from app.security.audit_attribution import AuditActorContext, TenantAuditService
from app.security.authorization import AuthorizationService, PolicyGrant, PolicySnapshot
from app.security.case import SecurityCase
from app.security.evidence_source import EvidenceSource
from app.security.identity import PrincipalKind


def uid(value: int) -> UUID:
    return UUID(f"70000000-0000-4000-8000-{value:012d}")


NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)
ACTOR = AuditActorContext(uid(1), uid(2), uid(3), PrincipalKind.USER, "reviewer")
CASE = SecurityCase(uid(4), uid(1), "Tenant A", NOW, uid(2))
OTHER_CASE = SecurityCase(uid(5), uid(6), "Tenant B", NOW, uid(7))


def test_explicit_grant_never_overrides_tenant_scope() -> None:
    service = AuthorizationService(
        PolicySnapshot(uid(8), 1, (PolicyGrant("reviewer", "case.read"),))
    )
    decision = service.authorize(actor=ACTOR, action_key="case.read", case=OTHER_CASE)
    assert (decision.allowed, decision.reason_code) == (False, "tenant_scope_mismatch")


def test_source_from_other_case_never_crosses_scope() -> None:
    source = EvidenceSource(uid(9), uid(1), OTHER_CASE.case_id, "candidate", "synthetic://x", NOW, uid(2))
    service = AuthorizationService(
        PolicySnapshot(uid(8), 1, (PolicyGrant("reviewer", "source.read"),))
    )
    decision = service.authorize(
        actor=ACTOR, action_key="source.read", case=CASE, evidence_source=source
    )
    assert (decision.allowed, decision.reason_code) == (False, "resource_scope_mismatch")


def test_cross_tenant_audit_denial_appends_nothing() -> None:
    evidence = register_evidence(
        tenant_id=uid(6), case_id=uid(5), evidence_source_id=uid(11),
        evidence_kind="SOURCE", source_type="SYNTHETIC",
        source_locator="synthetic://x", logical_identifier="x",
        intake_method="SYNTHETIC_TEST", registered_at=NOW,
        registered_by_actor_id=uid(7),
    )
    audit = AppendOnlyAuditService()
    with pytest.raises(PermissionError, match="Cross-tenant"):
        TenantAuditService(audit).append(
            evidence=evidence, actor=ACTOR,
            event_type=AuditEventType.EVIDENCE_VALIDATION_STARTED,
            result="DENIED", correlation_id=uid(14),
        )
    assert audit.events == ()
