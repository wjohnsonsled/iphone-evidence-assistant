"""Coverage schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CoverageRecordRead(BaseModel):
    """Artifact coverage response item."""

    id: UUID
    artifact_name: str
    coverage_status: str
    parser_name: str | None
    records_parsed: int
    warning_count: int
    error_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
