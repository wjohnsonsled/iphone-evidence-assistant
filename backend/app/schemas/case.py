"""Case API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CaseCreate(BaseModel):
    """Request body for creating a case."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    source_path: str | None = None


class CaseCreated(BaseModel):
    """Response body after creating a case."""

    id: UUID
    name: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceSummary(BaseModel):
    """Non-sensitive device summary."""

    id: UUID
    device_name: str | None
    device_type: str
    ios_version: str | None = None
    product_type: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CaseDetail(BaseModel):
    """Case metadata and aggregate state."""

    id: UUID
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None
    processing_state: dict
    devices: list[DeviceSummary]
    evidence_counts: dict[str, int]
    coverage_counts: dict[str, int]

    model_config = ConfigDict(from_attributes=True)
