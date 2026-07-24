"""Evidence repository."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import EvidenceEvent


class EvidenceRepository:
    """Data-access methods for evidence events."""

    def add_many(self, session: Session, events: list[EvidenceEvent]) -> None:
        """Persist many events in one unit of work."""

        session.add_all(events)

    def get_for_case(self, session: Session, case_id: UUID, evidence_id: UUID) -> EvidenceEvent | None:
        """Return one evidence event belonging to the case."""

        return session.scalars(
            select(EvidenceEvent).where(EvidenceEvent.case_id == case_id, EvidenceEvent.id == evidence_id)
        ).first()

    def query(
        self,
        session: Session,
        case_id: UUID,
        *,
        event_type: str | None = None,
        category: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        contact_key: str | None = None,
        conversation_key: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort: str = "asc",
    ) -> tuple[int, list[EvidenceEvent]]:
        """Return filtered evidence count and rows."""

        stmt = self._filtered_select(
            case_id,
            event_type=event_type,
            category=category,
            start_time=start_time,
            end_time=end_time,
            contact_key=contact_key,
            conversation_key=conversation_key,
        )
        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        order_column = EvidenceEvent.timestamp.desc() if sort == "desc" else EvidenceEvent.timestamp.asc()
        rows = list(session.scalars(stmt.order_by(order_column.nulls_last(), EvidenceEvent.id.asc()).limit(limit).offset(offset)))
        return int(total), rows

    def _filtered_select(self, case_id: UUID, **filters) -> Select[tuple[EvidenceEvent]]:
        stmt = select(EvidenceEvent).where(EvidenceEvent.case_id == case_id)
        if filters.get("event_type"):
            stmt = stmt.where(EvidenceEvent.event_type == filters["event_type"])
        if filters.get("category"):
            stmt = stmt.where(EvidenceEvent.category == filters["category"])
        if filters.get("start_time"):
            stmt = stmt.where(EvidenceEvent.timestamp >= filters["start_time"])
        if filters.get("end_time"):
            stmt = stmt.where(EvidenceEvent.timestamp <= filters["end_time"])
        if filters.get("contact_key"):
            stmt = stmt.where(EvidenceEvent.contact_key == filters["contact_key"])
        if filters.get("conversation_key"):
            stmt = stmt.where(EvidenceEvent.conversation_key == filters["conversation_key"])
        return stmt
