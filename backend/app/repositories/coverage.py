"""Coverage repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ArtifactCoverage


class CoverageRepository:
    """Data-access methods for artifact coverage."""

    def add_many(self, session: Session, records: list[ArtifactCoverage]) -> None:
        """Persist many coverage records in one unit of work."""

        session.add_all(records)
