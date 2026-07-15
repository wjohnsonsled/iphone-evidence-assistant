"""Case repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ArtifactCoverage, Case, Device, EvidenceEvent, ProcessingJob


class CaseRepository:
    """Data-access methods for cases."""

    def create(self, session: Session, name: str, description: str | None, source_path: str | None) -> Case:
        """Create and flush a case."""

        case = Case(name=name, description=description, source_path=source_path)
        session.add(case)
        session.flush()
        return case

    def get(self, session: Session, case_id: UUID) -> Case | None:
        """Return a case by ID."""

        return session.get(Case, case_id)

    def latest_job(self, session: Session, case_id: UUID) -> ProcessingJob | None:
        """Return the latest processing job for a case."""

        return session.scalars(
            select(ProcessingJob)
            .where(ProcessingJob.case_id == case_id)
            .order_by(ProcessingJob.created_at.desc())
            .limit(1)
        ).first()

    def evidence_counts(self, session: Session, case_id: UUID) -> dict[str, int]:
        """Return evidence aggregate counts."""

        total = session.scalar(select(func.count()).select_from(EvidenceEvent).where(EvidenceEvent.case_id == case_id)) or 0
        return {"total": int(total)}

    def coverage_counts(self, session: Session, case_id: UUID) -> dict[str, int]:
        """Return coverage counts by status."""

        rows = session.execute(
            select(ArtifactCoverage.coverage_status, func.count())
            .where(ArtifactCoverage.case_id == case_id)
            .group_by(ArtifactCoverage.coverage_status)
        ).all()
        return {str(status): int(count) for status, count in rows}

    def devices(self, session: Session, case_id: UUID) -> list[Device]:
        """Return devices attached to a case."""

        return list(session.scalars(select(Device).where(Device.case_id == case_id)))
