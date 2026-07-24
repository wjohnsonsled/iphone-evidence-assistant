"""Case API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.errors import ApiError
from app.repositories.cases import CaseRepository
from app.schemas.case import CaseCreate, CaseCreated, CaseDetail, DeviceSummary
from app.schemas.evidence import EvidenceSummary
from app.schemas.processing import ProcessCaseRequest, ProcessingJobRead
from app.services.case_processing import CaseProcessingService
from app.services.evidence_summary import EvidenceSummaryService

router = APIRouter()


@router.post("", response_model=CaseCreated, status_code=201)
def create_case(payload: CaseCreate, session: Session = Depends(get_session)) -> CaseCreated:
    """Create a case without exposing source path in later public responses."""

    case = CaseRepository().create(session, payload.name, payload.description, payload.source_path)
    session.commit()
    session.refresh(case)
    return CaseCreated.model_validate(case)


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: UUID, session: Session = Depends(get_session)) -> CaseDetail:
    """Return case details and aggregate processing state."""

    repo = CaseRepository()
    case = repo.get(session, case_id)
    if not case:
        raise ApiError(404, "case_not_found", "Case was not found.")
    latest_job = repo.latest_job(session, case_id)
    return CaseDetail(
        id=case.id,
        name=case.name,
        description=case.description,
        status=case.status,
        created_at=case.created_at,
        updated_at=case.updated_at,
        processed_at=case.processed_at,
        processing_state={
            "status": latest_job.status if latest_job else None,
            "stage": latest_job.stage if latest_job else None,
            "progress_percent": latest_job.progress_percent if latest_job else 0,
        },
        devices=[DeviceSummary.model_validate(device) for device in repo.devices(session, case_id)],
        evidence_counts=repo.evidence_counts(session, case_id),
        coverage_counts=repo.coverage_counts(session, case_id),
    )


@router.post("/{case_id}/process", response_model=ProcessingJobRead)
def process_case(
    case_id: UUID,
    payload: ProcessCaseRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ProcessingJobRead:
    """Process a server-local decrypted backup path."""

    job = CaseProcessingService(settings).process_local_backup(session, case_id, payload.backup_path)
    return ProcessingJobRead.model_validate(job)


@router.get("/{case_id}/summary", response_model=EvidenceSummary)
def get_summary(case_id: UUID, session: Session = Depends(get_session)) -> EvidenceSummary:
    """Return deterministic evidence summary for a case."""

    if not CaseRepository().get(session, case_id):
        raise ApiError(404, "case_not_found", "Case was not found.")
    return EvidenceSummary.model_validate(EvidenceSummaryService().build_summary(session, case_id))
