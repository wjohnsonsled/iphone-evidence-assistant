from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.evidence_core.processing_run import ProcessingRun, ProcessingRunService
from app.models.processing_run import SupportedProcessingRunModel
from app.security.audit_attribution import AuditActorContext
from app.security.authorization import AuthorizationService, PolicyGrant, PolicySnapshot
from app.security.case import SecurityCase
from app.security.evidence_source import EvidenceSource
from app.security.identity import PrincipalKind


def uid(value: int) -> UUID:
    return UUID(f"40000000-0000-4000-8000-{value:012d}")


NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
ACTOR = AuditActorContext(uid(1), uid(2), uid(3), PrincipalKind.SERVICE, "processor")
CASE = SecurityCase(uid(4), uid(1), "Synthetic", NOW, uid(2))
SOURCE = EvidenceSource(uid(5), uid(1), uid(4), "candidate", "synthetic://backup", NOW, uid(2))


def service(*grants: PolicyGrant) -> ProcessingRunService:
    return ProcessingRunService(AuthorizationService(PolicySnapshot(uid(6), 2, grants)))


def test_authorized_creation_preserves_scope_actor_policy_and_correlation() -> None:
    run = service(PolicyGrant("processor", "processing-run.create")).create(
        actor=ACTOR, case=CASE, evidence_source=SOURCE,
        purpose_key="candidate-validation", correlation_id=uid(7), requested_at=NOW,
    )
    assert (run.tenant_id, run.case_id, run.evidence_source_id) == (uid(1), uid(4), uid(5))
    assert (run.requested_by_actor_id, run.correlation_id) == (uid(2), uid(7))
    assert (run.authorization_policy_id, run.authorization_policy_version) == (uid(6), 2)
    assert run.processing_run_id.version == 4
    with pytest.raises(FrozenInstanceError):
        run.purpose_key = "changed"


def test_empty_policy_and_cross_scope_source_fail_before_creation() -> None:
    with pytest.raises(PermissionError, match="policy_denied"):
        service().create(
            actor=ACTOR, case=CASE, evidence_source=SOURCE,
            purpose_key="candidate-validation", correlation_id=uid(7),
        )
    foreign = EvidenceSource(uid(8), uid(9), uid(10), "candidate", "synthetic://foreign", NOW, uid(11))
    with pytest.raises(PermissionError, match="resource_scope_mismatch"):
        service(PolicyGrant("processor", "processing-run.create")).create(
            actor=ACTOR, case=CASE, evidence_source=foreign,
            purpose_key="candidate-validation", correlation_id=uid(7),
        )


@pytest.mark.parametrize("purpose", ["", "Candidate Validation", "candidate/validation"])
def test_invalid_purpose_is_rejected(purpose: str) -> None:
    with pytest.raises(ValueError):
        ProcessingRun(uid(12), uid(1), uid(4), uid(5), purpose, NOW, uid(2), uid(7), uid(6), 2)


def test_orm_contract_is_separate_from_legacy_jobs_and_tenant_scoped() -> None:
    table = SupportedProcessingRunModel.__table__
    assert table.name == "supported_processing_runs"
    assert table.name != "processing_jobs"
    assert {"tenant_id", "case_id", "evidence_source_id", "authorization_policy_id"} <= set(table.columns.keys())
    assert any(constraint.name == "fk_supported_run_case_tenant" for constraint in table.constraints)
