"""Evidence API endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.repositories.cases import CaseRepository
from app.repositories.evidence import EvidenceRepository
from app.schemas.evidence import EvidenceDetail, EvidenceListItem, EvidenceListResponse

router = APIRouter()


@router.get("/{case_id}/evidence", response_model=EvidenceListResponse)
def list_evidence(
    case_id: UUID,
    event_type: str | None = None,
    category: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    contact_key: str | None = None,
    conversation_key: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
) -> EvidenceListResponse:
    """List normalized evidence records without raw values by default."""

    if not CaseRepository().get(session, case_id):
        raise ApiError(404, "case_not_found", "Case was not found.")
    total, rows = EvidenceRepository().query(
        session,
        case_id,
        event_type=event_type,
        category=category,
        start_time=start_time,
        end_time=end_time,
        contact_key=contact_key,
        conversation_key=conversation_key,
        limit=limit,
        offset=offset,
        sort=sort,
    )
    return EvidenceListResponse(
        case_id=case_id,
        total=total,
        count=len(rows),
        items=[EvidenceListItem.model_validate(row) for row in rows],
    )


@router.get("/{case_id}/evidence/{evidence_id}", response_model=EvidenceDetail)
def get_evidence_record(case_id: UUID, evidence_id: UUID, session: Session = Depends(get_session)) -> EvidenceDetail:
    """Return a complete normalized evidence record for the requested case."""

    row = EvidenceRepository().get_for_case(session, case_id, evidence_id)
    if not row:
        raise ApiError(404, "evidence_record_not_found", "Evidence record was not found for this case.")
    return EvidenceDetail.model_validate(row)
