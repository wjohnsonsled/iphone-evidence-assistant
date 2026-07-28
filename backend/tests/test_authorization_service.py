from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.security.audit_attribution import AuditActorContext
from app.security.authorization import AuthorizationService, PolicyGrant, PolicySnapshot
from app.security.case import SecurityCase
from app.security.evidence_source import EvidenceSource
from app.security.identity import PrincipalKind


def uid(value: int) -> UUID:
    return UUID(f"30000000-0000-4000-8000-{value:012d}")


ACTOR = AuditActorContext(uid(1), uid(2), uid(3), PrincipalKind.USER, "reviewer")
CASE = SecurityCase(uid(4), uid(1), "Synthetic", datetime.now(timezone.utc), uid(2))
SOURCE = EvidenceSource(
    uid(5), uid(1), uid(4), "candidate", "synthetic://backup",
    datetime.now(timezone.utc), uid(2),
)


def service(*grants: PolicyGrant) -> AuthorizationService:
    return AuthorizationService(PolicySnapshot(uid(6), 1, grants))


def test_explicit_exact_grant_allows_and_is_traceable() -> None:
    result = service(PolicyGrant("reviewer", "case.read")).authorize(
        actor=ACTOR, action_key="case.read", case=CASE, evidence_source=SOURCE
    )
    assert result.allowed and result.reason_code == "policy_granted"
    assert (result.policy_id, result.policy_version) == (uid(6), 1)


@pytest.mark.parametrize("action", ["case.write", "", "Case.Read"])
def test_missing_or_invalid_action_denies_closed(action: str) -> None:
    assert not service(PolicyGrant("reviewer", "case.read")).authorize(
        actor=ACTOR, action_key=action, case=CASE
    ).allowed


def test_empty_policy_and_wrong_role_deny() -> None:
    assert not service().authorize(actor=ACTOR, action_key="case.read", case=CASE).allowed
    assert not service(PolicyGrant("admin", "case.read")).authorize(
        actor=ACTOR, action_key="case.read", case=CASE
    ).allowed


def test_cross_tenant_and_cross_case_resources_deny_before_policy() -> None:
    other_case = SecurityCase(uid(7), uid(8), "Other", datetime.now(timezone.utc), uid(2))
    mismatch = SOURCE.__class__(
        SOURCE.evidence_source_id, SOURCE.tenant_id, uid(9), SOURCE.source_type,
        SOURCE.source_locator, SOURCE.registered_at, SOURCE.registered_by_actor_id,
    )
    policy = service(PolicyGrant("reviewer", "case.read"))
    assert policy.authorize(actor=ACTOR, action_key="case.read", case=other_case).reason_code == "tenant_scope_mismatch"
    assert policy.authorize(
        actor=ACTOR, action_key="case.read", case=CASE, evidence_source=mismatch
    ).reason_code == "resource_scope_mismatch"


def test_require_raises_safe_reason_on_denial() -> None:
    with pytest.raises(PermissionError, match="policy_denied"):
        service().require(actor=ACTOR, action_key="case.read", case=CASE)


def test_policy_rejects_noncanonical_or_duplicate_grants() -> None:
    with pytest.raises(ValueError):
        PolicyGrant("Reviewer", "case.read")
    grant = PolicyGrant("reviewer", "case.read")
    with pytest.raises(ValueError):
        PolicySnapshot(uid(6), 1, (grant, grant))
