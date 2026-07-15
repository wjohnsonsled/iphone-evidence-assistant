"""Evidence API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvidenceListItem(BaseModel):
    """Evidence fields returned in list responses."""

    id: UUID
    timestamp: datetime | None
    event_type: str
    category: str | None
    summary: str | None
    source_artifact: str | None
    source_database: str | None
    source_record_id: str | None
    confidence_score: int | None
    conversation_key: str | None
    contact_key: str | None

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponse(BaseModel):
    """Paginated evidence list response."""

    case_id: UUID
    total: int
    count: int
    items: list[EvidenceListItem]


class EvidenceDetail(BaseModel):
    """Complete normalized evidence record."""

    id: UUID
    case_id: UUID
    device_id: UUID | None
    external_event_id: str | None
    event_type: str
    category: str | None
    timestamp: datetime | None
    timestamp_end: datetime | None
    timezone_name: str | None
    summary: str | None
    details_json: dict
    raw_values_json: dict
    source_artifact: str | None
    source_database: str | None
    source_table: str | None
    source_record_id: str | None
    source_path: str | None
    parser_name: str | None
    parser_version: str | None
    confidence_score: int | None
    confidence_basis_json: dict
    artifact_hash: str | None
    conversation_key: str | None
    contact_key: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceQuery(BaseModel):
    """Validated evidence query parameters."""

    event_type: str | None = None
    category: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    contact_key: str | None = None
    conversation_key: str | None = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    sort: str = Field(default="asc", pattern="^(asc|desc)$")


class EvidenceSummary(BaseModel):
    """Deterministic case summary."""

    case_id: UUID
    total_events: int
    earliest_timestamp: datetime | None
    latest_timestamp: datetime | None
    counts_by_event_type: dict[str, int]
    counts_by_artifact: dict[str, int]
    top_contacts: list[dict]
    top_conversations: list[dict]
    attachment_count: int
    coverage_statuses: dict[str, int]
    warning_count: int
    error_count: int
