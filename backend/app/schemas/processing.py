"""Processing API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProcessCaseRequest(BaseModel):
    """Request body for processing a server-local backup path."""

    backup_path: str


class ProcessingJobRead(BaseModel):
    """Processing job response."""

    id: UUID
    case_id: UUID
    status: str
    stage: str | None
    progress_percent: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    statistics_json: dict

    model_config = ConfigDict(from_attributes=True)
