"""Processing job repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProcessingJob


class JobRepository:
    """Data-access methods for processing jobs."""

    def create(self, session: Session, case_id: UUID, status: str = "queued", stage: str = "queued") -> ProcessingJob:
        """Create and flush a processing job."""

        job = ProcessingJob(case_id=case_id, status=status, stage=stage)
        session.add(job)
        session.flush()
        return job

    def active_for_case(self, session: Session, case_id: UUID) -> ProcessingJob | None:
        """Return an active processing job for a case, if present."""

        return session.scalars(
            select(ProcessingJob).where(
                ProcessingJob.case_id == case_id,
                ProcessingJob.status.in_(["queued", "running", "processing"]),
            )
        ).first()
