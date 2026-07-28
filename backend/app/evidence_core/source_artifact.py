"""Source-artifact identity; presence and registration do not imply support."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.evidence_core.processing_run import ProcessingRun
from app.security.audit_attribution import AuditActorContext
from app.security.authorization import AuthorizationService
from app.security.case import SecurityCase
from app.security.evidence_source import EvidenceSource


_KEY = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
REGISTER_ACTION = "source-artifact.register"


@dataclass(frozen=True, slots=True)
class SourceArtifact:
    source_artifact_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    processing_run_id: UUID
    evidence_uuid: UUID
    artifact_family_key: str
    observed_at: datetime
    observed_by_actor_id: UUID
    authorization_policy_id: UUID
    authorization_policy_version: int
    version: int = 1

    def __post_init__(self) -> None:
        if self.source_artifact_id.version != 4:
            raise ValueError("Source-artifact identity must be UUIDv4.")
        if not _KEY.fullmatch(self.artifact_family_key):
            raise ValueError("Artifact-family key must be canonical.")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("Observation time must be timezone-aware.")
        if self.authorization_policy_id.version != 4:
            raise ValueError("Authorization policy identity must be UUIDv4.")
        if self.authorization_policy_version < 1 or self.version < 1:
            raise ValueError("Versions must be positive.")


class SourceArtifactService:
    def __init__(self, authorization: AuthorizationService) -> None:
        self._authorization = authorization

    def register(
        self,
        *,
        actor: AuditActorContext,
        case: SecurityCase,
        evidence_source: EvidenceSource,
        processing_run: ProcessingRun,
        evidence_uuid: UUID,
        artifact_family_key: str,
        observed_at: datetime | None = None,
    ) -> SourceArtifact:
        if (
            processing_run.tenant_id != case.tenant_id
            or processing_run.case_id != case.case_id
            or processing_run.evidence_source_id != evidence_source.evidence_source_id
        ):
            raise PermissionError("processing_run_scope_mismatch")
        decision = self._authorization.require(
            actor=actor,
            action_key=REGISTER_ACTION,
            case=case,
            evidence_source=evidence_source,
        )
        return SourceArtifact(
            uuid4(), case.tenant_id, case.case_id, evidence_source.evidence_source_id,
            processing_run.processing_run_id, evidence_uuid, artifact_family_key,
            observed_at or datetime.now(timezone.utc), actor.principal_id,
            decision.policy_id, decision.policy_version,
        )
