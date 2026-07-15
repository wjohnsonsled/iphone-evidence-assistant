"""Deterministic evidence summary service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ArtifactCoverage, EvidenceEvent, ProcessingJob


class EvidenceSummaryService:
    """Build deterministic case summaries without LLM calls."""

    def build_summary(self, session: Session, case_id: UUID) -> dict:
        """Return aggregate evidence and coverage counts."""

        total = session.scalar(select(func.count()).select_from(EvidenceEvent).where(EvidenceEvent.case_id == case_id)) or 0
        earliest = session.scalar(select(func.min(EvidenceEvent.timestamp)).where(EvidenceEvent.case_id == case_id))
        latest = session.scalar(select(func.max(EvidenceEvent.timestamp)).where(EvidenceEvent.case_id == case_id))
        return {
            "case_id": case_id,
            "total_events": int(total),
            "earliest_timestamp": earliest,
            "latest_timestamp": latest,
            "counts_by_event_type": _counts(session, EvidenceEvent.event_type, case_id),
            "counts_by_artifact": _counts(session, EvidenceEvent.source_artifact, case_id),
            "top_contacts": _top_counts(session, EvidenceEvent.contact_key, case_id),
            "top_conversations": _top_counts(session, EvidenceEvent.conversation_key, case_id),
            "attachment_count": _attachment_count(session, case_id),
            "coverage_statuses": _coverage_counts(session, case_id),
            "warning_count": _job_sum(session, case_id, "warnings"),
            "error_count": _coverage_error_count(session, case_id),
        }


def _counts(session: Session, column, case_id: UUID) -> dict[str, int]:
    rows = session.execute(
        select(column, func.count()).where(EvidenceEvent.case_id == case_id, column.is_not(None)).group_by(column)
    ).all()
    return {str(key): int(count) for key, count in rows if key}


def _top_counts(session: Session, column, case_id: UUID, limit: int = 10) -> list[dict]:
    rows = session.execute(
        select(column, func.count())
        .where(EvidenceEvent.case_id == case_id, column.is_not(None), column != "")
        .group_by(column)
        .order_by(func.count().desc())
        .limit(limit)
    ).all()
    return [{"key": str(key), "count": int(count)} for key, count in rows if key]


def _attachment_count(session: Session, case_id: UUID) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(EvidenceEvent).where(
                EvidenceEvent.case_id == case_id,
                EvidenceEvent.event_type.ilike("%attachment%"),
            )
        )
        or 0
    )


def _coverage_counts(session: Session, case_id: UUID) -> dict[str, int]:
    rows = session.execute(
        select(ArtifactCoverage.coverage_status, func.count())
        .where(ArtifactCoverage.case_id == case_id)
        .group_by(ArtifactCoverage.coverage_status)
    ).all()
    return {str(status): int(count) for status, count in rows}


def _coverage_error_count(session: Session, case_id: UUID) -> int:
    return int(session.scalar(select(func.coalesce(func.sum(ArtifactCoverage.error_count), 0)).where(ArtifactCoverage.case_id == case_id)) or 0)


def _job_sum(session: Session, case_id: UUID, key: str) -> int:
    jobs = session.scalars(select(ProcessingJob).where(ProcessingJob.case_id == case_id)).all()
    if key == "warnings":
        return sum(len(job.warnings_json or []) for job in jobs)
    return 0
