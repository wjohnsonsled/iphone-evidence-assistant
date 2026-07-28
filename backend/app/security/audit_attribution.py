"""Tenant-safe principal attribution for append-only audit events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.integrity.domain import AuditEvent, AuditEventType, EvidenceObject
from app.integrity.services import AppendOnlyAuditService
from app.security.identity import Principal, PrincipalKind, TenantMembership


@dataclass(frozen=True, slots=True)
class AuditActorContext:
    tenant_id: UUID
    principal_id: UUID
    membership_id: UUID
    principal_kind: PrincipalKind
    role_key: str


def create_audit_actor(
    principal: Principal,
    membership: TenantMembership,
) -> AuditActorContext:
    if membership.principal_id != principal.principal_id:
        raise PermissionError("Membership does not belong to principal.")
    return AuditActorContext(
        tenant_id=membership.tenant_id,
        principal_id=principal.principal_id,
        membership_id=membership.membership_id,
        principal_kind=principal.kind,
        role_key=membership.role_key,
    )


class TenantAuditService:
    """Attribute events without creating a second audit store or taxonomy."""

    def __init__(self, audit: AppendOnlyAuditService) -> None:
        self._audit = audit

    def append(
        self,
        *,
        evidence: EvidenceObject,
        actor: AuditActorContext,
        event_type: AuditEventType,
        result: str,
        correlation_id: UUID,
        failure_code: str | None = None,
    ) -> AuditEvent:
        if evidence.tenant_id != actor.tenant_id:
            raise PermissionError("Cross-tenant audit attribution is prohibited.")
        return self._audit.append(
            evidence=evidence,
            event_type=event_type,
            actor_id=actor.principal_id,
            result=result,
            correlation_id=correlation_id,
            failure_code=failure_code,
        )
