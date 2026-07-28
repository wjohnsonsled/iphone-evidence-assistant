from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.evidence_core.processing_run import ProcessingRun
from app.evidence_core.source_artifact import SourceArtifactService
from app.security.audit_attribution import AuditActorContext
from app.security.authorization import AuthorizationService, PolicyGrant, PolicySnapshot
from app.security.case import SecurityCase
from app.security.evidence_source import EvidenceSource
from app.security.identity import PrincipalKind


def u(n: int) -> UUID:
    return UUID(f"41000000-0000-4000-8000-{n:012d}")


NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)
ACTOR = AuditActorContext(u(1), u(2), u(3), PrincipalKind.SERVICE, "processor")
CASE = SecurityCase(u(4), u(1), "Synthetic", NOW, u(2))
SOURCE = EvidenceSource(u(5), u(1), u(4), "candidate", "synthetic://backup", NOW, u(2))
RUN = ProcessingRun(u(6), u(1), u(4), u(5), "candidate-validation", NOW, u(2), u(7), u(8), 1)


def service(granted: bool = True) -> SourceArtifactService:
    grants = (PolicyGrant("processor", "source-artifact.register"),) if granted else ()
    return SourceArtifactService(AuthorizationService(PolicySnapshot(u(8), 1, grants)))


def test_registration_preserves_complete_scope_and_policy_provenance() -> None:
    artifact = service().register(
        actor=ACTOR, case=CASE, evidence_source=SOURCE, processing_run=RUN,
        evidence_uuid=u(9), artifact_family_key="backup-metadata", observed_at=NOW,
    )
    assert (artifact.tenant_id, artifact.case_id, artifact.evidence_source_id) == (u(1), u(4), u(5))
    assert (artifact.processing_run_id, artifact.evidence_uuid) == (u(6), u(9))
    assert artifact.authorization_policy_id == u(8)
    assert artifact.source_artifact_id.version == 4


def test_denied_policy_and_mismatched_run_fail_closed() -> None:
    with pytest.raises(PermissionError, match="policy_denied"):
        service(False).register(
            actor=ACTOR, case=CASE, evidence_source=SOURCE, processing_run=RUN,
            evidence_uuid=u(9), artifact_family_key="backup-metadata",
        )
    wrong_run = ProcessingRun(u(10), u(1), u(4), u(11), "candidate-validation", NOW, u(2), u(7), u(8), 1)
    with pytest.raises(PermissionError, match="processing_run_scope_mismatch"):
        service().register(
            actor=ACTOR, case=CASE, evidence_source=SOURCE, processing_run=wrong_run,
            evidence_uuid=u(9), artifact_family_key="backup-metadata",
        )


def test_registration_does_not_contain_support_or_locator_fields() -> None:
    names = set(SourceArtifactService.register.__annotations__)
    assert "support_status" not in names and "source_locator" not in names
