"""Translate evidence-engine domain objects into database rows."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ArtifactCoverage, EvidenceEvent
from app.repositories.coverage import CoverageRepository
from app.repositories.evidence import EvidenceRepository

logger = logging.getLogger(__name__)


@dataclass
class EvidenceEngineResult:
    """Domain result returned by the evidence-engine adapter."""

    events: list[Any] = field(default_factory=list)
    normalized_events: list[dict[str, Any]] = field(default_factory=list)
    coverage_records: list[Any] = field(default_factory=list)
    app_coverage_records: list[Any] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    device_metadata: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PersistenceStatistics:
    """Persistence result counts and validation details."""

    inserted_events: int = 0
    skipped_duplicate_events: int = 0
    inserted_coverage_records: int = 0
    warnings: int = 0
    errors: int = 0
    validation_failures: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-serializable statistics."""

        return {
            "inserted_events": self.inserted_events,
            "skipped_duplicate_events": self.skipped_duplicate_events,
            "inserted_coverage_records": self.inserted_coverage_records,
            "warnings": self.warnings,
            "errors": self.errors,
            "validation_failures": self.validation_failures,
        }


class EvidencePersistenceService:
    """Persist evidence-engine results without coupling the engine to SQLAlchemy."""

    def __init__(
        self,
        evidence_repo: EvidenceRepository | None = None,
        coverage_repo: CoverageRepository | None = None,
    ) -> None:
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.coverage_repo = coverage_repo or CoverageRepository()

    def persist_result(
        self,
        session: Session,
        case_id: UUID,
        device_id: UUID | None,
        result: EvidenceEngineResult,
    ) -> PersistenceStatistics:
        """Persist normalized events and coverage records in batch."""

        stats = PersistenceStatistics(warnings=len(result.warnings), errors=len(result.errors))
        try:
            event_rows = self._build_event_rows(case_id, device_id, result, stats)
            event_rows = self._remove_existing_duplicates(session, case_id, event_rows, stats)
            coverage_rows = self._build_coverage_rows(case_id, device_id, result)
            self.evidence_repo.add_many(session, event_rows)
            self.coverage_repo.add_many(session, coverage_rows)
            session.flush()
            stats.inserted_events = len(event_rows)
            stats.inserted_coverage_records = len(coverage_rows)
            return stats
        except Exception:
            logger.exception("evidence_persistence_failed case_id=%s", case_id)
            session.rollback()
            raise

    def _build_event_rows(
        self,
        case_id: UUID,
        device_id: UUID | None,
        result: EvidenceEngineResult,
        stats: PersistenceStatistics,
    ) -> list[EvidenceEvent]:
        rows: list[EvidenceEvent] = []
        normalized = result.normalized_events or [self._legacy_event_to_dict(event) for event in result.events]
        for index, item in enumerate(normalized):
            try:
                event_type = str(item.get("event_type") or item.get("event_subtype") or "").strip()
                if not event_type:
                    raise ValueError("event_type is required")
                fingerprint = item.get("external_event_id") or item.get("event_id") or derive_event_fingerprint(case_id, item)
                row = EvidenceEvent(
                    case_id=case_id,
                    device_id=device_id,
                    external_event_id=item.get("event_id") or item.get("external_event_id"),
                    event_type=event_type,
                    category=item.get("event_category") or item.get("category"),
                    timestamp=_parse_datetime(item.get("timestamp")),
                    timestamp_end=_parse_datetime(item.get("timestamp_end")),
                    timezone_name=item.get("timezone_name"),
                    summary=item.get("description") or item.get("summary"),
                    details_json=_details_json(item),
                    raw_values_json=item.get("raw_values") or item.get("raw_values_json") or item.get("metadata") or {},
                    source_artifact=item.get("source_artifact") or item.get("source"),
                    source_database=item.get("source_database"),
                    source_table=item.get("source_table"),
                    source_record_id=str(item.get("source_rowid") or item.get("source_record_id") or ""),
                    source_path=item.get("source_path"),
                    parser_name=item.get("parser_name") or item.get("source"),
                    parser_version=str(item.get("parser_version") or ""),
                    confidence_score=_safe_int(item.get("confidence_score")),
                    confidence_basis_json={"basis": item.get("confidence_basis"), "strength": item.get("evidence_strength")},
                    artifact_hash=str(fingerprint),
                    conversation_key=_first_value(item, ["conversation_key", "chat_rowid", "chat_identifier"]),
                    contact_key=_first_value(item, ["contact_key", "contact", "raw_contact", "resolved_contact"]),
                )
                rows.append(row)
            except Exception as exc:
                stats.validation_failures.append({"index": str(index), "error": str(exc)})
        if stats.validation_failures:
            raise ValueError(f"{len(stats.validation_failures)} evidence records failed validation")
        return rows

    def _remove_existing_duplicates(
        self,
        session: Session,
        case_id: UUID,
        rows: list[EvidenceEvent],
        stats: PersistenceStatistics,
    ) -> list[EvidenceEvent]:
        fingerprints = {row.artifact_hash for row in rows if row.artifact_hash}
        if not fingerprints:
            return rows
        existing = set(
            session.scalars(
                select(EvidenceEvent.artifact_hash).where(
                    EvidenceEvent.case_id == case_id,
                    EvidenceEvent.artifact_hash.in_(fingerprints),
                )
            )
        )
        seen: set[str] = set()
        unique_rows: list[EvidenceEvent] = []
        for row in rows:
            fingerprint = row.artifact_hash or ""
            if fingerprint in existing or fingerprint in seen:
                stats.skipped_duplicate_events += 1
                continue
            seen.add(fingerprint)
            unique_rows.append(row)
        return unique_rows

    def _build_coverage_rows(
        self,
        case_id: UUID,
        device_id: UUID | None,
        result: EvidenceEngineResult,
    ) -> list[ArtifactCoverage]:
        rows: list[ArtifactCoverage] = []
        for record in result.coverage_records:
            data = _object_to_dict(record)
            rows.append(
                ArtifactCoverage(
                    case_id=case_id,
                    device_id=device_id,
                    artifact_name=data.get("artifact_name") or data.get("artifact_id") or "unknown",
                    coverage_status=map_coverage_status(data.get("coverage_status")),
                    parser_name=data.get("parser_name"),
                    source_path=data.get("relative_path") or data.get("absolute_path"),
                    records_parsed=int(data.get("records_normalized_total") or 0),
                    warning_count=1 if data.get("unsupported_reason") else 0,
                    error_count=int(data.get("error_count") or 0),
                    details_json=data,
                )
            )
        return rows

    def _legacy_event_to_dict(self, event: Any) -> dict[str, Any]:
        metadata = getattr(event, "metadata", {}) or {}
        return {
            "timestamp": getattr(event, "timestamp", None),
            "source": getattr(event, "source", None),
            "event_type": getattr(event, "event_type", None),
            "event_category": getattr(event, "source", None),
            "description": getattr(event, "details", None) or getattr(event, "significance", None),
            "metadata": metadata,
            "source_database": metadata.get("source_db"),
            "source_rowid": metadata.get("rowid") or metadata.get("message_id"),
            "confidence_score": getattr(event, "confidence_score", None),
            "confidence_basis": getattr(event, "confidence_basis", None),
            "evidence_strength": getattr(event, "evidence_strength", None),
        }


def derive_event_fingerprint(case_id: UUID, item: dict[str, Any]) -> str:
    """Derive a deterministic event fingerprint for duplicate control."""

    parts = [
        str(case_id),
        str(item.get("source_database") or ""),
        str(item.get("source_table") or ""),
        str(item.get("source_rowid") or item.get("source_record_id") or ""),
        str(item.get("event_type") or item.get("event_subtype") or ""),
        str(item.get("timestamp") or ""),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def map_coverage_status(status: Any) -> str:
    """Map engine coverage statuses while retaining original status in details."""

    value = str(status or "UNKNOWN")
    if value == "PRESENT_PARSED_WITH_RECORDS":
        return "available_and_parsed"
    if value in {"PRESENT_PARSED_ZERO_RECORDS", "PRESENT_PARSED_NO_WINDOW_RECORDS"}:
        return "available_no_records"
    if value in {"PRESENT_UNSUPPORTED", "PRESENT_UNKNOWN_SCHEMA"}:
        return "unsupported"
    if value in {"PRESENT_PARSE_FAILED", "PRESENT_ENCRYPTED_OR_INACCESSIBLE"}:
        return "parser_failed"
    if value == "NOT_PRESENT":
        return "not_present"
    if value in {"OUTSIDE_ACQUISITION_SCOPE", "OUTSIDE_STANDARD_BACKUP", "NOT_COLLECTED"}:
        return "not_in_acquisition"
    return "unknown"


def _object_to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    if isinstance(value, dict):
        return value
    return {}


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def _first_value(item: dict[str, Any], keys: list[str]) -> str | None:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    for key in keys:
        value = item.get(key, metadata.get(key))
        if value not in (None, ""):
            return str(value)
    return None


def _details_json(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "description": item.get("description"),
        "text": item.get("text"),
        "limitations": item.get("limitations", []),
        "entity_links": item.get("entity_links", []),
    }
