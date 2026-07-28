"""Tenant-scoped processing-run identity without parser or lifecycle behavior."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.security.audit_attribution import AuditActorContext
from app.security.authorization import AuthorizationService
from app.security.case import SecurityCase
from app.security.evidence_source import EvidenceSource


_PURPOSE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
CREATE_ACTION = "processing-run.create"


@dataclass(frozen=True, slots=True)
class ProcessingRun:
    processing_run_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    purpose_key: str
    requested_at: datetime
    requested_by_actor_id: UUID
    correlation_id: UUID
    authorization_policy_id: UUID
    authorization_policy_version: int
    version: int = 1

    def __post_init__(self) -> None:
        if self.processing_run_id.version != 4:
            raise ValueError("Processing-run identity must be UUIDv4.")
        if not _PURPOSE.fullmatch(self.purpose_key):
            raise ValueError("Processing-run purpose must be canonical.")
        if self.requested_at.tzinfo is None or self.requested_at.utcoffset() is None:
            raise ValueError("Processing-run request time must be timezone-aware.")
        if self.authorization_policy_id.version != 4:
            raise ValueError("Authorization policy identity must be UUIDv4.")
        if self.authorization_policy_version < 1 or self.version < 1:
            raise ValueError("Versions must be positive.")


class ProcessingRunService:
    """Create traceable run identities only after exact scoped authorization."""

    def __init__(self, authorization: AuthorizationService) -> None:
        self._authorization = authorization

    def create(
        self,
        *,
        actor: AuditActorContext,
        case: SecurityCase,
        evidence_source: EvidenceSource,
        purpose_key: str,
        correlation_id: UUID,
        requested_at: datetime | None = None,
    ) -> ProcessingRun:
        decision = self._authorization.require(
            actor=actor,
            action_key=CREATE_ACTION,
            case=case,
            evidence_source=evidence_source,
        )
        return ProcessingRun(
            processing_run_id=uuid4(),
            tenant_id=case.tenant_id,
            case_id=case.case_id,
            evidence_source_id=evidence_source.evidence_source_id,
            purpose_key=purpose_key,
            requested_at=requested_at or datetime.now(timezone.utc),
            requested_by_actor_id=actor.principal_id,
            correlation_id=correlation_id,
            authorization_policy_id=decision.policy_id,
            authorization_policy_version=decision.policy_version,
        )
