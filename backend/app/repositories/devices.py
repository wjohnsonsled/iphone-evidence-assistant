"""Device repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Device


class DeviceRepository:
    """Data-access methods for devices."""

    def create(self, session: Session, case_id: UUID, **values) -> Device:
        """Create and flush a device."""

        device = Device(case_id=case_id, **values)
        session.add(device)
        session.flush()
        return device

    def first_for_case(self, session: Session, case_id: UUID) -> Device | None:
        """Return first device for a case."""

        return session.scalars(select(Device).where(Device.case_id == case_id).order_by(Device.created_at.asc())).first()
