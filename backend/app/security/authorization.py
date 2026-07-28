"""Fail-closed authorization using an explicit caller-supplied policy snapshot."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from app.security.audit_attribution import AuditActorContext
from app.security.case import SecurityCase
from app.security.evidence_source import EvidenceSource


_KEY = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")


@dataclass(frozen=True, slots=True)
class PolicyGrant:
    role_key: str
    action_key: str

    def __post_init__(self) -> None:
        if not _KEY.fullmatch(self.role_key) or not _KEY.fullmatch(self.action_key):
            raise ValueError("Policy keys must be canonical.")


@dataclass(frozen=True, slots=True)
class PolicySnapshot:
    policy_id: UUID
    version: int
    grants: tuple[PolicyGrant, ...]

    def __post_init__(self) -> None:
        if self.policy_id.version != 4 or self.version < 1:
            raise ValueError("Policy identity must be UUIDv4 and version positive.")
        if len(set(self.grants)) != len(self.grants):
            raise ValueError("Policy grants must be unique.")


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason_code: str
    tenant_id: UUID
    principal_id: UUID
    action_key: str
    policy_id: UUID
    policy_version: int


class AuthorizationService:
    """Exact-match policy evaluation; an empty policy denies every action."""

    def __init__(self, policy: PolicySnapshot) -> None:
        self._policy = policy

    def authorize(
        self,
        *,
        actor: AuditActorContext,
        action_key: str,
        case: SecurityCase,
        evidence_source: EvidenceSource | None = None,
    ) -> AuthorizationDecision:
        if not _KEY.fullmatch(action_key):
            return self._decision(False, "invalid_action", actor, action_key)
        if actor.tenant_id != case.tenant_id:
            return self._decision(False, "tenant_scope_mismatch", actor, action_key)
        if evidence_source is not None and (
            evidence_source.tenant_id != case.tenant_id
            or evidence_source.case_id != case.case_id
        ):
            return self._decision(False, "resource_scope_mismatch", actor, action_key)
        grant = PolicyGrant(actor.role_key, action_key)
        if grant not in self._policy.grants:
            return self._decision(False, "policy_denied", actor, action_key)
        return self._decision(True, "policy_granted", actor, action_key)

    def require(self, **kwargs: object) -> AuthorizationDecision:
        decision = self.authorize(**kwargs)  # type: ignore[arg-type]
        if not decision.allowed:
            raise PermissionError(decision.reason_code)
        return decision

    def _decision(
        self,
        allowed: bool,
        reason: str,
        actor: AuditActorContext,
        action: str,
    ) -> AuthorizationDecision:
        return AuthorizationDecision(
            allowed,
            reason,
            actor.tenant_id,
            actor.principal_id,
            action,
            self._policy.policy_id,
            self._policy.version,
        )
