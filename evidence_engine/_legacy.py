#!/usr/bin/env python3
"""
Window Investigator

Plugin-style forensic timeline builder for decrypted iPhone backups.

The tool intentionally uses cautious wording and best-effort parsing. Missing
or malformed artifacts are logged to reports/window_investigator_errors.log and
do not stop the run.
"""

import argparse
import csv
import hashlib
import html
import io
import ipaddress
import json
import os
import plistlib
import re
import sqlite3
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib import request as urlrequest
from urllib.error import URLError


APPLE_EPOCH = 978307200
WEBKIT_EPOCH = 978307200
OUTPUT_FIELDS = [
    "timestamp",
    "section",
    "source",
    "event_type",
    "significance",
    "confidence_score",
    "confidence_basis",
    "evidence_strength",
    "details",
    "metadata",
]

COVERAGE_STATUSES = {
    "NOT_PRESENT",
    "PRESENT_UNSUPPORTED",
    "PRESENT_PARSER_DISABLED",
    "PRESENT_PARSE_FAILED",
    "PRESENT_PARTIALLY_PARSED",
    "PRESENT_PARSED_ZERO_RECORDS",
    "PRESENT_PARSED_NO_WINDOW_RECORDS",
    "PRESENT_PARSED_WITH_RECORDS",
    "PRESENT_ONLY_WAL_SHM",
    "PRESENT_ENCRYPTED_OR_INACCESSIBLE",
    "PRESENT_UNKNOWN_SCHEMA",
    "OUTSIDE_ACQUISITION_SCOPE",
    "OUTSIDE_STANDARD_BACKUP",
    "NOT_COLLECTED",
    "UNKNOWN",
}

SUPPORTED_EXAMINATION_STATUSES = {
    "COMPLETE_FOR_SUPPORTED_ARTIFACTS",
    "PARTIAL_SUPPORTED_COVERAGE",
    "EXAMINATION_GAPS_PRESENT",
    "INSUFFICIENT_EXAMINATION",
    "UNKNOWN",
}

ACQUISITION_SUFFICIENCY_STATUSES = {
    "SUFFICIENT_FOR_QUESTION",
    "PARTIALLY_SUFFICIENT",
    "LIMITED_BY_ACQUISITION_TYPE",
    "REQUIRED_SOURCE_NOT_COLLECTED",
    "INSUFFICIENT_FOR_QUESTION",
    "UNKNOWN",
}

COVERAGE_DISPOSITIONS = {
    "SUCCESSFULLY_EXAMINED",
    "PARTIALLY_EXAMINED",
    "EXAMINATION_FAILURE",
    "PRESENT_UNSUPPORTED",
    "EXPECTED_BUT_NOT_PRESENT",
    "OPTIONAL_NOT_PRESENT",
    "OUTSIDE_STANDARD_ACQUISITION",
    "NOT_SEPARATELY_COLLECTED",
    "SUPPLEMENTAL_EVIDENCE",
    "IRRELEVANT_TO_FINDING",
    "UNKNOWN",
}

COMPLETENESS_LEVELS = {
    "COMPLETE_FOR_SUPPORTED_ARTIFACTS",
    "PARTIAL_SUPPORTED_COVERAGE",
    "EXAMINATION_GAPS_PRESENT",
    "INSUFFICIENT_EXAMINATION",
    "MATERIAL_GAPS",
    "INSUFFICIENT_COVERAGE",
    "UNKNOWN",
}

KEYWORDS = [
    "commcenter",
    "coretelephony",
    "wirelessdiagnostics",
    "baseband",
    "cellular",
    "carrier",
    "bluetooth",
    "airdrop",
    "nearby",
    "facetime",
    "location",
    "analytics",
    "sms",
    "mms",
    "rcs",
    "imessage",
    "notification",
    "springboard",
    "knowledge",
    "duet",
    "maps",
    "mail",
    "notes",
    "calendar",
    "reminders",
]


def parse_dt(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=None)
        except ValueError:
            pass
    raise ValueError(f"Unsupported datetime format: {value!r}")


def format_dt(value: Optional[datetime]) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def safe_fromtimestamp(seconds: Any) -> Optional[datetime]:
    try:
        num = float(seconds)
        if num <= 0 or num > 4102444800:  # 2100-01-01 UTC
            return None
        return datetime.fromtimestamp(num)
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def apple_datetime(value: Any) -> Optional[datetime]:
    try:
        num = safe_int(value)
        if num is None or num <= 0:
            return None
        if num > 100000000000000000:
            num = num // 1000000000
        return safe_fromtimestamp(num + APPLE_EPOCH)
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def unix_datetime(value: Any) -> Optional[datetime]:
    try:
        num = safe_int(value)
        if num is None or num <= 0:
            return None
        if num > 1000000000000:
            num = num // 1000
        return safe_fromtimestamp(num)
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def webkit_datetime(value: Any) -> Optional[datetime]:
    try:
        num = safe_int(value)
        if num is None or num <= 0:
            return None
        if num > 100000000000000:
            seconds = num // 1000000
        else:
            seconds = num
        return safe_fromtimestamp(seconds + WEBKIT_EPOCH)
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def iso_or_common_datetime(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        if value > 1000000000:
            return unix_datetime(value)
        return apple_datetime(value)
    text = str(value).strip()
    if not text:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
    ):
        try:
            return datetime.strptime(text[:26], fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def timestamp_from_any(value: Any, hint: str = "") -> Optional[datetime]:
    try:
        if value in (None, ""):
            return None
        hint_lower = hint.lower()
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, str) and any(ch in value for ch in ("-", "T", ":")):
            parsed = iso_or_common_datetime(value)
            if parsed:
                return parsed
        num = safe_int(value)
        if num is None or num <= 0:
            return iso_or_common_datetime(value)
        if "webkit" in hint_lower:
            return webkit_datetime(num)
        if "unix" in hint_lower or 1000000000 < num < 2000000000:
            return unix_datetime(num)
        if num > 100000000000000000 or "apple" in hint_lower or num < 1000000000:
            return apple_datetime(num)
        return unix_datetime(num)
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def in_range(ts: Optional[datetime], start: datetime, end: datetime) -> bool:
    return bool(ts and start <= ts <= end)


def section_for(ts: Optional[datetime], start: datetime, end: datetime) -> str:
    if not ts:
        return "undated"
    if ts < start:
        return "before"
    if ts > end:
        return "after"
    return "during"


def normalize_phone(value: Any) -> str:
    text = str(value or "").strip()
    keep_plus = text.startswith("+")
    digits = "".join(ch for ch in text if ch.isdigit())
    if keep_plus and digits:
        return "+" + digits
    return digits or text.lower()


def duration_text(seconds: Any) -> str:
    total = safe_int(seconds) or 0
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def short_path(path: Path, case_dir: Path) -> str:
    try:
        return str(path.relative_to(case_dir))
    except ValueError:
        return str(path)


def load_optional_pillow():
    try:
        from PIL import Image  # type: ignore
        from PIL.ExifTags import TAGS  # type: ignore

        return Image, TAGS
    except Exception:
        return None, None


@dataclass
class Event:
    timestamp: Optional[datetime]
    source: str
    event_type: str
    significance: str
    details: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_score: int = 0
    confidence_basis: str = ""
    evidence_strength: str = "UNKNOWN"

    def apply_confidence(self) -> None:
        score, basis, strength = confidence_for_event(self)
        self.confidence_score = score
        self.confidence_basis = basis
        self.evidence_strength = strength
        self.metadata.setdefault("confidence_score", score)
        self.metadata.setdefault("confidence_basis", basis)
        self.metadata.setdefault("evidence_strength", strength)

    def as_row(self, start: datetime, end: datetime) -> Dict[str, str]:
        if not self.confidence_basis:
            self.apply_confidence()
        return {
            "timestamp": format_dt(self.timestamp),
            "section": section_for(self.timestamp, start, end),
            "source": self.source,
            "event_type": self.event_type,
            "significance": self.significance,
            "confidence_score": str(self.confidence_score),
            "confidence_basis": self.confidence_basis,
            "evidence_strength": self.evidence_strength,
            "details": self.details,
            "metadata": json_dumps(self.metadata),
        }


@dataclass
class CoverageRecord:
    artifact_id: str = ""
    artifact_name: str = ""
    category: str = ""
    app_bundle_id: str = ""
    domain: str = ""
    relative_path: str = ""
    absolute_path: str = ""
    file_type: str = ""
    size_bytes: int = 0
    sha256: str = ""
    parser_name: str = ""
    parser_enabled: bool = False
    parser_status: str = "UNKNOWN"
    coverage_status: str = "UNKNOWN"
    file_present: bool = False
    companion_wal_present: bool = False
    companion_shm_present: bool = False
    database_opened: bool = False
    schema_recognized: bool = False
    tables_found: List[str] = field(default_factory=list)
    tables_parsed: List[str] = field(default_factory=list)
    tables_unparsed: List[str] = field(default_factory=list)
    rows_total_estimated: int = 0
    rows_examined: int = 0
    records_normalized_total: int = 0
    records_normalized_in_window: int = 0
    earliest_timestamp: str = ""
    latest_timestamp: str = ""
    timestamp_fields_found: List[str] = field(default_factory=list)
    timestamp_fields_unparsed: List[str] = field(default_factory=list)
    unsupported_reason: str = ""
    failure_reason: str = ""
    error_count: int = 0
    acquisition_scope: str = "UNKNOWN"
    examiner_note: str = ""
    confidence_in_coverage: str = "UNKNOWN"
    coverage_basis: str = ""
    wal_present: bool = False
    shm_present: bool = False
    wal_applied_by_sqlite: bool = False
    deleted_record_carving_performed: bool = False
    deleted_record_recovery_supported: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_name": self.artifact_name,
            "category": self.category,
            "app_bundle_id": self.app_bundle_id,
            "domain": self.domain,
            "relative_path": self.relative_path,
            "absolute_path": self.absolute_path,
            "file_type": self.file_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "parser_name": self.parser_name,
            "parser_enabled": self.parser_enabled,
            "parser_status": self.parser_status,
            "coverage_status": self.coverage_status,
            "file_present": self.file_present,
            "companion_wal_present": self.companion_wal_present,
            "companion_shm_present": self.companion_shm_present,
            "database_opened": self.database_opened,
            "schema_recognized": self.schema_recognized,
            "tables_found": ";".join(self.tables_found),
            "tables_parsed": ";".join(self.tables_parsed),
            "tables_unparsed": ";".join(self.tables_unparsed),
            "rows_total_estimated": self.rows_total_estimated,
            "rows_examined": self.rows_examined,
            "records_normalized_total": self.records_normalized_total,
            "records_normalized_in_window": self.records_normalized_in_window,
            "earliest_timestamp": self.earliest_timestamp,
            "latest_timestamp": self.latest_timestamp,
            "timestamp_fields_found": ";".join(self.timestamp_fields_found),
            "timestamp_fields_unparsed": ";".join(self.timestamp_fields_unparsed),
            "unsupported_reason": self.unsupported_reason,
            "failure_reason": self.failure_reason,
            "error_count": self.error_count,
            "acquisition_scope": self.acquisition_scope,
            "examiner_note": self.examiner_note,
            "confidence_in_coverage": self.confidence_in_coverage,
            "coverage_basis": self.coverage_basis,
            "wal_present": self.wal_present,
            "shm_present": self.shm_present,
            "wal_applied_by_sqlite": self.wal_applied_by_sqlite,
            "deleted_record_carving_performed": self.deleted_record_carving_performed,
            "deleted_record_recovery_supported": self.deleted_record_recovery_supported,
        }


@dataclass
class AppCoverageRecord:
    bundle_id: str = ""
    app_group_id: str = ""
    app_name: str = ""
    files_found: int = 0
    databases_found: int = 0
    parser_available: bool = False
    parser_status: str = "PRESENT_UNSUPPORTED"
    normalized_records: int = 0
    unsupported_files: int = 0
    likely_high_value_artifacts: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "app_group_id": self.app_group_id,
            "app_name": self.app_name,
            "files_found": self.files_found,
            "databases_found": self.databases_found,
            "parser_available": self.parser_available,
            "parser_status": self.parser_status,
            "normalized_records": self.normalized_records,
            "unsupported_files": self.unsupported_files,
            "likely_high_value_artifacts": ";".join(self.likely_high_value_artifacts),
        }


@dataclass
class CoverageCategoryResult:
    category: str
    weight: int
    possible_weight: int
    covered_weight: int
    coverage_percent: float
    records_total: int
    records_covered: int
    material_gaps: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "weight": self.weight,
            "possible_weight": self.possible_weight,
            "covered_weight": self.covered_weight,
            "coverage_percent": round(self.coverage_percent, 2),
            "records_total": self.records_total,
            "records_covered": self.records_covered,
            "material_gaps": self.material_gaps,
        }


@dataclass
class FindingConfidenceResult:
    finding_id: str
    finding_name: str
    confidence_level: str
    coverage_level: str
    deterministic_basis: str
    supporting_evidence_count: int
    material_gap_count: int
    confidence_ceiling: str
    cannot_exceed_reason: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_name": self.finding_name,
            "confidence_level": self.confidence_level,
            "coverage_level": self.coverage_level,
            "deterministic_basis": self.deterministic_basis,
            "supporting_evidence_count": self.supporting_evidence_count,
            "material_gap_count": self.material_gap_count,
            "confidence_ceiling": self.confidence_ceiling,
            "cannot_exceed_reason": self.cannot_exceed_reason,
        }


@dataclass
class FindingCompletenessResult:
    finding_id: str
    supported_examination_status: str
    acquisition_sufficiency_status: str
    relevant_artifacts_examined: List[str] = field(default_factory=list)
    relevant_artifacts_partially_examined: List[str] = field(default_factory=list)
    examination_gaps: List[str] = field(default_factory=list)
    acquisition_limitations: List[str] = field(default_factory=list)
    evidence_not_collected: List[str] = field(default_factory=list)
    supplemental_evidence_recommended: List[str] = field(default_factory=list)
    completeness_basis: str = ""
    examiner_confidence_in_examination: str = "UNKNOWN"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "supported_examination_status": self.supported_examination_status,
            "acquisition_sufficiency_status": self.acquisition_sufficiency_status,
            "relevant_artifacts_examined": self.relevant_artifacts_examined,
            "relevant_artifacts_partially_examined": self.relevant_artifacts_partially_examined,
            "examination_gaps": self.examination_gaps,
            "acquisition_limitations": self.acquisition_limitations,
            "evidence_not_collected": self.evidence_not_collected,
            "supplemental_evidence_recommended": self.supplemental_evidence_recommended,
            "completeness_basis": self.completeness_basis,
            "examiner_confidence_in_examination": self.examiner_confidence_in_examination,
        }


@dataclass
class ReportConfig:
    audience: str = "attorney"
    include_technical_appendix: bool = True
    include_full_unsupported_inventory: bool = False
    include_relationship_ids: bool = False
    include_normalized_event_ids: bool = False
    include_hashes_in_main_report: bool = False
    max_context_messages: int = 5
    max_correlated_events: int = 5
    redact_personal_data: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "audience": self.audience,
            "include_technical_appendix": self.include_technical_appendix,
            "include_full_unsupported_inventory": self.include_full_unsupported_inventory,
            "include_relationship_ids": self.include_relationship_ids,
            "include_normalized_event_ids": self.include_normalized_event_ids,
            "include_hashes_in_main_report": self.include_hashes_in_main_report,
            "max_context_messages": self.max_context_messages,
            "max_correlated_events": self.max_correlated_events,
            "redact_personal_data": self.redact_personal_data,
        }


@dataclass
class NormalizedEvent:
    event_id: str
    timestamp: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None
    event_category: str = "system"
    event_type: str = ""
    event_subtype: str = ""
    source: str = ""
    source_artifact: str = ""
    source_database: str = ""
    source_table: str = ""
    source_rowid: str = ""
    source_guid: str = ""
    parser_name: str = ""
    parser_version: str = "1"
    direction: str = ""
    service: str = ""
    description: str = ""
    text: str = ""
    filename: str = ""
    mime_type: str = ""
    sha256: str = ""
    url: str = ""
    domain: str = ""
    application: str = ""
    bundle_id: str = ""
    location: str = ""
    latitude: str = ""
    longitude: str = ""
    local_ip: str = ""
    remote_ip: str = ""
    local_port: str = ""
    remote_port: str = ""
    ssid: str = ""
    bssid: str = ""
    bluetooth_name: str = ""
    bluetooth_address: str = ""
    bytes_sent: str = ""
    bytes_received: str = ""
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    attachment_count: int = 0
    parent_message_event_id: str = ""
    parent_message_rowid: str = ""
    entity_links: List[Dict[str, Any]] = field(default_factory=list)
    correlation_cluster_ids: List[str] = field(default_factory=list)
    allegation_time_proximity_seconds: Optional[int] = None
    confidence_score: int = 0
    confidence_basis: str = ""
    evidence_strength: str = "UNKNOWN"
    coverage_status: str = "UNKNOWN"
    limitations: List[str] = field(default_factory=list)
    raw_event_reference: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": format_dt(self.timestamp),
            "timestamp_end": format_dt(self.timestamp_end),
            "event_category": self.event_category,
            "event_type": self.event_type,
            "event_subtype": self.event_subtype,
            "source": self.source,
            "source_artifact": self.source_artifact,
            "source_database": self.source_database,
            "source_table": self.source_table,
            "source_rowid": self.source_rowid,
            "source_guid": self.source_guid,
            "parser_name": self.parser_name,
            "parser_version": self.parser_version,
            "direction": self.direction,
            "service": self.service,
            "description": self.description,
            "text": self.text,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "sha256": self.sha256,
            "url": self.url,
            "domain": self.domain,
            "application": self.application,
            "bundle_id": self.bundle_id,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "local_ip": self.local_ip,
            "remote_ip": self.remote_ip,
            "local_port": self.local_port,
            "remote_port": self.remote_port,
            "ssid": self.ssid,
            "bssid": self.bssid,
            "bluetooth_name": self.bluetooth_name,
            "bluetooth_address": self.bluetooth_address,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "attachments": self.attachments,
            "attachment_count": self.attachment_count,
            "parent_message_event_id": self.parent_message_event_id,
            "parent_message_rowid": self.parent_message_rowid,
            "entity_links": self.entity_links,
            "correlation_cluster_ids": self.correlation_cluster_ids,
            "allegation_time_proximity_seconds": self.allegation_time_proximity_seconds,
            "confidence_score": self.confidence_score,
            "confidence_basis": self.confidence_basis,
            "evidence_strength": self.evidence_strength,
            "coverage_status": self.coverage_status,
            "limitations": self.limitations,
            "raw_event_reference": self.raw_event_reference,
        }


@dataclass
class Entity:
    entity_id: str
    entity_type: str
    canonical_value: str
    display_name: str = ""
    aliases: List[str] = field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    source_count: int = 0
    event_count: int = 0
    confidence_score: int = 0
    confidence_basis: str = ""
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "canonical_value": self.canonical_value,
            "display_name": self.display_name,
            "aliases": sorted(set(self.aliases)),
            "first_seen": format_dt(self.first_seen),
            "last_seen": format_dt(self.last_seen),
            "source_count": self.source_count,
            "event_count": self.event_count,
            "confidence_score": self.confidence_score,
            "confidence_basis": self.confidence_basis,
            "provenance": self.provenance,
            "attributes": self.attributes,
        }


@dataclass
class Relationship:
    relationship_id: str
    source_entity_id: str
    relationship_type: str
    target_entity_id: str
    timestamp: Optional[datetime] = None
    normalized_event_id: str = ""
    source_artifact: str = ""
    confidence_score: int = 0
    confidence_basis: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_entity_id": self.source_entity_id,
            "relationship_type": self.relationship_type,
            "target_entity_id": self.target_entity_id,
            "timestamp": format_dt(self.timestamp),
            "normalized_event_id": self.normalized_event_id,
            "source_artifact": self.source_artifact,
            "confidence_score": self.confidence_score,
            "confidence_basis": self.confidence_basis,
            "provenance": self.provenance,
        }


CRITICAL_ARTIFACT_WEIGHTS = {
    "sms.db": 10,
    "CallHistory.storedata": 9,
    "AddressBook": 8,
    "Safari History": 7,
    "KnowledgeC": 8,
    "notifications": 7,
    "Wi-Fi known networks": 6,
    "Bluetooth paired devices": 6,
    "Cellular/telephony artifacts": 10,
    "CommCenter": 10,
    "CoreTelephony": 10,
    "sysdiagnose": 10,
    "Packet capture files": 10,
    "Data usage databases": 8,
}

HIGH_ARTIFACT_WEIGHTS = {
    "Photos.sqlite": 6,
    "NoteStore.sqlite": 5,
    "Mail / Envelope Index": 6,
    "Calendar.sqlitedb": 5,
    "Reminders / CloudKitReminders.sqlite": 5,
    "Network configuration": 5,
    "VPN": 6,
    "AirDrop artifacts": 7,
    "Nearby/Continuity artifacts": 6,
}

MEDIUM_ARTIFACT_WEIGHTS = {
    "analytics": 4,
    "crash logs": 4,
    "unified logs": 4,
    "Maps history": 4,
    "Files app": 4,
    "iCloud Drive metadata": 4,
}

LOW_ARTIFACT_WEIGHTS = {
    "QuickLook previews": 2,
    "downloads": 3,
    "Focus mode": 2,
    "Screen Time": 3,
}


def artifact_weight(record: CoverageRecord) -> int:
    text = (record.artifact_name + " " + record.category + " " + record.parser_name).lower()
    for mapping in (CRITICAL_ARTIFACT_WEIGHTS, HIGH_ARTIFACT_WEIGHTS, MEDIUM_ARTIFACT_WEIGHTS, LOW_ARTIFACT_WEIGHTS):
        for key, weight in mapping.items():
            if key.lower() in text:
                return weight
    if record.category == "Third-party app":
        return 6
    if record.file_type == "sqlite":
        return 5
    return 2


class ErrorLog:
    def __init__(self) -> None:
        self.records: List[str] = []

    def log(self, plugin: str, artifact: Any, error: BaseException, context: str = "") -> None:
        message = [
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {plugin}",
            f"artifact={artifact}",
            f"context={context}",
            f"error={type(error).__name__}: {error}",
            traceback.format_exc(),
        ]
        self.records.append("\n".join(message))

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            if not self.records:
                f.write("No errors recorded.\n")
                return
            f.write("\n\n".join(self.records))
            f.write("\n")


class CaseContext:
    def __init__(
        self,
        case_dir: Path,
        start: datetime,
        end: datetime,
        context_minutes: int,
        conversation_context_count: int = 10,
        correlation_window_minutes: int = 3,
        min_correlation_score: int = 6,
    ) -> None:
        self.case_dir = case_dir
        self.root = case_dir / "decrypted"
        self.start = start
        self.end = end
        self.context_start = start - timedelta(minutes=context_minutes)
        self.context_end = end + timedelta(minutes=context_minutes)
        self.context_minutes = context_minutes
        self.conversation_context_count = conversation_context_count
        self.correlation_window_minutes = correlation_window_minutes
        self.min_correlation_score = min_correlation_score
        self.errors = ErrorLog()
        self.contacts = ContactResolver(self)
        self.plugin_stats: Dict[str, Dict[str, Any]] = {}
        self.hypotheses: List[str] = []
        self.allegation_times: List[datetime] = []
        self.question: Optional[str] = None
        self.question_output: Optional[Path] = None
        self.score_bucket_minutes = 5
        self.min_bucket_score = 5
        self.ai_summary = False
        self.ollama_url = "http://172.29.128.1:11434/api/generate"
        self.ollama_model = "qwen3:14b"
        self.ai_top_events = 50
        self.ollama_timeout = 600
        self.ai_summary_path: Optional[Path] = None
        self.case_name = ""
        self.single_report = False
        self.window_only = False
        self.coverage_hash_all = False
        self.coverage_hash_max_size_mb = 100
        self.coverage_inventory_only = False
        self.export_coverage_files = False
        self.export_case_knowledge = False
        self.case_knowledge: Optional[Dict[str, Any]] = None
        self.report_config = ReportConfig()
        self.manifest_records: Dict[str, Dict[str, Any]] = {}
        self.coverage_records: List[CoverageRecord] = []
        self.app_coverage_records: List[AppCoverageRecord] = []
        self._all_files: Optional[List[Path]] = None
        self._files_by_name: Dict[str, List[Path]] = {}
        self._files_by_extension: Dict[str, List[Path]] = {}

    @property
    def all_files(self) -> List[Path]:
        if self._all_files is None:
            self._build_file_index()
        return self._all_files or []

    def _build_file_index(self) -> None:
        self._all_files = []
        if not self.root.exists():
            return
        try:
            for path in self.root.rglob("*"):
                if not path.is_file():
                    continue
                self._all_files.append(path)
                self._files_by_name.setdefault(path.name.lower(), []).append(path)
                self._files_by_extension.setdefault(path.suffix.lower(), []).append(path)
        except Exception as exc:
            self.errors.log("finder", self.root, exc, "build filesystem index")

    def find(self, pattern: str) -> List[Path]:
        try:
            if pattern.startswith("*."):
                return list(self._files_by_extension.get(pattern[1:].lower(), [])) if self._all_files is not None else [
                    p for p in self.all_files if p.match(pattern)
                ]
            if "*" not in pattern and "?" not in pattern:
                return list(self._files_by_name.get(pattern.lower(), [])) if self._all_files is not None else [
                    p for p in self.all_files if p.name.lower() == pattern.lower()
                ]
            return [p for p in self.all_files if p.match(pattern)]
        except Exception as exc:
            self.errors.log("finder", self.root, exc, pattern)
            return []

    def find_named(self, names: Sequence[str]) -> List[Path]:
        lowered = {name.lower() for name in names}
        found: List[Path] = []
        try:
            for name in lowered:
                found.extend(self._files_by_name.get(name, []) if self._all_files is not None else [p for p in self.all_files if p.name.lower() == name])
        except Exception as exc:
            self.errors.log("finder", self.root, exc, ",".join(names))
        return found

    def find_path_tokens(self, tokens: Sequence[str], suffixes: Optional[Sequence[str]] = None) -> List[Path]:
        lowered = [token.lower() for token in tokens]
        suffix_set = {suffix.lower() for suffix in suffixes} if suffixes else None
        found = []
        for path in self.all_files:
            try:
                if suffix_set and path.suffix.lower() not in suffix_set:
                    continue
                text = str(path).replace("\\", "/").lower()
                if any(token in text for token in lowered):
                    found.append(path)
            except Exception as exc:
                self.errors.log("finder", path, exc, "path token match")
        return found


class SQLiteArtifact:
    def __init__(self, ctx: CaseContext, db_path: Path, plugin_name: str) -> None:
        self.ctx = ctx
        self.db_path = db_path
        self.plugin_name = plugin_name

    def connect(self) -> Optional[sqlite3.Connection]:
        if not self.db_path.exists():
            return None
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as exc:
            self.ctx.errors.log(self.plugin_name, self.db_path, exc, "connect")
            return None

    def query(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        conn = self.connect()
        if conn is None:
            return []
        try:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
        except Exception as exc:
            self.ctx.errors.log(self.plugin_name, self.db_path, exc, sql[:200])
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def tables(self) -> List[str]:
        rows = self.query("SELECT name FROM sqlite_master WHERE type='table'")
        return [str(row["name"]) for row in rows if row.get("name")]

    def columns(self, table: str) -> List[str]:
        rows = self.query(f"PRAGMA table_info({quote_ident(table)})")
        return [str(row["name"]) for row in rows if row.get("name")]


def quote_ident(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


class ContactResolver:
    def __init__(self, ctx: CaseContext) -> None:
        self.ctx = ctx
        self.lookup: Dict[str, str] = {}
        self.loaded = False

    def load(self) -> None:
        if self.loaded:
            return
        self.loaded = True
        for db in self.ctx.find_named(["AddressBook.sqlitedb"]):
            artifact = SQLiteArtifact(self.ctx, db, "contacts")
            rows = artifact.query(
                """
                SELECT
                    ABPerson.ROWID AS person_id,
                    ABPerson.First,
                    ABPerson.Middle,
                    ABPerson.Last,
                    ABPerson.Organization,
                    ABMultiValue.value AS value,
                    ABMultiValueLabel.value AS label
                FROM ABPerson
                JOIN ABMultiValue ON ABPerson.ROWID = ABMultiValue.record_id
                LEFT JOIN ABMultiValueLabel
                  ON ABMultiValue.label = ABMultiValueLabel.ROWID
                """
            )
            if not rows:
                rows = artifact.query(
                    """
                    SELECT
                        ABPerson.ROWID AS person_id,
                        ABPerson.First,
                        ABPerson.Last,
                        ABPerson.Organization,
                        ABMultiValue.value AS value
                    FROM ABPerson
                    JOIN ABMultiValue ON ABPerson.ROWID = ABMultiValue.record_id
                    """
                )
            for row in rows:
                name = self._name(row)
                value = str(row.get("value") or "").strip()
                if not name or not value:
                    continue
                keys = {value.lower(), normalize_phone(value)}
                normalized = normalize_phone(value)
                if normalized.startswith("+1") and len(normalized) == 12:
                    keys.add(normalized[-10:])
                if normalized and len(normalized) >= 10:
                    keys.add(normalized[-10:])
                for key in keys:
                    if key:
                        self.lookup[key] = name

    def _name(self, row: Dict[str, Any]) -> str:
        parts = [
            str(row.get("First") or "").strip(),
            str(row.get("Middle") or "").strip(),
            str(row.get("Last") or "").strip(),
        ]
        full = " ".join(part for part in parts if part)
        return full or str(row.get("Organization") or "").strip()

    def resolve(self, value: Any) -> str:
        self.load()
        if not value:
            return "UNKNOWN"
        raw = str(value)
        keys = [raw.lower(), normalize_phone(raw)]
        norm = normalize_phone(raw)
        if norm and len(norm) >= 10:
            keys.append(norm[-10:])
        for key in keys:
            if key in self.lookup:
                return self.lookup[key]
        return raw


class ArtifactPlugin:
    name = "base"

    def collect(self, ctx: CaseContext) -> List[Event]:
        raise NotImplementedError

    def safe_collect(self, ctx: CaseContext) -> List[Event]:
        try:
            return self.collect(ctx)
        except Exception as exc:
            ctx.errors.log(self.name, ctx.case_dir, exc, "plugin failed")
            return []


class SmsPlugin(ArtifactPlugin):
    name = "sms"

    def collect(self, ctx: CaseContext) -> List[Event]:
        db = ctx.case_dir / "decrypted/HomeDomain/Library/SMS/sms.db"
        if not db.exists():
            alternatives = ctx.find_named(["sms.db"])
            if alternatives:
                db = alternatives[0]
        if not db.exists():
            return []

        artifact = SQLiteArtifact(ctx, db, self.name)
        start = format_dt(ctx.context_start)
        end = format_dt(ctx.context_end)
        sql = """
        SELECT
            message.ROWID AS rowid,
            CASE
              WHEN message.date > 100000000000000000
              THEN datetime((message.date / 1000000000) + 978307200, 'unixepoch')
              ELSE datetime(message.date + 978307200, 'unixepoch')
            END AS ts,
            handle.id AS contact,
            message.service,
            message.is_from_me,
            message.cache_has_attachments,
            message.associated_message_type,
            message.associated_message_guid,
            message.text,
            message.guid,
            chat.ROWID AS chat_rowid,
            chat.chat_identifier AS chat_identifier,
            chat.display_name AS chat_display_name
        FROM message
        LEFT JOIN handle ON message.handle_id = handle.ROWID
        LEFT JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
        LEFT JOIN chat ON chat.ROWID = chat_message_join.chat_id
        WHERE ts BETWEEN ? AND ?
        ORDER BY message.date;
        """

        events: List[Event] = []
        for row in artifact.query(sql, (start, end)):
            ts = iso_or_common_datetime(row.get("ts"))
            direction = "FROM_DEVICE" if row.get("is_from_me") == 1 else "TO_DEVICE"
            raw_contact = row.get("contact")
            contact = ctx.contacts.resolve(raw_contact)
            in_primary = in_range(ts, ctx.start, ctx.end)
            significance = "REVIEW" if in_primary else "CONTEXT"
            if in_primary and (not row.get("text") or row.get("cache_has_attachments")):
                significance = "REVIEW"
            text = row.get("text") or "<NO TEXT CONTENT>"
            chat_bits = [
                f"chat={row.get('chat_display_name') or row.get('chat_identifier') or 'UNKNOWN'}"
            ]
            details = (
                f"{direction} | contact={contact} | raw_contact={raw_contact} | "
                f"service={row.get('service')} | attachment={row.get('cache_has_attachments')} | "
                f"associated_type={row.get('associated_message_type')} | "
                f"associated_guid={row.get('associated_message_guid')} | "
                f"{' | '.join(chat_bits)} | rowid={row.get('rowid')} | "
                f"guid={row.get('guid')} | text={text}"
            )
            events.append(
                Event(
                    ts,
                    "sms.db",
                    "SMS/iMessage/RCS record",
                    significance,
                    details,
                    {
                        "db": short_path(db, ctx.case_dir),
                        "rowid": row.get("rowid"),
                        "guid": row.get("guid"),
                        "raw_contact": raw_contact,
                        "resolved_contact": contact,
                        "direction": direction,
                        "service": row.get("service"),
                        "chat_rowid": row.get("chat_rowid"),
                        "chat_identifier": row.get("chat_identifier"),
                        "chat_display_name": row.get("chat_display_name"),
                        "in_requested_window": in_primary,
                    },
                )
            )
            if row.get("cache_has_attachments"):
                events.extend(self.attachments_for_message(ctx, artifact, db, row, ts))
        return events

    def attachments_for_message(
        self,
        ctx: CaseContext,
        artifact: SQLiteArtifact,
        db: Path,
        message_row: Dict[str, Any],
        message_ts: Optional[datetime],
    ) -> List[Event]:
        sql = """
        SELECT
            attachment.ROWID AS rowid,
            attachment.filename,
            attachment.mime_type,
            attachment.total_bytes,
            attachment.transfer_name,
            attachment.guid,
            attachment.created_date,
            attachment.start_date,
            attachment.user_info
        FROM attachment
        JOIN message_attachment_join
          ON attachment.ROWID = message_attachment_join.attachment_id
        WHERE message_attachment_join.message_id = ?
        """
        events: List[Event] = []
        for row in artifact.query(sql, (message_row.get("rowid"),)):
            filename = str(row.get("filename") or "")
            found_path = find_attachment_path(ctx, filename)
            digest = sha256(found_path) if found_path else ""
            attachment_created = apple_datetime(row.get("created_date")) or unix_datetime(row.get("created_date"))
            attachment_start = apple_datetime(row.get("start_date")) or unix_datetime(row.get("start_date"))
            attachment_specific_ts = attachment_created or attachment_start
            timestamp_basis = "parent message timestamp"
            if attachment_specific_ts:
                timestamp_basis = "attachment created_date" if attachment_created else "attachment start_date"
            stat_meta: Dict[str, Any] = {}
            exif_meta: Dict[str, Any] = {}
            if found_path:
                try:
                    stat = found_path.stat()
                    stat_meta = {
                        "path": short_path(found_path, ctx.case_dir),
                        "size": stat.st_size,
                        "mtime": format_dt(datetime.fromtimestamp(stat.st_mtime)),
                        "sha256": digest,
                    }
                except Exception as exc:
                    ctx.errors.log(self.name, found_path, exc, "attachment stat")
                exif_meta = extract_exif(found_path, ctx.errors, self.name)

            details = (
                f"message_rowid={message_row.get('rowid')} | filename={filename} | "
                f"mime={row.get('mime_type')} | bytes={row.get('total_bytes')} | "
                f"transfer_name={row.get('transfer_name')} | guid={row.get('guid')} | "
                f"path={str(found_path) if found_path else ''} | sha256={digest}"
            )
            if exif_meta:
                details += f" | exif_keys={sorted(exif_meta.keys())}"
            events.append(
                Event(
                    message_ts,
                    "sms.db attachment",
                    "Message attachment metadata",
                    "REVIEW" if in_range(message_ts, ctx.start, ctx.end) else "CONTEXT",
                    details,
                    {
                        "db": short_path(db, ctx.case_dir),
                        "message_rowid": message_row.get("rowid"),
                        "attachment_rowid": row.get("rowid"),
                        "filename": filename,
                        "mime_type": row.get("mime_type"),
                        "total_bytes": row.get("total_bytes"),
                        "transfer_name": row.get("transfer_name"),
                        "guid": row.get("guid"),
                        "created_date_raw": row.get("created_date"),
                        "start_date_raw": row.get("start_date"),
                        "attachment_created_timestamp": format_dt(attachment_created),
                        "attachment_start_timestamp": format_dt(attachment_start),
                        "attachment_event_timestamp_basis": timestamp_basis,
                        "parent_message_timestamp": format_dt(message_ts),
                        "recovered_path": short_path(found_path, ctx.case_dir) if found_path else "",
                        "filesystem_status": "FOUND" if found_path else "NOT_FOUND_IN_DECRYPTED_BACKUP_PATHS",
                        "sha256": digest,
                        "file": stat_meta,
                        "exif": exif_meta,
                    },
                )
            )
        return events


def find_attachment_path(ctx: CaseContext, filename: str) -> Optional[Path]:
    if not filename:
        return None
    direct = ctx.case_dir / "decrypted" / filename.lstrip("/~")
    if direct.exists():
        return direct
    basename = Path(filename).name
    if not basename:
        return None
    matches = ctx.find(basename)
    return matches[0] if matches else None


def extract_exif(path: Path, errors: ErrorLog, plugin_name: str) -> Dict[str, Any]:
    if path.suffix.lower() not in {".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".png"}:
        return {}
    Image, TAGS = load_optional_pillow()
    if Image is None or TAGS is None:
        return {}
    try:
        with Image.open(path) as img:
            raw = img.getexif()
            out: Dict[str, Any] = {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
            }
            for key, value in raw.items():
                tag = TAGS.get(key, str(key))
                if isinstance(value, bytes):
                    value = value[:64].hex()
                out[str(tag)] = value
            return out
    except Exception as exc:
        errors.log(plugin_name, path, exc, "exif")
        return {}


class CallHistoryPlugin(ArtifactPlugin):
    name = "call_history"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        for db in ctx.find_named(["CallHistory.storedata"]):
            artifact = SQLiteArtifact(ctx, db, self.name)
            sql = """
            SELECT
                ZDATE,
                datetime(ZDATE + 978307200, 'unixepoch') AS ts,
                ZADDRESS,
                ZORIGINATED,
                ZANSWERED,
                ZCALLTYPE,
                ZDURATION,
                ZSERVICE_PROVIDER,
                ZLOCATION,
                ZDISCONNECTED_CAUSE,
                ZUNIQUE_ID
            FROM ZCALLRECORD
            WHERE datetime(ZDATE + 978307200, 'unixepoch') BETWEEN ? AND ?
            ORDER BY ZDATE;
            """
            for row in artifact.query(sql, (format_dt(ctx.context_start), format_dt(ctx.context_end))):
                ts = iso_or_common_datetime(row.get("ts"))
                direction = "OUTGOING" if row.get("ZORIGINATED") == 1 else "INCOMING"
                answered = "ANSWERED" if row.get("ZANSWERED") == 1 else "NOT_ANSWERED"
                contact = ctx.contacts.resolve(row.get("ZADDRESS"))
                dur = duration_text(row.get("ZDURATION"))
                details = (
                    f"{direction} | {answered} | contact={contact} | raw_address={row.get('ZADDRESS')} | "
                    f"duration={dur} ({row.get('ZDURATION')} seconds) | provider={row.get('ZSERVICE_PROVIDER')} | "
                    f"location={row.get('ZLOCATION')} | disconnect_cause={row.get('ZDISCONNECTED_CAUSE')} | "
                    f"id={row.get('ZUNIQUE_ID')}"
                )
                events.append(
                    Event(
                        ts,
                        "CallHistory",
                        "Call record",
                        "REVIEW" if in_range(ts, ctx.start, ctx.end) else "CONTEXT",
                        details,
                        {
                            "db": short_path(db, ctx.case_dir),
                            "raw": row,
                            "direction": direction,
                            "raw_contact": row.get("ZADDRESS"),
                            "resolved_contact": contact,
                            "duration_formatted": dur,
                            "location_label": row.get("ZLOCATION"),
                            "location_label_type": "Call record location label",
                            "location_limitation": "This geographic label may be derived from telephone-number metadata and does not establish the physical location of the device or caller.",
                        },
                    )
                )
        return events


class SafariPlugin(ArtifactPlugin):
    name = "safari"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        for db in ctx.find_named(["History.db"]):
            if "safari" not in str(db).lower():
                continue
            artifact = SQLiteArtifact(ctx, db, self.name)
            history_item_cols = set(artifact.columns("history_items"))
            title_expr = "history_items.title" if "title" in history_item_cols else "''"
            sql = f"""
            SELECT
                history_visits.visit_time,
                datetime(history_visits.visit_time + 978307200, 'unixepoch') AS ts,
                history_items.url,
                {title_expr} AS title,
                history_visits.load_successful
            FROM history_visits
            JOIN history_items ON history_items.id = history_visits.history_item
            WHERE datetime(history_visits.visit_time + 978307200, 'unixepoch') BETWEEN ? AND ?
            ORDER BY history_visits.visit_time;
            """
            for row in artifact.query(sql, (format_dt(ctx.context_start), format_dt(ctx.context_end))):
                ts = iso_or_common_datetime(row.get("ts"))
                events.append(
                    Event(
                        ts,
                        "Safari",
                        "Browser visit",
                        "INFO" if in_range(ts, ctx.start, ctx.end) else "CONTEXT",
                        f"title={row.get('title')} | url={row.get('url')} | load_successful={row.get('load_successful')}",
                        {"db": short_path(db, ctx.case_dir), "raw": row},
                    )
                )
        return events


class PhotosPlugin(ArtifactPlugin):
    name = "photos"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        for db in ctx.find_named(["Photos.sqlite"]):
            artifact = SQLiteArtifact(ctx, db, self.name)
            tables = set(artifact.tables())
            if "ZASSET" not in tables:
                continue
            cols = set(artifact.columns("ZASSET"))
            select_cols = [
                "Z_PK",
                "ZDATECREATED",
                "ZADDEDDATE",
                "ZMODIFICATIONDATE",
                "ZFILENAME",
                "ZDIRECTORY",
                "ZLATITUDE",
                "ZLONGITUDE",
                "ZDURATION",
                "ZKIND",
                "ZMEDIATYPE",
                "ZUUID",
            ]
            existing = [c for c in select_cols if c in cols]
            if not existing:
                continue
            sql = f"SELECT {', '.join(existing)} FROM ZASSET"
            for row in artifact.query(sql):
                candidates = [
                    ("created", timestamp_from_any(row.get("ZDATECREATED"), "apple")),
                    ("added", timestamp_from_any(row.get("ZADDEDDATE"), "apple")),
                    ("modified", timestamp_from_any(row.get("ZMODIFICATIONDATE"), "apple")),
                ]
                for label, ts in candidates:
                    if not (ctx.context_start <= ts <= ctx.context_end if ts else False):
                        continue
                    filename = row.get("ZFILENAME")
                    details = (
                        f"{label} photo/library asset | filename={filename} | "
                        f"lat={row.get('ZLATITUDE')} | lon={row.get('ZLONGITUDE')} | "
                        f"duration={row.get('ZDURATION')} | kind={row.get('ZKIND') or row.get('ZMEDIATYPE')} | "
                        f"uuid={row.get('ZUUID')}"
                    )
                    events.append(
                        Event(
                            ts,
                            "Photos",
                            "Photos metadata",
                            "INFO" if in_range(ts, ctx.start, ctx.end) else "CONTEXT",
                            details,
                            {"db": short_path(db, ctx.case_dir), "timestamp_field": label, "raw": row},
                        )
                    )
        return events


class GenericSQLitePlugin(ArtifactPlugin):
    db_names: Sequence[str] = ()
    source = "Generic"
    event_type = "Artifact record"
    timestamp_columns: Sequence[Tuple[str, str]] = ()
    detail_columns: Sequence[str] = ()
    table_preferences: Sequence[str] = ()

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        for db in ctx.find_named(self.db_names):
            artifact = SQLiteArtifact(ctx, db, self.name)
            for table in self.choose_tables(artifact):
                cols = artifact.columns(table)
                ts_cols = [(c, hint) for c, hint in self.timestamp_columns if c in cols]
                if not ts_cols:
                    continue
                selected = sorted(set([c for c, _ in ts_cols] + [c for c in self.detail_columns if c in cols]))
                selected_sql = ", ".join(quote_ident(c) for c in selected)
                sql = f"SELECT rowid AS _rowid, {selected_sql} FROM {quote_ident(table)}"
                for row in artifact.query(sql):
                    for col, hint in ts_cols:
                        ts = timestamp_from_any(row.get(col), hint)
                        if not (ctx.context_start <= ts <= ctx.context_end if ts else False):
                            continue
                        details = self.build_details(table, row, col)
                        events.append(
                            Event(
                                ts,
                                self.source,
                                self.event_type,
                                "INFO" if in_range(ts, ctx.start, ctx.end) else "CONTEXT",
                                details,
                                {
                                    "db": short_path(db, ctx.case_dir),
                                    "table": table,
                                    "rowid": row.get("_rowid"),
                                    "timestamp_field": col,
                                    "raw": row,
                                },
                            )
                        )
        return events

    def choose_tables(self, artifact: SQLiteArtifact) -> List[str]:
        tables = artifact.tables()
        preferred = [t for t in self.table_preferences if t in tables]
        return preferred or tables[:8]

    def build_details(self, table: str, row: Dict[str, Any], timestamp_field: str) -> str:
        parts = [f"table={table}", f"timestamp_field={timestamp_field}"]
        for col in self.detail_columns:
            if col in row and row.get(col) not in (None, ""):
                parts.append(f"{col}={row.get(col)}")
        return " | ".join(parts)


class NotesPlugin(GenericSQLitePlugin):
    name = "notes"
    db_names = ("NoteStore.sqlite", "notes.sqlite", "NotesV7.storedata")
    source = "Notes"
    event_type = "Notes metadata"
    timestamp_columns = (
        ("ZCREATIONDATE", "apple"),
        ("ZMODIFICATIONDATE", "apple"),
        ("ZDATEFORLASTTITLEMODIFICATION", "apple"),
        ("creationDate", "apple"),
        ("modificationDate", "apple"),
    )
    detail_columns = ("ZTITLE", "ZSUMMARY", "ZSNIPPET", "ZIDENTIFIER", "ZFOLDER", "title", "summary")
    table_preferences = ("ZICCLOUDSYNCINGOBJECT", "ZNOTE", "ZNOTEBODY")


class MailPlugin(GenericSQLitePlugin):
    name = "mail"
    db_names = ("Envelope Index", "Mail.sqlite")
    source = "Mail"
    event_type = "Mail metadata"
    timestamp_columns = (
        ("date_received", "unix"),
        ("date_sent", "unix"),
        ("date_last_viewed", "unix"),
        ("ZDATE", "apple"),
        ("ZRECEIVEDDATE", "apple"),
    )
    detail_columns = (
        "subject",
        "sender",
        "to",
        "from",
        "snippet",
        "remote_id",
        "message_id",
        "ZSUBJECT",
        "ZSENDER",
    )
    table_preferences = ("messages", "mailboxes", "ZMESSAGE")


class CalendarPlugin(GenericSQLitePlugin):
    name = "calendar"
    db_names = ("Calendar.sqlitedb", "Calendar.sqlite")
    source = "Calendar"
    event_type = "Calendar metadata"
    timestamp_columns = (
        ("start_date", "apple"),
        ("end_date", "apple"),
        ("creation_date", "apple"),
        ("last_modified", "apple"),
        ("ZSTARTDATE", "apple"),
        ("ZENDDATE", "apple"),
        ("ZCREATIONDATE", "apple"),
        ("ZMODIFIEDDATE", "apple"),
    )
    detail_columns = ("summary", "title", "location", "description", "ZTITLE", "ZLOCATION", "ZNOTES")
    table_preferences = ("CalendarItem", "Event", "ZCALENDARITEM", "ZICSELEMENT")


class RemindersPlugin(GenericSQLitePlugin):
    name = "reminders"
    db_names = ("Calendar.sqlitedb", "CloudKitReminders.sqlite", "DataAccess.sqlite")
    source = "Reminders"
    event_type = "Reminders metadata"
    timestamp_columns = (
        ("due_date", "apple"),
        ("completion_date", "apple"),
        ("creation_date", "apple"),
        ("last_modified", "apple"),
        ("ZDUEDATE", "apple"),
        ("ZCOMPLETIONDATE", "apple"),
        ("ZCREATIONDATE", "apple"),
        ("ZLASTMODIFIEDDATE", "apple"),
    )
    detail_columns = ("title", "summary", "notes", "ZTITLE", "ZNOTES", "ZEXTERNALIDENTIFIER")
    table_preferences = ("Reminder", "CalendarItem", "ZREMCDREMINDER", "ZCALENDARITEM")

    def choose_tables(self, artifact: SQLiteArtifact) -> List[str]:
        tables = artifact.tables()
        reminder_like = [t for t in tables if "reminder" in t.lower() or "remcd" in t.lower()]
        return reminder_like or super().choose_tables(artifact)


class MapsLocationPlugin(GenericSQLitePlugin):
    name = "maps_location"
    db_names = (
        "MapsSync_0.0.1",
        "MapsSync.db",
        "History.mapsdata",
        "GeoHistory.mapsdata",
        "consolidated.db",
        "cache_encryptedB.db",
    )
    source = "Maps/Location"
    event_type = "Maps or location metadata"
    timestamp_columns = (
        ("ZDATE", "apple"),
        ("ZCREATIONDATE", "apple"),
        ("ZMODIFICATIONDATE", "apple"),
        ("timestamp", "unix"),
        ("time", "unix"),
        ("startTime", "unix"),
        ("endTime", "unix"),
    )
    detail_columns = (
        "ZLOCATION",
        "ZTITLE",
        "ZADDRESS",
        "latitude",
        "longitude",
        "Latitude",
        "Longitude",
        "ZLATITUDE",
        "ZLONGITUDE",
        "horizontalAccuracy",
    )

    def choose_tables(self, artifact: SQLiteArtifact) -> List[str]:
        tables = artifact.tables()
        interesting = [
            t
            for t in tables
            if any(token in t.lower() for token in ("history", "location", "map", "visit", "place"))
        ]
        return interesting or tables[:8]


class KnowledgeCPlugin(GenericSQLitePlugin):
    name = "knowledgec"
    db_names = ("knowledgeC.db", "knowledgeC.db-wal")
    source = "KnowledgeC"
    event_type = "App/activity context"
    timestamp_columns = (
        ("ZSTARTDATE", "apple"),
        ("ZENDDATE", "apple"),
        ("startDate", "apple"),
        ("endDate", "apple"),
        ("creationDate", "apple"),
    )
    detail_columns = (
        "ZSTREAMNAME",
        "ZVALUESTRING",
        "ZOBJECT",
        "ZSECONDSFROMGMT",
        "Z_DKINTENTMETADATAKEY__SERIALIZEDINTERACTION",
    )
    table_preferences = ("ZOBJECT", "ZSTRUCTUREDMETADATA", "ZSOURCE")


class NotificationsPlugin(GenericSQLitePlugin):
    name = "notifications"
    db_names = ("BulletinBoard.sqlite", "DeliveredNotifications.db", "NotificationUsage.sqlite")
    source = "Notifications"
    event_type = "Notification metadata"
    timestamp_columns = (
        ("date", "unix"),
        ("timestamp", "unix"),
        ("last_modified", "unix"),
        ("ZDATE", "apple"),
        ("ZTIMESTAMP", "apple"),
    )
    detail_columns = ("section_id", "publisher_bulletin_id", "title", "message", "subtitle", "bundle_id", "ZSECTIONID")

    def choose_tables(self, artifact: SQLiteArtifact) -> List[str]:
        tables = artifact.tables()
        interesting = [t for t in tables if any(x in t.lower() for x in ("bulletin", "notification", "record"))]
        return interesting or tables[:8]


class SystemFilePlugin(ArtifactPlugin):
    name = "system_files"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        if not ctx.root.exists():
            return events
        for path in ctx.root.rglob("*"):
            try:
                if not path.is_file():
                    continue
                lowered = str(path).lower()
                matched = [kw for kw in KEYWORDS if kw in lowered]
                if not matched:
                    continue
                stat = path.stat()
                ts = datetime.fromtimestamp(stat.st_mtime)
                if not (ctx.context_start <= ts <= ctx.context_end):
                    continue
                source = classify_system_source(path, matched)
                events.append(
                    Event(
                        ts,
                        source,
                        "Relevant file timestamp",
                        "LOW" if in_range(ts, ctx.start, ctx.end) else "CONTEXT",
                        f"keywords={matched} | path={path} | size={stat.st_size} | sha256={sha256(path)}",
                        {
                            "path": short_path(path, ctx.case_dir),
                            "keywords": matched,
                            "size": stat.st_size,
                            "mtime": format_dt(ts),
                            "sha256": sha256(path),
                        },
                    )
                )
            except Exception as exc:
                ctx.errors.log(self.name, path, exc, "filesystem scan")
        return events


def classify_system_source(path: Path, matched: Sequence[str]) -> str:
    text = str(path).lower()
    if "bluetooth" in text:
        return "Bluetooth"
    if "airdrop" in text or "sharing" in text:
        return "AirDrop"
    if "nearby" in text or "nearbyinteraction" in text:
        return "Nearby Interaction"
    if "analytics" in text or "diagnostic" in text:
        return "Analytics/Diagnostics"
    if "log" in text or "tracev3" in text:
        return "Unified/System Logs"
    if "knowledge" in text or "duet" in text:
        return "KnowledgeC"
    return "Filesystem"


class PlistSystemPlugin(ArtifactPlugin):
    name = "plist_system"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        if not ctx.root.exists():
            return events
        for path in ctx.root.rglob("*.plist"):
            lowered = str(path).lower()
            if not any(k in lowered for k in ("bluetooth", "airdrop", "nearby", "notification", "location")):
                continue
            try:
                stat = path.stat()
                ts = datetime.fromtimestamp(stat.st_mtime)
                if not (ctx.context_start <= ts <= ctx.context_end):
                    continue
                summary = summarize_plist(path)
                source = classify_system_source(path, [])
                events.append(
                    Event(
                        ts,
                        source,
                        "Property list context",
                        "LOW" if in_range(ts, ctx.start, ctx.end) else "CONTEXT",
                        f"path={path} | summary={summary}",
                        {
                            "path": short_path(path, ctx.case_dir),
                            "mtime": format_dt(ts),
                            "summary": summary,
                        },
                    )
                )
            except Exception as exc:
                ctx.errors.log(self.name, path, exc, "plist parse")
        return events


def summarize_plist(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        data = plistlib.load(f)
    if isinstance(data, dict):
        out: Dict[str, Any] = {"keys": sorted(str(k) for k in list(data.keys())[:30])}
        for key in ("LastSeen", "Name", "DeviceName", "Address", "Identifier", "BundleID"):
            if key in data:
                out[key] = str(data[key])[:200]
        return out
    if isinstance(data, list):
        return {"list_length": len(data), "sample_type": type(data[0]).__name__ if data else ""}
    return {"type": type(data).__name__}


NETWORK_METADATA_FIELDS = [
    "interface_type",
    "interface_name",
    "protocol",
    "local_ip",
    "remote_ip",
    "local_port",
    "remote_port",
    "hostname",
    "domain",
    "ssid",
    "bssid",
    "wifi_security",
    "bluetooth_name",
    "bluetooth_address",
    "bluetooth_identifier",
    "device_class",
    "connection_state",
    "first_seen",
    "last_seen",
    "bytes_sent",
    "bytes_received",
    "packet_count",
    "source_artifact",
    "raw_record_identifier",
    "timestamp_basis",
    "timestamp_reliability",
]


def normalize_ip(value: Any) -> str:
    try:
        text = str(value or "").strip().strip("[]")
        if not text:
            return ""
        return str(ipaddress.ip_address(text))
    except ValueError:
        return ""


def classify_ip(value: Any) -> str:
    ip_text = normalize_ip(value)
    if not ip_text:
        return ""
    ip = ipaddress.ip_address(ip_text)
    if ip.is_loopback:
        return "loopback"
    if ip.is_link_local:
        return "link-local"
    if ip.is_multicast:
        return "multicast"
    if ip.is_private:
        return "private"
    if ip.is_global:
        return "public"
    return "reserved"


def normalize_mac(value: Any) -> str:
    text = str(value or "").strip().lower()
    hexchars = re.sub(r"[^0-9a-f]", "", text)
    if len(hexchars) != 12:
        return ""
    return ":".join(hexchars[i : i + 2] for i in range(0, 12, 2))


def extract_valid_ips(value: Any) -> List[str]:
    text = json_dumps(value) if isinstance(value, (dict, list, tuple)) else str(value or "")
    candidates = set(re.findall(r"(?<![\w:])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])", text))
    candidates.update(re.findall(r"(?<![\w.])(?:[0-9a-fA-F]{1,4}:){2,}[0-9a-fA-F]{1,4}(?![\w.])", text))
    out = []
    for candidate in candidates:
        normalized = normalize_ip(candidate)
        if normalized:
            out.append(normalized)
    return sorted(set(out))


def extract_domains(value: Any) -> List[str]:
    text = json_dumps(value) if isinstance(value, (dict, list, tuple)) else str(value or "")
    out = set()
    for match in re.findall(r"\b(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,63}\b", text):
        if normalize_ip(match):
            continue
        out.add(match.lower().strip("."))
    return sorted(out)


def extract_ports(value: Any) -> List[int]:
    text = json_dumps(value) if isinstance(value, (dict, list, tuple)) else str(value or "")
    ports = set()
    for match in re.findall(r"\b(?:port|local_port|remote_port|dport|sport)[^\d]{0,8}(\d{1,5})\b", text, re.I):
        num = safe_int(match)
        if num and 0 < num <= 65535:
            ports.add(num)
    return sorted(ports)


def plist_load(path: Path) -> Optional[Any]:
    try:
        with path.open("rb") as f:
            return plistlib.load(f)
    except Exception:
        return None


def walk_structured_records(obj: Any, max_depth: int = 8, max_records: int = 250) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    def walk(node: Any, path: str, depth: int) -> None:
        if len(records) >= max_records or depth > max_depth:
            return
        if isinstance(node, dict):
            if any(is_networkish_key(str(k)) for k in node.keys()) or any(isinstance(v, (str, int, float, datetime)) for v in node.values()):
                item = dict(node)
                item["_record_path"] = path
                records.append(item)
            for key, value in node.items():
                if isinstance(value, (dict, list, tuple)):
                    walk(value, f"{path}/{key}", depth + 1)
        elif isinstance(node, (list, tuple)):
            for index, value in enumerate(node[:max_records]):
                if isinstance(value, (dict, list, tuple)):
                    walk(value, f"{path}[{index}]", depth + 1)

    walk(obj, "$", 0)
    return records[:max_records]


def is_networkish_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        token in lowered
        for token in (
            "ssid",
            "bssid",
            "wifi",
            "wi-fi",
            "bluetooth",
            "bt",
            "airdrop",
            "nearby",
            "handoff",
            "continuity",
            "ip",
            "ipv4",
            "ipv6",
            "dns",
            "dhcp",
            "router",
            "gateway",
            "proxy",
            "vpn",
            "carrier",
            "cellular",
            "mcc",
            "mnc",
            "ims",
            "bytes",
            "packets",
        )
    )


def record_value(record: Dict[str, Any], keys: Sequence[str]) -> Any:
    lowered = {str(k).lower(): v for k, v in record.items()}
    for key in keys:
        if key.lower() in lowered:
            return lowered[key.lower()]
    for wanted in keys:
        wanted_lower = wanted.lower()
        for key, value in lowered.items():
            if wanted_lower in key:
                return value
    return None


def record_timestamp(record: Dict[str, Any]) -> Tuple[Optional[datetime], str]:
    timestamp_keys = (
        "lastjoined",
        "lastconnected",
        "lastseen",
        "last_seen",
        "last connection",
        "lastconnection",
        "firstjoined",
        "firstpaired",
        "timestamp",
        "date",
        "time",
        "starttime",
        "endtime",
        "connectedtime",
        "disconnectedtime",
    )
    for key in timestamp_keys:
        value = record_value(record, (key,))
        ts = timestamp_from_any(value)
        if ts:
            return ts, key
    return None, ""


def network_event(
    ts: Optional[datetime],
    source: str,
    event_type: str,
    significance: str,
    details: str,
    metadata: Dict[str, Any],
    score: int,
    basis: str,
    strength: str,
) -> Event:
    metadata.setdefault("network_event", True)
    for field_name in NETWORK_METADATA_FIELDS:
        metadata.setdefault(field_name, "")
    event = Event(ts, source, event_type, significance, details, metadata, score, basis, strength)
    event.metadata["confidence_score"] = score
    event.metadata["confidence_basis"] = basis
    event.metadata["evidence_strength"] = strength
    return event


def plist_files_for_tokens(ctx: CaseContext, tokens: Sequence[str]) -> List[Path]:
    return ctx.find_path_tokens(tokens, suffixes=(".plist", ".backup"))


SUPPORTED_SQLITE_SCHEMAS = {
    "sms": {"message", "handle", "chat"},
    "call_history": {"ZCALLRECORD"},
    "safari": {"history_items", "history_visits"},
    "photos": {"ZASSET"},
    "notes": {"ZICCLOUDSYNCINGOBJECT", "ZNOTE"},
    "mail": {"messages", "ZMESSAGE"},
    "calendar": {"CalendarItem", "Event", "ZCALENDARITEM"},
    "reminders": {"Reminder", "ZREMCDREMINDER"},
    "knowledgec": {"ZOBJECT", "ZSTRUCTUREDMETADATA"},
    "notifications": {"bulletin", "notification"},
    "data_usage": {"usage", "data", "network"},
}

NATIVE_COVERAGE_TARGETS = [
    ("sms.db", "Communications", ("sms.db",), ("sms",), "Messages database"),
    ("message attachments", "Communications", (), ("sms/attachments", "library/sms/attachments"), "Message attachment directory"),
    ("CallHistory.storedata", "Communications", ("CallHistory.storedata",), ("call_history",), "Call history database"),
    ("FaceTime call records", "Communications", (), ("facetime",), "May not be present in this backup"),
    ("voicemail", "Communications", (), ("voicemail",), "Voicemail artifacts vary by carrier/acquisition"),
    ("blocked contacts", "Communications", (), ("blocked", "callblocking"), "Blocked contact artifacts"),
    ("AddressBook", "Communications", ("AddressBook.sqlitedb",), ("contacts",), "Contacts database"),
    ("recent contacts", "Communications", (), ("recent", "recents"), "Recent contacts artifacts"),
    ("message edits/unsent indicators", "Communications", ("sms.db",), ("sms",), "Requires supported sms.db schema fields"),
    ("Tapbacks/reactions", "Communications", ("sms.db",), ("sms",), "Requires supported associated-message fields"),
    ("group chat membership", "Communications", ("sms.db",), ("sms",), "Requires chat tables"),
    ("chat sync/cloud state", "Communications", ("sms.db",), ("sms",), "Requires schema support"),
    ("Safari History", "Web and apps", ("History.db",), ("safari",), "Safari history database"),
    ("Safari downloads", "Web and apps", (), ("safari", "downloads"), "Safari download artifacts"),
    ("Safari tabs/session state", "Web and apps", (), ("safari", "session"), "Safari session artifacts"),
    ("Chrome/Firefox", "Web and apps", (), ("chrome", "firefox"), "Third-party browser container may require app parser"),
    ("app usage", "Web and apps", (), ("knowledge", "duet", "appusage"), "KnowledgeC/CoreDuet app context"),
    ("KnowledgeC", "Web and apps", ("knowledgeC.db",), ("knowledgec",), "KnowledgeC database"),
    ("CoreDuet", "Web and apps", (), ("coreduet", "duet"), "CoreDuet artifacts"),
    ("Screen Time", "Web and apps", (), ("screentime",), "Screen Time artifacts"),
    ("notifications", "Web and apps", ("BulletinBoard.sqlite", "DeliveredNotifications.db"), ("notifications",), "Notification databases"),
    ("Focus mode", "Web and apps", (), ("focus", "donotdisturb"), "Focus/DND artifacts"),
    ("Files app", "Files and cloud", (), ("files", "document"), "Files app/document provider artifacts"),
    ("iCloud Drive metadata", "Files and cloud", (), ("icloud", "clouddocs"), "iCloud Drive metadata"),
    ("OneDrive", "Files and cloud", (), ("onedrive",), "Third-party app container"),
    ("Dropbox", "Files and cloud", (), ("dropbox",), "Third-party app container"),
    ("Google Drive", "Files and cloud", (), ("googledrive", "drive"), "Third-party app container"),
    ("downloads", "Files and cloud", (), ("downloads",), "Downloaded file artifacts"),
    ("document-provider metadata", "Files and cloud", (), ("fileprovider", "documentprovider"), "Document provider metadata"),
    ("QuickLook previews", "Files and cloud", (), ("quicklook",), "Preview cache"),
    ("share-sheet history", "Files and cloud", (), ("sharesheet", "sharing"), "Sharing artifacts"),
    ("Maps history", "Location", (), ("maps", "geohistory"), "Maps artifacts"),
    ("routined/significant locations", "Location", (), ("routined", "significant"), "Location artifacts may be outside backup scope"),
    ("motion/activity", "Location", (), ("motion", "activity"), "Motion/activity artifacts"),
    ("photo GPS", "Location", ("Photos.sqlite",), ("photos",), "Photo metadata"),
    ("weather location", "Location", (), ("weather", "location"), "Weather location cache"),
    ("app location caches", "Location", (), ("location", "cache"), "App-specific location caches"),
    ("geofences", "Location", (), ("geofence",), "Geofence artifacts"),
    ("installed profiles", "Security/configuration", (), ("profile", "configurationprofile"), "Profiles"),
    ("MDM", "Security/configuration", (), ("mdm", "managed"), "MDM artifacts"),
    ("VPN", "Security/configuration", (), ("vpn", "networkextension"), "VPN configuration/state"),
    ("certificates", "Security/configuration", (), ("certificate", "trust"), "Certificate/trust artifacts"),
    ("trust records", "Security/configuration", (), ("trust",), "Trust records"),
    ("Apple ID/iCloud metadata", "Security/configuration", (), ("icloud", "appleid"), "Account metadata"),
    ("Wi-Fi known networks", "Security/configuration", ("com.apple.wifi.plist",), ("wifi", "wi-fi"), "Wi-Fi configuration"),
    ("Bluetooth paired devices", "Security/configuration", ("com.apple.MobileBluetooth.plist",), ("bluetooth",), "Bluetooth records"),
    ("cellular configuration", "Security/configuration", (), ("commcenter", "coretelephony", "carrier"), "Cellular/telephony"),
    ("analytics", "System/diagnostic", (), ("analytics",), "Analytics logs"),
    ("crash logs", "System/diagnostic", (), ("crash",), "Crash logs"),
    ("jetsam", "System/diagnostic", (), ("jetsam",), "Jetsam logs"),
    ("sysdiagnose", "System/diagnostic", (), ("sysdiagnose",), "Usually not in standard backup unless collected"),
    ("unified logs", "System/diagnostic", ("*.tracev3",), ("uuidtext", "logarchive"), "Unified logging material"),
    ("CoreCapture", "System/diagnostic", (), ("corecapture",), "CoreCapture material"),
    ("Wireless Diagnostics", "System/diagnostic", (), ("wirelessdiagnostics",), "Wireless diagnostics"),
    ("CommCenter", "System/diagnostic", (), ("commcenter",), "Telephony diagnostics"),
    ("CoreTelephony", "System/diagnostic", (), ("coretelephony",), "Telephony diagnostics"),
]


def build_coverage_audit(ctx: CaseContext, events: List[Event]) -> Tuple[List[CoverageRecord], List[AppCoverageRecord]]:
    manifest = parse_backup_manifests(ctx)
    ctx.manifest_records = manifest
    records: List[CoverageRecord] = []
    if not any(key.startswith("plist:") or value.get("domain") not in (None, "") for key, value in manifest.items()):
        records.append(
            CoverageRecord(
                artifact_id="backup_manifest",
                artifact_name="Manifest.db / backup manifests",
                category="Acquisition metadata",
                parser_name="coverage_manifest",
                parser_enabled=True,
                parser_status="FAILED",
                coverage_status="NOT_COLLECTED",
                file_present=False,
                failure_reason="Manifest.db was absent or unreadable; manifest-based coverage validation was unavailable.",
                error_count=1,
                acquisition_scope="NOT_COLLECTED",
                examiner_note="Decrypted-folder coverage is still available, but logical domain/fileID validation is materially limited.",
                confidence_in_coverage="LOW",
                coverage_basis="Manifest audit attempted before filesystem coverage audit.",
            )
        )
    for path in ctx.all_files:
        if path.name.lower().endswith(("-wal", "-shm")):
            continue
        records.append(audit_file_coverage(ctx, path, events, manifest))
    records.extend(build_native_target_coverage(ctx, records, events))
    app_records = build_app_coverage(ctx, records, events, manifest)
    ctx.coverage_records = records
    ctx.app_coverage_records = app_records
    return records, app_records


def parse_backup_manifests(ctx: CaseContext) -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    for db in ctx.find_named(["Manifest.db"]):
        artifact = SQLiteArtifact(ctx, db, "coverage_manifest")
        rows = artifact.query("SELECT fileID, domain, relativePath, flags FROM Files")
        for row in rows:
            file_id = str(row.get("fileID") or "")
            domain = str(row.get("domain") or "")
            rel = str(row.get("relativePath") or "")
            recovered = find_manifest_recovered_path(ctx, file_id, domain, rel)
            records[file_id] = {
                "fileID": file_id,
                "domain": domain,
                "relativePath": rel,
                "flags": row.get("flags"),
                "recovered_path": str(recovered) if recovered else "",
            }
    for plist_name in ("Manifest.plist", "Info.plist", "Status.plist"):
        for plist_path in ctx.find_named([plist_name]):
            data = plist_load(plist_path)
            records[f"plist:{plist_name}"] = {
                "fileID": "",
                "domain": "BackupManifest",
                "relativePath": plist_name,
                "flags": "",
                "recovered_path": str(plist_path),
                "plist_keys": sorted(data.keys()) if isinstance(data, dict) else [],
            }
    if not records:
        ctx.errors.log("coverage_manifest", ctx.case_dir, RuntimeError("Manifest.db absent or unreadable"), "manifest-based coverage validation unavailable")
    return records


def find_manifest_recovered_path(ctx: CaseContext, file_id: str, domain: str, rel: str) -> Optional[Path]:
    candidates = []
    if file_id:
        candidates.extend(ctx.find_named([file_id, file_id[:2] + "/" + file_id]))
        shard = ctx.root / file_id[:2] / file_id
        if shard.exists():
            candidates.append(shard)
    structured = ctx.root / domain / rel if domain and rel else None
    if structured and structured.exists():
        candidates.append(structured)
    return candidates[0] if candidates else None


def audit_file_coverage(
    ctx: CaseContext,
    path: Path,
    events: List[Event],
    manifest: Dict[str, Dict[str, Any]],
) -> CoverageRecord:
    rel = short_path(path, ctx.case_dir)
    manifest_info = manifest_lookup_for_path(ctx, path, manifest)
    domain = manifest_info.get("domain", domain_from_path(path, ctx))
    relative_path = manifest_info.get("relativePath", rel)
    category = category_for_path(path, domain)
    parser_name, parser_enabled = parser_for_path(path)
    wal = sqlite_companion(path, "-wal")
    shm = sqlite_companion(path, "-shm")
    record = CoverageRecord(
        artifact_id=manifest_info.get("fileID", hashlib.sha1(rel.encode("utf-8")).hexdigest()[:16]),
        artifact_name=path.name,
        category=category,
        app_bundle_id=app_bundle_from_domain(domain),
        domain=domain,
        relative_path=relative_path,
        absolute_path=str(path),
        file_type=file_type_for_path(path),
        size_bytes=safe_file_size(path),
        sha256=coverage_sha256(ctx, path),
        parser_name=parser_name,
        parser_enabled=parser_enabled,
        parser_status="NOT_RUN",
        coverage_status="PRESENT_UNSUPPORTED",
        file_present=True,
        companion_wal_present=wal.exists(),
        companion_shm_present=shm.exists(),
        wal_present=wal.exists(),
        shm_present=shm.exists(),
        acquisition_scope=acquisition_scope_for_domain(domain),
        confidence_in_coverage="MEDIUM",
        coverage_basis="File was present in recovered backup filesystem index.",
        deleted_record_carving_performed=False,
        deleted_record_recovery_supported=False,
    )
    if is_sqlite_file(path):
        audit_sqlite_database(ctx, record, path, events)
    elif path.suffix.lower() in (".plist", ".backup"):
        audit_plist_coverage(ctx, record, path, events)
    else:
        annotate_nonstructured_coverage(record, path, events)
    return record


def manifest_lookup_for_path(ctx: CaseContext, path: Path, manifest: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    path_text = str(path)
    for item in manifest.values():
        recovered = item.get("recovered_path") or ""
        if recovered and os.path.normcase(recovered) == os.path.normcase(path_text):
            return item
    return {}


def domain_from_path(path: Path, ctx: CaseContext) -> str:
    try:
        parts = path.relative_to(ctx.root).parts
    except ValueError:
        return "UNKNOWN"
    return parts[0] if parts else "UNKNOWN"


def category_for_path(path: Path, domain: str) -> str:
    text = (str(path) + " " + domain).lower()
    if any(token in text for token in ("sms", "callhistory", "addressbook", "facetime", "voicemail")):
        return "Communications"
    if any(token in text for token in ("safari", "chrome", "firefox", "knowledge", "duet", "notification")):
        return "Web and apps"
    if any(token in text for token in ("maps", "location", "routined", "photos")):
        return "Location"
    if any(token in text for token in ("wifi", "bluetooth", "vpn", "network", "commcenter", "coretelephony")):
        return "Security/configuration"
    if any(token in text for token in ("analytics", "crash", "jetsam", "sysdiagnose", "tracev3")):
        return "System/diagnostic"
    if "appdomain" in domain.lower() or "appdomaingroup" in domain.lower():
        return "Third-party app"
    return "Other"


def app_bundle_from_domain(domain: str) -> str:
    for prefix in ("AppDomain-", "AppDomainGroup-", "AppDomainPlugin-", "SysSharedContainerDomain-"):
        if domain.startswith(prefix):
            return domain[len(prefix):]
    return ""


def acquisition_scope_for_domain(domain: str) -> str:
    if domain in ("UNKNOWN", ""):
        return "UNKNOWN"
    if domain.startswith(("AppDomain", "HomeDomain", "WirelessDomain", "RootDomain", "SystemPreferencesDomain", "SysSharedContainerDomain", "ManagedPreferencesDomain", "MediaDomain", "CameraRollDomain")):
        return "IN_SUPPLIED_BACKUP"
    return "UNKNOWN"


def file_type_for_path(path: Path) -> str:
    if is_sqlite_file(path):
        return "sqlite"
    if path.suffix.lower() in (".plist", ".backup"):
        return "plist"
    if path.suffix.lower() in (".tracev3",):
        return "unified_log_trace"
    return path.suffix.lower().lstrip(".") or "unknown"


def safe_file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except Exception:
        return 0


def coverage_sha256(ctx: CaseContext, path: Path) -> str:
    size = safe_file_size(path)
    max_bytes = max(0, ctx.coverage_hash_max_size_mb) * 1024 * 1024
    key = path.suffix.lower() in (".db", ".sqlite", ".sqlite3", ".storedata", ".plist", ".tracev3") or path.name.lower() in ("manifest.db", "manifest.plist", "info.plist", "status.plist")
    if ctx.coverage_hash_all or (key and (not max_bytes or size <= max_bytes)):
        return sha256(path)
    return ""


def sqlite_companion(path: Path, suffix: str) -> Path:
    return Path(str(path) + suffix)


def is_sqlite_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except Exception:
        return False


def parser_for_path(path: Path) -> Tuple[str, bool]:
    text = str(path).lower()
    name = path.name.lower()
    mapping = [
        ("sms", "sms.db"),
        ("call_history", "callhistory.storedata"),
        ("contacts", "addressbook.sqlitedb"),
        ("safari", "history.db"),
        ("photos", "photos.sqlite"),
        ("notes", "notestore.sqlite"),
        ("mail", "envelope index"),
        ("calendar", "calendar.sqlitedb"),
        ("reminders", "cloudkitreminders.sqlite"),
        ("knowledgec", "knowledgec.db"),
        ("notifications", "bulletinboard.sqlite"),
        ("wifi", "wifi"),
        ("bluetooth_network", "bluetooth"),
        ("airdrop_nearby", "airdrop"),
        ("network_configuration", "network"),
        ("cellular_telephony", "commcenter"),
        ("cellular_telephony", "coretelephony"),
        ("data_usage", "datausage"),
    ]
    for parser, token in mapping:
        if token in name or token in text:
            return parser, True
    return "", False


def audit_sqlite_database(ctx: CaseContext, record: CoverageRecord, path: Path, events: List[Event]) -> None:
    artifact = SQLiteArtifact(ctx, path, "coverage_sqlite")
    tables = artifact.tables()
    record.database_opened = bool(tables)
    record.tables_found = tables
    record.wal_applied_by_sqlite = record.wal_present
    if not tables:
        record.coverage_status = "PRESENT_PARSE_FAILED"
        record.parser_status = "FAILED"
        record.failure_reason = "SQLite database could not be opened read-only or contained no enumerable tables."
        record.error_count = 1
        return
    lower_tables = {t.lower(): t for t in tables}
    supported = supported_tables_for_record(record, lower_tables)
    record.schema_recognized = bool(supported)
    record.tables_parsed = supported
    record.tables_unparsed = [t for t in tables if t not in supported]
    timestamp_fields = []
    rows_total = 0
    rows_examined = 0
    for table in tables[:50]:
        cols = artifact.columns(table)
        timestamp_fields.extend([col for col in cols if is_timestamp_like(col)])
        count = safe_table_count(artifact, table)
        rows_total += count
        if table in supported:
            rows_examined += count
    record.timestamp_fields_found = sorted(set(timestamp_fields))
    record.timestamp_fields_unparsed = record.timestamp_fields_found if not supported else []
    record.rows_total_estimated = rows_total
    record.rows_examined = rows_examined
    related_events = events_for_coverage(record, events)
    record.records_normalized_total = len(related_events)
    record.records_normalized_in_window = len([e for e in related_events if e.timestamp and ctx.start <= e.timestamp <= ctx.end])
    timestamps = [e.timestamp for e in related_events if e.timestamp]
    if timestamps:
        record.earliest_timestamp = format_dt(min(timestamps))
        record.latest_timestamp = format_dt(max(timestamps))
    if not record.parser_enabled:
        record.coverage_status = "PRESENT_UNSUPPORTED"
        record.parser_status = "NO_PARSER"
        record.unsupported_reason = "No parser is registered for this SQLite artifact."
    elif not record.schema_recognized:
        record.coverage_status = "PRESENT_UNKNOWN_SCHEMA"
        record.parser_status = "UNKNOWN_SCHEMA"
        record.unsupported_reason = "SQLite opened but schema did not match supported parser tables."
    elif record.records_normalized_total == 0 and rows_total == 0:
        record.coverage_status = "PRESENT_PARSED_ZERO_RECORDS"
        record.parser_status = "PARSED"
    elif record.records_normalized_total == 0:
        record.coverage_status = "PRESENT_PARSED_NO_WINDOW_RECORDS" if rows_total else "PRESENT_PARSED_ZERO_RECORDS"
        record.parser_status = "PARSED"
        record.examiner_note = "Database opened and supported tables were identified, but no normalized records were produced by the current parser/time filters."
    elif record.records_normalized_in_window == 0:
        record.coverage_status = "PRESENT_PARSED_NO_WINDOW_RECORDS"
        record.parser_status = "PARSED"
    elif record.tables_unparsed:
        record.coverage_status = "PRESENT_PARTIALLY_PARSED"
        record.parser_status = "PARTIAL"
    else:
        record.coverage_status = "PRESENT_PARSED_WITH_RECORDS"
        record.parser_status = "PARSED"
    if record.wal_present:
        record.examiner_note = (record.examiner_note + " " if record.examiner_note else "") + "WAL material was present and available to SQLite during read-only parsing; no specialized deleted-record recovery was performed."
    record.confidence_in_coverage = "HIGH" if record.database_opened else "LOW"
    record.coverage_basis = "SQLite magic header detected; tables enumerated and compared with registered parser support."


def supported_tables_for_record(record: CoverageRecord, lower_tables: Dict[str, str]) -> List[str]:
    if not record.parser_name:
        return []
    expected = SUPPORTED_SQLITE_SCHEMAS.get(record.parser_name, set())
    supported = []
    for expected_name in expected:
        for lower, original in lower_tables.items():
            if expected_name.lower() in lower:
                supported.append(original)
    return sorted(set(supported))


def safe_table_count(artifact: SQLiteArtifact, table: str) -> int:
    try:
        rows = artifact.query(f"SELECT COUNT(*) AS c FROM {quote_ident(table)}")
        return safe_int(rows[0].get("c")) if rows else 0
    except Exception:
        return 0


def is_timestamp_like(column: str) -> bool:
    lowered = column.lower()
    return any(token in lowered for token in ("date", "time", "timestamp", "created", "modified", "lastseen", "lastconnected"))


def events_for_coverage(record: CoverageRecord, events: List[Event]) -> List[Event]:
    related = []
    rel = (record.relative_path or record.absolute_path or "").lower()
    parser = record.parser_name
    for event in events:
        md = event.metadata or {}
        hay = json_dumps(md).lower() + " " + event.source.lower()
        if rel and rel in hay:
            related.append(event)
        elif parser and parser_event_match(parser, event):
            related.append(event)
    return related


def parser_event_match(parser: str, event: Event) -> bool:
    source = event.source.lower()
    return (
        (parser == "sms" and source in ("sms.db", "sms.db attachment"))
        or (parser == "call_history" and source == "callhistory")
        or (parser == "safari" and source == "safari")
        or (parser == "photos" and source == "photos")
        or (parser == "notes" and source == "notes")
        or (parser == "mail" and source == "mail")
        or (parser == "calendar" and source == "calendar")
        or (parser == "reminders" and source == "reminders")
        or (parser == "knowledgec" and source == "knowledgec")
        or (parser == "notifications" and source == "notifications")
        or (parser == "wifi" and source == "wi-fi")
        or (parser == "bluetooth_network" and source == "bluetooth")
        or (parser == "airdrop_nearby" and source == "airdrop/nearby")
        or (parser == "network_configuration" and source == "network configuration")
        or (parser == "cellular_telephony" and source == "cellular/telephony")
        or (parser == "data_usage" and source == "data usage")
    )


def audit_plist_coverage(ctx: CaseContext, record: CoverageRecord, path: Path, events: List[Event]) -> None:
    data = plist_load(path)
    if data is None:
        record.coverage_status = "PRESENT_ENCRYPTED_OR_INACCESSIBLE"
        record.parser_status = "FAILED"
        record.failure_reason = "plistlib could not parse the property list; it may be encrypted, malformed, or inaccessible."
        record.error_count = 1
        record.confidence_in_coverage = "LOW"
        return
    related_events = events_for_coverage(record, events)
    record.records_normalized_total = len(related_events)
    record.records_normalized_in_window = len([e for e in related_events if e.timestamp and ctx.start <= e.timestamp <= ctx.end])
    record.database_opened = False
    record.schema_recognized = record.parser_enabled
    record.parser_status = "PARSED" if record.parser_enabled else "NO_PARSER"
    if not record.parser_enabled:
        record.coverage_status = "PRESENT_UNSUPPORTED"
        record.unsupported_reason = "Property list was parseable, but no specific parser is registered for this artifact."
    elif record.records_normalized_total and record.records_normalized_in_window:
        record.coverage_status = "PRESENT_PARSED_WITH_RECORDS"
    elif record.records_normalized_total:
        record.coverage_status = "PRESENT_PARSED_NO_WINDOW_RECORDS"
    else:
        record.coverage_status = "PRESENT_PARSED_ZERO_RECORDS"
    record.confidence_in_coverage = "MEDIUM"
    record.coverage_basis = "Property list parsed with plistlib; structured records may be only partially interpreted."


def annotate_nonstructured_coverage(record: CoverageRecord, path: Path, events: List[Event]) -> None:
    if record.wal_present and path.name.lower().endswith(("-wal", "-shm")):
        record.coverage_status = "PRESENT_ONLY_WAL_SHM"
    elif not record.parser_enabled:
        record.coverage_status = "PRESENT_UNSUPPORTED"
        record.unsupported_reason = "No parser is registered for this file type/path."
    else:
        record.coverage_status = "PRESENT_PARTIALLY_PARSED"
    record.parser_status = "NO_PARSER" if not record.parser_enabled else "PARTIAL"
    related_events = events_for_coverage(record, events)
    record.records_normalized_total = len(related_events)
    record.records_normalized_in_window = len(related_events)
    record.coverage_basis = "File was inventoried; no table-level parser audit applies."


def build_native_target_coverage(ctx: CaseContext, file_records: List[CoverageRecord], events: List[Event]) -> List[CoverageRecord]:
    records = []
    for name, category, filenames, tokens, note in NATIVE_COVERAGE_TARGETS:
        matching_files = [
            record for record in file_records
            if any(record.artifact_name.lower() == f.lower() or (f.startswith("*.") and record.artifact_name.lower().endswith(f[1:].lower())) for f in filenames)
            or any(token.lower() in (record.relative_path + " " + record.absolute_path).lower() for token in tokens)
        ]
        parser_name = matching_files[0].parser_name if matching_files else ""
        parser_enabled = any(record.parser_enabled for record in matching_files)
        event_matches = [
            event for event in events
            if any(token.lower() in (event.source + " " + event.event_type + " " + event.details).lower() for token in tokens)
        ]
        in_window = [event for event in event_matches if event.timestamp and ctx.start <= event.timestamp <= ctx.end]
        target_probe = CoverageRecord(artifact_name=name, category=category, examiner_note=note)
        expectation = expected_for_acquisition(target_probe, "encrypted_iphone_backup")
        if not matching_files:
            status = "OUTSIDE_STANDARD_BACKUP" if expectation == "OUTSIDE_STANDARD_BACKUP" else "NOT_PRESENT"
            parser_status = "NOT_RUN"
        elif any(record.coverage_status == "PRESENT_PARSE_FAILED" for record in matching_files):
            status = "PRESENT_PARSE_FAILED"
            parser_status = "FAILED"
        elif not parser_enabled:
            status = "PRESENT_UNSUPPORTED"
            parser_status = "NO_PARSER"
        elif in_window:
            status = "PRESENT_PARSED_WITH_RECORDS"
            parser_status = "PARSED"
        elif event_matches:
            status = "PRESENT_PARSED_NO_WINDOW_RECORDS"
            parser_status = "PARSED"
        else:
            status = "PRESENT_PARSED_ZERO_RECORDS" if parser_enabled else "PRESENT_UNSUPPORTED"
            parser_status = "PARSED" if parser_enabled else "NO_PARSER"
        records.append(
            CoverageRecord(
                artifact_id="native:" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_"),
                artifact_name=name,
                category=category,
                parser_name=parser_name,
                parser_enabled=parser_enabled,
                parser_status=parser_status,
                coverage_status=status,
                file_present=bool(matching_files),
                records_normalized_total=len(event_matches),
                records_normalized_in_window=len(in_window),
                unsupported_reason="" if parser_enabled else "No dedicated parser or source artifact was identified by coverage audit.",
                error_count=sum(record.error_count for record in matching_files),
                acquisition_scope="IN_SUPPLIED_BACKUP" if matching_files else "OUTSIDE_STANDARD_BACKUP" if status == "OUTSIDE_STANDARD_BACKUP" else "NOT_PRESENT",
                examiner_note=note,
                confidence_in_coverage="MEDIUM",
                coverage_basis="Native coverage matrix check using manifest/filesystem index and normalized events.",
                companion_wal_present=any(record.wal_present for record in matching_files),
                companion_shm_present=any(record.shm_present for record in matching_files),
                wal_present=any(record.wal_present for record in matching_files),
                shm_present=any(record.shm_present for record in matching_files),
            )
        )
    return records


HIGH_VALUE_APP_PATTERNS = {
    "WhatsApp": ("whatsapp",),
    "Signal": ("signal",),
    "Telegram": ("telegram",),
    "Facebook Messenger": ("messenger", "facebook"),
    "Instagram": ("instagram",),
    "Snapchat": ("snapchat",),
    "Gmail": ("gmail", "googlemail"),
    "Outlook": ("outlook",),
    "Teams": ("teams",),
    "Slack": ("slack",),
    "Chrome": ("chrome",),
    "Firefox": ("firefox",),
    "Google Drive": ("googledrive", "drive"),
    "OneDrive": ("onedrive",),
    "Dropbox": ("dropbox",),
    "Google Maps": ("googlemaps", "maps"),
    "banking apps": ("bank", "chase", "wellsfargo", "boa", "capitalone"),
    "cryptocurrency apps": ("coinbase", "crypto", "wallet", "binance", "kraken"),
    "job/employment apps": ("indeed", "linkedin", "workday", "greenhouse"),
    "cloud-storage providers": ("drive", "dropbox", "onedrive", "box"),
    "document-provider apps": ("fileprovider", "document"),
}


def build_app_coverage(
    ctx: CaseContext,
    coverage_records: List[CoverageRecord],
    events: List[Event],
    manifest: Dict[str, Dict[str, Any]],
) -> List[AppCoverageRecord]:
    grouped: Dict[str, List[CoverageRecord]] = {}
    for record in coverage_records:
        bundle = record.app_bundle_id
        if bundle:
            grouped.setdefault(bundle, []).append(record)
    app_records = []
    for bundle, records in sorted(grouped.items()):
        text = bundle.lower()
        high_value = [name for name, patterns in HIGH_VALUE_APP_PATTERNS.items() if any(pattern in text for pattern in patterns)]
        app_records.append(
            AppCoverageRecord(
                bundle_id=bundle if not bundle.startswith("group.") else "",
                app_group_id=bundle if bundle.startswith("group.") else "",
                app_name=bundle,
                files_found=len(records),
                databases_found=len([r for r in records if r.file_type == "sqlite"]),
                parser_available=any(r.parser_enabled for r in records),
                parser_status="PRESENT_PARTIALLY_PARSED" if any(r.parser_enabled for r in records) else "PRESENT_UNSUPPORTED",
                normalized_records=sum(r.records_normalized_total for r in records),
                unsupported_files=len([r for r in records if not r.parser_enabled]),
                likely_high_value_artifacts=high_value,
            )
        )
    return app_records


ACQUISITION_PROFILES = {
    "encrypted_iphone_backup": {
        "expected_tokens": (
            "manifest", "sms.db", "sms attachments", "callhistory", "addressbook", "safari",
            "photos", "notes", "calendar", "reminders", "knowledgec", "notifications",
            "wi-fi", "wifi", "bluetooth", "application containers",
        ),
        "optional_tokens": (
            "facetime", "voicemail", "focus", "screen time", "third-party", "cloud provider",
            "files app", "document-provider", "quicklook", "chrome/firefox", "weather", "geofence",
        ),
        "outside_standard_tokens": (
            "carrier signaling", "carrier sms routing", "baseband", "live ram", "packet capture",
            "router", "access-point logs", "sysdiagnose", "unified logs", "corecapture",
            "secure enclave", "volatile", "deleted/unallocated", "full filesystem",
        ),
        "separately_collectable_tokens": (
            "carrier records", "router/ap logs", "cloud provider exports", "apple legal return",
            "mdm logs", "vpn provider logs", "contemporaneous sysdiagnose", "associated computer",
        ),
    }
}


def coverage_record_text(record: CoverageRecord) -> str:
    return " ".join(
        str(value or "")
        for value in (
            record.artifact_id,
            record.artifact_name,
            record.category,
            record.parser_name,
            record.examiner_note,
            record.relative_path,
            record.app_bundle_id,
            record.coverage_status,
        )
    ).lower()


def coverage_item_label(record: CoverageRecord) -> str:
    return f"{record.artifact_name}: {record.coverage_status}"


def acquisition_type_key(acquisition_type: str) -> str:
    text = (acquisition_type or "encrypted_iphone_backup").strip().lower().replace(" ", "_").replace("-", "_")
    if text in {"encrypted_iphone_backup", "encrypted_itunes_backup", "itunes_backup"}:
        return "encrypted_iphone_backup"
    return text or "encrypted_iphone_backup"


def expected_for_acquisition(record: CoverageRecord, acquisition_type: str = "encrypted_iphone_backup") -> str:
    text = coverage_record_text(record)
    profile = ACQUISITION_PROFILES.get(acquisition_type_key(acquisition_type), ACQUISITION_PROFILES["encrypted_iphone_backup"])
    if any(token in text for token in profile["outside_standard_tokens"]):
        return "OUTSIDE_STANDARD_BACKUP"
    if any(token in text for token in profile["separately_collectable_tokens"]):
        return "NOT_SEPARATELY_COLLECTED"
    if any(token in text for token in profile["optional_tokens"]):
        return "OPTIONAL"
    if record.artifact_id.startswith("native:") or record.parser_enabled or record.category == "Acquisition metadata":
        return "EXPECTED"
    if any(token in text for token in profile["expected_tokens"]):
        return "EXPECTED"
    return "OPTIONAL"


def classify_coverage_disposition(record: CoverageRecord, acquisition_type: str) -> str:
    expectation = expected_for_acquisition(record, acquisition_type)
    status = record.coverage_status
    if status == "OUTSIDE_ACQUISITION_SCOPE":
        return "SUPPLEMENTAL_EVIDENCE"
    if expectation == "OUTSIDE_STANDARD_BACKUP" or status == "OUTSIDE_STANDARD_BACKUP":
        return "OUTSIDE_STANDARD_ACQUISITION"
    if expectation == "NOT_SEPARATELY_COLLECTED":
        return "NOT_SEPARATELY_COLLECTED"
    if status in {"PRESENT_PARSED_WITH_RECORDS", "PRESENT_PARSED_NO_WINDOW_RECORDS", "PRESENT_PARSED_ZERO_RECORDS"}:
        return "SUCCESSFULLY_EXAMINED"
    if status == "PRESENT_PARTIALLY_PARSED":
        return "PARTIALLY_EXAMINED"
    if status in {"PRESENT_PARSE_FAILED", "PRESENT_UNKNOWN_SCHEMA", "PRESENT_ENCRYPTED_OR_INACCESSIBLE", "PRESENT_ONLY_WAL_SHM"}:
        return "EXAMINATION_FAILURE"
    if status in {"PRESENT_UNSUPPORTED", "PRESENT_PARSER_DISABLED"}:
        return "PRESENT_UNSUPPORTED"
    if status == "NOT_PRESENT":
        return "OPTIONAL_NOT_PRESENT" if expectation == "OPTIONAL" else "EXPECTED_BUT_NOT_PRESENT"
    if status == "NOT_COLLECTED":
        return "NOT_SEPARATELY_COLLECTED"
    if not record.file_present and expectation == "OPTIONAL":
        return "OPTIONAL_NOT_PRESENT"
    return "UNKNOWN"


def is_relevant_record(record: CoverageRecord, relevant_finding: Optional[str]) -> bool:
    if not relevant_finding:
        return True
    return record in relevant_artifacts_for_finding(relevant_finding, [record])


def build_examination_gaps(
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    relevant_finding: Optional[str] = None,
) -> List[str]:
    gaps: List[str] = []
    relevant_records = relevant_artifacts_for_finding(relevant_finding, records) if relevant_finding else records
    for record in relevant_records:
        disposition = classify_coverage_disposition(record, "encrypted_iphone_backup")
        if disposition in {"EXAMINATION_FAILURE", "PARTIALLY_EXAMINED"}:
            gaps.append(coverage_item_label(record))
        elif disposition == "PRESENT_UNSUPPORTED" and (artifact_weight(record) >= 5 or record.file_present):
            gaps.append(coverage_item_label(record))
        elif disposition == "EXPECTED_BUT_NOT_PRESENT":
            gaps.append(coverage_item_label(record))
    if relevant_finding in (None, "normal_communications", "command_activity", "malware_or_compromise"):
        for app in app_records:
            high_value = bool(app.likely_high_value_artifacts)
            relevant_app = relevant_finding in {None, "normal_communications", "command_activity", "malware_or_compromise"} and high_value
            if not app.parser_available and relevant_app:
                gaps.append(f"Application container was present but unsupported: {app.app_name}")
    return sorted(set(gaps))[:200]


def build_acquisition_limitations(
    records: List[CoverageRecord],
    acquisition_type: str,
    relevant_finding: Optional[str] = None,
) -> List[str]:
    limitations: List[str] = []
    relevant_records = relevant_artifacts_for_finding(relevant_finding, records) if relevant_finding else records
    for record in relevant_records:
        disposition = classify_coverage_disposition(record, acquisition_type)
        if disposition == "OUTSIDE_STANDARD_ACQUISITION":
            limitations.append(f"{record.artifact_name}: ordinarily outside {acquisition_type_key(acquisition_type)}")
    if relevant_finding in {"silent_sms", "unusual_network_transmission", "network_activity"}:
        limitations.append("Carrier signaling, baseband telemetry, packet contents, router/AP logs, and complete connection history are ordinarily outside a standard encrypted iPhone backup.")
    if relevant_finding in {"command_activity", "malware_or_compromise"}:
        limitations.append("Live RAM, complete process execution history, full filesystem deleted/unallocated data, and volatile application state are ordinarily outside a standard encrypted iPhone backup.")
    return sorted(set(limitations))[:200]


def build_not_collected_sources(
    records: List[CoverageRecord],
    relevant_finding: Optional[str] = None,
) -> List[str]:
    sources: List[str] = []
    relevant_records = relevant_artifacts_for_finding(relevant_finding, records) if relevant_finding else records
    for record in relevant_records:
        if classify_coverage_disposition(record, "encrypted_iphone_backup") == "NOT_SEPARATELY_COLLECTED":
            sources.append(record.artifact_name)
    if relevant_finding in {"silent_sms", "network_activity", "unusual_network_transmission"}:
        sources.extend(["Carrier records", "Router/AP logs", "Contemporaneous sysdiagnose"])
    if relevant_finding in {"command_activity", "malware_or_compromise"}:
        sources.extend(["Associated computer evidence", "MDM/security logs", "Contemporaneous sysdiagnose", "Full filesystem acquisition where lawful and available"])
    return sorted(set(sources))[:200]


def material_coverage_gaps(records: List[CoverageRecord], app_records: List[AppCoverageRecord]) -> List[str]:
    return build_examination_gaps(records, app_records)


def coverage_completeness_level(records: List[CoverageRecord], app_records: List[AppCoverageRecord]) -> str:
    gaps = build_examination_gaps(records, app_records)
    failures = [
        r for r in records
        if classify_coverage_disposition(r, "encrypted_iphone_backup") == "EXAMINATION_FAILURE"
    ]
    if failures:
        return "EXAMINATION_GAPS_PRESENT"
    if gaps:
        return "PARTIAL_SUPPORTED_COVERAGE"
    if not records:
        return "UNKNOWN"
    return "COMPLETE_FOR_SUPPORTED_ARTIFACTS"


def coverage_summary(records: List[CoverageRecord], app_records: List[AppCoverageRecord]) -> Dict[str, Any]:
    status_counts: Dict[str, int] = {}
    for record in records:
        status_counts[record.coverage_status] = status_counts.get(record.coverage_status, 0) + 1
    dbs = [record for record in records if record.file_type == "sqlite"]
    examination_gaps = build_examination_gaps(records, app_records)
    acquisition_limitations = build_acquisition_limitations(records, "encrypted_iphone_backup")
    not_collected = build_not_collected_sources(records)
    recommendations = build_additional_evidence_recommendations(records, app_records)
    supported_status = coverage_completeness_level(records, app_records)
    return {
        "total_files_inventoried": len([r for r in records if r.absolute_path]),
        "databases_identified": len(dbs),
        "databases_opened": len([r for r in dbs if r.database_opened]),
        "supported_databases": len([r for r in dbs if r.parser_enabled]),
        "unsupported_databases": len([r for r in dbs if not r.parser_enabled]),
        "parse_failures": len([r for r in records if r.coverage_status == "PRESENT_PARSE_FAILED"]),
        "partially_parsed_artifacts": len([r for r in records if r.coverage_status == "PRESENT_PARTIALLY_PARSED"]),
        "third_party_app_containers_found": len(app_records),
        "unsupported_app_containers": len([a for a in app_records if not a.parser_available]),
        "artifacts_with_wal_shm": len([r for r in records if r.wal_present or r.shm_present]),
        "records_normalized": sum(r.records_normalized_total for r in records),
        "records_in_requested_window": sum(r.records_normalized_in_window for r in records),
        "supported_examination_status": supported_status,
        "examination_gaps": examination_gaps,
        "examination_gap_count": len(examination_gaps),
        "acquisition_limitations": acquisition_limitations,
        "acquisition_limitation_count": len(acquisition_limitations),
        "not_collected_sources": not_collected,
        "not_collected_source_count": len(not_collected),
        "additional_evidence_recommendations": recommendations,
        "material_coverage_gaps": examination_gaps,
        "status_counts": status_counts,
        "completeness_level": supported_status,
    }


def is_record_covered(record: CoverageRecord) -> bool:
    return coverage_multiplier(record) >= 0.9


def coverage_multiplier(record: CoverageRecord) -> float:
    status = record.coverage_status
    if status in {"PRESENT_PARSED_WITH_RECORDS", "PRESENT_PARSED_NO_WINDOW_RECORDS"}:
        return 1.0
    if status == "PRESENT_PARSED_ZERO_RECORDS":
        return 0.9
    if status == "PRESENT_PARTIALLY_PARSED":
        table_ratio = ratio(len(record.tables_parsed), len(record.tables_found)) if record.tables_found else 0.5
        row_ratio = ratio(record.rows_examined, record.rows_total_estimated) if record.rows_total_estimated else 0.5
        schema_credit = 1.0 if record.schema_recognized else 0.5
        timestamp_credit = 1.0 if record.timestamp_fields_found and not record.timestamp_fields_unparsed else 0.7 if record.timestamp_fields_found else 0.6
        error_penalty = min(0.2, record.error_count * 0.05)
        partial = ((table_ratio + row_ratio + schema_credit + timestamp_credit) / 4.0) - error_penalty
        return max(0.5, min(0.8, partial))
    if status == "PRESENT_UNKNOWN_SCHEMA":
        return 0.15
    if status == "PRESENT_ONLY_WAL_SHM":
        return 0.10
    return 0.0


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))


def canonical_logical_artifact_id(record: CoverageRecord) -> str:
    if record.artifact_id.startswith("native:"):
        return record.artifact_id
    logical = [record.parser_name or record.file_type or "artifact", record.domain, record.relative_path, record.app_bundle_id]
    if record.parser_name:
        return "parser:" + ":".join(part.lower() for part in logical if part)
    return "file:" + hashlib.sha1("|".join(part for part in logical if part).lower().encode("utf-8")).hexdigest()[:16]


def scoreable_coverage_records(records: List[CoverageRecord]) -> Tuple[List[CoverageRecord], Dict[str, Any]]:
    native_ids = {
        canonical_native_match_id(record)
        for record in records
        if record.artifact_id.startswith("native:")
    }
    selected: Dict[str, CoverageRecord] = {}
    excluded = 0
    duplicate_suppressed = 0
    expected_missing = []
    optional_absent = []
    outside_standard = []
    for record in records:
        expectation = expected_for_acquisition(record)
        if expectation == "OPTIONAL" and not record.file_present:
            optional_absent.append(record.artifact_name)
            excluded += 1
            continue
        if expectation == "OUTSIDE_STANDARD_BACKUP":
            outside_standard.append(record.artifact_name)
            excluded += 1
            continue
        if not is_scoreable_record(record):
            excluded += 1
            continue
        if not record.artifact_id.startswith("native:") and canonical_native_match_id(record) in native_ids:
            duplicate_suppressed += 1
            continue
        key = canonical_logical_artifact_id(record)
        if key in selected:
            duplicate_suppressed += 1
            if artifact_weight(record) > artifact_weight(selected[key]) or record.artifact_id.startswith("native:"):
                selected[key] = record
            continue
        selected[key] = record
        if expectation == "EXPECTED" and not record.file_present:
            expected_missing.append(record.artifact_name)
    basis = {
        "scoreable_artifact_count": len(selected),
        "excluded_artifact_count": excluded,
        "duplicate_records_suppressed": duplicate_suppressed,
        "denominator_basis": "Expected and scoreable forensic artifacts only; optional absent and outside-standard-backup sources are excluded from denominators.",
        "expected_artifacts_missing": sorted(set(expected_missing)),
        "optional_artifacts_absent": sorted(set(optional_absent)),
        "outside_standard_backup_artifacts": sorted(set(outside_standard)),
    }
    return list(selected.values()), basis


def canonical_native_match_id(record: CoverageRecord) -> str:
    text = (record.artifact_name + " " + record.parser_name + " " + record.relative_path).lower()
    for name, _category, _filenames, tokens, _note in NATIVE_COVERAGE_TARGETS:
        if name.lower() in text or any(token.lower() in text for token in tokens):
            return "native:" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return canonical_logical_artifact_id(record)


def is_scoreable_record(record: CoverageRecord) -> bool:
    if record.artifact_id.startswith("native:") or record.category == "Acquisition metadata":
        return True
    if record.file_type == "sqlite" and (record.parser_enabled or record.parser_name):
        return True
    if record.parser_enabled:
        return True
    if record.category in {"Security/configuration", "System/diagnostic", "Communications", "Web and apps", "Location"} and record.parser_name:
        return True
    if record.category == "Third-party app" and record.app_bundle_id:
        return True
    return False


def achieved_points(record: CoverageRecord) -> float:
    return artifact_weight(record) * coverage_multiplier(record)


def weighted_percent(records: List[CoverageRecord], predicate=None) -> float:
    possible = sum(artifact_weight(record) for record in records)
    if possible <= 0:
        return 0.0
    if predicate:
        covered = sum(artifact_weight(record) for record in records if predicate(record))
    else:
        covered = sum(achieved_points(record) for record in records)
    return round((covered / possible) * 100.0, 2)


def build_coverage_category_results(records: List[CoverageRecord]) -> List[CoverageCategoryResult]:
    grouped: Dict[str, List[CoverageRecord]] = {}
    for record in records:
        grouped.setdefault(record.category or "Unknown", []).append(record)
    results = []
    for category, items in sorted(grouped.items()):
        possible = sum(artifact_weight(record) for record in items)
        covered = sum(achieved_points(record) for record in items)
        percent = (covered / possible * 100.0) if possible else 0.0
        gaps = [
            f"{record.artifact_name}: {record.coverage_status}"
            for record in items
            if classify_coverage_disposition(record, "encrypted_iphone_backup") in {"EXAMINATION_FAILURE", "PARTIALLY_EXAMINED", "PRESENT_UNSUPPORTED", "EXPECTED_BUT_NOT_PRESENT"}
        ][:20]
        results.append(
            CoverageCategoryResult(
                category=category,
                weight=possible,
                possible_weight=possible,
                covered_weight=int(round(covered)),
                coverage_percent=percent,
                records_total=len(items),
                records_covered=len([record for record in items if coverage_multiplier(record) > 0]),
                material_gaps=gaps,
            )
        )
    return results


def build_evidence_coverage_score(
    ctx: CaseContext,
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    events: List[Event],
) -> Dict[str, Any]:
    scoreable, score_basis = scoreable_coverage_records(records)
    supported = [record for record in scoreable if record.parser_enabled]
    native = [record for record in records if record.category != "Third-party app" and not record.app_bundle_id]
    native_scoreable = [record for record in scoreable if record.category != "Third-party app" and not record.app_bundle_id]
    third_party = [record for record in scoreable if record.category == "Third-party app" or record.app_bundle_id]
    critical = [record for record in scoreable if artifact_weight(record) >= 8]
    score = {
        "supported_examination_status": coverage_completeness_level(scoreable, app_records),
        "examination_gaps": build_examination_gaps(scoreable, app_records),
        "acquisition_limitations": build_acquisition_limitations(records, "encrypted_iphone_backup"),
        "evidence_not_collected": build_not_collected_sources(records),
        "additional_evidence_recommendations": build_additional_evidence_recommendations(records, app_records),
        "supported_parser_coverage_percent": weighted_percent(supported),
        "overall_evidence_coverage_percent": weighted_percent(scoreable),
        "native_artifact_coverage_percent": weighted_percent(native_scoreable),
        "third_party_artifact_coverage_percent": weighted_percent(third_party),
        "requested_window_coverage_percent": weighted_percent(scoreable, requested_window_examined),
        "critical_artifact_coverage_percent": weighted_percent(critical),
        "coverage_categories": [result.as_dict() for result in build_coverage_category_results(scoreable)],
        "category_heat_map": category_heat_map_lines(build_coverage_category_results(scoreable)),
        "heat_map": coverage_heat_map(weighted_percent(scoreable)),
        "scoreable_artifact_count": score_basis["scoreable_artifact_count"],
        "excluded_artifact_count": score_basis["excluded_artifact_count"],
        "duplicate_records_suppressed": score_basis["duplicate_records_suppressed"],
        "denominator_basis": score_basis["denominator_basis"],
        "status_multipliers": STATUS_MULTIPLIERS,
        "expected_artifacts_missing": score_basis["expected_artifacts_missing"],
        "optional_artifacts_absent": score_basis["optional_artifacts_absent"],
        "outside_standard_backup_artifacts": score_basis["outside_standard_backup_artifacts"],
        "note": "Coverage percentages are weighted audit measures, not probabilities.",
    }
    score["internal_validation"] = validate_coverage_scoring(records, app_records, score)
    return score


STATUS_MULTIPLIERS = {
    "PRESENT_PARSED_WITH_RECORDS": 1.00,
    "PRESENT_PARSED_NO_WINDOW_RECORDS": 1.00,
    "PRESENT_PARSED_ZERO_RECORDS": 0.90,
    "PRESENT_PARTIALLY_PARSED": "0.50-0.80 calculated",
    "PRESENT_UNKNOWN_SCHEMA": 0.15,
    "PRESENT_ONLY_WAL_SHM": 0.10,
    "PRESENT_UNSUPPORTED": 0.00,
    "PRESENT_PARSER_DISABLED": 0.00,
    "PRESENT_PARSE_FAILED": 0.00,
    "PRESENT_ENCRYPTED_OR_INACCESSIBLE": 0.00,
    "NOT_COLLECTED": 0.00,
    "OUTSIDE_ACQUISITION_SCOPE": 0.00,
    "OUTSIDE_STANDARD_BACKUP": 0.00,
    "UNKNOWN": 0.00,
}


def requested_window_examined(record: CoverageRecord) -> bool:
    return record.parser_status in {"PARSED", "PARTIAL"} and record.coverage_status not in {
        "PRESENT_PARSE_FAILED",
        "PRESENT_UNSUPPORTED",
        "PRESENT_UNKNOWN_SCHEMA",
        "NOT_COLLECTED",
        "OUTSIDE_ACQUISITION_SCOPE",
    }


def coverage_heat_map(percent: float, width: int = 20) -> str:
    filled = max(0, min(width, int(round((percent / 100.0) * width))))
    try:
        return ("█" * filled) + ("░" * (width - filled)) + f" {percent:.2f}% {coverage_label(percent)}"
    except UnicodeEncodeError:
        return ("#" * filled) + ("-" * (width - filled)) + f" {percent:.2f}% {coverage_label(percent)}"


def coverage_label(percent: float) -> str:
    if percent >= 85:
        return "STRONG"
    if percent >= 60:
        return "MODERATE"
    if percent > 0:
        return "MATERIAL GAP"
    return "NOT COLLECTED"


def category_heat_map_lines(results: List[CoverageCategoryResult]) -> List[Dict[str, Any]]:
    lines = []
    for result in results:
        lines.append(
            {
                "category": result.category,
                "bar": coverage_heat_map(result.coverage_percent),
                "coverage_percent": round(result.coverage_percent, 2),
                "completeness_label": coverage_label(result.coverage_percent),
                "material_gaps": result.material_gaps,
                "achieved_points": round(result.covered_weight, 2),
                "possible_points": result.possible_weight,
            }
        )
    return lines


def validate_coverage_scoring(
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    score: Dict[str, Any],
) -> Dict[str, Any]:
    checks: Dict[str, bool] = {}
    pct_keys = [
        "supported_parser_coverage_percent",
        "overall_evidence_coverage_percent",
        "native_artifact_coverage_percent",
        "third_party_artifact_coverage_percent",
        "requested_window_coverage_percent",
        "critical_artifact_coverage_percent",
    ]
    checks["scores_stay_between_0_and_100"] = all(0.0 <= float(score.get(key, 0.0)) <= 100.0 for key in pct_keys)
    partial = CoverageRecord(
        artifact_name="Synthetic partial DB",
        category="Communications",
        parser_enabled=True,
        parser_status="PARTIAL",
        coverage_status="PRESENT_PARTIALLY_PARSED",
        schema_recognized=True,
        tables_found=["a", "b", "c", "d"],
        tables_parsed=["a", "b"],
        rows_total_estimated=100,
        rows_examined=60,
        timestamp_fields_found=["date"],
        timestamp_fields_unparsed=[],
    )
    partial_mult = coverage_multiplier(partial)
    checks["partial_artifacts_receive_partial_credit"] = 0.50 <= partial_mult <= 0.80
    dup_native = CoverageRecord(artifact_id="native:sms_db", artifact_name="sms.db", category="Communications", parser_name="sms", parser_enabled=True, coverage_status="PRESENT_PARSED_WITH_RECORDS", file_present=True)
    dup_file = CoverageRecord(artifact_id="file_sms", artifact_name="sms.db", category="Communications", parser_name="sms", parser_enabled=True, coverage_status="PRESENT_PARSED_WITH_RECORDS", file_present=True, relative_path="HomeDomain/Library/SMS/sms.db")
    scoreable, basis = scoreable_coverage_records([dup_native, dup_file])
    checks["duplicate_artifacts_not_counted_twice"] = len(scoreable) == 1 and basis["duplicate_records_suppressed"] >= 1
    arbitrary = CoverageRecord(artifact_id="cache", artifact_name="random.cache", category="Other", coverage_status="PRESENT_UNSUPPORTED", file_present=True)
    scoreable2, _basis2 = scoreable_coverage_records([arbitrary])
    checks["arbitrary_unsupported_files_do_not_dominate_scores"] = not scoreable2
    optional = CoverageRecord(artifact_id="native:voicemail", artifact_name="voicemail", category="Communications", coverage_status="NOT_PRESENT", file_present=False)
    scoreable3, basis3 = scoreable_coverage_records([optional])
    checks["optional_absent_artifacts_do_not_reduce_denominator"] = not scoreable3 and "voicemail" in " ".join(basis3["optional_artifacts_absent"]).lower()
    outside = CoverageRecord(artifact_id="native:packet_capture_files", artifact_name="Packet capture files", category="System/diagnostic", coverage_status="NOT_PRESENT", file_present=False)
    scoreable4, basis4 = scoreable_coverage_records([outside])
    checks["outside_standard_backup_affects_blind_spots_not_supported_parser_coverage"] = (not scoreable4) and bool(basis4["outside_standard_backup_artifacts"])
    parsed_zero = CoverageRecord(artifact_name="Parsed zero window DB", category="Communications", parser_enabled=True, parser_status="PARSED", coverage_status="PRESENT_PARSED_NO_WINDOW_RECORDS", file_present=True)
    checks["requested_window_coverage_measures_examination_capability"] = requested_window_examined(parsed_zero)
    checks["category_heat_map_contains_one_line_per_category"] = len(score.get("category_heat_map", [])) == len(score.get("coverage_categories", []))
    relevant = relevant_artifacts_for_finding("silent_sms", records)
    checks["silent_sms_confidence_uses_only_relevant_evidence_categories"] = all(
        any(token in (record.artifact_name + " " + record.category + " " + record.parser_name + " " + record.examiner_note).lower() for token in ("sms", "cellular", "telephony", "commcenter", "coretelephony", "sysdiagnose", "carrier", "baseband"))
        for record in relevant
    )
    checks["coverage_percentages_are_never_probabilities"] = "not probabilities" in str(score.get("note", "")).lower()
    checks.update(deterministic_completeness_model_tests())
    checks.update(deterministic_attachment_linking_tests())
    checks.update(deterministic_reporting_pipeline_tests())
    return {"passed": all(checks.values()), "checks": checks}


def deterministic_completeness_model_tests() -> Dict[str, bool]:
    ctx = CaseContext(Path("synthetic_case"), datetime(2026, 1, 1, 0, 0, 0), datetime(2026, 1, 1, 1, 0, 0), 5)
    sms_ok = CoverageRecord(
        artifact_id="native:sms_db",
        artifact_name="sms.db",
        category="Communications",
        parser_name="sms",
        parser_enabled=True,
        parser_status="PARSED",
        coverage_status="PRESENT_PARSED_WITH_RECORDS",
        file_present=True,
    )
    carrier = CoverageRecord(
        artifact_id="native:carrier_signaling",
        artifact_name="Carrier signaling records",
        category="System/diagnostic",
        coverage_status="OUTSIDE_STANDARD_BACKUP",
        file_present=False,
        examiner_note="carrier signaling",
    )
    silent = assess_finding_completeness(ctx, "silent_sms", [sms_ok, carrier], [])
    failed_sms = CoverageRecord(
        artifact_id="native:sms_db",
        artifact_name="sms.db",
        category="Communications",
        parser_name="sms",
        parser_enabled=True,
        parser_status="FAILED",
        coverage_status="PRESENT_PARSE_FAILED",
        file_present=True,
    )
    failed = assess_finding_completeness(ctx, "silent_sms", [failed_sms, carrier], [])
    whatsapp_app = AppCoverageRecord(app_name="net.whatsapp.WhatsApp", parser_available=False, likely_high_value_artifacts=["messaging"])
    normal = assess_finding_completeness(ctx, "normal_communications", [sms_ok], [whatsapp_app])
    silent_unrelated = assess_finding_completeness(ctx, "silent_sms", [sms_ok], [AppCoverageRecord(app_name="com.example.weather", parser_available=False)])
    voicemail = CoverageRecord(artifact_id="native:voicemail", artifact_name="voicemail", category="Communications", coverage_status="NOT_PRESENT", file_present=False)
    optional_gaps = build_examination_gaps([voicemail], [])
    outside = CoverageRecord(artifact_id="native:packet_capture_files", artifact_name="Packet capture files", category="System/diagnostic", coverage_status="OUTSIDE_STANDARD_BACKUP", file_present=False)
    not_collected = CoverageRecord(artifact_name="Carrier records", category="System/diagnostic", coverage_status="NOT_COLLECTED", file_present=False)
    out_scope = CoverageRecord(artifact_name="MDM logs", category="Security/configuration", coverage_status="OUTSIDE_ACQUISITION_SCOPE", file_present=False)
    recs = build_additional_evidence_recommendations([sms_ok, carrier], [], "silent_sms")
    qwen_payload_ok = bool(silent.supported_examination_status and silent.acquisition_sufficiency_status)
    distinct = {
        classify_coverage_disposition(voicemail, "encrypted_iphone_backup"),
        classify_coverage_disposition(not_collected, "encrypted_iphone_backup"),
        classify_coverage_disposition(out_scope, "encrypted_iphone_backup"),
        classify_coverage_disposition(outside, "encrypted_iphone_backup"),
    }
    return {
        "complete_sms_plus_unavailable_carrier_is_complete_for_supported_artifacts": silent.supported_examination_status == "COMPLETE_FOR_SUPPORTED_ARTIFACTS",
        "silent_sms_limited_by_acquisition_type": silent.acquisition_sufficiency_status == "LIMITED_BY_ACQUISITION_TYPE",
        "carrier_signaling_absence_not_examination_gap": not silent.examination_gaps,
        "failed_sms_parser_creates_examination_gap": failed.supported_examination_status == "EXAMINATION_GAPS_PRESENT",
        "unsupported_whatsapp_affects_normal_communications": bool(normal.examination_gaps),
        "unsupported_unrelated_app_does_not_affect_silent_sms": not silent_unrelated.examination_gaps,
        "optional_absent_artifact_not_examination_gap": not optional_gaps,
        "not_present_not_collected_outside_scope_outside_backup_distinct": len(distinct) == 4,
        "additional_evidence_recommendations_do_not_reduce_supported_parser_coverage": silent.supported_examination_status == "COMPLETE_FOR_SUPPORTED_ARTIFACTS" and bool(recs),
        "qwen_receives_separate_examination_and_acquisition_statuses": qwen_payload_ok,
        "can_be_complete_and_limited_simultaneously": silent.supported_examination_status == "COMPLETE_FOR_SUPPORTED_ARTIFACTS" and silent.acquisition_sufficiency_status == "LIMITED_BY_ACQUISITION_TYPE",
        "ordinary_encrypted_backup_limits_not_unexpected_missing": all("unexpected" not in item.lower() for item in silent.acquisition_limitations),
    }


def deterministic_attachment_linking_tests() -> Dict[str, bool]:
    base_ts = datetime(2026, 6, 25, 16, 49, 4)
    parent = Event(
        base_ts,
        "sms.db",
        "SMS/iMessage/RCS record",
        "REVIEW",
        "TO_DEVICE | contact=Jane | rowid=51775 | text=<NO TEXT CONTENT>",
        {
            "rowid": 51775,
            "guid": "p-guid",
            "direction": "TO_DEVICE",
            "raw_contact": "+1 (704) 352-9820",
            "resolved_contact": "Jane",
            "chat_identifier": "chat-1",
            "service": "iMessage",
        },
    )
    attachment = Event(
        base_ts,
        "sms.db attachment",
        "Message attachment metadata",
        "REVIEW",
        "message_rowid=51775 | filename=~/Library/SMS/Attachments/IMG_9566.PNG | mime=image/png | bytes=418490",
        {
            "message_rowid": 51775,
            "attachment_rowid": 9,
            "filename": "~/Library/SMS/Attachments/IMG_9566.PNG",
            "transfer_name": "IMG_9566.PNG",
            "mime_type": "image/png",
            "total_bytes": 418490,
            "guid": "a-guid",
            "filesystem_status": "NOT_FOUND_IN_DECRYPTED_BACKUP_PATHS",
            "attachment_event_timestamp_basis": "parent message timestamp",
            "parent_message_timestamp": format_dt(base_ts),
        },
    )
    duplicate = Event(base_ts, attachment.source, attachment.event_type, attachment.significance, attachment.details, dict(attachment.metadata))
    same_name_other_message = Event(
        base_ts,
        "sms.db attachment",
        "Message attachment metadata",
        "REVIEW",
        "message_rowid=999 | filename=~/Library/SMS/Attachments/IMG_9566.PNG",
        dict(attachment.metadata, message_rowid=999, attachment_rowid=10, guid="other-guid"),
    )
    outgoing_parent = Event(base_ts, "sms.db", "SMS/iMessage/RCS record", "REVIEW", "FROM_DEVICE | rowid=1", {"rowid": 1, "direction": "FROM_DEVICE"})
    incoming_parent = Event(base_ts, "sms.db", "SMS/iMessage/RCS record", "REVIEW", "TO_DEVICE | rowid=2", {"rowid": 2, "direction": "TO_DEVICE"})
    unknown_parent = Event(base_ts, "sms.db", "SMS/iMessage/RCS record", "REVIEW", "UNKNOWN | rowid=3", {"rowid": 3, "direction": ""})
    events = [parent, attachment, duplicate, same_name_other_message, outgoing_parent, incoming_parent, unknown_parent]
    index = link_message_attachments(events)
    for event in events:
        event.apply_confidence()
    buf = io.StringIO()
    write_event_attachment_details(buf, parent, index)
    rendered = buf.getvalue()
    ctx = CaseContext(Path("synthetic_case"), datetime(2026, 6, 25, 16, 25), datetime(2026, 6, 25, 16, 58), 30)
    clusters = build_single_report_clusters(ctx, [parent, attachment])
    knowledge = build_case_knowledge(ctx, [parent, attachment], clusters, [], [], [])
    parent_json = next((item for item in knowledge["events"] if item["source"] == "sms.db"), {})
    attachment_json = next((item for item in knowledge["events"] if item["source"] == "sms.db attachment"), {})
    rel_types_in = {
        direction_attachment_relationship("FROM_DEVICE"),
        direction_attachment_relationship("TO_DEVICE"),
        direction_attachment_relationship(""),
    }
    attachment_links = attachment.metadata.get("normalized_entity_links", [])
    shared_parent_entities = [
        link for link in attachment_links
        if isinstance(link, dict) and link.get("provenance") == "message_attachment_join"
    ]
    return {
        "attachment_index_uses_message_rowid": index.get("51775", [None])[0] is attachment,
        "parent_message_displays_attachment_filename": "IMG_9566.PNG" in rendered,
        "parent_message_no_longer_says_no_attachment_metadata": "No attachment metadata normalized for this event" not in rendered and "No attachment metadata was identified for this event" not in rendered,
        "multiple_attachments_can_display": "Linked attachment count: 1" in rendered,
        "duplicate_attachment_suppressed_under_parent": len(index.get("51775", [])) == 1,
        "outgoing_parent_creates_sent_attachment": "SENT_ATTACHMENT" in rel_types_in,
        "incoming_parent_creates_received_attachment": "RECEIVED_ATTACHMENT" in rel_types_in,
        "unknown_direction_creates_included_attachment": "INCLUDED_ATTACHMENT" in rel_types_in,
        "attachment_event_inherits_parent_entities": len(shared_parent_entities) >= 3,
        "attachment_correlation_can_share_parent_entities": any(link.get("role") == "conversation" for link in shared_parent_entities if isinstance(link, dict)),
        "same_filename_different_message_not_linked": len(index.get("999", [])) == 1 and index["999"][0] is same_name_other_message,
        "linking_uses_message_rowid_not_timestamp": same_name_other_message not in index.get("51775", []),
        "missing_filesystem_file_still_displays_database_metadata": "NOT_FOUND_IN_DECRYPTED_BACKUP_PATHS" in rendered and "418,490 bytes" in rendered,
        "missing_sha256_does_not_suppress_attachment": "IMG_9566.PNG" in rendered,
        "case_knowledge_has_bidirectional_links": bool(parent_json.get("attachments")) and attachment_json.get("parent_message_event_id") == parent_json.get("event_id"),
    }


def deterministic_reporting_pipeline_tests() -> Dict[str, bool]:
    with tempfile.TemporaryDirectory() as tmp:
        case_dir = Path(tmp) / "case"
        dec = case_dir / "decrypted"
        dec.mkdir(parents=True, exist_ok=True)
        info = {
            "Device Name": "Test iPhone",
            "Product Type": "iPhone16,1",
            "Product Version": "18.5",
            "Build Version": "22F76",
            "Serial Number": "SER123",
            "Unique Identifier": "UDID123",
            "Phone Number": "+17045550123",
            "ICCID": "8901",
            "IMEI": "123456789012345",
            "Last Backup Date": "2026-06-25 16:00:00",
            "Is Encrypted": True,
        }
        with (dec / "Info.plist").open("wb") as f:
            plistlib.dump(info, f)
        ctx = CaseContext(case_dir, datetime(2026, 6, 25, 16, 25), datetime(2026, 6, 25, 16, 58), 30)
        ctx.case_name = "synthetic"
        incoming_call = Event(datetime(2026, 6, 25, 16, 30), "CallHistory", "Call record", "REVIEW", "INCOMING call", {"direction": "INCOMING", "resolved_contact": "Nadia", "location_label": "Charlotte, NC"})
        outgoing_call = Event(datetime(2026, 6, 25, 16, 31), "CallHistory", "Call record", "REVIEW", "OUTGOING call", {"direction": "OUTGOING", "resolved_contact": "Nadia"})
        incoming_msg = Event(datetime(2026, 6, 25, 16, 32), "sms.db", "SMS/iMessage/RCS record", "REVIEW", "TO_DEVICE message", {"direction": "TO_DEVICE", "raw_contact": "+17045550123", "rowid": 1})
        records = [
            CoverageRecord(artifact_name=f"unsupported_{i}.db", category="Third-party app", file_type="sqlite", coverage_status="PRESENT_UNSUPPORTED", file_present=True, relative_path=f"App/{i}.db")
            for i in range(40)
        ]
        records.append(CoverageRecord(artifact_name="sms.db", category="Communications", file_type="sqlite", parser_enabled=True, parser_status="PARSED", coverage_status="PRESENT_PARSED_WITH_RECORDS", file_present=True))
        app_records = [AppCoverageRecord(app_name="com.example.chat", parser_available=False, likely_high_value_artifacts=["messaging"])]
        hypotheses = [{"hypothesis": "silent_sms", "confidence_in_assessment": "LOW", "supported_examination_status": "COMPLETE_FOR_SUPPORTED_ARTIFACTS", "acquisition_sufficiency_status": "LIMITED_BY_ACQUISITION_TYPE", "basis": "Synthetic test basis."}]
        device = extract_device_metadata(ctx)
        client = case_dir / "reports" / "report_client.md"
        appendix = case_dir / "reports" / "report_technical_appendix.md"
        case_dir.joinpath("reports").mkdir(exist_ok=True)
        write_client_report(client, ctx, device, [incoming_call, outgoing_call, incoming_msg], records, app_records, hypotheses, [])
        with appendix.open("w", encoding="utf-8") as handle:
            handle.write("# Window Investigator Technical Appendix\n\n")
            handle.write("## Unsupported Artifact Summary\n\n")
            write_unsupported_summary_table(handle, unsupported_artifact_summaries(records, app_records))
            handle.write("## Full filename-level inventory\n\n")
            for record in records:
                handle.write(
                    f"- {record.artifact_name} | {record.relative_path} | {record.coverage_status} | "
                    f"category={record.category} | parser={record.parser_name or 'none'} | "
                    "technical appendix retains filename-level detail for examiner review and does not appear in the client summary.\n"
                )
        client_text = client.read_text(encoding="utf-8")
        appendix_text = appendix.read_text(encoding="utf-8")
        missing_ctx = CaseContext(Path(tmp) / "missing", ctx.start, ctx.end, 5)
        missing_device = extract_device_metadata(missing_ctx)
        return {
            "device_name_extracted_from_backup_metadata": device["device"]["device_name"] == "Test iPhone",
            "missing_device_metadata_handled": missing_device["device"]["device_name"] is None,
            "incoming_calls_described_correctly": "Nadia called the examined iPhone" in event_direction_sentence(incoming_call),
            "outgoing_calls_described_correctly": "examined iPhone called Nadia" in event_direction_sentence(outgoing_call),
            "message_direction_described_correctly": "sent a message to the examined iPhone" in event_direction_sentence(incoming_msg),
            "unsupported_artifacts_summarized_in_main_report": "unsupported_39.db" not in client_text,
            "full_unsupported_inventory_available_in_appendix_or_csv": "Unsupported Artifact Summary" in appendix_text,
            "coverage_percentages_not_prominent_in_main_report": "%" not in client_text,
            "confidence_wording_uses_maximum_supportable_confidence": "Maximum supportable confidence from the available evidence" in client_text,
            "client_report_substantially_shorter_than_appendix": len(client_text) < len(appendix_text),
            "no_unsupported_conclusion_generated": "No Silent SMS occurred" not in client_text and "confirmed Silent SMS" not in client_text,
        }


def build_forensic_blind_spots(records: List[CoverageRecord], app_records: List[AppCoverageRecord]) -> List[Dict[str, Any]]:
    blind_spots = []
    for record in records:
        disposition = classify_coverage_disposition(record, "encrypted_iphone_backup")
        if disposition in {"EXAMINATION_FAILURE", "PARTIALLY_EXAMINED", "PRESENT_UNSUPPORTED", "EXPECTED_BUT_NOT_PRESENT", "OUTSIDE_STANDARD_ACQUISITION", "NOT_SEPARATELY_COLLECTED"}:
            blind_type = "Examination Blind Spots"
            if disposition == "OUTSIDE_STANDARD_ACQUISITION":
                blind_type = "Acquisition-Type Blind Spots"
            elif disposition == "NOT_SEPARATELY_COLLECTED":
                blind_type = "External Evidence Not Collected"
            elif "deleted" in coverage_record_text(record) or "volatile" in coverage_record_text(record) or record.deleted_record_recovery_supported:
                blind_type = "Deleted and Volatile Data Limitations"
            blind_spots.append(
                {
                    "source": record.artifact_name,
                    "category": record.category,
                    "coverage_status": record.coverage_status,
                    "blind_spot_type": blind_type,
                    "disposition": disposition,
                    "severity": blind_spot_severity(record),
                    "basis": coverage_limitation(record) if "coverage_limitation" in globals() else record.examiner_note,
                }
            )
    for app in app_records:
        if not app.parser_available:
            blind_spots.append(
                {
                    "source": f"Application container: {app.app_name}",
                    "category": "Third-party app",
                    "coverage_status": app.parser_status,
                    "blind_spot_type": "Examination Blind Spots",
                    "disposition": "PRESENT_UNSUPPORTED",
                    "severity": "HIGH" if app.likely_high_value_artifacts else "MEDIUM",
                    "basis": "Application container was present but no parser is available; presence is not activity.",
                }
            )
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return sorted(blind_spots, key=lambda item: (order.get(item["severity"], 9), item["source"]))[:200]


def blind_spot_severity(record: CoverageRecord) -> str:
    weight = artifact_weight(record)
    if record.coverage_status in {"NOT_COLLECTED", "PRESENT_PARSE_FAILED"} and weight >= 8:
        return "CRITICAL"
    if weight >= 8:
        return "HIGH"
    if weight >= 5:
        return "MEDIUM"
    return "LOW"


def build_additional_evidence_recommendations(
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    relevant_finding: Optional[str] = None,
) -> List[Dict[str, Any]]:
    recommendations = []
    names = " ".join(record.artifact_name.lower() + " " + record.coverage_status.lower() for record in records)
    if relevant_finding in {None, "silent_sms", "network_activity", "unusual_network_transmission"} and ("sysdiagnose" in names or "commcenter" in names or "coretelephony" in names or "packet capture" in names or relevant_finding in {"silent_sms", "network_activity", "unusual_network_transmission"}):
        recommendations.append(
            {
                "priority": "CRITICAL",
                "recommendation": "Obtain carrier signaling records, sysdiagnose/baseband diagnostics, CommCenter/CoreTelephony operational logs, or packet/network telemetry for Silent SMS or network-transport questions.",
                "basis": "This supplemental evidence could increase confidence; its absence is an acquisition limitation or not-collected source, not automatically a parser failure.",
            }
        )
    if relevant_finding in {"command_activity", "malware_or_compromise"}:
        recommendations.append(
            {
                "priority": "CRITICAL",
                "recommendation": "Obtain MDM/security logs, full filesystem or sysdiagnose material where lawful and available, and associated computer evidence for command-activity or compromise questions.",
                "basis": "Execution, persistence, volatile, and full diagnostic evidence may be outside a standard backup.",
            }
        )
    if any(record.wal_present for record in records):
        recommendations.append(
            {
                "priority": "HIGH",
                "recommendation": "Perform specialized SQLite WAL/deleted-record recovery where legally and technically appropriate.",
                "basis": "WAL/SHM material was present; standard parsing does not recover all deleted records.",
            }
        )
    if any(not app.parser_available for app in app_records):
        recommendations.append(
            {
                "priority": "HIGH",
                "recommendation": "Apply dedicated third-party app parsers for present unsupported app containers.",
                "basis": "Third-party containers may contain relevant communications or cloud activity but presence alone does not indicate use.",
            }
        )
    if any(record.coverage_status == "PRESENT_UNKNOWN_SCHEMA" for record in records):
        recommendations.append(
            {
                "priority": "MEDIUM",
                "recommendation": "Review unknown SQLite schemas manually and add parser support for relevant tables.",
                "basis": "Unknown schemas were inventoried but not normalized as evidence.",
            }
        )
    if any(record.artifact_name.startswith("Manifest.db") and record.coverage_status == "NOT_COLLECTED" for record in records):
        recommendations.append(
            {
                "priority": "MEDIUM",
                "recommendation": "Acquire or preserve original iTunes backup manifest files for logical-domain validation.",
                "basis": "Manifest-based coverage validation was unavailable.",
            }
        )
    return recommendations


def assess_finding_confidence(
    ctx: CaseContext,
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    events: List[Event],
) -> List[FindingConfidenceResult]:
    score = build_evidence_coverage_score(ctx, records, app_records, events)
    network_direct = [
        event for event in events
        if event.source == "Data Usage" or event.metadata.get("remote_ip") or "packet" in event.event_type.lower() or "session" in event.event_type.lower()
    ]
    results = []
    for finding_id, name in (
        ("silent_sms", "Silent SMS assessment"),
        ("malware_or_compromise", "Malware or compromise absence assessment"),
        ("unusual_network_transmission", "Unusual network transmission assessment"),
        ("normal_communications", "Normal communications assessment"),
    ):
        ceiling = "HIGH"
        reason = "No deterministic ceiling applied."
        supporting = 0
        relevant_records = relevant_artifacts_for_finding(finding_id, records)
        relevant_blind_spots = build_forensic_blind_spots(relevant_records, [])
        material_gap_count = len([spot for spot in relevant_blind_spots if spot["severity"] in {"CRITICAL", "HIGH"}])
        if finding_id == "silent_sms":
            telephony_ok = any(r.parser_name == "cellular_telephony" and coverage_multiplier(r) >= 0.9 for r in relevant_records)
            if not telephony_ok or any("sysdiagnose" in spot["source"].lower() or "commcenter" in spot["source"].lower() or "coretelephony" in spot["source"].lower() for spot in relevant_blind_spots):
                ceiling = "LOW"
                reason = "Carrier signaling, baseband, sysdiagnose, CommCenter, or CoreTelephony operational evidence is unavailable or incomplete."
            else:
                ceiling = "MODERATE"
                reason = "Relevant handset/telephony artifacts were parsed without material failures; standard backup still cannot produce HIGH confidence for Silent SMS."
        elif finding_id == "malware_or_compromise":
            ceiling = "LOW" if material_gap_count else "MODERATE"
            reason = "A standard backup and supported parsers cannot provide HIGH confidence that compromise did not occur."
        elif finding_id == "unusual_network_transmission":
            supporting = len(network_direct)
            ceiling = "HIGH" if network_direct else "LOW"
            reason = "HIGH requires explicit session, packet, or valid byte-delta evidence; configuration and paired-device records are insufficient."
        elif finding_id == "normal_communications":
            supporting = len([e for e in events if e.source in {"sms.db", "CallHistory", "sms.db attachment"}])
            relevant_percent = weighted_percent(relevant_records)
            ceiling = "HIGH" if relevant_percent >= 75 else "MODERATE"
            reason = "Confidence depends on supported communications artifact coverage."
        coverage_level = weighted_percent(relevant_records)
        confidence = min_confidence(ceiling, "MODERATE" if material_gap_count else "HIGH")
        results.append(
            FindingConfidenceResult(
                finding_id=finding_id,
                finding_name=name,
                confidence_level=confidence,
                coverage_level=f"{coverage_level:.2f}%",
                deterministic_basis=reason,
                supporting_evidence_count=supporting,
                material_gap_count=material_gap_count,
                confidence_ceiling=ceiling,
                cannot_exceed_reason=reason,
            )
        )
    return results


def relevant_artifacts_for_finding(finding_id: str, records: List[CoverageRecord]) -> List[CoverageRecord]:
    tokens_by_finding = {
        "silent_sms": ("sms", "cellular", "telephony", "commcenter", "coretelephony", "sysdiagnose", "carrier", "baseband"),
        "normal_communications": ("sms", "callhistory", "facetime", "whatsapp", "signal", "telegram", "messenger"),
        "network_activity": ("wi-fi", "wifi", "bluetooth", "cellular", "vpn", "data usage", "airdrop", "nearby", "network"),
        "unusual_network_transmission": ("data usage", "packet", "session", "vpn", "carrier", "router", "cellular", "remote endpoint", "network"),
        "command_activity": ("execution", "process", "remote access", "persistence", "profile", "mdm", "device management", "diagnostic", "security", "analytics", "system"),
        "malware_or_compromise": ("profile", "mdm", "security", "diagnostic", "analytics", "crash", "sysdiagnose", "filesystem", "installed", "trust", "persistence", "execution"),
    }
    tokens = tokens_by_finding.get(finding_id, (finding_id,))
    relevant = []
    for record in records:
        hay = (record.artifact_name + " " + record.category + " " + record.parser_name + " " + record.examiner_note).lower()
        if any(token in hay for token in tokens):
            relevant.append(record)
    return relevant


def assess_finding_completeness(
    ctx: CaseContext,
    finding_id: str,
    coverage_records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
) -> FindingCompletenessResult:
    relevant_records = relevant_artifacts_for_finding(finding_id, coverage_records)
    examined: List[str] = []
    partial: List[str] = []
    for record in relevant_records:
        disposition = classify_coverage_disposition(record, "encrypted_iphone_backup")
        if disposition == "SUCCESSFULLY_EXAMINED":
            examined.append(record.artifact_name)
        elif disposition == "PARTIALLY_EXAMINED":
            partial.append(record.artifact_name)
    examination_gaps = build_examination_gaps(relevant_records, app_records, finding_id)
    acquisition_limitations = build_acquisition_limitations(relevant_records, "encrypted_iphone_backup", finding_id)
    not_collected = build_not_collected_sources(relevant_records, finding_id)
    recommendations = [
        item["recommendation"]
        for item in build_additional_evidence_recommendations(relevant_records, app_records, finding_id)
    ]
    if any(classify_coverage_disposition(record, "encrypted_iphone_backup") == "EXAMINATION_FAILURE" for record in relevant_records):
        supported_status = "EXAMINATION_GAPS_PRESENT"
    elif examination_gaps:
        supported_status = "PARTIAL_SUPPORTED_COVERAGE"
    elif relevant_records:
        supported_status = "COMPLETE_FOR_SUPPORTED_ARTIFACTS"
    else:
        supported_status = "UNKNOWN"
    if finding_id in {"silent_sms", "unusual_network_transmission", "command_activity", "malware_or_compromise"} and acquisition_limitations:
        acquisition_status = "LIMITED_BY_ACQUISITION_TYPE"
    elif not_collected:
        acquisition_status = "REQUIRED_SOURCE_NOT_COLLECTED"
    elif examination_gaps:
        acquisition_status = "PARTIALLY_SUFFICIENT"
    elif relevant_records:
        acquisition_status = "SUFFICIENT_FOR_QUESTION"
    else:
        acquisition_status = "UNKNOWN"
    examiner_confidence = "HIGH" if supported_status == "COMPLETE_FOR_SUPPORTED_ARTIFACTS" else "MEDIUM" if supported_status == "PARTIAL_SUPPORTED_COVERAGE" else "LOW"
    if acquisition_status in {"LIMITED_BY_ACQUISITION_TYPE", "REQUIRED_SOURCE_NOT_COLLECTED"} and examiner_confidence == "HIGH":
        examiner_confidence = "MODERATE"
    basis = (
        "Completeness separates examination of supplied supported artifacts from whether the acquisition type "
        "contains all evidence needed for the finding."
    )
    return FindingCompletenessResult(
        finding_id=finding_id,
        supported_examination_status=supported_status,
        acquisition_sufficiency_status=acquisition_status,
        relevant_artifacts_examined=sorted(set(examined)),
        relevant_artifacts_partially_examined=sorted(set(partial)),
        examination_gaps=examination_gaps,
        acquisition_limitations=acquisition_limitations,
        evidence_not_collected=not_collected,
        supplemental_evidence_recommended=sorted(set(recommendations)),
        completeness_basis=basis,
        examiner_confidence_in_examination=examiner_confidence,
    )


def min_confidence(a: str, b: str) -> str:
    order = {"LOW": 0, "MODERATE": 1, "MEDIUM": 1, "HIGH": 2}
    reverse = {0: "LOW", 1: "MODERATE", 2: "HIGH"}
    return reverse[min(order.get(a, 0), order.get(b, 0))]


def coverage_aware_absence_statement(
    artifact_category: str,
    query_or_hypothesis: str,
    coverage_records: List[CoverageRecord],
) -> str:
    relevant = [
        record for record in coverage_records
        if artifact_category.lower() in (record.category + " " + record.artifact_name + " " + record.parser_name).lower()
    ]
    if not relevant:
        return f"The expected artifact category for {query_or_hypothesis} was not present or not identified in the supplied acquisition."
    if any(r.coverage_status == "PRESENT_PARSED_WITH_RECORDS" for r in relevant):
        return f"Relevant records were identified in parsed {artifact_category} artifacts for {query_or_hypothesis}."
    if all(r.coverage_status in {"PRESENT_PARSED_ZERO_RECORDS", "PRESENT_PARSED_NO_WINDOW_RECORDS"} for r in relevant):
        if any(r.coverage_status == "PRESENT_PARSED_NO_WINDOW_RECORDS" for r in relevant):
            return "The database parsed successfully and contained records outside the requested window, but no supported records were identified within the requested window."
        return f"No relevant records were identified in the parsed {artifact_category} artifacts for the requested window."
    if any(r.coverage_status == "PRESENT_UNSUPPORTED" for r in relevant):
        return f"No conclusion can be reached regarding {query_or_hypothesis} because at least one relevant {artifact_category} artifact was present but unsupported by the current tool."
    if any(r.coverage_status == "PRESENT_PARSE_FAILED" for r in relevant):
        return f"No conclusion can be reached regarding {query_or_hypothesis} because at least one relevant {artifact_category} artifact was present but the parser failed."
    if any(r.coverage_status == "PRESENT_ONLY_WAL_SHM" or r.wal_present for r in relevant):
        return "Related WAL material was present; however, no specialized deleted-record recovery was performed."
    if all(r.coverage_status == "NOT_PRESENT" for r in relevant):
        return "The expected artifact was not present in the supplied acquisition."
    return f"Coverage for {query_or_hypothesis} is incomplete; distinguish absent, unsupported, failed, and outside-window states before drawing a negative conclusion."


class WifiPlugin(ArtifactPlugin):
    name = "wifi"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        files = ctx.find_named(
            [
                "com.apple.wifi.plist",
                "com.apple.wifi.known-networks.plist",
                "com.apple.wifi.known-networks.plist.backup",
                "com.apple.wifi-networks.plist",
                "com.apple.network.identification.plist",
                "com.apple.preferences.plist",
            ]
        )
        files.extend(plist_files_for_tokens(ctx, ("wifi", "wi-fi", "wirelessdomain", "networkd")))
        for path in sorted(set(files), key=str)[:200]:
            data = plist_load(path)
            if data is None:
                events.extend(filesystem_network_event(ctx, path, "Wi-Fi", "Wi-Fi filesystem timestamp", "wifi plist unreadable or unsupported"))
                continue
            produced = 0
            for record in walk_structured_records(data):
                ssid = record_value(record, ("SSID", "ssid", "SSID_STR", "networkName", "Name"))
                bssid = normalize_mac(record_value(record, ("BSSID", "bssid", "Bssid")))
                security = record_value(record, ("SecurityType", "security", "wifi_security", "EncryptionType"))
                if not (ssid or bssid or security or record_value(record, ("lastJoined", "lastConnected", "lastSeen", "IPAddress", "Router", "DNS"))):
                    continue
                ts, basis_key = record_timestamp(record)
                ips = extract_valid_ips(record)
                domains = extract_domains(record)
                event_type = "Wi-Fi connection-state record" if ts else "Wi-Fi known network record"
                details = (
                    f"recorded network configuration | ssid={ssid or ''} | bssid={bssid or ''} "
                    f"(Wi-Fi access point MAC when present) | security={security or ''} | timestamp_basis={basis_key or 'none'}"
                )
                metadata = {
                    "interface_type": "wifi",
                    "interface_name": str(record_value(record, ("InterfaceName", "interface", "ifname")) or ""),
                    "ssid": str(ssid or ""),
                    "bssid": bssid,
                    "wifi_security": str(security or ""),
                    "local_ip": ips[0] if ips else "",
                    "hostname": str(record_value(record, ("Hostname", "hostName")) or ""),
                    "domain": domains[0] if domains else "",
                    "connection_state": str(record_value(record, ("State", "AutoJoin", "Captive", "Joined")) or ""),
                    "first_seen": format_dt(timestamp_from_any(record_value(record, ("firstJoined", "FirstJoined", "created")))),
                    "last_seen": format_dt(ts),
                    "source_artifact": short_path(path, ctx.case_dir),
                    "raw_record_identifier": str(record.get("_record_path") or ""),
                    "timestamp_basis": basis_key or "structured configuration without timestamp",
                    "timestamp_reliability": "structured_record" if ts else "configuration_only",
                    "raw": redact_sensitive_record(record),
                }
                events.append(
                    network_event(
                        ts,
                        "Wi-Fi",
                        event_type,
                        "INFO" if ts and in_range(ts, ctx.start, ctx.end) else "LOW",
                        details,
                        metadata,
                        80 if ts else 60,
                        "Structured Wi-Fi artifact with timestamp" if ts else "Structured Wi-Fi configuration without usage timestamp",
                        "DIRECT" if ts else "HEURISTIC",
                    )
                )
                produced += 1
            if not produced:
                events.extend(filesystem_network_event(ctx, path, "Wi-Fi", "Wi-Fi configuration artifact", "structured file present; no timestamped use record identified"))
        return events


class BluetoothPlugin(ArtifactPlugin):
    name = "bluetooth_network"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        files = ctx.find_named(["com.apple.MobileBluetooth.devices.plist", "com.apple.MobileBluetooth.plist", "com.apple.Bluetooth.plist"])
        files.extend(plist_files_for_tokens(ctx, ("bluetooth", "bluetoothd", "systemgroup.com.apple.bluetooth", "airpods", "beats")))
        for path in sorted(set(files), key=str)[:200]:
            data = plist_load(path)
            if data is None:
                events.extend(filesystem_network_event(ctx, path, "Bluetooth", "Bluetooth filesystem timestamp", "Bluetooth artifact unreadable or unsupported"))
                continue
            produced = 0
            for record in walk_structured_records(data):
                name = record_value(record, ("Name", "DeviceName", "displayName", "name"))
                address = normalize_mac(record_value(record, ("Address", "BD_ADDR", "BluetoothAddress", "DeviceAddress", "MAC")))
                identifier = record_value(record, ("Identifier", "UUID", "DeviceID", "id"))
                if not (name or address or identifier or record_value(record, ("Connected", "Paired", "Trusted", "LastSeen"))):
                    continue
                ts, basis_key = record_timestamp(record)
                connected = record_value(record, ("Connected", "connected", "isConnected", "ConnectionState"))
                paired = record_value(record, ("Paired", "paired", "Trusted", "trusted"))
                event_type = "Bluetooth connection-state record" if ts and connected not in (None, "", False, 0) else "Bluetooth paired device record"
                details = (
                    f"recorded Bluetooth artifact | name={name or ''} | address={address or ''} | "
                    f"identifier={identifier or ''} | paired_or_trusted={paired or ''} | connected_state={connected or ''}"
                )
                metadata = {
                    "interface_type": "bluetooth",
                    "bluetooth_name": str(name or ""),
                    "bluetooth_address": address,
                    "bluetooth_identifier": str(identifier or ""),
                    "device_class": str(record_value(record, ("ClassOfDevice", "DeviceClass", "class")) or ""),
                    "connection_state": str(connected if connected is not None else paired if paired is not None else ""),
                    "first_seen": format_dt(timestamp_from_any(record_value(record, ("FirstPaired", "firstPaired", "Created")))),
                    "last_seen": format_dt(ts),
                    "source_artifact": short_path(path, ctx.case_dir),
                    "raw_record_identifier": str(record.get("_record_path") or ""),
                    "timestamp_basis": basis_key or "paired/configuration record without timestamp",
                    "timestamp_reliability": "structured_record" if ts else "configuration_only",
                    "raw": redact_sensitive_record(record),
                }
                events.append(
                    network_event(
                        ts,
                        "Bluetooth",
                        event_type,
                        "INFO" if ts and in_range(ts, ctx.start, ctx.end) else "LOW",
                        details,
                        metadata,
                        80 if ts else 60,
                        "Structured Bluetooth state record" if ts else "Bluetooth paired/configuration record without confirmed connection timestamp",
                        "DIRECT" if ts and "connection" in event_type.lower() else "HEURISTIC",
                    )
                )
                produced += 1
            if not produced:
                events.extend(filesystem_network_event(ctx, path, "Bluetooth", "Bluetooth filesystem timestamp", "Bluetooth artifact present; no confirmed connection-state record identified"))
        return events


class AirDropNearbyPlugin(ArtifactPlugin):
    name = "airdrop_nearby"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        tokens = ("airdrop", "sharingd", "sharesheet", "nearbyd", "nearby", "proximity", "continuity", "handoff", "activitycontinuation", "com.apple.sharing")
        files = plist_files_for_tokens(ctx, tokens)
        for path in sorted(set(files), key=str)[:200]:
            data = plist_load(path)
            if data is None:
                events.extend(filesystem_network_event(ctx, path, "AirDrop/Nearby", "Nearby filesystem artifact", "nearby/AirDrop artifact unreadable or unsupported"))
                continue
            produced = 0
            for record in walk_structured_records(data):
                joined = json_dumps(record).lower()
                if not any(token in joined for token in ("airdrop", "nearby", "handoff", "continuity", "sharing", "peer", "transfer")):
                    continue
                ts, basis_key = record_timestamp(record)
                filename = record_value(record, ("Filename", "FileName", "fileName", "TransferName"))
                peer = record_value(record, ("PeerID", "peerIdentifier", "DeviceName", "Sender", "Recipient"))
                status = record_value(record, ("Status", "TransferStatus", "accepted", "rejected", "failed"))
                if not (ts or filename or peer or status):
                    continue
                if "airdrop" in joined and filename:
                    event_type = "AirDrop transfer record"
                elif "handoff" in joined or "continuity" in joined:
                    event_type = "Handoff/Continuity record"
                else:
                    event_type = "Nearby peer record"
                metadata = {
                    "interface_type": "awdl/nearby",
                    "hostname": str(peer or ""),
                    "connection_state": str(status or ""),
                    "source_artifact": short_path(path, ctx.case_dir),
                    "raw_record_identifier": str(record.get("_record_path") or ""),
                    "timestamp_basis": basis_key or "structured nearby record without timestamp",
                    "timestamp_reliability": "structured_record" if ts else "configuration_only",
                    "filename": str(filename or ""),
                    "raw": redact_sensitive_record(record),
                }
                details = f"{event_type} | peer={peer or ''} | filename={filename or ''} | status={status or ''} | timestamp_basis={basis_key or 'none'}"
                events.append(network_event(ts, "AirDrop/Nearby", event_type, "INFO" if ts and in_range(ts, ctx.start, ctx.end) else "LOW", details, metadata, 85 if ts else 50, "Structured nearby/AirDrop content" if ts else "Structured nearby artifact without timestamped transfer", "DIRECT" if ts else "HEURISTIC"))
                produced += 1
            if not produced:
                events.extend(filesystem_network_event(ctx, path, "AirDrop/Nearby", "Nearby filesystem artifact", "path/content artifact present; not proof of AirDrop use"))
        return events


class NetworkConfigurationPlugin(ArtifactPlugin):
    name = "network_configuration"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        tokens = ("networkextension", "vpn", "neconfiguration", "systemconfiguration", "proxy", "dhcp", "dns", "hotspot", "tethering", "networkd")
        files = plist_files_for_tokens(ctx, tokens)
        for path in sorted(set(files), key=str)[:250]:
            data = plist_load(path)
            if data is None:
                continue
            produced = 0
            for record in walk_structured_records(data):
                blob = json_dumps(record).lower()
                if not any(token in blob for token in ("vpn", "proxy", "dns", "dhcp", "ipv4", "ipv6", "router", "gateway", "hotspot", "tether")):
                    continue
                ts, basis_key = record_timestamp(record)
                ips = extract_valid_ips(record)
                domains = extract_domains(record)
                event_type = "VPN configuration" if "vpn" in blob else "Network interface configuration"
                if "proxy" in blob:
                    event_type = "Proxy configuration"
                if "dns" in blob:
                    event_type = "DNS configuration"
                if "dhcp" in blob:
                    event_type = "DHCP configuration"
                metadata = {
                    "interface_type": str(record_value(record, ("InterfaceType", "type", "service")) or ""),
                    "interface_name": str(record_value(record, ("InterfaceName", "ifname", "DeviceName")) or ""),
                    "local_ip": ips[0] if ips else "",
                    "hostname": str(record_value(record, ("Hostname", "ServerAddress", "RemoteAddress")) or ""),
                    "domain": domains[0] if domains else "",
                    "connection_state": str(record_value(record, ("Enabled", "Status", "State")) or ""),
                    "source_artifact": short_path(path, ctx.case_dir),
                    "raw_record_identifier": str(record.get("_record_path") or ""),
                    "timestamp_basis": basis_key or "configuration record",
                    "timestamp_reliability": "structured_record" if ts else "configuration_only",
                    "raw": redact_sensitive_record(record),
                }
                details = f"{event_type} | ips={ips[:5]} | domains={domains[:5]} | timestamp_basis={basis_key or 'configuration only'}"
                events.append(network_event(ts, "Network Configuration", event_type, "INFO" if ts and in_range(ts, ctx.start, ctx.end) else "LOW", details, metadata, 80 if ts else 60, "Structured network configuration artifact", "DIRECT" if ts else "HEURISTIC"))
                produced += 1
            if not produced and any(token in str(path).lower() for token in ("vpn", "network", "dhcp", "dns")):
                events.extend(filesystem_network_event(ctx, path, "Network Configuration", "Network configuration filesystem artifact", "configuration artifact present; no active-use record identified"))
        return events


class CellularTelephonyPlugin(ArtifactPlugin):
    name = "cellular_telephony"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        tokens = ("commcenter", "coretelephony", "baseband", "carrier", "ims", "cellular", "applebasebandmanager")
        files = plist_files_for_tokens(ctx, tokens)
        for path in sorted(set(files), key=str)[:250]:
            data = plist_load(path)
            if data is None:
                events.extend(filesystem_network_event(ctx, path, "Cellular/Telephony", "Telephony filesystem timestamp", "telephony artifact present; not proof of activity"))
                continue
            produced = 0
            for record in walk_structured_records(data):
                blob = json_dumps(record).lower()
                if not any(token in blob for token in ("carrier", "mcc", "mnc", "ims", "lte", "5g", "umts", "gsm", "registration", "sim", "cell")):
                    continue
                ts, basis_key = record_timestamp(record)
                carrier = record_value(record, ("CarrierName", "carrier", "OperatorName"))
                state = record_value(record, ("RegistrationState", "IMSRegistrationState", "RadioAccessTechnology", "RAT", "State"))
                details = f"cellular/telephony artifact | carrier={carrier or ''} | state={state or ''} | timestamp_basis={basis_key or 'configuration only'}"
                metadata = {
                    "interface_type": "cellular",
                    "protocol": str(record_value(record, ("RadioAccessTechnology", "RAT", "AccessTechnology")) or ""),
                    "connection_state": str(state or ""),
                    "hostname": str(carrier or ""),
                    "source_artifact": short_path(path, ctx.case_dir),
                    "raw_record_identifier": str(record.get("_record_path") or ""),
                    "timestamp_basis": basis_key or "configuration record",
                    "timestamp_reliability": "structured_record" if ts else "configuration_only",
                    "sensitive_identifier_warning": "Human-readable report masks SIM/mobile identifiers where possible.",
                    "raw": redact_sensitive_record(record),
                }
                event_type = "Cellular registration/IMS operational event" if ts and state else "Cellular/telephony configuration"
                events.append(network_event(ts, "Cellular/Telephony", event_type, "INFO" if ts and in_range(ts, ctx.start, ctx.end) else "LOW", details, metadata, 80 if ts else 60, "Structured cellular/telephony artifact; not evidence of Silent SMS", "DIRECT" if ts else "HEURISTIC"))
                produced += 1
            if not produced:
                events.extend(filesystem_network_event(ctx, path, "Cellular/Telephony", "Telephony filesystem timestamp", "carrier/telephony artifact present; no timestamped operational record identified"))
        return events


class DataUsagePlugin(ArtifactPlugin):
    name = "data_usage"

    def collect(self, ctx: CaseContext) -> List[Event]:
        events: List[Event] = []
        dbs = ctx.find_named(["DataUsage.sqlite", "CellularUsage.db"])
        dbs.extend(ctx.find_path_tokens(("netusage", "networkstatistics", "datausage", "cellularusage"), suffixes=(".db", ".sqlite", ".sqlite3")))
        for db in sorted(set(dbs), key=str)[:100]:
            artifact = SQLiteArtifact(ctx, db, self.name)
            for table in artifact.tables()[:25]:
                cols = artifact.columns(table)
                lowered = {col.lower(): col for col in cols}
                byte_cols = [col for key, col in lowered.items() if any(token in key for token in ("bytes", "wifi_in", "wifi_out", "cellular_in", "cellular_out", "rx", "tx"))]
                ts_cols = [col for key, col in lowered.items() if any(token in key for token in ("timestamp", "time", "date", "created", "modified"))]
                if not byte_cols or not ts_cols:
                    continue
                selected = list(dict.fromkeys(byte_cols + ts_cols + [col for key, col in lowered.items() if any(t in key for t in ("bundle", "process", "interface", "app"))]))
                sql = f"SELECT rowid AS _rowid, {', '.join(quote_ident(c) for c in selected)} FROM {quote_ident(table)} LIMIT 10000"
                for row in artifact.query(sql):
                    ts = None
                    ts_key = ""
                    for col in ts_cols:
                        ts = timestamp_from_any(row.get(col))
                        if ts:
                            ts_key = col
                            break
                    if not (ts and ctx.context_start <= ts <= ctx.context_end):
                        continue
                    sent = first_numeric(row, ("bytes_sent", "tx_bytes", "wifi_out", "cellular_out", "out"))
                    received = first_numeric(row, ("bytes_received", "rx_bytes", "wifi_in", "cellular_in", "in"))
                    bundle = str(record_value(row, ("bundle_id", "bundle", "process_name", "process")) or "")
                    metadata = {
                        "interface_type": str(record_value(row, ("interface", "ifname", "type")) or ""),
                        "bytes_sent": sent if sent is not None else "",
                        "bytes_received": received if received is not None else "",
                        "source_artifact": short_path(db, ctx.case_dir),
                        "raw_record_identifier": f"{table}:{row.get('_rowid')}",
                        "timestamp_basis": ts_key,
                        "timestamp_reliability": "structured_counter_timestamp",
                        "counter_type": "cumulative_or_recorded_counter",
                        "bundle_id": bundle,
                        "raw": row,
                    }
                    details = f"network usage counter | table={table} | bundle={bundle} | bytes_sent={sent} | bytes_received={received} | timestamp_field={ts_key}"
                    events.append(network_event(ts, "Data Usage", "Direct data-usage record", "INFO" if in_range(ts, ctx.start, ctx.end) else "CONTEXT", details, metadata, 85, "Structured timestamped usage counter; may be cumulative", "DIRECT"))
        return events


def first_numeric(row: Dict[str, Any], tokens: Sequence[str]) -> Optional[int]:
    for token in tokens:
        value = record_value(row, (token,))
        num = safe_int(value)
        if num is not None:
            return num
    return None


def filesystem_network_event(ctx: CaseContext, path: Path, source: str, event_type: str, note: str) -> List[Event]:
    try:
        stat = path.stat()
        ts = datetime.fromtimestamp(stat.st_mtime)
    except Exception as exc:
        ctx.errors.log(source, path, exc, "filesystem network event")
        return []
    metadata = {
        "source_artifact": short_path(path, ctx.case_dir),
        "timestamp_basis": "filesystem_mtime",
        "timestamp_reliability": "filesystem_only",
        "file_size": stat.st_size,
    }
    return [
        network_event(
            ts,
            source,
            event_type,
            "LOW" if in_range(ts, ctx.start, ctx.end) else "CONTEXT",
            f"{note} | filesystem timestamp={format_dt(ts)} | path={path}",
            metadata,
            60,
            "Filesystem timestamp only; not proof of active connection or transmission",
            "FILESYSTEM_ONLY",
        )
    ]


def redact_sensitive_record(record: Dict[str, Any]) -> Dict[str, Any]:
    redacted = {}
    sensitive = ("imsi", "iccid", "imei", "meid", "sim", "subscriber")
    for key, value in record.items():
        key_text = str(key)
        if any(token in key_text.lower() for token in sensitive):
            redacted[key_text] = mask_sensitive(value)
        elif key_text == "_record_path":
            redacted[key_text] = value
        elif isinstance(value, (str, int, float, bool)) or value is None:
            redacted[key_text] = value
    return redacted


def mask_sensitive(value: Any) -> str:
    text = str(value or "")
    if len(text) <= 6:
        return "***"
    return text[:3] + "***" + text[-3:]


def plugins() -> List[ArtifactPlugin]:
    return [
        SmsPlugin(),
        CallHistoryPlugin(),
        SafariPlugin(),
        PhotosPlugin(),
        NotesPlugin(),
        MailPlugin(),
        CalendarPlugin(),
        RemindersPlugin(),
        MapsLocationPlugin(),
        KnowledgeCPlugin(),
        NotificationsPlugin(),
        WifiPlugin(),
        BluetoothPlugin(),
        AirDropNearbyPlugin(),
        NetworkConfigurationPlugin(),
        CellularTelephonyPlugin(),
        DataUsagePlugin(),
        PlistSystemPlugin(),
        SystemFilePlugin(),
    ]


def confidence_for_event(event: Event) -> Tuple[int, str, str]:
    source = event.source.lower()
    metadata = event.metadata or {}
    if metadata.get("network_event") and metadata.get("confidence_basis"):
        return (
            safe_int(metadata.get("confidence_score")) or event.confidence_score or 0,
            str(metadata.get("confidence_basis")),
            str(metadata.get("evidence_strength") or event.evidence_strength or "UNKNOWN"),
        )
    has_rowid = any(metadata.get(key) not in (None, "") for key in ("rowid", "message_rowid", "attachment_rowid"))
    has_hash = bool(metadata.get("file", {}).get("sha256") or metadata.get("sha256"))
    if event.significance == "ERROR":
        return 0, "Parser error or unknown artifact state", "UNKNOWN"
    if source == "sms.db attachment" and has_hash:
        return 95, "Direct database attachment record with recovered file hash", "DIRECT"
    if source in {"sms.db", "callhistory", "safari"} and event.timestamp and has_rowid:
        return 100, "Direct database record with timestamp and row identifier", "DIRECT"
    if source in {"sms.db", "callhistory", "safari"} and event.timestamp:
        return 90, "Direct database record with timestamp", "DIRECT"
    if source in {"photos", "mail", "notes", "calendar", "reminders", "knowledgec", "notifications", "maps/location"}:
        return 80, "Database record parsed with possible schema-version uncertainty", "DIRECT"
    if event.event_type == "Relevant file timestamp":
        return 60, "Filesystem timestamp only; not proof of user action", "FILESYSTEM_ONLY"
    if event.event_type == "Property list context":
        return 40, "Property list or path heuristic requiring examiner validation", "HEURISTIC"
    if source in {"filesystem", "bluetooth", "airdrop", "nearby interaction", "analytics/diagnostics", "unified/system logs"}:
        return 20, "Keyword or path match only", "HEURISTIC"
    return 0, "No confidence rule matched", "UNKNOWN"


def apply_confidence(events: List[Event]) -> None:
    for event in events:
        event.apply_confidence()


def dedupe_events(events: Iterable[Event]) -> List[Event]:
    seen = set()
    out: List[Event] = []
    for event in events:
        key = (
            format_dt(event.timestamp),
            event.source,
            event.event_type,
            event.details,
            json_dumps(event.metadata),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(event)
    return out


SINGLE_REPORT_SIDECARS = [
    "window_investigator_events.csv",
    "window_investigator_network_events.csv",
    "window_investigator_network_indicators.csv",
    "window_investigator_network_summary.json",
    "window_investigator_scored_buckets.csv",
    "window_investigator_relationships.csv",
    "window_investigator_graph.graphml",
    "window_investigator_graph.mmd",
    "window_investigator_entity_correlations.csv",
    "window_investigator_hypotheses.json",
    "window_investigator_question.md",
    "window_investigator_ai_summary.md",
]


def window_event_subset(ctx: CaseContext, events: List[Event]) -> List[Event]:
    if ctx.single_report and ctx.window_only:
        return [event for event in events if event.timestamp and ctx.start <= event.timestamp <= ctx.end]
    return [event for event in events if event.timestamp]


DEVICE_FIELD_KEYS = {
    "device_name": ("Device Name", "Display Name", "deviceName", "Name"),
    "product_type": ("Product Type", "ProductType", "Product Name"),
    "ios_version": ("Product Version", "ProductVersion", "iOS Version", "Build Version"),
    "build_version": ("Build Version", "BuildVersion"),
    "serial_number": ("Serial Number", "SerialNumber"),
    "udid": ("Unique Identifier", "UniqueDeviceID", "UDID", "Target Identifier", "Device Identifier"),
    "phone_number": ("Phone Number", "PhoneNumber", "International Mobile Subscriber Identity"),
    "iccid": ("ICCID", "Integrated Circuit Card Identity"),
    "imei": ("IMEI", "MEID", "International Mobile Equipment Identity"),
    "backup_date": ("Last Backup Date", "Backup Date", "Date", "Snapshot Date"),
}


MODEL_NAMES = {
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",
    "iPhone16,1": "iPhone 15 Pro",
    "iPhone16,2": "iPhone 15 Pro Max",
    "iPhone17,1": "iPhone 16 Pro",
    "iPhone17,2": "iPhone 16 Pro Max",
}


def plist_value(data: Any, keys: Sequence[str]) -> Any:
    if not isinstance(data, dict):
        return None
    lowered = {str(k).lower(): v for k, v in data.items()}
    for key in keys:
        if key.lower() in lowered:
            return lowered[key.lower()]
    for key in keys:
        needle = key.lower()
        for found_key, value in lowered.items():
            if needle in found_key:
                return value
    return None


def extract_device_metadata(ctx: CaseContext) -> Dict[str, Any]:
    sources: List[Tuple[str, Dict[str, Any]]] = []
    for plist_name in ("Info.plist", "Manifest.plist", "Status.plist"):
        for path in ctx.find_named([plist_name]):
            data = plist_load(path)
            if isinstance(data, dict):
                sources.append((short_path(path, ctx.case_dir), data))
    device: Dict[str, Any] = {
        "device_name": None,
        "product_type": None,
        "model_name": None,
        "ios_version": None,
        "build_version": None,
        "serial_number": None,
        "udid": None,
        "phone_number": None,
        "iccid": None,
        "imei": None,
    }
    backup: Dict[str, Any] = {
        "backup_date": None,
        "backup_type": "encrypted_local_iphone_backup",
        "encrypted": True,
        "source_path": str(ctx.case_dir),
    }
    provenance: Dict[str, str] = {}
    for source, data in sources:
        for field, keys in DEVICE_FIELD_KEYS.items():
            value = plist_value(data, keys)
            if value in (None, ""):
                continue
            if field == "backup_date":
                if backup["backup_date"] is None:
                    ts = timestamp_from_any(value)
                    backup["backup_date"] = format_dt(ts) if ts else str(value)
                    provenance["backup.backup_date"] = source
            elif device.get(field) is None:
                device[field] = str(value)
                provenance[f"device.{field}"] = source
        encrypted = plist_value(data, ("Is Encrypted", "Encrypted", "WasPasscodeSet"))
        if encrypted not in (None, ""):
            backup["encrypted"] = bool(encrypted)
            provenance["backup.encrypted"] = source
    if device["product_type"]:
        device["model_name"] = MODEL_NAMES.get(str(device["product_type"]), None)
    return {"device": device, "backup": backup, "provenance": provenance}


def display_device_value(value: Any) -> str:
    return str(value) if value not in (None, "") else "Not identified in supplied backup"


def coverage_plain_label(summary: Dict[str, Any]) -> str:
    status = str(summary.get("supported_examination_status") or summary.get("completeness_level") or "UNKNOWN")
    if status == "COMPLETE_FOR_SUPPORTED_ARTIFACTS":
        return "Strong"
    if status == "PARTIAL_SUPPORTED_COVERAGE":
        return "Moderate"
    if status in {"EXAMINATION_GAPS_PRESENT", "INSUFFICIENT_EXAMINATION"}:
        return "Limited"
    return "Not available"


def unsupported_artifact_summaries(records: List[CoverageRecord], app_records: List[AppCoverageRecord]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for record in records:
        if record.coverage_status not in {"PRESENT_UNSUPPORTED", "PRESENT_UNKNOWN_SCHEMA", "PRESENT_PARSE_FAILED", "PRESENT_PARTIALLY_PARSED", "PRESENT_ENCRYPTED_OR_INACCESSIBLE"}:
            continue
        key = (record.category or "Unknown", record.file_type or Path(record.artifact_name).suffix or "artifact", record.coverage_status)
        item = grouped.setdefault(key, {"category": key[0], "file_type": key[1], "status": key[2], "count": 0, "potential_relevance": potential_relevance_for_category(key[0])})
        item["count"] += 1
    if any(not app.parser_available for app in app_records):
        item = grouped.setdefault(("Third-party application artifacts", "container", "Present but unsupported"), {"category": "Third-party application artifacts", "file_type": "container", "status": "Present but unsupported", "count": 0, "potential_relevance": "May contain communications, cloud activity, or application usage."})
        item["count"] += len([app for app in app_records if not app.parser_available])
    return sorted(grouped.values(), key=lambda x: (-x["count"], x["category"]))[:50]


def potential_relevance_for_category(category: str) -> str:
    text = category.lower()
    if "communication" in text:
        return "May affect call, message, attachment, or participant completeness."
    if "web" in text or "app" in text:
        return "May contain application usage, browsing, or notification context."
    if "location" in text:
        return "May contain location-related context if supported and timestamped."
    if "security" in text or "diagnostic" in text:
        return "May contain configuration, diagnostic, or network context."
    return "May contain relevant structured records depending on artifact contents."


def write_device_information(handle: Any, metadata: Dict[str, Any]) -> None:
    device = metadata.get("device", {})
    backup = metadata.get("backup", {})
    rows = [
        ("Device name", device.get("device_name")),
        ("Product type / model identifier", device.get("product_type")),
        ("Human-readable model name", device.get("model_name")),
        ("iOS version", device.get("ios_version")),
        ("Build version", device.get("build_version")),
        ("Serial number", device.get("serial_number")),
        ("UDID or backup device identifier", device.get("udid")),
        ("Phone number", device.get("phone_number")),
        ("ICCID", device.get("iccid")),
        ("IMEI / MEID", device.get("imei")),
        ("Backup date", backup.get("backup_date")),
        ("Backup type", backup.get("backup_type")),
        ("Encryption status", "Encrypted" if backup.get("encrypted") else "Not identified as encrypted"),
        ("Source path", backup.get("source_path")),
    ]
    for label, value in rows:
        handle.write(f"- {label}: {display_device_value(value)}\n")
    handle.write("\n")


def event_direction_sentence(event: Event) -> str:
    md = event.metadata or {}
    contact = event_contact(event) or "the recorded participant"
    if event.source == "CallHistory":
        direction = str(md.get("direction") or "").upper()
        if direction == "INCOMING":
            return f"{contact} called the examined iPhone."
        if direction == "OUTGOING":
            return f"The examined iPhone called {contact}."
        return f"A call record involved {contact}."
    if event.source == "sms.db":
        direction = str(md.get("direction") or "").upper()
        if direction == "TO_DEVICE":
            return f"{contact} sent a message to the examined iPhone."
        if direction == "FROM_DEVICE":
            return f"The examined iPhone sent a message to {contact}."
        return f"A message record involved {contact}."
    return concise_event(event)


def write_attorney_executive_summary(
    handle: Any,
    ctx: CaseContext,
    window_events: List[Event],
    coverage_records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    hypotheses: List[Dict[str, Any]],
    network_events: List[Event],
) -> None:
    counts = source_counts(window_events)
    attachments = [event for event in window_events if event.source == "sms.db attachment"]
    linked_messages = [event for event in window_events if event.source == "sms.db" and (event.metadata or {}).get("linked_attachment_count")]
    significant = [event for event in window_events if event.significance in {"REVIEW", "HIGH"}]
    cov = coverage_summary(coverage_records, app_records)
    handle.write(f"- Evidence examined: encrypted iPhone backup artifacts parsed by Window Investigator from `{ctx.case_dir}`.\n")
    handle.write(f"- Requested date/time window: `{format_dt(ctx.start)}` to `{format_dt(ctx.end)}`.\n")
    handle.write(f"- Significant in-window events: {len(significant)}.\n")
    handle.write(f"- Coverage rating: {coverage_plain_label(cov)}. Coverage ratings are not probabilities and do not indicate the percentage of the entire device analyzed.\n\n")
    handle.write("Key observations:\n")
    handle.write(f"- {counts.get('CallHistory', 0)} call record(s), {counts.get('sms.db', 0)} message record(s), and {len(attachments)} attachment record(s) were identified in the requested window.\n")
    if linked_messages:
        handle.write(f"- {len(attachments)} message attachment record(s) were linked to {len(linked_messages)} parent message record(s).\n")
    else:
        handle.write("- No linked message attachments were identified in the requested window.\n")
    if network_events:
        handle.write(f"- {len(network_events)} timestamped network-context event(s) were identified; configuration records are not packet contents.\n")
    else:
        handle.write("- No timestamped operational network records were identified in the requested window.\n")
    handle.write("- The supplied backup is insufficient by itself to confirm or exclude carrier-layer Silent SMS activity.\n\n")
    handle.write("What was not identified:\n")
    handle.write("- No direct handset artifact was identified that independently confirms Silent SMS, command activity, or unusual network transmission.\n")
    handle.write("- No packet capture, carrier signaling, baseband memory, or complete sysdiagnose source was identified in the supplied backup.\n\n")
    handle.write("Recommended next steps:\n")
    for item in build_additional_evidence_recommendations(coverage_records, app_records)[:4]:
        handle.write(f"- {item.get('recommendation')}\n")
    handle.write("\n")


def write_key_findings(handle: Any, ctx: CaseContext, window_events: List[Event], hypotheses: List[Dict[str, Any]]) -> None:
    calls = [event for event in window_events if event.source == "CallHistory"]
    messages = [event for event in window_events if event.source == "sms.db"]
    attachments = [event for event in window_events if event.source == "sms.db attachment"]
    handle.write(f"- Calls in requested window: {len(calls)}\n")
    handle.write(f"- Messages in requested window: {len(messages)}\n")
    handle.write(f"- Message attachment records in requested window: {len(attachments)}\n")
    if calls[:3]:
        handle.write("- Representative call direction wording:\n")
        for event in calls[:3]:
            handle.write(f"  - {format_dt(event.timestamp)}: {event_direction_sentence(event)}\n")
    if messages[:3]:
        handle.write("- Representative message direction wording:\n")
        for event in messages[:3]:
            handle.write(f"  - {format_dt(event.timestamp)}: {event_direction_sentence(event)}\n")
    for item in hypotheses:
        handle.write(f"- {item.get('hypothesis')}: maximum supportable confidence from the available evidence: {item.get('confidence_in_assessment', 'UNKNOWN')}.\n")
    handle.write("\n")


def write_condensed_timeline(handle: Any, ctx: CaseContext, events: List[Event]) -> None:
    max_events = 25
    if not events:
        handle.write("No in-window events were identified.\n\n")
        return
    for event in sorted(events, key=lambda e: (e.timestamp or datetime.max, e.source))[:max_events]:
        handle.write(f"- `{format_dt(event.timestamp)}` | {event_direction_sentence(event)} Source: {event.source}; record: {event_provenance(event)}\n")
    if len(events) > max_events:
        handle.write(f"- {len(events) - max_events} additional event(s) are listed in the technical appendix.\n")
    handle.write("\n")


def write_significant_communications(handle: Any, events: List[Event]) -> None:
    comms = [event for event in events if event.source in {"CallHistory", "sms.db", "sms.db attachment"}]
    if not comms:
        handle.write("No call, message, or message-attachment events were identified in the requested window.\n\n")
        return
    for event in comms[:25]:
        handle.write(f"- `{format_dt(event.timestamp)}` | {event_direction_sentence(event)}\n")
        if event.source == "sms.db" and (event.metadata or {}).get("linked_attachments"):
            for linked in (event.metadata or {}).get("linked_attachments", [])[:5]:
                handle.write(f"  - Attachment: {Path(str(linked.get('filename') or '')).name} | {linked.get('mime_type')} | {human_size(linked.get('size_bytes'))}\n")
    if len(comms) > 25:
        handle.write(f"- {len(comms) - 25} additional communication event(s) are listed in the technical appendix.\n")
    handle.write("\n")


def write_client_hypotheses(handle: Any, hypotheses: List[Dict[str, Any]]) -> None:
    if not hypotheses:
        handle.write("No hypotheses were requested.\n\n")
        return
    for item in hypotheses:
        handle.write(f"### {item.get('hypothesis')}\n\n")
        handle.write(f"- Maximum supportable confidence from the available evidence: {item.get('confidence_in_assessment', 'UNKNOWN')}\n")
        handle.write(f"- Supported examination status: {item.get('supported_examination_status', 'UNKNOWN')}\n")
        handle.write(f"- Acquisition sufficiency: {item.get('acquisition_sufficiency_status', 'UNKNOWN')}\n")
        handle.write(f"- Basis: {item.get('basis', '')}\n\n")


def write_limitations_once(handle: Any, coverage_records: List[CoverageRecord], app_records: List[AppCoverageRecord]) -> None:
    summary = coverage_summary(coverage_records, app_records)
    handle.write("- The supplied encrypted iPhone backup does not ordinarily include carrier signaling, baseband memory, live RAM, packet captures, router logs, or complete sysdiagnose material.\n")
    for item in summary.get("acquisition_limitations", [])[:6]:
        handle.write(f"- {item}\n")
    for item in summary.get("examination_gaps", [])[:6]:
        handle.write(f"- Examination gap: {item}\n")
    handle.write("- Call-location labels, when present, are call-record or number-associated labels and do not establish the physical location of the device or caller.\n\n")


def write_recommended_next_steps(handle: Any, coverage_records: List[CoverageRecord], app_records: List[AppCoverageRecord]) -> None:
    recommendations = build_additional_evidence_recommendations(coverage_records, app_records)
    if not recommendations:
        handle.write("No supplemental evidence recommendations were generated beyond ordinary examiner validation.\n\n")
        return
    for item in recommendations[:8]:
        handle.write(f"- {item.get('priority')}: {item.get('recommendation')}\n")
    handle.write("\n")


def write_client_conclusion(handle: Any, ctx: CaseContext, window_events: List[Event], network_events: List[Event]) -> None:
    comms = [event for event in window_events if event.source in {"sms.db", "CallHistory", "sms.db attachment"}]
    if comms:
        handle.write("The supplied encrypted iPhone backup contained call, message, or attachment activity during the requested period. ")
    else:
        handle.write("The supplied encrypted iPhone backup did not yield parsed call, message, or attachment events during the requested period in this run. ")
    handle.write("No direct handset artifact was identified that supported Silent SMS, command activity, or unusual network transmission. ")
    handle.write("However, the acquisition does not contain the carrier, baseband, packet, or sysdiagnose evidence required to conclusively exclude those activities.\n\n")


def write_client_report(
    path: Path,
    ctx: CaseContext,
    device_metadata: Dict[str, Any],
    window_events: List[Event],
    coverage_records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    hypotheses: List[Dict[str, Any]],
    network_events: List[Event],
) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Window Investigator Client Report\n\n")
        handle.write("## Examination Scope\n\n")
        handle.write(f"- Case: {ctx.case_name or ctx.case_dir.name}\n")
        handle.write(f"- Requested window: `{format_dt(ctx.start)}` to `{format_dt(ctx.end)}`\n")
        handle.write(f"- Source path: `{ctx.case_dir}`\n\n")
        handle.write("## Device Information\n\n")
        write_device_information(handle, device_metadata)
        handle.write("## Attorney Executive Summary\n\n")
        write_attorney_executive_summary(handle, ctx, window_events, coverage_records, app_records, hypotheses, network_events)
        handle.write("## Key Findings\n\n")
        write_key_findings(handle, ctx, window_events, hypotheses)
        handle.write("## Allegation-Time Analysis\n\n")
        write_allegation_time_analysis(handle, ctx, window_events)
        handle.write("## Condensed Timeline\n\n")
        write_condensed_timeline(handle, ctx, window_events)
        handle.write("## Significant Communications and Attachments\n\n")
        write_significant_communications(handle, window_events)
        handle.write("## Hypothesis Assessments\n\n")
        write_client_hypotheses(handle, hypotheses)
        handle.write("## Limitations\n\n")
        write_limitations_once(handle, coverage_records, app_records)
        handle.write("## Recommended Next Steps\n\n")
        write_recommended_next_steps(handle, coverage_records, app_records)
        handle.write("## Conclusion\n\n")
        write_client_conclusion(handle, ctx, window_events, network_events)


def write_technical_appendix(
    path: Path,
    ctx: CaseContext,
    inventory: List[Dict[str, Any]],
    coverage_records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    clusters: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    case_knowledge: Optional[Dict[str, Any]],
    error_path: Path,
) -> None:
    score = build_evidence_coverage_score(ctx, coverage_records, app_records, window_event_subset(ctx, []))
    blind_spots = build_forensic_blind_spots(coverage_records, app_records)
    unsupported = unsupported_artifact_summaries(coverage_records, app_records)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Window Investigator Technical Appendix\n\n")
        handle.write("## Full Parser Coverage\n\n")
        write_evidence_coverage_section(handle, ctx, coverage_records, app_records)
        handle.write("## Coverage Scoring Methodology\n\n")
        write_evidence_coverage_score_section(handle, score)
        handle.write("## Detailed Artifact Inventory\n\n")
        write_artifact_inventory(handle, inventory)
        handle.write("## Unsupported Artifact Summary\n\n")
        write_unsupported_summary_table(handle, unsupported)
        handle.write("## Parser Failures and Unknown Schemas\n\n")
        write_parser_failure_summary(handle, coverage_records)
        handle.write("## Full Blind-Spot Lists\n\n")
        write_forensic_blind_spots_section(handle, blind_spots)
        handle.write("## Full Relationship Table\n\n")
        write_relationship_summary_table(handle, relationships)
        handle.write("## Full Correlation Details\n\n")
        write_single_cluster_summary(handle, ctx, clusters)
        handle.write("## Full Normalized Event Metadata\n\n")
        if case_knowledge:
            handle.write("```json\n")
            handle.write(json_dumps(case_knowledge))
            handle.write("\n```\n\n")
        handle.write("## Parser Errors\n\n")
        write_error_summary(handle, ctx, error_path)


def write_unsupported_summary_table(handle: Any, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        handle.write("No unsupported-artifact categories were summarized.\n\n")
        return
    handle.write("| Category | Count | Status | File type | Potential relevance |\n")
    handle.write("|---|---:|---|---|---|\n")
    for row in rows:
        handle.write(f"| {row['category']} | {row['count']} | {row['status']} | {row['file_type']} | {row['potential_relevance']} |\n")
    handle.write("\n")


def write_parser_failure_summary(handle: Any, records: List[CoverageRecord]) -> None:
    failures = [r for r in records if r.coverage_status in {"PRESENT_PARSE_FAILED", "PRESENT_UNKNOWN_SCHEMA"}]
    if not failures:
        handle.write("No parser failures or unknown schemas were recorded.\n\n")
        return
    for record in failures[:200]:
        handle.write(f"- {record.artifact_name} | {record.coverage_status} | {record.failure_reason or record.unsupported_reason or record.examiner_note}\n")
    handle.write("\n")


def markdown_to_html(markdown_text: str, title: str) -> str:
    return "<!doctype html><html><head><meta charset='utf-8'><title>" + html.escape(title) + "</title><style>body{font-family:Segoe UI,Arial,sans-serif;max-width:980px;margin:40px auto;line-height:1.45}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:4px 6px}code,pre{background:#f6f8fa}</style></head><body><pre>" + html.escape(markdown_text) + "</pre></body></html>"


def write_html_from_markdown(md_path: Path, html_path: Path, title: str) -> None:
    html_path.write_text(markdown_to_html(md_path.read_text(encoding="utf-8"), title), encoding="utf-8")


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf_from_markdown(md_path: Path, pdf_path: Path, title: str) -> None:
    lines = md_path.read_text(encoding="utf-8", errors="replace").splitlines()
    pages = [lines[i : i + 46] for i in range(0, min(len(lines), 460), 46)] or [[]]
    objects: List[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + i * 2} 0 R" for i in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("ascii"))
    for i, page_lines in enumerate(pages):
        content_obj = 4 + i * 2
        page = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_obj} 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>"
        objects.append(page.encode("ascii"))
        text_cmds = ["BT /F1 10 Tf 40 760 Td"]
        for line in ([title, ""] + page_lines):
            clipped = pdf_escape(line[:110])
            text_cmds.append(f"({clipped}) Tj 0 -14 Td")
        text_cmds.append("ET")
        stream = "\n".join(text_cmds).encode("latin-1", errors="replace")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream")
    offsets = []
    pdf = bytearray(b"%PDF-1.4\n")
    for idx, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("ascii"))
    for off in offsets:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    pdf_path.write_bytes(bytes(pdf))


def write_unsupported_artifacts_csv(path: Path, records: List[CoverageRecord], app_records: List[AppCoverageRecord]) -> None:
    fields = ["artifact_name", "category", "file_type", "coverage_status", "relative_path", "absolute_path", "potential_relevance"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for record in records:
            if record.coverage_status in {"PRESENT_UNSUPPORTED", "PRESENT_UNKNOWN_SCHEMA", "PRESENT_PARSE_FAILED", "PRESENT_PARTIALLY_PARSED", "PRESENT_ENCRYPTED_OR_INACCESSIBLE"}:
                writer.writerow({
                    "artifact_name": record.artifact_name,
                    "category": record.category,
                    "file_type": record.file_type,
                    "coverage_status": record.coverage_status,
                    "relative_path": record.relative_path,
                    "absolute_path": record.absolute_path,
                    "potential_relevance": potential_relevance_for_category(record.category),
                })
        for app in app_records:
            if not app.parser_available:
                writer.writerow({
                    "artifact_name": app.app_name,
                    "category": "Third-party application artifacts",
                    "file_type": "container",
                    "coverage_status": app.parser_status,
                    "relative_path": "",
                    "absolute_path": "",
                    "potential_relevance": "May contain communications, cloud activity, or application usage.",
                })


def write_parser_failures_csv(path: Path, records: List[CoverageRecord]) -> None:
    fields = ["artifact_name", "category", "coverage_status", "failure_reason", "relative_path", "absolute_path"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for record in records:
            if record.coverage_status in {"PRESENT_PARSE_FAILED", "PRESENT_UNKNOWN_SCHEMA"}:
                writer.writerow({
                    "artifact_name": record.artifact_name,
                    "category": record.category,
                    "coverage_status": record.coverage_status,
                    "failure_reason": record.failure_reason or record.unsupported_reason,
                    "relative_path": record.relative_path,
                    "absolute_path": record.absolute_path,
                })


def write_client_report_outputs(
    ctx: CaseContext,
    out_dir: Path,
    device_metadata: Dict[str, Any],
    window_events: List[Event],
    inventory: List[Dict[str, Any]],
    clusters: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    network_events: List[Event],
    coverage_records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    hypotheses: List[Dict[str, Any]],
    case_knowledge: Optional[Dict[str, Any]],
    error_path: Path,
) -> None:
    client_md = out_dir / "report_client.md"
    client_html = out_dir / "report_client.html"
    client_pdf = out_dir / "report_client.pdf"
    appendix_md = out_dir / "report_technical_appendix.md"
    appendix_html = out_dir / "report_technical_appendix.html"
    write_client_report(client_md, ctx, device_metadata, window_events, coverage_records, app_records, hypotheses, network_events)
    if ctx.report_config.include_technical_appendix:
        write_technical_appendix(appendix_md, ctx, inventory, coverage_records, app_records, clusters, relationships, case_knowledge, error_path)
    write_html_from_markdown(client_md, client_html, "Window Investigator Client Report")
    if ctx.report_config.include_technical_appendix:
        write_html_from_markdown(appendix_md, appendix_html, "Window Investigator Technical Appendix")
    write_simple_pdf_from_markdown(client_md, client_pdf, "Window Investigator Client Report")
    write_unsupported_artifacts_csv(out_dir / "unsupported_artifacts.csv", coverage_records, app_records)
    write_parser_failures_csv(out_dir / "parser_failures.csv", coverage_records)
    (out_dir / "device_metadata.json").write_text(json.dumps(device_metadata, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    evidence = dict(case_knowledge or {})
    evidence["device"] = device_metadata.get("device", {})
    evidence["backup"] = device_metadata.get("backup", {})
    evidence["report_config"] = ctx.report_config.as_dict()
    (out_dir / "case_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def write_single_report_outputs(ctx: CaseContext, all_events: List[Event]) -> Tuple[Path, Path]:
    out_dir = ctx.case_dir / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "window_investigator_final_report.md"
    error_path = out_dir / "window_investigator_errors.log"
    apply_confidence(all_events)
    window_events = sorted(window_event_subset(ctx, all_events), key=lambda e: (e.timestamp or datetime.max, e.source, e.event_type))
    coverage_records, app_coverage_records = build_coverage_audit(ctx, all_events)
    inventory = build_artifact_inventory(ctx, window_events)
    conversations = build_conversation_context(ctx, all_events)
    conversations_by_message = map_conversations_by_message(conversations)
    attachment_index = link_message_attachments(all_events)
    clusters = build_single_report_clusters(ctx, window_events)
    buckets = build_scored_buckets(ctx, window_events)
    relationships = relationship_edges(window_events)
    network_events = [event for event in window_events if event.metadata.get("network_event")]
    network_indicators = build_network_indicators(network_events)
    network_summary = build_network_summary(ctx, network_events, network_indicators, inventory)
    hypotheses = evaluate_hypotheses(ctx, window_events)
    question_answer = answer_question(ctx, window_events, clusters)
    device_metadata = extract_device_metadata(ctx)
    case_knowledge = build_case_knowledge(ctx, all_events, clusters, coverage_records, app_coverage_records, hypotheses)
    case_knowledge["device"] = device_metadata.get("device", {})
    case_knowledge["backup"] = device_metadata.get("backup", {})
    ctx.case_knowledge = case_knowledge
    attachment_index = link_message_attachments(all_events)
    if ctx.export_case_knowledge:
        write_case_knowledge(out_dir / "window_investigator_case_knowledge.json", case_knowledge)
    if ctx.export_coverage_files:
        write_coverage_outputs(
            out_dir / "window_investigator_coverage.json",
            out_dir / "window_investigator_coverage.csv",
            out_dir / "window_investigator_app_coverage.csv",
            out_dir / "window_investigator_sqlite_coverage.csv",
            out_dir / "window_investigator_unparsed_artifacts.csv",
            out_dir / "window_investigator_coverage_scores.json",
            out_dir / "window_investigator_finding_confidence.csv",
            out_dir / "window_investigator_forensic_blind_spots.csv",
            out_dir / "window_investigator_evidence_recommendations.csv",
            ctx,
            coverage_records,
            app_coverage_records,
            window_events,
        )
    with report_path.open("w", encoding="utf-8") as f:
        write_single_report(
            f,
            ctx,
            all_events,
            window_events,
            inventory,
            conversations_by_message,
            clusters,
            buckets,
            relationships,
            network_events,
            network_indicators,
            network_summary,
            coverage_records,
            app_coverage_records,
            hypotheses,
            question_answer,
            case_knowledge,
            attachment_index,
            error_path,
        )
    write_client_report_outputs(
        ctx,
        out_dir,
        device_metadata,
        window_events,
        inventory,
        clusters,
        relationships,
        network_events,
        coverage_records,
        app_coverage_records,
        hypotheses,
        case_knowledge,
        error_path,
    )
    ctx.errors.write(error_path)
    return report_path, error_path


def write_single_report(
    handle: Any,
    ctx: CaseContext,
    all_events: List[Event],
    window_events: List[Event],
    inventory: List[Dict[str, Any]],
    conversations_by_message: Dict[str, Dict[str, Any]],
    clusters: List[Dict[str, Any]],
    buckets: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    network_events: List[Event],
    network_indicators: List[Dict[str, Any]],
    network_summary: Dict[str, Any],
    coverage_records: List[CoverageRecord],
    app_coverage_records: List[AppCoverageRecord],
    hypotheses: List[Dict[str, Any]],
    question_answer: Optional[Dict[str, Any]],
    case_knowledge: Optional[Dict[str, Any]],
    attachment_index: Dict[str, List[Event]],
    error_path: Path,
) -> None:
    counts = source_counts(window_events)
    device_metadata = extract_device_metadata(ctx)
    handle.write("# Window Investigator Final Report\n\n")
    handle.write("## Examination Scope\n\n")
    handle.write(f"- Case: {ctx.case_name or ctx.case_dir.name}\n")
    handle.write(f"- Requested start: `{format_dt(ctx.start)}`\n")
    handle.write(f"- Requested end: `{format_dt(ctx.end)}`\n")
    handle.write("- Timezone statement: timestamps are reported as parsed from artifacts/local runtime context; verify source timezone assumptions during examination.\n")
    handle.write(f"- Evidence source: `{ctx.case_dir}`\n")
    handle.write("- Acquisition limitations: a standard encrypted iPhone backup usually does not contain complete packet captures, complete destination IP history, complete byte-transfer accounting, complete TCP/UDP connection history, remote internet MAC addresses, or proof of packet contents.\n")
    handle.write("- Display scope: standalone timeline events are limited to primary timestamps inside the exact requested window.\n\n")

    handle.write("## Device Information\n\n")
    write_device_information(handle, device_metadata)

    handle.write("## Executive Findings\n\n")
    write_single_executive_findings(handle, ctx, window_events, counts, network_events, network_summary)
    if question_answer:
        write_single_question_response(handle, question_answer)

    coverage_score = build_evidence_coverage_score(ctx, coverage_records, app_coverage_records, window_events)
    confidence_results = assess_finding_confidence(ctx, coverage_records, app_coverage_records, window_events)
    blind_spots = build_forensic_blind_spots(coverage_records, app_coverage_records)
    recommendations = build_additional_evidence_recommendations(coverage_records, app_coverage_records)
    cov_summary = coverage_summary(coverage_records, app_coverage_records)

    handle.write("## Supported Parser Coverage\n\n")
    write_supported_parser_coverage_section(handle, ctx, coverage_records, app_coverage_records)

    handle.write("## Evidence Coverage Score\n\n")
    write_evidence_coverage_score_section(handle, coverage_score)

    handle.write("## Evidence Coverage Heat Map\n\n")
    write_evidence_coverage_heat_map(handle, coverage_score)

    handle.write("## Evidence Confidence\n\n")
    write_evidence_confidence_section(handle, confidence_results)

    handle.write("## Examination Gaps\n\n")
    write_examination_gaps_section(handle, cov_summary.get("examination_gaps", []))

    handle.write("## Acquisition Limitations\n\n")
    write_acquisition_limitations_section(handle, cov_summary.get("acquisition_limitations", []))

    handle.write("## Evidence Not Collected\n\n")
    write_evidence_not_collected_section(handle, cov_summary.get("not_collected_sources", []))

    handle.write("## Additional Evidence That Could Increase Confidence\n\n")
    write_additional_evidence_recommendations_section(handle, recommendations)

    handle.write("## Artifact Coverage\n\n")
    write_single_artifact_coverage(handle, inventory)

    handle.write("## Detailed Parsing Status\n\n")
    write_evidence_coverage_section(handle, ctx, coverage_records, app_coverage_records)

    handle.write("## Forensic Blind Spots\n\n")
    write_forensic_blind_spots_section(handle, blind_spots)

    handle.write("## Coverage Effect on Conclusions\n\n")
    write_coverage_effect_section(handle, coverage_records, app_coverage_records)

    handle.write("## Allegation-Time Analysis\n\n")
    write_allegation_time_analysis(handle, ctx, window_events)

    handle.write("## Exact-Window Enriched Timeline\n\n")
    if not window_events:
        handle.write("No normalized events with primary timestamps inside the exact requested window were identified.\n\n")
    cluster_by_event = map_clusters_by_event(clusters)
    for event in window_events:
        write_enriched_event(handle, ctx, event, window_events, conversations_by_message, cluster_by_event, attachment_index)

    handle.write("## Correlated Activity Summary\n\n")
    write_single_cluster_summary(handle, ctx, clusters)

    handle.write("## Relationship Summary\n\n")
    write_relationship_summary_table(handle, relationships)

    handle.write("## Normalized Evidence Summary\n\n")
    write_normalized_evidence_summary(handle, case_knowledge)

    handle.write("## Network Context Summary\n\n")
    write_single_network_summary(handle, network_summary, network_events, network_indicators)

    handle.write("## Hypothesis Assessment\n\n")
    write_hypotheses(handle, hypotheses)

    handle.write("## Conclusion\n\n")
    write_single_conclusion(handle, ctx, window_events, network_summary)

    if ctx.ai_summary:
        handle.write("## AI-Assisted Draft Summary\n\n")
        write_embedded_ai_summary(handle, ctx, window_events, inventory, clusters, hypotheses)

    handle.write("## Parser Errors\n\n")
    write_error_summary(handle, ctx, error_path)


def source_counts(events: List[Event]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for event in events:
        counts[event.source] = counts.get(event.source, 0) + 1
    return counts


def write_single_executive_findings(
    handle: Any,
    ctx: CaseContext,
    window_events: List[Event],
    counts: Dict[str, int],
    network_events: List[Event],
    network_summary: Dict[str, Any],
) -> None:
    messages = [event for event in window_events if event.source == "sms.db"]
    calls = [event for event in window_events if event.source == "CallHistory"]
    attachments = [event for event in window_events if event.source == "sms.db attachment"]
    timestamped_network = [
        event for event in network_events
        if event.timestamp and event.metadata.get("timestamp_reliability") not in ("configuration_only", "filesystem_only")
    ]
    direct_near = {
        format_dt(t): len([event for event in window_events if event.timestamp and abs(event.timestamp - t) <= timedelta(seconds=30)])
        for t in ctx.allegation_times
    }
    handle.write(f"- In-window events: {len(window_events)}\n")
    handle.write(f"- Calls: {len(calls)}\n")
    handle.write(f"- Messages: {len(messages)}\n")
    handle.write(f"- Attachments: {len(attachments)}\n")
    handle.write(f"- Safari events: {counts.get('Safari', 0)}\n")
    handle.write(f"- Photos: {counts.get('Photos', 0)}\n")
    handle.write(f"- Notifications: {counts.get('Notifications', 0)}\n")
    handle.write(f"- Timestamped operational network events: {len(timestamped_network)}\n")
    for when, count in direct_near.items():
        handle.write(f"- Direct events within 30 seconds of {when}: {count}\n")
    silent_result = assess_finding_completeness(ctx, "silent_sms", ctx.coverage_records, ctx.app_coverage_records)
    command_result = assess_finding_completeness(ctx, "command_activity", ctx.coverage_records, ctx.app_coverage_records)
    silent_support = [
        event for event in window_events
        if event.source in {"sms.db", "Cellular/Telephony"} and ("silent" in event.details.lower() or "no-text" in event.details.lower())
    ]
    command_support = [
        event for event in window_events
        if any(term in (event.source + " " + event.event_type + " " + event.details).lower() for term in ("command", "execution", "remote access", "mdm"))
    ]
    if silent_support:
        handle.write(f"- Silent SMS-related handset artifacts requiring examiner review: {len(silent_support)}. No-text messages or attachment-only iMessages are not proof of Silent SMS.\n")
    else:
        handle.write("- Silent SMS: No direct supporting handset artifact was identified in the relevant supported artifacts successfully parsed for the requested window. The supplied encrypted iPhone backup is not, by itself, sufficient to confirm or exclude carrier-layer Silent SMS activity.\n")
    handle.write(f"  Supported examination status: {silent_result.supported_examination_status}; acquisition sufficiency: {silent_result.acquisition_sufficiency_status}.\n")
    if command_support:
        handle.write(f"- Command activity-related artifacts requiring examiner review: {len(command_support)}.\n")
    else:
        handle.write("- Command activity: No direct supporting handset artifact was identified in the relevant supported artifacts successfully parsed for the requested window, subject to acquisition and parser limitations.\n")
    handle.write(f"  Supported examination status: {command_result.supported_examination_status}; acquisition sufficiency: {command_result.acquisition_sufficiency_status}.\n")
    packet_count = len(network_summary.get("packet_capture_evidence", []))
    handle.write(f"- Packet-level evidence available in examined backup: {'Yes' if packet_count else 'No'}\n\n")


def write_single_question_response(handle: Any, question_answer: Dict[str, Any]) -> None:
    handle.write("Deterministic investigator question response:\n")
    handle.write(f"- Question: {question_answer['question']}\n")
    handle.write(f"- Answer: {question_answer['answer']}\n")
    handle.write(f"- Evidence reviewed: {question_answer.get('evidence_reviewed', 'unknown')}\n")
    handle.write(f"- Supported examination status: {question_answer.get('supported_examination_status', 'UNKNOWN')}\n")
    handle.write(f"- Acquisition sufficiency for this question: {question_answer.get('acquisition_sufficiency_status', 'UNKNOWN')}\n")
    handle.write(f"- Examiner confidence in examination completeness: {question_answer.get('examiner_confidence_in_examination_completeness', 'UNKNOWN')}\n")
    support = question_answer.get("supporting_events", [])
    handle.write(f"- Supporting in-window events identified by question rules: {len(support)}\n")
    unsupported = question_answer.get("unparsed_or_unsupported_sources", [])
    failures = question_answer.get("parser_failures", [])
    if unsupported:
        handle.write(f"- Unparsed or unsupported sources affecting completeness: {', '.join(unsupported[:10])}\n")
    if failures:
        handle.write(f"- Parser failures affecting completeness: {', '.join(failures[:10])}\n")
    for title, key in (
        ("Examination gaps affecting this answer", "examination_gaps"),
        ("Acquisition limitations affecting this answer", "acquisition_limitations"),
        ("Evidence not collected", "evidence_not_collected"),
        ("Additional evidence that could increase confidence", "additional_evidence_that_could_increase_confidence"),
    ):
        values = question_answer.get(key) or ["None identified"]
        handle.write(f"- {title}: {', '.join(values[:6])}\n")
    for item in question_answer.get("contradictory_or_non_supporting", [])[:6]:
        handle.write(f"- Non-supporting evidence/constraint: {item}\n")
    for item in question_answer.get("additional_evidence_needed", [])[:6]:
        handle.write(f"- Additional evidence needed: {item}\n")
    handle.write("\n")


def write_single_artifact_coverage(handle: Any, inventory: List[Dict[str, Any]]) -> None:
    handle.write("| Artifact | Found | Parsed | In-Window Events | Operational Records | Configuration Records | Errors | Limitation |\n")
    handle.write("|---|---:|---:|---:|---:|---:|---:|---|\n")
    for item in inventory:
        limitation = artifact_limitation_text(item)
        handle.write(
            f"| {item['artifact']} | {item['found']} | {item['parsed_successfully']} | "
            f"{item['event_count']} | {item.get('operational_records', 0)} | "
            f"{item.get('configuration_only', 0)} | {item['errors']} | {limitation} |\n"
        )
    handle.write("\n")


def artifact_limitation_text(item: Dict[str, Any]) -> str:
    artifact = str(item.get("artifact", "")).lower()
    if item.get("found") == "NO":
        return "Artifact absent or not located in indexed backup paths."
    if "wi-fi" in artifact or "wifi" in artifact:
        return "Known-network/configuration records are not proof of active Wi-Fi use."
    if "bluetooth" in artifact:
        return "Paired-device records are not proof of connection."
    if "data usage" in artifact:
        return "Counters may be cumulative unless a valid delta is documented."
    if "packet" in artifact:
        return "Packet-level evidence is unavailable unless explicit capture files are present."
    return "Interpret in context of parser support and artifact schema."


def write_evidence_coverage_section(
    handle: Any,
    ctx: CaseContext,
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
) -> None:
    summary = coverage_summary(records, app_records)
    handle.write(f"- Total files inventoried: {summary['total_files_inventoried']}\n")
    handle.write(f"- Databases identified: {summary['databases_identified']}\n")
    handle.write(f"- Databases opened: {summary['databases_opened']}\n")
    handle.write(f"- Supported databases: {summary['supported_databases']}\n")
    handle.write(f"- Unsupported databases: {summary['unsupported_databases']}\n")
    handle.write(f"- Parse failures: {summary['parse_failures']}\n")
    handle.write(f"- Partially parsed artifacts: {summary['partially_parsed_artifacts']}\n")
    handle.write(f"- Third-party app containers found: {summary['third_party_app_containers_found']}\n")
    handle.write(f"- Unsupported app containers: {summary['unsupported_app_containers']}\n")
    handle.write(f"- Artifacts with WAL/SHM: {summary['artifacts_with_wal_shm']}\n")
    handle.write(f"- Records normalized: {summary['records_normalized']}\n")
    handle.write(f"- Records in requested window: {summary['records_in_requested_window']}\n")
    handle.write(f"- Examination gaps: {summary['examination_gap_count']}\n")
    handle.write(f"- Acquisition limitations: {summary['acquisition_limitation_count']}\n")
    handle.write(f"- Evidence not collected sources: {summary['not_collected_source_count']}\n")
    handle.write(f"- Supported examination status: {summary['supported_examination_status']}\n\n")
    handle.write("| Artifact / App | Present | Supported | Parsed | Records Total | Records In Window | Coverage Status | Errors | Limitation |\n")
    handle.write("|---|---:|---:|---:|---:|---:|---|---:|---|\n")
    material = sorted(
        records,
        key=lambda r: (
            0 if r.coverage_status in {"PRESENT_UNSUPPORTED", "PRESENT_PARSE_FAILED", "PRESENT_UNKNOWN_SCHEMA", "PRESENT_PARTIALLY_PARSED"} else 1,
            r.category,
            r.artifact_name,
        ),
    )
    for record in material[:120]:
        if not record.file_present and not record.records_normalized_total and record.coverage_status == "NOT_PRESENT":
            continue
        handle.write(
            f"| {record.artifact_name} | {'YES' if record.file_present else 'NO'} | "
            f"{'YES' if record.parser_enabled else 'NO'} | {record.parser_status} | "
            f"{record.records_normalized_total} | {record.records_normalized_in_window} | "
            f"{record.coverage_status} | {record.error_count} | {coverage_limitation(record)} |\n"
        )
    for app in app_records[:80]:
        handle.write(
            f"| App container: {app.app_name} | YES | {'YES' if app.parser_available else 'NO'} | "
            f"{app.parser_status} | {app.normalized_records} | 0 | {app.parser_status} | 0 | "
            "Application container was present; this does not establish application activity. |\n"
        )
    handle.write("\n")


def write_supported_parser_coverage_section(
    handle: Any,
    ctx: CaseContext,
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
) -> None:
    summary = coverage_summary(records, app_records)
    handle.write("Supported parser coverage describes how completely this tool examined supported artifacts actually supplied. It is distinct from acquisition sufficiency.\n\n")
    handle.write(f"- Supported examination status: {summary.get('supported_examination_status', 'UNKNOWN')}\n")
    handle.write(f"- Supported databases: {summary.get('supported_databases', 0)}\n")
    handle.write(f"- Supported databases opened: {summary.get('databases_opened', 0)}\n")
    handle.write(f"- Parse failures: {summary.get('parse_failures', 0)}\n")
    handle.write(f"- Partially parsed artifacts: {summary.get('partially_parsed_artifacts', 0)}\n")
    handle.write(f"- Records normalized: {summary.get('records_normalized', 0)}\n")
    handle.write(f"- Records in requested window: {summary.get('records_in_requested_window', 0)}\n\n")


def write_examination_gaps_section(handle: Any, gaps: List[str]) -> None:
    if not gaps:
        handle.write("No material examination gaps affecting the requested findings were identified.\n\n")
        return
    handle.write("These are present, expected, unsupported, failed, unknown-schema, or partially parsed sources that can affect the examination of supplied evidence.\n\n")
    for gap in gaps[:100]:
        handle.write(f"- {gap}\n")
    handle.write("\n")


def write_acquisition_limitations_section(handle: Any, limitations: List[str]) -> None:
    handle.write("These limitations arise from the acquisition type and do not indicate a parser failure or an omitted examination step.\n\n")
    if not limitations:
        handle.write("No acquisition-type limitations were identified by the coverage model for the requested findings.\n\n")
        return
    for limitation in limitations[:100]:
        handle.write(f"- {limitation}\n")
    handle.write("\n")


def write_evidence_not_collected_section(handle: Any, sources: List[str]) -> None:
    if not sources:
        handle.write("No separately collectable external evidence sources were identified as not supplied for the requested findings.\n\n")
        return
    handle.write("These sources may be obtainable separately, but were not supplied as part of the examined encrypted iPhone backup.\n\n")
    for source in sources[:100]:
        handle.write(f"- {source}\n")
    handle.write("\n")


def write_evidence_coverage_score_section(handle: Any, score: Dict[str, Any]) -> None:
    handle.write("Coverage percentages are weighted audit measures, not probabilities.\n\n")
    handle.write(f"- Scoreable artifacts: {score.get('scoreable_artifact_count', 0)}\n")
    handle.write(f"- Excluded-from-score files/artifacts: {score.get('excluded_artifact_count', 0)}\n")
    handle.write(f"- Duplicate records suppressed: {score.get('duplicate_records_suppressed', 0)}\n")
    handle.write(f"- Denominator basis: {score.get('denominator_basis', '')}\n")
    for key in (
        "supported_parser_coverage_percent",
        "overall_evidence_coverage_percent",
        "native_artifact_coverage_percent",
        "third_party_artifact_coverage_percent",
        "requested_window_coverage_percent",
        "critical_artifact_coverage_percent",
    ):
        label = key.replace("_", " ")
        handle.write(f"- {label}: {score.get(key, 0):.2f}%\n")
    if score.get("expected_artifacts_missing"):
        handle.write(f"- Expected artifacts missing: {', '.join(score.get('expected_artifacts_missing', [])[:20])}\n")
    if score.get("optional_artifacts_absent"):
        handle.write(f"- Optional artifacts absent and excluded from denominator: {', '.join(score.get('optional_artifacts_absent', [])[:20])}\n")
    if score.get("outside_standard_backup_artifacts"):
        handle.write(f"- Outside-standard-backup artifacts tracked as blind spots, excluded from ordinary parser denominator: {', '.join(score.get('outside_standard_backup_artifacts', [])[:20])}\n")
    handle.write("\nCategory-level weighted coverage:\n\n")
    handle.write("| Category | Coverage | Covered Weight | Possible Weight | Records Covered | Records Total | Material Gaps |\n")
    handle.write("|---|---:|---:|---:|---:|---:|---|\n")
    for item in score.get("coverage_categories", []):
        handle.write(
            f"| {item['category']} | {item['coverage_percent']:.2f}% | {item['covered_weight']} | "
            f"{item['possible_weight']} | {item['records_covered']} | {item['records_total']} | "
            f"{'; '.join(item.get('material_gaps', [])[:5])} |\n"
        )
    handle.write("\n")


def write_evidence_coverage_heat_map(handle: Any, score: Dict[str, Any]) -> None:
    handle.write("Each category line contains a 20-character bar. Coverage percentages are weighted audit measures, not probabilities.\n\n")
    lines = score.get("category_heat_map", [])
    if not lines:
        heat_map = score.get("heat_map") or coverage_heat_map(score.get("overall_evidence_coverage_percent", 0))
        handle.write(f"`Overall                 {heat_map}`\n\n")
        return
    for item in lines:
        gap_label = " MATERIAL GAP" if item.get("material_gaps") else ""
        handle.write(f"`{item['category'][:24]:24} {item['bar']}{gap_label}`\n")
    handle.write("\n")


def write_evidence_confidence_section(handle: Any, confidence_results: List[FindingConfidenceResult]) -> None:
    if not confidence_results:
        handle.write("No deterministic finding-confidence assessments were generated.\n\n")
        return
    handle.write("| Finding | Confidence | Coverage Level | Supporting Evidence | Material Gaps | Ceiling | Basis |\n")
    handle.write("|---|---|---:|---:|---:|---|---|\n")
    for item in confidence_results:
        handle.write(
            f"| {item.finding_name} | {item.confidence_level} | {item.coverage_level} | "
            f"{item.supporting_evidence_count} | {item.material_gap_count} | {item.confidence_ceiling} | "
            f"{item.deterministic_basis} |\n"
        )
    handle.write("\n")


def write_forensic_blind_spots_section(handle: Any, blind_spots: List[Dict[str, Any]]) -> None:
    if not blind_spots:
        handle.write("No material forensic blind spots were identified by the coverage auditor.\n\n")
        return
    for heading in (
        "Examination Blind Spots",
        "Acquisition-Type Blind Spots",
        "Deleted and Volatile Data Limitations",
        "External Evidence Not Collected",
    ):
        handle.write(f"### {heading}\n\n")
        group = [spot for spot in blind_spots if spot.get("blind_spot_type") == heading]
        if not group:
            handle.write("None identified.\n\n")
            continue
        for spot in group[:100]:
            handle.write(
                f"- {spot['severity']} | {spot['source']} | {spot['coverage_status']} | "
                f"{spot['basis']}\n"
            )
        handle.write("\n")


def write_additional_evidence_recommendations_section(handle: Any, recommendations: List[Dict[str, Any]]) -> None:
    if not recommendations:
        handle.write("No additional evidence recommendations were generated beyond ordinary examiner validation.\n\n")
        return
    for item in recommendations:
        handle.write(f"- {item['priority']}: {item['recommendation']} Basis: {item['basis']}\n")
    handle.write("\n")


def coverage_limitation(record: CoverageRecord) -> str:
    if record.coverage_status == "PRESENT_UNSUPPORTED":
        return record.unsupported_reason or "Artifact present but unsupported by the current parser set."
    if record.coverage_status == "PRESENT_PARSE_FAILED":
        return record.failure_reason or "Parser failed; review error log."
    if record.coverage_status == "PRESENT_UNKNOWN_SCHEMA":
        return "SQLite opened but schema was not recognized by supported parsers."
    if record.coverage_status == "PRESENT_PARTIALLY_PARSED":
        return "Some tables or fields were not parsed."
    if record.coverage_status == "PRESENT_PARSED_NO_WINDOW_RECORDS":
        return "Parsed records may exist outside the requested window; none normalized inside it."
    if record.wal_present:
        return "WAL material present; no specialized deleted-record recovery was performed."
    return record.examiner_note or "Coverage status should be considered when interpreting absence of records."


def write_unparsed_sources_section(
    handle: Any,
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
) -> None:
    material = [
        record for record in records
        if record.coverage_status in {
            "PRESENT_UNSUPPORTED",
            "PRESENT_PARSER_DISABLED",
            "PRESENT_PARSE_FAILED",
            "PRESENT_PARTIALLY_PARSED",
            "PRESENT_ONLY_WAL_SHM",
            "PRESENT_ENCRYPTED_OR_INACCESSIBLE",
            "PRESENT_UNKNOWN_SCHEMA",
            "NOT_COLLECTED",
            "OUTSIDE_ACQUISITION_SCOPE",
        }
    ]
    unsupported_apps = [app for app in app_records if not app.parser_available]
    if not material and not unsupported_apps:
        handle.write("No material unparsed or unsupported evidence sources were identified by the coverage auditor.\n\n")
        return
    for record in material[:200]:
        handle.write(
            f"- {record.artifact_name} | {record.coverage_status} | parser={record.parser_name or 'none'} | "
            f"path={record.relative_path or record.absolute_path} | limitation={coverage_limitation(record)}\n"
        )
    for app in unsupported_apps:
        high_value = f" | high-value category={', '.join(app.likely_high_value_artifacts)}" if app.likely_high_value_artifacts else ""
        handle.write(
            f"- Application container was present: {app.app_name} | files={app.files_found} | "
            f"databases={app.databases_found} | unsupported_files={app.unsupported_files}{high_value}\n"
        )
    handle.write("\n")


def write_coverage_effect_section(
    handle: Any,
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
) -> None:
    summary = coverage_summary(records, app_records)
    level = summary["supported_examination_status"]
    handle.write(f"Supported examination status: {level}\n\n")
    handle.write(f"Acquisition limitations identified: {summary.get('acquisition_limitation_count', 0)}\n\n")
    handle.write(f"Evidence-not-collected sources identified: {summary.get('not_collected_source_count', 0)}\n\n")
    if level == "COMPLETE_FOR_SUPPORTED_ARTIFACTS":
        handle.write("The report may be complete for supplied artifacts supported by the current parser set while still being limited by the encrypted iPhone backup acquisition type.\n\n")
    elif level == "PARTIAL_SUPPORTED_COVERAGE":
        handle.write("The report is partial for supported artifacts: some relevant supplied artifacts were unsupported, partially parsed, unexpectedly absent, or outside parser scope.\n\n")
    elif level == "EXAMINATION_GAPS_PRESENT":
        handle.write("The report has examination gaps: parser failures, unsupported high-value present artifacts, unknown schemas, or partial parsing may affect negative conclusions.\n\n")
    elif level == "INSUFFICIENT_EXAMINATION":
        handle.write("Coverage is insufficient for broad conclusions about the requested activity.\n\n")
    else:
        handle.write("Coverage completeness is unknown.\n\n")
    handle.write(
        "Absence statements in this report should be read using the hierarchy: direct record identified; relevant supported artifact parsed with no matching record; artifact partially parsed; artifact unsupported; parser failed; expected artifact not present in supplied acquisition; acquisition-type limitation; source not separately collected. Additional evidence recommendations do not by themselves reduce supported-parser coverage.\n\n"
    )


def write_allegation_time_analysis(handle: Any, ctx: CaseContext, window_events: List[Event]) -> None:
    if not ctx.allegation_times:
        handle.write("No allegation times were supplied.\n\n")
        return
    for allegation in ctx.allegation_times:
        prior = [event for event in window_events if event.timestamp and event.timestamp <= allegation]
        subsequent = [event for event in window_events if event.timestamp and event.timestamp >= allegation]
        within_30 = events_near_times(window_events, [allegation], timedelta(seconds=30))
        within_1 = events_near_times(window_events, [allegation], timedelta(minutes=1))
        within_corr = events_near_times(window_events, [allegation], timedelta(minutes=ctx.correlation_window_minutes))
        comms = [event for event in within_corr if is_communication(event) or is_attachment(event)]
        net_ops = [
            event for event in within_corr
            if event.metadata.get("network_event")
            and event.metadata.get("timestamp_reliability") not in ("configuration_only", "filesystem_only")
        ]
        config_only = [
            event for event in within_corr
            if event.metadata.get("network_event") and event.metadata.get("timestamp_reliability") == "configuration_only"
        ]
        handle.write(f"### Allegation time: {format_dt(allegation)}\n\n")
        handle.write(f"- Closest prior event: {event_summary(max(prior, key=lambda e: e.timestamp)) if prior else 'none'}\n")
        handle.write(f"- Closest subsequent event: {event_summary(min(subsequent, key=lambda e: e.timestamp)) if subsequent else 'none'}\n")
        handle.write(f"- Events within 30 seconds: {len(within_30)}\n")
        handle.write(f"- Events within 1 minute: {len(within_1)}\n")
        handle.write(f"- Events within correlation window (+/- {ctx.correlation_window_minutes} minutes): {len(within_corr)}\n")
        handle.write(f"- Communications active at that time window: {len(comms)}\n")
        handle.write(f"- Network operational records at that time window: {len(net_ops)}\n")
        handle.write(f"- Configuration-only records at that time window: {len(config_only)}\n")
        handle.write("- Evidence interpretation: temporal proximity is reported for examiner review and does not establish causation.\n")
        handle.write("- Limitations: absence of a normalized event near this time does not prove absence of activity; source artifacts may be unavailable or outside backup scope.\n\n")


def map_conversations_by_message(conversations: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    mapped: Dict[str, Dict[str, Any]] = {}
    for conversation in conversations:
        for message in conversation.get("messages", []):
            rowid = message.get("rowid")
            if rowid not in (None, ""):
                mapped[str(rowid)] = conversation
    return mapped


def event_stable_id(event: Event) -> str:
    md = event.metadata or {}
    return "|".join(
        [
            format_dt(event.timestamp),
            event.source,
            event.event_type,
            str(md.get("rowid") or md.get("message_rowid") or md.get("attachment_rowid") or md.get("raw_record_identifier") or event.details[:80]),
        ]
    )


def attachment_stable_key(event: Event) -> str:
    md = event.metadata or {}
    file_meta = md.get("file") if isinstance(md.get("file"), dict) else {}
    return "|".join(
        str(value or "")
        for value in (
            md.get("message_rowid"),
            md.get("attachment_rowid"),
            md.get("guid"),
            md.get("filename"),
            md.get("sha256") or file_meta.get("sha256"),
        )
    )


def attachment_sort_key(event: Event) -> Tuple[int, str, datetime]:
    md = event.metadata or {}
    rowid = safe_int(md.get("attachment_rowid"))
    return (
        rowid if rowid is not None else 10**18,
        str(md.get("filename") or ""),
        event.timestamp or datetime.max,
    )


def build_attachment_index(events: List[Event]) -> Dict[str, List[Event]]:
    index: Dict[str, List[Event]] = {}
    seen_by_message: Dict[str, set] = {}
    for event in events:
        if event.source != "sms.db attachment":
            continue
        message_rowid = (event.metadata or {}).get("message_rowid")
        if message_rowid in (None, ""):
            continue
        key = str(message_rowid)
        stable = attachment_stable_key(event)
        seen = seen_by_message.setdefault(key, set())
        if stable in seen:
            continue
        seen.add(stable)
        index.setdefault(key, []).append(event)
    for key in list(index):
        index[key] = sorted(index[key], key=attachment_sort_key)
    return index


def direction_attachment_relationship(direction: Any) -> str:
    text = str(direction or "").upper()
    if text in {"FROM_DEVICE", "OUTGOING", "SENT"} or "FROM" in text or "OUT" in text:
        return "SENT_ATTACHMENT"
    if text in {"TO_DEVICE", "INCOMING", "RECEIVED"} or "TO" in text or "IN" in text:
        return "RECEIVED_ATTACHMENT"
    return "INCLUDED_ATTACHMENT"


def human_size(value: Any) -> str:
    num = safe_int(value)
    if num is None:
        return ""
    if num >= 1024 * 1024:
        return f"{num:,} bytes ({num / (1024 * 1024):.1f} MiB)"
    if num >= 1024:
        return f"{num:,} bytes ({num / 1024:.1f} KiB)"
    return f"{num:,} bytes"


def exif_summary_from_event(event: Event) -> str:
    exif = (event.metadata or {}).get("exif")
    if not isinstance(exif, dict) or not exif:
        return ""
    return ", ".join(f"{key}={exif[key]}" for key in sorted(exif.keys())[:12])


def attachment_metadata_summary(event: Event) -> Dict[str, Any]:
    md = event.metadata or {}
    file_meta = md.get("file") if isinstance(md.get("file"), dict) else {}
    return {
        "attachment_event_id": md.get("normalized_event_id", ""),
        "message_rowid": str(md.get("message_rowid") or ""),
        "attachment_rowid": str(md.get("attachment_rowid") or ""),
        "filename": str(md.get("filename") or ""),
        "transfer_name": str(md.get("transfer_name") or ""),
        "mime_type": str(md.get("mime_type") or ""),
        "size_bytes": safe_int(md.get("total_bytes") or file_meta.get("size")) or 0,
        "total_bytes": safe_int(md.get("total_bytes") or file_meta.get("size")) or 0,
        "guid": str(md.get("guid") or ""),
        "sha256": str(md.get("sha256") or file_meta.get("sha256") or ""),
        "recovered_path": str(md.get("recovered_path") or file_meta.get("path") or ""),
        "source_artifact": str(md.get("db") or md.get("source_artifact") or ""),
        "timestamp": format_dt(event.timestamp),
        "timestamp_basis": str(md.get("attachment_event_timestamp_basis") or ""),
        "parent_message_timestamp": str(md.get("parent_message_timestamp") or ""),
        "attachment_created_timestamp": str(md.get("attachment_created_timestamp") or ""),
        "attachment_start_timestamp": str(md.get("attachment_start_timestamp") or ""),
        "filesystem_status": str(md.get("filesystem_status") or ("FOUND" if file_meta else "")),
        "confidence": event.confidence_score,
        "coverage_status": str(md.get("normalized_coverage_status") or ""),
        "normalized_event_id": str(md.get("normalized_event_id") or ""),
        "attachment_entity_id": str(md.get("attachment_entity_id") or ""),
        "file_hash_entity_id": str(md.get("file_hash_entity_id") or ""),
        "relationship_id": str((md.get("normalized_relationship_ids") or [""])[0] if isinstance(md.get("normalized_relationship_ids"), list) and md.get("normalized_relationship_ids") else md.get("relationship_id") or ""),
        "relationship_ids": md.get("normalized_relationship_ids") if isinstance(md.get("normalized_relationship_ids"), list) else [],
        "exif_summary": exif_summary_from_event(event),
    }


def link_message_attachments(events: List[Event]) -> Dict[str, List[Event]]:
    index = build_attachment_index(events)
    messages_by_rowid: Dict[str, Event] = {}
    for event in events:
        if event.source == "sms.db":
            rowid = (event.metadata or {}).get("rowid")
            if rowid not in (None, ""):
                messages_by_rowid[str(rowid)] = event
    for rowid, attachments in index.items():
        parent = messages_by_rowid.get(rowid)
        if not parent:
            continue
        parent_md = parent.metadata or {}
        direction = parent_md.get("direction", "")
        linked = []
        for attachment in attachments:
            amd = attachment.metadata or {}
            amd["parent_message_rowid"] = rowid
            amd["parent_message_guid"] = parent_md.get("guid", "")
            amd["parent_message_direction"] = direction
            amd["parent_chat_identifier"] = parent_md.get("chat_identifier", "")
            amd["parent_chat_rowid"] = parent_md.get("chat_rowid", "")
            amd["parent_raw_contact"] = parent_md.get("raw_contact", "")
            amd["parent_resolved_contact"] = parent_md.get("resolved_contact", "")
            amd["parent_service"] = parent_md.get("service", "")
            amd["parent_message_stable_id"] = event_stable_id(parent)
            amd["attachment_relationship_type"] = direction_attachment_relationship(direction)
            linked.append(attachment_metadata_summary(attachment))
        parent_md["linked_attachments"] = linked
        parent_md["linked_attachment_count"] = len(linked)
    for event in events:
        if event.source == "sms.db":
            event.metadata.setdefault("linked_attachments", [])
            event.metadata.setdefault("linked_attachment_count", 0)
    return index


def build_single_report_clusters(ctx: CaseContext, events: List[Event]) -> List[Dict[str, Any]]:
    clusters = []
    seen = set()
    window = timedelta(minutes=max(0, ctx.correlation_window_minutes))
    for event in events:
        if not event.timestamp:
            continue
        related = [other for other in events if other.timestamp and abs(other.timestamp - event.timestamp) <= window]
        if len(related) < 2:
            continue
        ids = sorted(event_stable_id(item) for item in related)
        earliest = min(item.timestamp for item in related if item.timestamp)
        cluster_id = hashlib.sha1((format_dt(earliest) + "|" + "|".join(ids)).encode("utf-8")).hexdigest()[:12]
        if cluster_id in seen:
            continue
        seen.add(cluster_id)
        score = sum(correlation_event_score(item) for item in related)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "central_timestamp": event.timestamp,
                "start": earliest,
                "end": max(item.timestamp for item in related if item.timestamp),
                "score": score,
                "sources": sorted({item.source for item in related}),
                "events": sorted(related, key=lambda e: (e.timestamp or datetime.max, e.source)),
                "shared_entities": shared_entities_for_events(related),
            }
        )
    return sorted(clusters, key=lambda c: (c["start"], c["cluster_id"]))


def map_clusters_by_event(clusters: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    mapped: Dict[str, List[Dict[str, Any]]] = {}
    for cluster in clusters:
        for event in cluster.get("events", []):
            mapped.setdefault(event_stable_id(event), []).append(cluster)
    return mapped


def shared_entities_for_events(events: List[Event]) -> List[str]:
    counts: Dict[str, int] = {}
    labels: Dict[str, str] = {}
    for event in events:
        for entity_id, entity_type, label in extract_entities(event):
            counts[entity_id] = counts.get(entity_id, 0) + 1
            labels[entity_id] = f"{entity_type}:{label}"
    return [labels[key] for key, count in sorted(counts.items()) if count > 1][:20]


def write_enriched_event(
    handle: Any,
    ctx: CaseContext,
    event: Event,
    window_events: List[Event],
    conversations_by_message: Dict[str, Dict[str, Any]],
    cluster_by_event: Dict[str, List[Dict[str, Any]]],
    attachment_index: Dict[str, List[Event]],
) -> None:
    md = event.metadata or {}
    handle.write(f"### {format_dt(event.timestamp)} - {event.source} - {event.event_type}\n\n")
    handle.write(f"Direct observation: {event_brief(event)}\n\n")
    handle.write(f"Confidence: {event.confidence_score} ({event.evidence_strength}) - {event.confidence_basis}\n\n")
    handle.write(f"Provenance: {event_provenance(event)}\n\n")
    normalized_id = md.get("normalized_event_id")
    if normalized_id:
        entity_links = md.get("normalized_entity_links") if isinstance(md.get("normalized_entity_links"), list) else []
        relationship_ids = md.get("normalized_relationship_ids") if isinstance(md.get("normalized_relationship_ids"), list) else []
        cluster_ids = md.get("normalized_correlation_cluster_ids") if isinstance(md.get("normalized_correlation_cluster_ids"), list) else []
        linked_entities = ", ".join(
            f"{link.get('role')}={link.get('entity_id')}" for link in entity_links[:12] if isinstance(link, dict)
        ) or "none"
        handle.write(f"Normalized event ID: `{normalized_id}`\n\n")
        handle.write(f"Event category: `{md.get('normalized_event_category', '')}`\n\n")
        handle.write(f"Normalized event type: `{md.get('normalized_event_type', '')}`\n\n")
        handle.write(f"Linked entities: {linked_entities}\n\n")
        handle.write(f"Relationships: {', '.join(relationship_ids[:12]) if relationship_ids else 'none'}\n\n")
        handle.write(f"Correlation cluster IDs: {', '.join(cluster_ids[:12]) if cluster_ids else 'none'}\n\n")
        handle.write(f"Coverage status: `{md.get('normalized_coverage_status', 'UNKNOWN')}`\n\n")
    handle.write("Entities and relationships:\n")
    relationships = event_relationship_lines(event)
    for line in relationships or ["No explicit relationship entities were normalized for this event."]:
        handle.write(f"- {line}\n")
    handle.write("\n")
    write_event_conversation_context(handle, event, conversations_by_message, ctx)
    write_event_attachment_details(handle, event, attachment_index)
    write_event_network_context(handle, ctx, event, window_events)
    write_event_correlations(handle, ctx, event, cluster_by_event)
    handle.write(f"Interpretive limitation: {event_limitation(event)}\n\n")


def event_brief(event: Event) -> str:
    text = event.details.replace("\n", " ")
    return text if len(text) <= 500 else text[:497] + "..."


def event_provenance(event: Event) -> str:
    md = event.metadata or {}
    parts = []
    for label, key in (
        ("database/source artifact", "db"),
        ("source artifact", "source_artifact"),
        ("table/record", "table"),
        ("ROWID", "rowid"),
        ("message ROWID", "message_rowid"),
        ("attachment ROWID", "attachment_rowid"),
        ("record identifier", "raw_record_identifier"),
        ("GUID", "guid"),
    ):
        value = md.get(key)
        if value not in (None, ""):
            parts.append(f"{label}={value}")
    raw = md.get("raw") if isinstance(md.get("raw"), dict) else {}
    if raw.get("_rowid") and not any(part.startswith("ROWID=") for part in parts):
        parts.append(f"ROWID={raw.get('_rowid')}")
    return " | ".join(parts) if parts else "Normalized event metadata did not include a database path or primary record identifier."


def event_relationship_lines(event: Event) -> List[str]:
    md = event.metadata or {}
    lines = []
    contact = event_contact(event)
    if event.source == "sms.db" and contact:
        direction = str(md.get("direction") or "").upper()
        if direction == "FROM_DEVICE":
            lines.append(f"Examined iPhone sent a message to {contact}")
        elif direction == "TO_DEVICE":
            lines.append(f"{contact} sent a message to the examined iPhone")
        else:
            lines.append(f"Message participant recorded: {contact}")
    if event.source == "CallHistory" and contact:
        direction = str(md.get("direction") or "").upper()
        if direction == "OUTGOING":
            lines.append(f"Examined iPhone called {contact}")
        elif direction == "INCOMING":
            lines.append(f"{contact} called the examined iPhone")
        else:
            lines.append(f"Call participant recorded: {contact}")
        if md.get("location_label"):
            lines.append(f"{md.get('location_label_type') or 'Call record location label'}: {md.get('location_label')} (not device/caller physical location)")
    if md.get("chat_identifier"):
        lines.append(f"Message ASSOCIATED_WITH_CHAT {md['chat_identifier']}")
    if md.get("filename"):
        lines.append(f"Message INCLUDED_ATTACHMENT {Path(str(md['filename'])).name}")
    for linked in md.get("linked_attachments", []) if isinstance(md.get("linked_attachments"), list) else []:
        if isinstance(linked, dict) and linked.get("filename"):
            lines.append(f"Message INCLUDED_ATTACHMENT {Path(str(linked['filename'])).name}")
    file_meta = md.get("file") if isinstance(md.get("file"), dict) else {}
    if file_meta.get("sha256"):
        lines.append(f"Attachment HASHED_AS {file_meta['sha256']}")
    raw = md.get("raw") if isinstance(md.get("raw"), dict) else {}
    if event.source == "Safari" and raw.get("url"):
        domain = domain_from_url(str(raw.get("url")))
        lines.append(f"Safari VISITED {domain or raw.get('url')}")
    if md.get("ssid"):
        lines.append(f"Device RECORDED_WIFI_NETWORK {md['ssid']}")
    if md.get("bssid"):
        lines.append(f"Device RECORDED_BSSID {md['bssid']}")
    if md.get("bluetooth_name") or md.get("bluetooth_address"):
        lines.append(f"Device RECORDED_BLUETOOTH_DEVICE {md.get('bluetooth_name') or md.get('bluetooth_address')}")
    for key in ("local_ip", "remote_ip"):
        if md.get(key):
            lines.append(f"Event RECORDED_IP {md[key]} ({classify_ip(md[key])})")
    return lines


def write_event_conversation_context(
    handle: Any,
    event: Event,
    conversations_by_message: Dict[str, Dict[str, Any]],
    ctx: CaseContext,
) -> None:
    handle.write("Conversation context:\n")
    rowid = str((event.metadata or {}).get("rowid") or "")
    conversation = conversations_by_message.get(rowid)
    if not conversation or event.source != "sms.db":
        handle.write("- Not applicable or no same-chat context was reconstructed for this event.\n\n")
        return
    for message in conversation.get("messages", []):
        marker = "IN-WINDOW" if message.get("section") == "during" else "CONTEXT OUTSIDE REQUESTED WINDOW"
        handle.write(
            f"- {message.get('timestamp')} [{marker}] {message.get('direction')} "
            f"contact={message.get('contact')} service={message.get('service')} "
            f"attachments={message.get('attachment_summary')} guid={message.get('guid')} text={message.get('text')}\n"
        )
    handle.write("\n")


def write_event_attachment_details(handle: Any, event: Event, attachment_index: Optional[Dict[str, List[Event]]] = None) -> None:
    handle.write("Attachment details:\n")
    md = event.metadata or {}
    attachment_index = attachment_index or {}
    linked: List[Event] = []
    if event.source == "sms.db":
        rowid = md.get("rowid")
        if rowid not in (None, ""):
            linked = attachment_index.get(str(rowid), [])
    if linked:
        handle.write(f"- Linked attachment count: {len(linked)}\n\n")
        for idx, attachment in enumerate(linked, 1):
            handle.write(f"#### Attachment {idx}\n\n")
            write_single_attachment_metadata(handle, attachment, parent_event=event)
        return
    if event.source == "sms.db attachment" or md.get("filename"):
        write_single_attachment_metadata(handle, event, parent_event=None)
        return
    handle.write("- No attachment metadata was identified for this event.\n\n")


def write_single_attachment_metadata(handle: Any, attachment: Event, parent_event: Optional[Event] = None) -> None:
    md = attachment.metadata or {}
    file_meta = md.get("file") if isinstance(md.get("file"), dict) else {}
    summary = attachment_metadata_summary(attachment)
    parent_md = parent_event.metadata if parent_event else {}
    relationship_ids = summary.get("relationship_ids") or []
    attachment_entity = summary.get("attachment_entity_id") or ""
    if not attachment_entity:
        for link in md.get("normalized_entity_links", []) if isinstance(md.get("normalized_entity_links"), list) else []:
            if isinstance(link, dict) and link.get("role") == "attachment":
                attachment_entity = str(link.get("entity_id") or "")
                break
    handle.write(f"- Parent message ROWID: {summary.get('message_rowid') or parent_md.get('rowid', '')}\n")
    handle.write(f"- Attachment ROWID: {summary.get('attachment_rowid')}\n")
    handle.write(f"- Filename: {summary.get('filename')}\n")
    handle.write(f"- Transfer name: {summary.get('transfer_name')}\n")
    handle.write(f"- MIME type: {summary.get('mime_type')}\n")
    handle.write(f"- File size: {human_size(summary.get('size_bytes')) or summary.get('size_bytes') or ''}\n")
    handle.write(f"- Attachment GUID: {summary.get('guid')}\n")
    handle.write(f"- Recovered path: {summary.get('recovered_path')}\n")
    handle.write(f"- SHA-256: {summary.get('sha256')}\n")
    handle.write(f"- EXIF summary: {summary.get('exif_summary') or 'none available'}\n")
    handle.write(f"- Source database: {summary.get('source_artifact')}\n")
    handle.write(f"- Timestamp: {summary.get('timestamp')}\n")
    if summary.get("parent_message_timestamp"):
        handle.write(f"- Parent message timestamp: {summary.get('parent_message_timestamp')}\n")
    handle.write(f"- Attachment created timestamp: {summary.get('attachment_created_timestamp') or 'unavailable'}\n")
    handle.write(f"- Attachment start timestamp: {summary.get('attachment_start_timestamp') or 'unavailable'}\n")
    handle.write(f"- Timestamp basis: {summary.get('timestamp_basis')}\n")
    handle.write(f"- Filesystem status: {summary.get('filesystem_status')}\n")
    handle.write(f"- Confidence: {attachment.confidence_score} ({attachment.evidence_strength}) - {attachment.confidence_basis}\n")
    handle.write(f"- Coverage status: {summary.get('coverage_status') or md.get('normalized_coverage_status', 'UNKNOWN')}\n")
    handle.write(f"- Normalized attachment event ID: {summary.get('normalized_event_id')}\n")
    handle.write(f"- Attachment entity ID: {attachment_entity}\n")
    handle.write(f"- Relationship ID: {', '.join(relationship_ids) if relationship_ids else summary.get('relationship_id', '')}\n")
    handle.write("\n")


def write_event_network_context(handle: Any, ctx: CaseContext, event: Event, window_events: List[Event]) -> None:
    handle.write("Network context:\n")
    nearby = [
        other for other in window_events
        if other.metadata.get("network_event")
        and other.timestamp and event.timestamp
        and abs(other.timestamp - event.timestamp) <= timedelta(minutes=ctx.correlation_window_minutes)
    ]
    if event.metadata.get("network_event"):
        nearby.insert(0, event)
    seen = set()
    unique = []
    for item in nearby:
        key = event_stable_id(item)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    if not unique:
        handle.write("- No in-window structured network context was normalized near this event.\n")
        handle.write("- Packet evidence unavailable unless explicitly listed in the network summary.\n\n")
        return
    for item in unique[:10]:
        md = item.metadata
        reliability = md.get("timestamp_reliability") or "unknown"
        handle.write(
            f"- {format_dt(item.timestamp)} | {item.source} | {item.event_type} | "
            f"{reliability} | ssid={md.get('ssid','')} bssid={md.get('bssid','')} "
            f"bt={md.get('bluetooth_name') or md.get('bluetooth_address','')} ip={md.get('local_ip') or md.get('remote_ip','')} "
            f"bytes_sent={md.get('bytes_sent','')} bytes_received={md.get('bytes_received','')}\n"
        )
    handle.write("- Wi-Fi known-network, Bluetooth paired-device, and filesystem timestamp records are not treated as confirmed active network use.\n\n")


def write_event_correlations(
    handle: Any,
    ctx: CaseContext,
    event: Event,
    cluster_by_event: Dict[str, List[Dict[str, Any]]],
) -> None:
    handle.write("Correlated events:\n")
    clusters = cluster_by_event.get(event_stable_id(event), [])
    if not clusters:
        handle.write("- No other in-window events were found inside the configured correlation window.\n\n")
        return
    reported = set()
    for cluster in clusters:
        if cluster["cluster_id"] in reported:
            continue
        reported.add(cluster["cluster_id"])
        handle.write(f"- Cluster {cluster['cluster_id']} score={cluster['score']} shared_entities={', '.join(cluster.get('shared_entities', [])) or 'none'}\n")
        for other in cluster.get("events", []):
            if event_stable_id(other) == event_stable_id(event):
                continue
            delta = int((other.timestamp - event.timestamp).total_seconds()) if other.timestamp and event.timestamp else 0
            shared = ", ".join(shared_entities_for_events([event, other])) or "none"
            handle.write(
                f"  - {format_dt(other.timestamp)} | {other.source} | {other.event_type} | "
                f"delta={delta:+d}s | confidence={other.confidence_score} | shared={shared} | {event_brief(other)[:180]}\n"
            )
    handle.write("\n")


def event_limitation(event: Event) -> str:
    md = event.metadata or {}
    if md.get("network_event"):
        reliability = md.get("timestamp_reliability")
        if reliability == "configuration_only":
            return "This is a recorded configuration artifact and is not proof of active use during the window."
        if reliability == "filesystem_only":
            return "This is a filesystem timestamp and is not a confirmed connection time."
        if event.source == "Data Usage":
            return "Byte counters are reported only as recorded; cumulative counters are not window-specific traffic without valid delta evidence."
        return "Network context is reported only from explicit artifact values; no packet contents or endpoint ownership are inferred."
    if event.source == "sms.db":
        return "Message records do not establish transport path, intent, or Silent SMS by themselves."
    if event.source == "sms.db attachment":
        return "Attachment metadata requires examiner review of recovered content where available."
    return "Interpretation is limited to the normalized artifact record and available corroboration."


def write_single_cluster_summary(handle: Any, ctx: CaseContext, clusters: List[Dict[str, Any]]) -> None:
    if not clusters:
        handle.write("No unique in-window correlated activity clusters were identified.\n\n")
        return
    for cluster in clusters:
        handle.write(f"### Cluster {cluster['cluster_id']}\n\n")
        handle.write(f"- Start/end: {format_dt(cluster['start'])} to {format_dt(cluster['end'])}\n")
        handle.write(f"- Score: {cluster['score']}\n")
        handle.write(f"- Sources: {', '.join(cluster['sources'])}\n")
        handle.write(f"- Shared entities: {', '.join(cluster.get('shared_entities', [])) or 'none'}\n")
        handle.write("- Events:\n")
        for event in cluster.get("events", []):
            handle.write(f"  - {event_summary(event)}\n")
        handle.write("- Cautious interpretation: this is a temporal/entity correlation for examiner review and does not establish causation or malicious activity.\n\n")


def write_relationship_summary_table(handle: Any, relationships: List[Dict[str, Any]]) -> None:
    if not relationships:
        handle.write("No in-window relationships were derived from normalized events.\n\n")
        return
    handle.write("| Source entity | Relationship | Target entity | Timestamp | Evidence source | Confidence |\n")
    handle.write("|---|---|---|---|---|---:|\n")
    for edge in relationships[:250]:
        handle.write(
            f"| {edge.get('source_label','')} | {edge.get('relationship','')} | {edge.get('target_label','')} | "
            f"{edge.get('timestamp','')} | {edge.get('event_source','')} / {edge.get('event_type','')} | {edge.get('confidence_score','')} |\n"
        )
    handle.write("\n")


def write_single_network_summary(
    handle: Any,
    network_summary: Dict[str, Any],
    network_events: List[Event],
    network_indicators: List[Dict[str, Any]],
) -> None:
    operational = [
        event for event in network_events
        if event.metadata.get("timestamp_reliability") not in ("configuration_only", "filesystem_only")
    ]
    config = [event for event in network_events if event.metadata.get("timestamp_reliability") == "configuration_only"]
    handle.write(f"- In-window timestamped operational network events: {len(operational)}\n")
    handle.write(f"- Directly related configuration context records: {len(config)}\n")
    handle.write(f"- Validated IP indicators: {len([i for i in network_indicators if i['indicator_type'] == 'ip'])}\n")
    handle.write(f"- SSIDs: {', '.join(network_summary.get('wifi_summary', {}).get('known_ssids', [])[:20]) or 'none'}\n")
    handle.write(f"- BSSIDs: {', '.join(network_summary.get('wifi_summary', {}).get('bssids', [])[:20]) or 'none'}\n")
    handle.write(f"- Bluetooth devices: {', '.join(network_summary.get('bluetooth_summary', {}).get('devices', [])[:20]) or 'none'}\n")
    handle.write(f"- Direct byte counters: {network_summary.get('data_usage_summary', {}).get('byte_counter_records', 0)}\n")
    handle.write(f"- Packet evidence present: {'yes' if network_summary.get('packet_capture_evidence') else 'no'}\n\n")
    handle.write("Limitations: configuration-only records are not active-use records; paired Bluetooth devices are not confirmed connections; BSSID/Bluetooth MAC values are local-network or accessory identifiers, not remote internet endpoints.\n\n")


def write_single_conclusion(handle: Any, ctx: CaseContext, window_events: List[Event], network_summary: Dict[str, Any]) -> None:
    cov_summary = coverage_summary(ctx.coverage_records, ctx.app_coverage_records) if ctx.coverage_records else {"completeness_level": "UNKNOWN"}
    handle.write(
        f"The exact-window analysis identified {len(window_events)} normalized event(s) between "
        f"`{format_dt(ctx.start)}` and `{format_dt(ctx.end)}`. The report does not use outside-window context "
        "as standalone timeline evidence.\n\n"
    )
    handle.write(f"Coverage completeness for conclusions: {cov_summary.get('completeness_level', 'UNKNOWN')}.\n\n")
    handle.write(
        "Direct evidence of Silent SMS was not identified in the supported, parsed handset artifacts represented by this workflow. No-text messages are not proof of Silent SMS, "
        "and attachment-only iMessages are not proof of Silent SMS. A standard backup generally cannot confirm Silent SMS; "
        "carrier signaling, baseband diagnostics, CommCenter/CoreTelephony logs, sysdiagnose material, or packet/network telemetry may be required.\n\n"
    )
    handle.write(
        "Direct command activity or unusual network transmission is not concluded unless supported by explicit operational artifacts. "
        "Configuration records, paired-device records, and filesystem timestamps are reported as context only.\n\n"
    )


def write_embedded_ai_summary(
    handle: Any,
    ctx: CaseContext,
    window_events: List[Event],
    inventory: List[Dict[str, Any]],
    clusters: List[Dict[str, Any]],
    hypotheses: List[Dict[str, Any]],
) -> None:
    handle.write("Examiner-review-required draft. AI text cannot override deterministic findings.\n\n")
    try:
        payload = {
            "model": ctx.ollama_model,
            "stream": False,
            "prompt": build_single_report_ai_prompt(ctx, window_events, inventory, clusters, hypotheses),
        }
        data = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(ctx.ollama_url, data=data, headers={"Content-Type": "application/json"})
        with urlrequest.urlopen(req, timeout=ctx.ollama_timeout) as resp:
            result = json.loads(resp.read().decode("utf-8", errors="replace"))
        handle.write(result.get("response") or json_dumps(result))
        handle.write("\n\n")
    except Exception as exc:
        ctx.errors.log("single_report_ai", ctx.ollama_url, exc, "embedded ai summary")
        handle.write(f"AI summary was requested, but Ollama was unavailable, timed out, or returned an error after up to {ctx.ollama_timeout} seconds. See parser errors.\n\n")


def build_single_report_ai_prompt(
    ctx: CaseContext,
    window_events: List[Event],
    inventory: List[Dict[str, Any]],
    clusters: List[Dict[str, Any]],
    hypotheses: List[Dict[str, Any]],
) -> str:
    knowledge = ctx.case_knowledge or {}
    normalized_events = knowledge.get("events", [])[: ctx.ai_top_events] if knowledge else []
    normalized_entities = knowledge.get("entities", [])[:100] if knowledge else []
    normalized_relationships = knowledge.get("relationships", [])[:150] if knowledge else []
    normalized_clusters = knowledge.get("correlation_clusters", [])[:20] if knowledge else []
    cov_summary = coverage_summary(ctx.coverage_records, ctx.app_coverage_records) if ctx.coverage_records else {"completeness_level": "UNKNOWN", "material_coverage_gaps": []}
    cov_score = build_evidence_coverage_score(ctx, ctx.coverage_records, ctx.app_coverage_records, window_events) if ctx.coverage_records else {}
    finding_confidence = [item.as_dict() for item in assess_finding_confidence(ctx, ctx.coverage_records, ctx.app_coverage_records, window_events)] if ctx.coverage_records else []
    deterministic = {
        "scope": {"start": format_dt(ctx.start), "end": format_dt(ctx.end), "window_only": True},
        "normalized_events": normalized_events,
        "entity_summaries": normalized_entities,
        "relationships": normalized_relationships,
        "correlation_clusters": normalized_clusters,
        "inventory": inventory,
        "hypotheses": hypotheses,
        "coverage_summary": cov_summary,
        "coverage_score": cov_score,
        "finding_confidence": finding_confidence,
        "finding_completeness": knowledge.get("finding_completeness", {}),
        "examination_status": knowledge.get("examination_status", {}),
        "acquisition_status": knowledge.get("acquisition_status", {}),
        "forensic_blind_spots": build_forensic_blind_spots(ctx.coverage_records, ctx.app_coverage_records)[:50] if ctx.coverage_records else [],
        "additional_evidence_recommendations": build_additional_evidence_recommendations(ctx.coverage_records, ctx.app_coverage_records) if ctx.coverage_records else [],
        "unsupported_artifacts": [r.as_dict() for r in ctx.coverage_records if r.coverage_status in {"PRESENT_UNSUPPORTED", "PRESENT_UNKNOWN_SCHEMA", "PRESENT_PARTIALLY_PARSED"}][:50],
        "parser_failures": [r.as_dict() for r in ctx.coverage_records if r.coverage_status == "PRESENT_PARSE_FAILED"][:50],
    }
    return (
        "Draft a concise examiner-facing summary using only the normalized evidence supplied. "
        "Every factual statement must be traceable to a normalized_event_id or relationship_id. "
        "Do not infer identity from aliases unless a direct relationship links them. "
        "Do not invent facts. Do not claim Silent SMS, command activity, causation, malicious intent, or unusual "
        "network transmission without direct evidence. Distinguish configuration from active use and local MAC "
        "identifiers from remote endpoints. You must never interpret absence of normalized records as absence of "
        "underlying evidence unless the relevant artifact was present, supported, successfully parsed, and covered "
        "the requested time window. When coverage is incomplete, explicitly say the answer is incomplete. Distinguish "
        "no relevant parsed record, artifact absent, artifact unsupported, parser failed, acquisition did not include "
        "the source, and evidence unavailable. Do not use the phrase 'no evidence' without a coverage qualification. "
        "Do not raise confidence above deterministic finding_confidence ceilings supplied in the JSON. "
        "Do not describe an acquisition limitation as a parser failure. "
        "Do not describe evidence that is ordinarily absent from an encrypted iPhone backup as unexpectedly missing. "
        "Distinguish complete examination of supplied supported evidence from whether the acquisition type is sufficient to answer the question. "
        "An answer may be COMPLETE_FOR_SUPPORTED_ARTIFACTS and simultaneously LIMITED_BY_ACQUISITION_TYPE. "
        "Do not turn recommended additional evidence into an allegation that the current examination was defective. "
        "Do not describe an attachment as sent or received unless the parent message direction supports that classification. "
        "Note limitations.\n\n"
        f"Evidence JSON:\n{json_dumps(deterministic)}"
    )


def write_error_summary(handle: Any, ctx: CaseContext, error_path: Path) -> None:
    handle.write(f"- Parser error count: {len(ctx.errors.records)}\n")
    if not ctx.errors.records:
        handle.write("- Affected artifacts: none recorded.\n")
        handle.write("- Material limitation: no parser errors were recorded.\n\n")
        return
    affected = []
    for record in ctx.errors.records:
        for line in record.splitlines():
            if line.startswith("artifact="):
                affected.append(line.replace("artifact=", "", 1))
                break
    for artifact in affected[:20]:
        handle.write(f"- Affected artifact: {artifact}\n")
    handle.write("- Material limitation: review the error log to determine whether parser failures limit any specific conclusion. Full tracebacks are kept out of this final report.\n")
    handle.write(f"- Error log: `{error_path}`\n\n")


def build_artifact_inventory(ctx: CaseContext, events: Optional[List[Event]] = None) -> List[Dict[str, Any]]:
    definitions = [
        ("sms.db", ("sms.db",), (), "YES", ("sms",), ("sms.db", "sms.db attachment")),
        ("CallHistory.storedata", ("CallHistory.storedata",), (), "YES", ("call_history",), ("CallHistory",)),
        ("AddressBook.sqlitedb", ("AddressBook.sqlitedb",), (), "YES", ("contacts",), ()),
        ("Safari History.db", ("History.db",), ("safari",), "YES", ("safari",), ("Safari",)),
        ("Photos.sqlite", ("Photos.sqlite",), (), "PARTIAL", ("photos",), ("Photos",)),
        ("NoteStore.sqlite", ("NoteStore.sqlite",), (), "PARTIAL", ("notes",), ("Notes",)),
        ("Mail / Envelope Index", ("Envelope Index", "Mail.sqlite"), (), "PARTIAL", ("mail",), ("Mail",)),
        ("Calendar.sqlitedb", ("Calendar.sqlitedb", "Calendar.sqlite"), (), "PARTIAL", ("calendar",), ("Calendar",)),
        ("Reminders / CloudKitReminders.sqlite", ("CloudKitReminders.sqlite",), ("reminder",), "PARTIAL", ("reminders",), ("Reminders",)),
        ("KnowledgeC.db", ("knowledgeC.db",), (), "PARTIAL", ("knowledgec",), ("KnowledgeC",)),
        ("BulletinBoard.sqlite / Notifications", ("BulletinBoard.sqlite", "DeliveredNotifications.db", "NotificationUsage.sqlite"), ("notification",), "PARTIAL", ("notifications",), ("Notifications",)),
        ("Bluetooth artifacts", (), ("bluetooth",), "PARTIAL", ("plist_system", "system_files"), ("Bluetooth",)),
        ("AirDrop artifacts", (), ("airdrop", "sharing"), "PARTIAL", ("plist_system", "system_files"), ("AirDrop",)),
        ("Nearby Interaction artifacts", (), ("nearbyinteraction", "nearby interaction", "nearby"), "PARTIAL", ("plist_system", "system_files"), ("Nearby Interaction",)),
        ("Analytics / Diagnostics artifacts", (), ("analytics", "diagnostic", "diagnostics"), "PARTIAL", ("system_files",), ("Analytics/Diagnostics",)),
        ("Unified logs / tracev3 files", ("*.tracev3",), ("tracev3", "uuidtext", "logarchive"), "NO", ("system_files",), ("Unified/System Logs",)),
        ("CoreTelephony / CommCenter related artifacts", (), ("coretelephony", "commcenter"), "PARTIAL", ("system_files",), ("Filesystem",)),
        ("SMS attachments folder", (), ("library/sms/attachments", "sms/attachments"), "PARTIAL", ("sms",), ("sms.db attachment",)),
        ("Wi-Fi known networks", ("com.apple.wifi.plist", "com.apple.wifi.known-networks.plist", "com.apple.wifi-networks.plist"), ("wifi", "wi-fi"), "PARTIAL", ("wifi",), ("Wi-Fi",)),
        ("Wi-Fi operational/state artifacts", (), ("wifi", "networkd", "wirelessdomain"), "PARTIAL", ("wifi",), ("Wi-Fi",)),
        ("Bluetooth paired devices", ("com.apple.MobileBluetooth.devices.plist", "com.apple.MobileBluetooth.plist", "com.apple.Bluetooth.plist"), ("bluetooth",), "PARTIAL", ("bluetooth_network",), ("Bluetooth",)),
        ("Bluetooth operational/state artifacts", (), ("bluetoothd", "systemgroup.com.apple.bluetooth"), "PARTIAL", ("bluetooth_network",), ("Bluetooth",)),
        ("AirDrop artifacts", (), ("airdrop", "sharingd", "com.apple.sharing"), "PARTIAL", ("airdrop_nearby",), ("AirDrop/Nearby",)),
        ("Nearby/Continuity artifacts", (), ("nearbyd", "nearby", "proximity", "continuity", "handoff", "activitycontinuation"), "PARTIAL", ("airdrop_nearby",), ("AirDrop/Nearby",)),
        ("Network configuration", (), ("systemconfiguration", "networkextension", "networkd", "dhcp", "dns", "proxy"), "PARTIAL", ("network_configuration",), ("Network Configuration",)),
        ("VPN configuration", ("com.apple.networkextension.plist", "com.apple.vpn.managed.plist"), ("vpn", "neconfiguration"), "PARTIAL", ("network_configuration",), ("Network Configuration",)),
        ("Cellular/telephony artifacts", (), ("commcenter", "coretelephony", "baseband", "carrier", "ims", "cellular"), "PARTIAL", ("cellular_telephony",), ("Cellular/Telephony",)),
        ("Data usage databases", ("DataUsage.sqlite", "CellularUsage.db"), ("netusage", "networkstatistics", "datausage", "cellularusage"), "PARTIAL", ("data_usage",), ("Data Usage",)),
        ("DNS/network statistics artifacts", (), ("dns", "networkstatistics", "netusage"), "PARTIAL", ("network_configuration", "data_usage"), ("Network Configuration", "Data Usage")),
        ("Packet capture files", ("*.pcap", "*.pcapng", "*.cap"), ("packet", "pcap"), "NO", (), ()),
        ("sysdiagnose", (), ("sysdiagnose",), "NO", (), ()),
        ("Wireless Diagnostics", (), ("wirelessdiagnostics", "wi-fi diagnostics"), "NO", (), ()),
        ("CoreCapture", (), ("corecapture",), "NO", (), ()),
        ("Unified logs", ("*.tracev3",), ("uuidtext", "logarchive"), "NO", (), ("Unified/System Logs",)),
    ]
    all_paths: List[Path] = ctx.all_files

    inventory: List[Dict[str, Any]] = []
    events = events or []
    for label, names, path_tokens, support, plugin_names, event_sources in definitions:
        matches: List[Path] = []
        lowered_tokens = tuple(token.lower() for token in path_tokens)
        for path in all_paths:
            path_text = str(path).replace("\\", "/").lower()
            name = path.name.lower()
            for wanted in names:
                wanted_lower = wanted.lower()
                if wanted_lower.startswith("*."):
                    if path.match(wanted):
                        matches.append(path)
                        break
                elif name == wanted_lower:
                    matches.append(path)
                    break
            else:
                if lowered_tokens and any(token in path_text for token in lowered_tokens):
                    matches.append(path)
        unique = sorted(set(matches), key=lambda p: str(p).lower())
        plugin_events = sum(int(ctx.plugin_stats.get(name, {}).get("events", 0)) for name in plugin_names)
        plugin_errors = sum(int(ctx.plugin_stats.get(name, {}).get("errors", 0)) for name in plugin_names)
        source_events = sum(1 for event in events if event.source in event_sources)
        event_count = source_events or plugin_events
        related_events = [event for event in events if event.source in event_sources]
        configuration_only = sum(1 for event in related_events if "configuration" in event.event_type.lower() or event.metadata.get("timestamp_reliability") == "configuration_only")
        operational_records = sum(1 for event in related_events if event.timestamp and event.metadata.get("timestamp_reliability") not in ("configuration_only", "filesystem_only"))
        parser_enabled = support != "NO"
        if not unique:
            parsed_successfully = "ABSENT"
        elif not parser_enabled:
            parsed_successfully = "UNSUPPORTED"
        elif plugin_errors:
            parsed_successfully = "FAILED"
        elif event_count:
            parsed_successfully = "EVENTS"
        else:
            parsed_successfully = "ZERO_EVENTS"
        inventory.append(
            {
                "artifact": label,
                "found": "YES" if unique else "NO",
                "file_count": len(unique),
                "parser_enabled": "YES" if parser_enabled else "NO",
                "parsed_successfully": parsed_successfully,
                "event_count": event_count,
                "configuration_only": configuration_only,
                "operational_records": operational_records,
                "errors": plugin_errors,
                "paths": [short_path(p, ctx.case_dir) for p in unique[:5]],
            }
        )
    return inventory


def build_conversation_context(ctx: CaseContext, events: List[Event]) -> List[Dict[str, Any]]:
    sms_events = [
        event
        for event in events
        if event.source == "sms.db"
        and event.event_type == "SMS/iMessage/RCS record"
        and in_range(event.timestamp, ctx.start, ctx.end)
    ]
    chat_ids = {
        event.metadata.get("chat_rowid")
        for event in sms_events
        if event.metadata.get("chat_rowid") not in (None, "")
    }
    if not chat_ids:
        return []

    db = ctx.case_dir / "decrypted/HomeDomain/Library/SMS/sms.db"
    if not db.exists():
        alternatives = ctx.find_named(["sms.db"])
        if alternatives:
            db = alternatives[0]
    if not db.exists():
        return []

    artifact = SQLiteArtifact(ctx, db, "conversation_context")
    conversations: List[Dict[str, Any]] = []
    context_count = max(0, ctx.conversation_context_count)
    for chat_rowid in sorted(chat_ids, key=lambda x: str(x)):
        rows = artifact.query(
            """
            SELECT
                message.ROWID AS rowid,
                CASE
                  WHEN message.date > 100000000000000000
                  THEN datetime((message.date / 1000000000) + 978307200, 'unixepoch')
                  ELSE datetime(message.date + 978307200, 'unixepoch')
                END AS ts,
                message.date AS raw_date,
                handle.id AS contact,
                message.service,
                message.is_from_me,
                message.text,
                message.guid,
                message.cache_has_attachments,
                chat.ROWID AS chat_rowid,
                chat.chat_identifier AS chat_identifier,
                chat.display_name AS chat_display_name,
                (
                    SELECT COUNT(*)
                    FROM message_attachment_join
                    WHERE message_attachment_join.message_id = message.ROWID
                ) AS attachment_count
            FROM message
            JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
            JOIN chat ON chat.ROWID = chat_message_join.chat_id
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            WHERE chat.ROWID = ?
            ORDER BY message.date, message.ROWID;
            """,
            (chat_rowid,),
        )
        if not rows:
            continue

        center_indexes = [
            index
            for index, row in enumerate(rows)
            if in_range(iso_or_common_datetime(row.get("ts")), ctx.start, ctx.end)
        ]
        wanted_indexes = set()
        for index in center_indexes:
            first = max(0, index - context_count)
            last = min(len(rows), index + context_count + 1)
            wanted_indexes.update(range(first, last))

        messages: List[Dict[str, Any]] = []
        for index in sorted(wanted_indexes):
            row = rows[index]
            ts = iso_or_common_datetime(row.get("ts"))
            attachment_count = safe_int(row.get("attachment_count")) or 0
            messages.append(
                {
                    "timestamp": format_dt(ts),
                    "section": section_for(ts, ctx.start, ctx.end),
                    "direction": "FROM_DEVICE" if row.get("is_from_me") == 1 else "TO_DEVICE",
                    "contact": ctx.contacts.resolve(row.get("contact")),
                    "raw_contact": row.get("contact"),
                    "service": row.get("service"),
                    "text": row.get("text") or "<NO TEXT CONTENT>",
                    "attachment_summary": f"{attachment_count} attachment(s)" if attachment_count else "none",
                    "guid": row.get("guid"),
                    "rowid": row.get("rowid"),
                }
            )

        first_row = rows[0]
        conversations.append(
            {
                "chat_rowid": chat_rowid,
                "chat_identifier": first_row.get("chat_identifier"),
                "chat_display_name": first_row.get("chat_display_name"),
                "messages": messages,
                "window_message_count": len(center_indexes),
            }
        )
    return conversations


def correlation_event_score(event: Event) -> int:
    source = event.source.lower()
    event_type = event.event_type.lower()
    details = event.details.lower()
    if event.metadata.get("network_event"):
        if "airdrop transfer" in event_type:
            return 6
        if "wi-fi connection" in event_type or "wifi connection" in event_type:
            return 5
        if "bluetooth connection" in event_type:
            return 5
        if "vpn" in event_type and "connection" in event_type:
            return 5
        if event.metadata.get("remote_ip"):
            return 5
        if "cellular registration" in event_type or "ims operational" in event_type:
            return 4
        if "data-usage" in event_type or source == "data usage":
            return 4
        if event.metadata.get("hostname") or event.metadata.get("domain"):
            return 3
        if "nearby peer" in event_type:
            return 3
        if event.evidence_strength == "FILESYSTEM_ONLY":
            return 1
        if "configuration" in event_type:
            return 1
        return 1
    if source == "callhistory":
        return 5
    if source == "sms.db attachment":
        return 5
    if source == "sms.db":
        if "<no text content>" in details:
            return 4
        return 3
    if source == "safari":
        return 3
    if source == "photos":
        return 3
    if source == "mail":
        return 3
    if source in {"notes", "calendar", "reminders"}:
        return 2
    if source == "notifications":
        return 2
    if event.significance == "LOW" or event_type in {"relevant file timestamp", "property list context"}:
        return 1
    return 1


def build_correlation_clusters(ctx: CaseContext, events: List[Event]) -> List[Dict[str, Any]]:
    timed_events = [event for event in events if event.timestamp]
    window = timedelta(minutes=max(0, ctx.correlation_window_minutes))
    clusters: List[Dict[str, Any]] = []
    seen = set()
    for central in timed_events:
        if not in_range(central.timestamp, ctx.start, ctx.end):
            continue
        related = [
            event
            for event in timed_events
            if abs(event.timestamp - central.timestamp) <= window
        ]
        score = sum(correlation_event_score(event) for event in related)
        if score < ctx.min_correlation_score:
            continue
        key = tuple(
            sorted(
                (format_dt(event.timestamp), event.source, event.event_type, event.details[:120])
                for event in related
            )
        )
        if key in seen:
            continue
        seen.add(key)
        clusters.append(
            {
                "central_timestamp": central.timestamp,
                "score": score,
                "sources": sorted({event.source for event in related}),
                "events": sorted(related, key=lambda e: (e.timestamp or datetime.max, e.source, e.event_type)),
            }
        )
    return sorted(clusters, key=lambda c: (c["central_timestamp"], -c["score"]))


def event_weight(event: Event) -> int:
    return correlation_event_score(event)


def event_contact(event: Event) -> str:
    metadata = event.metadata or {}
    return str(metadata.get("resolved_contact") or metadata.get("raw_contact") or "")


def is_communication(event: Event) -> bool:
    return event.source in {"sms.db", "CallHistory", "Mail"}


def is_attachment(event: Event) -> bool:
    return event.source == "sms.db attachment" or "attachment" in event.event_type.lower()


def build_scored_buckets(ctx: CaseContext, events: List[Event]) -> List[Dict[str, Any]]:
    bucket_minutes = max(1, ctx.score_bucket_minutes)
    buckets: Dict[datetime, Dict[str, Any]] = {}
    for event in events:
        if not event.timestamp or not in_range(event.timestamp, ctx.context_start, ctx.context_end):
            continue
        minute = (event.timestamp.minute // bucket_minutes) * bucket_minutes
        bucket_start = event.timestamp.replace(minute=minute, second=0, microsecond=0)
        bucket = buckets.setdefault(
            bucket_start,
            {"start": bucket_start, "end": bucket_start + timedelta(minutes=bucket_minutes), "events": [], "score": 0},
        )
        bucket["events"].append(event)
        bucket["score"] += event_weight(event)

    scored: List[Dict[str, Any]] = []
    for bucket in buckets.values():
        bucket_events = bucket["events"]
        sources = {event.source for event in bucket_events}
        bonuses: List[str] = []
        if len(sources) >= 3:
            bucket["score"] += 3
            bonuses.append("three_or_more_sources")
        if any(is_communication(event) for event in bucket_events) and any(is_attachment(event) for event in bucket_events):
            bucket["score"] += 2
            bonuses.append("communication_and_attachment")
        if any(
            event.confidence_score >= 90
            and any(abs(event.timestamp - allegation) <= timedelta(minutes=1) for allegation in ctx.allegation_times)
            for event in bucket_events
            if event.timestamp
        ):
            bucket["score"] += 2
            bonuses.append("high_confidence_near_allegation_time")
        contacts_by_source: Dict[str, set] = {}
        for event in bucket_events:
            contact = event_contact(event)
            if contact:
                contacts_by_source.setdefault(contact, set()).add(event.source)
        if any({"CallHistory", "sms.db"}.issubset(sources) for sources in contacts_by_source.values()):
            bucket["score"] += 2
            bonuses.append("same_contact_calls_and_messages")
        if any(event.metadata.get("network_event") for event in bucket_events) and any(is_communication(event) for event in bucket_events):
            bucket["score"] += 3
            bonuses.append("network_context_and_messaging")
        if any(
            event.metadata.get("network_event")
            and event.source in {"Wi-Fi", "Bluetooth"}
            and event.timestamp
            and any(abs(event.timestamp - allegation) <= timedelta(minutes=1) for allegation in ctx.allegation_times)
            for event in bucket_events
        ):
            bucket["score"] += 3
            bonuses.append("wifi_or_bluetooth_state_near_allegation_time")
        if any(event.source == "AirDrop/Nearby" for event in bucket_events) and any(event.source == "sms.db attachment" for event in bucket_events):
            bucket["score"] += 3
            bonuses.append("airdrop_nearby_and_recovered_attachment")
        bundle_sources: Dict[str, set] = {}
        for event in bucket_events:
            bundle = str(event.metadata.get("bundle_id") or "")
            if bundle:
                bundle_sources.setdefault(bundle, set()).add(event.source)
        if any("Data Usage" in srcs and len(srcs) > 1 for srcs in bundle_sources.values()):
            bucket["score"] += 2
            bonuses.append("data_usage_and_app_activity_same_bundle")
        bucket["bonuses"] = bonuses
        if bucket["score"] >= ctx.min_bucket_score:
            scored.append(bucket)
    return sorted(scored, key=lambda b: (-b["score"], b["start"]))


def extract_entities(event: Event) -> List[Tuple[str, str, str]]:
    metadata = event.metadata or {}
    details = event.details or ""
    entities: List[Tuple[str, str, str]] = []
    for key in ("resolved_contact", "raw_contact"):
        value = metadata.get(key)
        if value:
            entities.append((f"{key}:{str(value).lower()}", "contact", str(value)))
    if event.source == "sms.db attachment":
        for key in ("parent_resolved_contact", "parent_raw_contact"):
            value = metadata.get(key)
            if value:
                entities.append((f"{key}:{str(value).lower()}", "contact", str(value)))
    for key in ("chat_identifier", "chat_rowid"):
        value = metadata.get(key)
        if value:
            entities.append((f"chat:{str(value).lower()}", "chat", str(value)))
    if event.source == "sms.db attachment":
        for key in ("parent_chat_identifier", "parent_chat_rowid", "parent_message_rowid"):
            value = metadata.get(key)
            if value:
                prefix = "message" if key == "parent_message_rowid" else "chat"
                entities.append((f"{prefix}:{str(value).lower()}", prefix, str(value)))
    for key, entity_type in (
        ("local_ip", "ip"),
        ("remote_ip", "ip"),
        ("ssid", "ssid"),
        ("bssid", "bssid"),
        ("bluetooth_address", "bluetooth_address"),
        ("bluetooth_identifier", "bluetooth_identifier"),
        ("domain", "domain"),
        ("hostname", "hostname"),
        ("bundle_id", "app"),
    ):
        value = metadata.get(key)
        if value:
            normalized = normalize_ip(value) if entity_type == "ip" else normalize_mac(value) if "address" in entity_type or entity_type == "bssid" else str(value).lower()
            entities.append((f"{entity_type}:{normalized or str(value).lower()}", entity_type, str(value)))
    for key in ("filename",):
        value = metadata.get(key)
        if value:
            entities.append((f"file:{Path(str(value)).name.lower()}", "filename", Path(str(value)).name))
    file_meta = metadata.get("file") if isinstance(metadata.get("file"), dict) else {}
    if file_meta.get("sha256"):
        entities.append((f"sha256:{file_meta['sha256']}", "attachment_hash", str(file_meta["sha256"])))
    raw = metadata.get("raw") if isinstance(metadata.get("raw"), dict) else {}
    for key in ("url", "URL"):
        if raw.get(key):
            url = str(raw[key])
            domain = domain_from_url(url)
            entities.append((f"url:{url.lower()}", "url", url))
            if domain:
                entities.append((f"domain:{domain}", "domain", domain))
    for key in ("bundle_id", "ZBUNDLEID", "bundleID"):
        if raw.get(key):
            entities.append((f"app:{str(raw[key]).lower()}", "app", str(raw[key])))
    for match in re.findall(r"[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}", details):
        entities.append((f"email:{match.lower()}", "email", match))
    for match in re.findall(r"\+?\d[\d\s().-]{7,}\d", details):
        norm = normalize_phone(match)
        if norm:
            entities.append((f"phone:{norm}", "phone", norm))
    seen = set()
    unique: List[Tuple[str, str, str]] = []
    for entity in entities:
        if entity[0] in seen:
            continue
        seen.add(entity[0])
        unique.append(entity)
    return unique


def domain_from_url(url: str) -> str:
    match = re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://([^/]+)", url)
    if not match:
        return ""
    return match.group(1).split("@")[-1].split(":")[0].lower()


def build_entity_correlations(ctx: CaseContext, events: List[Event]) -> List[Dict[str, Any]]:
    entity_events: Dict[str, Dict[str, Any]] = {}
    for event in events:
        for entity_id, entity_type, label in extract_entities(event):
            item = entity_events.setdefault(
                entity_id,
                {"entity": label, "entity_type": entity_type, "events": []},
            )
            item["events"].append(event)
    correlations: List[Dict[str, Any]] = []
    for entity_id, item in entity_events.items():
        related = item["events"]
        sources = {event.source for event in related}
        if len(related) < 2 and len(sources) < 2:
            continue
        timestamps = [event.timestamp for event in related if event.timestamp]
        correlations.append(
            {
                "entity_id": entity_id,
                "entity": item["entity"],
                "entity_type": item["entity_type"],
                "events": related,
                "source_count": len(sources),
                "first_seen": min(timestamps) if timestamps else None,
                "last_seen": max(timestamps) if timestamps else None,
                "total_event_count": len(related),
                "confidence": max((event.confidence_score for event in related), default=0),
            }
        )
    return sorted(correlations, key=lambda c: (-c["source_count"], -c["total_event_count"], str(c["entity"])))


def relationship_edges(events: List[Event]) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    for event in events:
        metadata = event.metadata or {}
        source_node = "device:examined_iphone"
        source_label = "Examined iPhone"
        def add_edge(target_id: str, target_type: str, target_label: str, rel: str) -> None:
            edges.append(
                {
                    "source_id": source_node,
                    "source_type": "device",
                    "source_label": source_label,
                    "target_id": target_id,
                    "target_type": target_type,
                    "target_label": target_label,
                    "relationship": rel,
                    "timestamp": format_dt(event.timestamp),
                    "event_source": event.source,
                    "event_type": event.event_type,
                    "confidence_score": event.confidence_score,
                }
            )
        contact = event_contact(event)
        if event.source == "CallHistory" and contact:
            add_edge(f"contact:{contact.lower()}", "contact", contact, "CALLED")
        if event.source == "sms.db" and contact:
            add_edge(f"contact:{contact.lower()}", "contact", contact, "MESSAGED")
        if event.source == "sms.db attachment":
            filename = str(metadata.get("filename") or "attachment")
            rel = direction_attachment_relationship(metadata.get("parent_message_direction") or metadata.get("direction"))
            add_edge(f"file:{Path(filename).name.lower()}", "filename", Path(filename).name, rel)
        raw = metadata.get("raw") if isinstance(metadata.get("raw"), dict) else {}
        if event.source == "Safari" and raw.get("url"):
            add_edge(f"url:{str(raw['url']).lower()}", "url", str(raw["url"]), "VISITED_URL")
        if metadata.get("chat_identifier"):
            add_edge(f"chat:{str(metadata['chat_identifier']).lower()}", "chat", str(metadata["chat_identifier"]), "ASSOCIATED_WITH_CHAT")
        if metadata.get("network_event"):
            if metadata.get("ssid"):
                add_edge(f"ssid:{str(metadata['ssid']).lower()}", "ssid", str(metadata["ssid"]), "RECORDED_NETWORK_CONFIGURATION")
            if metadata.get("bssid"):
                add_edge(f"bssid:{metadata['bssid']}", "bssid", str(metadata["bssid"]), "RECORDED_LOCAL_LAYER2_IDENTIFIER")
            if metadata.get("bluetooth_address"):
                add_edge(f"bt:{metadata['bluetooth_address']}", "bluetooth_address", str(metadata["bluetooth_address"]), "RECORDED_BLUETOOTH_IDENTIFIER")
            if metadata.get("local_ip"):
                add_edge(f"ip:{metadata['local_ip']}", "ip", str(metadata["local_ip"]), "RECORDED_IP_VALUE")
            if metadata.get("remote_ip"):
                add_edge(f"ip:{metadata['remote_ip']}", "ip", str(metadata["remote_ip"]), "RECORDED_IP_VALUE")
            if metadata.get("domain"):
                add_edge(f"domain:{str(metadata['domain']).lower()}", "domain", str(metadata["domain"]), "RECORDED_DOMAIN_VALUE")
    return edges


def normalize_phone_entity(value: Any) -> Tuple[str, str]:
    text = str(value or "").strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if text.upper().startswith("P:+"):
        digits = "".join(ch for ch in text[3:] if ch.isdigit())
    if len(digits) == 10:
        return f"phone:+1{digits}", f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"phone:+{digits}", f"+{digits}"
    normalized = normalize_phone(text)
    return f"phone:{normalized.lower()}", normalized


def normalize_email_entity(value: Any) -> Tuple[str, str]:
    text = str(value or "").strip()
    return f"email_address:{text.lower()}", text.lower()


def normalize_domain_entity(value: Any) -> Tuple[str, str]:
    text = str(value or "").strip().rstrip(".").lower()
    return f"domain:{text}", text


def normalize_file_entity(filename: Any, source_artifact: str = "", file_hash: str = "") -> Tuple[str, str]:
    if file_hash:
        return f"file_hash:{file_hash.lower()}", file_hash.lower()
    name = Path(str(filename or "")).name
    basis = f"{name.lower()}|{source_artifact.lower()}"
    return f"file:{hashlib.sha1(basis.encode('utf-8')).hexdigest()[:16]}", name


class EntityRegistry:
    def __init__(self) -> None:
        self.entities: Dict[str, Entity] = {}
        self.sources_by_entity: Dict[str, set] = {}
        self.merge_warnings: List[str] = []
        self.unresolved_identifiers: List[str] = []

    def examined_device(self, timestamp: Optional[datetime], event_id: str, context_only: bool = False) -> Entity:
        return self.register(
            "examined_device",
            "examined_device",
            "Examined iPhone",
            timestamp,
            event_id,
            "examined device placeholder for backup under review",
            100,
            "Tool-scoped examined-device entity; not a person identity assertion.",
            context_only=context_only,
        )

    def register(
        self,
        entity_type: str,
        canonical_value: Any,
        display_name: Any,
        timestamp: Optional[datetime],
        event_id: str,
        source: str,
        confidence_score: int,
        confidence_basis: str,
        attributes: Optional[Dict[str, Any]] = None,
        alias: Optional[Any] = None,
        context_only: bool = False,
    ) -> Entity:
        canonical = str(canonical_value or "").strip()
        display = str(display_name or canonical).strip()
        if not canonical:
            self.unresolved_identifiers.append(f"{entity_type}: blank value from {source}")
            canonical = "unknown"
        entity_id = self.entity_id_for(entity_type, canonical, source, attributes or {})
        entity = self.entities.get(entity_id)
        if not entity:
            entity = Entity(
                entity_id=entity_id,
                entity_type=entity_type,
                canonical_value=canonical,
                display_name=display,
                confidence_score=confidence_score,
                confidence_basis=confidence_basis,
                attributes=attributes or {},
            )
            self.entities[entity_id] = entity
        if display and display not in entity.aliases:
            entity.aliases.append(display)
        if alias not in (None, "") and str(alias) not in entity.aliases:
            entity.aliases.append(str(alias))
        if timestamp:
            entity.first_seen = min(entity.first_seen, timestamp) if entity.first_seen else timestamp
            entity.last_seen = max(entity.last_seen, timestamp) if entity.last_seen else timestamp
        entity.event_count += 1
        entity.confidence_score = max(entity.confidence_score, confidence_score)
        self.sources_by_entity.setdefault(entity_id, set()).add(source)
        entity.source_count = len(self.sources_by_entity[entity_id])
        provenance = {
            "normalized_event_id": event_id,
            "source": source,
            "context_only": context_only,
        }
        if provenance not in entity.provenance:
            entity.provenance.append(provenance)
        return entity

    def entity_id_for(self, entity_type: str, canonical: str, source: str, attributes: Dict[str, Any]) -> str:
        if entity_type == "phone_number":
            entity_id, _ = normalize_phone_entity(canonical)
            return entity_id
        if entity_type == "email_address":
            entity_id, _ = normalize_email_entity(canonical)
            return entity_id
        if entity_type == "wifi_network":
            normalized = canonical.strip().casefold()
            return f"wifi_network:{hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:20]}"
        if entity_type in {"wifi_access_point", "bluetooth_device"}:
            mac = normalize_mac(canonical)
            if mac:
                prefix = "wifi_access_point" if entity_type == "wifi_access_point" else "bluetooth_device"
                return f"{prefix}:{mac}"
            stable = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:20]
            return f"{entity_type}:{stable}"
        if entity_type == "ip_address":
            ip_text = normalize_ip(canonical)
            return f"ip_address:{ip_text or canonical.lower()}"
        if entity_type == "domain":
            entity_id, _ = normalize_domain_entity(canonical)
            return entity_id
        if entity_type == "url":
            return f"url:{hashlib.sha1(canonical.strip().encode('utf-8')).hexdigest()[:20]}"
        if entity_type in {"file", "attachment", "file_hash"}:
            file_hash = str(attributes.get("sha256") or "")
            entity_id, _ = normalize_file_entity(canonical, source, file_hash)
            return entity_id if entity_type != "file_hash" else f"file_hash:{canonical.lower()}"
        if entity_type == "person":
            return f"person:{hashlib.sha1(canonical.casefold().encode('utf-8')).hexdigest()[:20]}"
        if entity_type == "chat":
            return f"chat:{hashlib.sha1(canonical.encode('utf-8')).hexdigest()[:20]}"
        if entity_type == "application":
            return f"application:{canonical.lower()}"
        if entity_type == "location":
            return f"location:{hashlib.sha1(canonical.encode('utf-8')).hexdigest()[:20]}"
        if entity_type == "examined_device":
            return "examined_device:backup_subject"
        return f"{entity_type}:{hashlib.sha1(canonical.encode('utf-8')).hexdigest()[:20]}"

    def as_list(self) -> List[Dict[str, Any]]:
        return [entity.as_dict() for entity in sorted(self.entities.values(), key=lambda item: item.entity_id)]


def source_database_from_event(event: Event) -> str:
    md = event.metadata or {}
    for key in ("db", "database", "source_database", "source_artifact"):
        if md.get(key):
            return str(md[key])
    return ""


def build_coverage_lookup(records: List[CoverageRecord]) -> Dict[str, CoverageRecord]:
    lookup: Dict[str, CoverageRecord] = {}
    for record in records:
        for value in (
            record.parser_name,
            record.artifact_name,
            record.artifact_id,
            record.relative_path,
            record.absolute_path,
        ):
            if value:
                lookup[str(value).lower()] = record
    return lookup


def coverage_status_for_event(event: Event, coverage_lookup: Dict[str, CoverageRecord]) -> str:
    md = event.metadata or {}
    candidates = [
        event.source,
        md.get("parser_name"),
        md.get("db"),
        md.get("database"),
        md.get("source_artifact"),
        md.get("source_database"),
        md.get("logical_artifact_id"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        text = str(candidate).lower()
        if text in coverage_lookup:
            return coverage_lookup[text].coverage_status
        basename = Path(str(candidate)).name.lower()
        if basename in coverage_lookup:
            return coverage_lookup[basename].coverage_status
        for key, record in coverage_lookup.items():
            if key and (key in text or text in key):
                return record.coverage_status
    return "UNKNOWN"


def normalized_event_id(event: Event) -> str:
    return "nevt_" + hashlib.sha1(event_stable_id(event).encode("utf-8")).hexdigest()[:16]


def normalized_category_and_type(event: Event) -> Tuple[str, str, str]:
    source = event.source.lower()
    etype = event.event_type.lower()
    if source in {"sms.db", "sms.db attachment", "callhistory", "mail", "facetime"}:
        category = "communication"
    elif source in {"safari", "chrome", "firefox"}:
        category = "browser"
    elif source == "photos" or "photo gps" in etype:
        category = "media"
    elif source in {"knowledgec", "coreduet", "notifications"}:
        category = "application_activity"
    elif source in {"wi-fi", "bluetooth", "airdrop/nearby", "network configuration", "cellular/telephony", "data usage"}:
        category = "network"
    elif source == "maps/location" or "location" in etype:
        category = "location"
    elif any(term in source or term in etype for term in ("files", "download", "attachment")):
        category = "file_activity"
    elif any(term in source or term in etype for term in ("profile", "mdm", "vpn", "known network", "paired")):
        category = "configuration"
    else:
        category = "system"

    normalized = event.event_type
    direction = str((event.metadata or {}).get("direction") or "").lower()
    if source == "sms.db attachment":
        normalized = "message_attachment"
    elif source == "sms.db":
        normalized = "outgoing_message" if "out" in direction else "incoming_message" if "in" in direction else "message"
    elif source == "callhistory":
        normalized = "outgoing_call" if "out" in direction else "incoming_call" if "in" in direction else "call"
    elif source == "safari":
        normalized = "browser_visit"
    elif source == "photos":
        normalized = "photo_created"
    elif source == "knowledgec":
        normalized = "app_activity"
    elif source == "notifications":
        normalized = "notification"
    elif source == "wi-fi":
        normalized = "wifi_configuration" if "known" in etype or "config" in etype else "wifi_state"
    elif source == "bluetooth":
        normalized = "bluetooth_paired_device" if "paired" in etype else "bluetooth_state"
    elif source == "airdrop/nearby":
        normalized = "airdrop_transfer" if "airdrop" in etype else "nearby_peer"
    elif source == "cellular/telephony":
        normalized = "cellular_state"
    elif source == "data usage":
        normalized = "network_usage"
    elif category == "location":
        normalized = "location_record"
    elif category == "system":
        normalized = "filesystem_timestamp"
    return category, normalized, event.event_type


def normalize_event(ctx: CaseContext, event: Event, coverage_lookup: Dict[str, CoverageRecord]) -> NormalizedEvent:
    md = event.metadata or {}
    raw = md.get("raw") if isinstance(md.get("raw"), dict) else {}
    file_meta = md.get("file") if isinstance(md.get("file"), dict) else {}
    event_id = normalized_event_id(event)
    category, normalized_type, subtype = normalized_category_and_type(event)
    source_database = source_database_from_event(event)
    url = str(md.get("url") or raw.get("url") or raw.get("URL") or "")
    domain = str(md.get("domain") or (domain_from_url(url) if url else "") or raw.get("domain") or raw.get("hostname") or "")
    filename = str(md.get("filename") or file_meta.get("filename") or file_meta.get("path") or "")
    sha_value = str(md.get("sha256") or file_meta.get("sha256") or "")
    lat = md.get("latitude") or raw.get("latitude") or raw.get("ZLATITUDE")
    lon = md.get("longitude") or raw.get("longitude") or raw.get("ZLONGITUDE")
    local_ip = normalize_ip(md.get("local_ip") or raw.get("local_ip") or "")
    remote_ip = normalize_ip(md.get("remote_ip") or raw.get("remote_ip") or "")
    bssid = normalize_mac(md.get("bssid") or raw.get("bssid") or "") or str(md.get("bssid") or "")
    bt_addr = normalize_mac(md.get("bluetooth_address") or raw.get("bluetooth_address") or "") or str(md.get("bluetooth_address") or md.get("bluetooth_identifier") or "")
    proximities = [
        abs(int((event.timestamp - allegation).total_seconds()))
        for allegation in ctx.allegation_times
        if event.timestamp
    ]
    limitations = [event_limitation(event)]
    if category == "network":
        limitations.append("Network/configuration artifacts do not by themselves prove active remote communication or packet contents.")
    nevent = NormalizedEvent(
        event_id=event_id,
        timestamp=event.timestamp,
        timestamp_end=timestamp_from_any(md.get("timestamp_end") or md.get("end_time") or raw.get("end_time")),
        event_category=category,
        event_type=normalized_type,
        event_subtype=subtype,
        source=event.source,
        source_artifact=str(md.get("source_artifact") or md.get("db") or source_database or event.source),
        source_database=source_database,
        source_table=str(md.get("table") or raw.get("_table") or ""),
        source_rowid=str(md.get("rowid") or md.get("message_rowid") or md.get("attachment_rowid") or raw.get("_rowid") or ""),
        source_guid=str(md.get("guid") or raw.get("guid") or raw.get("ZUUID") or ""),
        parser_name=str(md.get("parser_name") or event.source),
        direction=str(md.get("direction") or raw.get("direction") or ""),
        service=str(md.get("service") or raw.get("service") or raw.get("ZACCOUNT") or ""),
        description=event_brief(event),
        text=str(md.get("text") or raw.get("text") or raw.get("body") or ""),
        filename=filename,
        mime_type=str(md.get("mime_type") or file_meta.get("mime_type") or raw.get("mime_type") or ""),
        sha256=sha_value,
        url=url,
        domain=domain.rstrip(".").lower(),
        application=str(md.get("application") or md.get("app_name") or raw.get("application") or ""),
        bundle_id=str(md.get("bundle_id") or raw.get("bundle_id") or raw.get("ZBUNDLEID") or raw.get("bundleID") or ""),
        location=str(md.get("location") or raw.get("location") or raw.get("address") or ""),
        latitude="" if lat in (None, "") else str(lat),
        longitude="" if lon in (None, "") else str(lon),
        local_ip=local_ip,
        remote_ip=remote_ip,
        local_port="" if md.get("local_port") in (None, "") else str(md.get("local_port")),
        remote_port="" if md.get("remote_port") in (None, "") else str(md.get("remote_port")),
        ssid=str(md.get("ssid") or raw.get("ssid") or ""),
        bssid=bssid,
        bluetooth_name=str(md.get("bluetooth_name") or raw.get("bluetooth_name") or ""),
        bluetooth_address=bt_addr,
        bytes_sent="" if md.get("bytes_sent") in (None, "") else str(md.get("bytes_sent")),
        bytes_received="" if md.get("bytes_received") in (None, "") else str(md.get("bytes_received")),
        attachments=md.get("linked_attachments") if isinstance(md.get("linked_attachments"), list) else [],
        attachment_count=safe_int(md.get("linked_attachment_count")) or 0,
        parent_message_rowid=str(md.get("parent_message_rowid") or md.get("message_rowid") or ""),
        allegation_time_proximity_seconds=min(proximities) if proximities else None,
        confidence_score=event.confidence_score,
        confidence_basis=event.confidence_basis,
        evidence_strength=event.evidence_strength,
        coverage_status=coverage_status_for_event(event, coverage_lookup),
        limitations=limitations,
        raw_event_reference=event_stable_id(event),
    )
    return nevent


def add_entity_link(nevent: NormalizedEvent, entity: Entity, role: str, confidence: int, provenance: str) -> None:
    link = {
        "entity_id": entity.entity_id,
        "role": role,
        "confidence": confidence,
        "provenance": provenance,
    }
    if link not in nevent.entity_links:
        nevent.entity_links.append(link)


def link_entities_for_normalized_event(registry: EntityRegistry, nevent: NormalizedEvent, event: Event, context_only: bool = False) -> None:
    md = event.metadata or {}
    device = registry.examined_device(nevent.timestamp, nevent.event_id, context_only=context_only)
    contact = event_contact(event)
    raw_contact = str(md.get("raw_contact") or md.get("address") or md.get("phone_number") or "")
    participant_contact = raw_contact or contact
    direction = (nevent.direction or "").lower()
    if nevent.source == "sms.db" and participant_contact:
        _, canonical = normalize_phone_entity(participant_contact)
        phone = registry.register("phone_number", canonical, participant_contact, nevent.timestamp, nevent.event_id, nevent.source, 80, "Phone/contact value recorded in message metadata.", alias=participant_contact, context_only=context_only)
        add_entity_link(nevent, phone, "recipient" if "out" in direction else "sender", 80, "sms.db participant metadata")
        add_entity_link(nevent, device, "sender" if "out" in direction else "recipient", 90, "examined device perspective")
    if nevent.source == "sms.db" and md.get("rowid"):
        msg_entity = registry.register("message", md.get("rowid"), f"message_rowid={md.get('rowid')}", nevent.timestamp, nevent.event_id, nevent.source, 95, "Message ROWID recorded by sms.db.", context_only=context_only)
        add_entity_link(nevent, msg_entity, "message", 95, "sms.db message ROWID")
    elif nevent.source == "CallHistory" and participant_contact:
        _, canonical = normalize_phone_entity(participant_contact)
        phone = registry.register("phone_number", canonical, participant_contact, nevent.timestamp, nevent.event_id, nevent.source, 80, "Phone/contact value recorded in call metadata.", alias=participant_contact, context_only=context_only)
        add_entity_link(nevent, phone, "recipient" if "out" in direction else "sender", 80, "CallHistory participant metadata")
        add_entity_link(nevent, device, "sender" if "out" in direction else "recipient", 90, "examined device perspective")
    if md.get("resolved_contact") and md.get("raw_contact") and str(md.get("resolved_contact")) != str(md.get("raw_contact")):
        person = registry.register("person", md.get("resolved_contact"), md.get("resolved_contact"), nevent.timestamp, nevent.event_id, nevent.source, 75, "Direct resolver/name artifact supplied this contact name.", alias=md.get("resolved_contact"), context_only=context_only)
        add_entity_link(nevent, person, "contact", 75, "resolved contact metadata")
    if nevent.source == "sms.db attachment":
        parent_contact = str(md.get("parent_raw_contact") or md.get("parent_resolved_contact") or "")
        if parent_contact:
            _, canonical = normalize_phone_entity(parent_contact)
            parent_phone = registry.register("phone_number", canonical, parent_contact, nevent.timestamp, nevent.event_id, nevent.source, 100, "Parent message participant propagated through message_attachment_join.", alias=parent_contact, context_only=context_only)
            add_entity_link(nevent, parent_phone, "participant", 100, "message_attachment_join")
        if md.get("parent_resolved_contact") and md.get("parent_raw_contact") and str(md.get("parent_resolved_contact")) != str(md.get("parent_raw_contact")):
            parent_person = registry.register("person", md.get("parent_resolved_contact"), md.get("parent_resolved_contact"), nevent.timestamp, nevent.event_id, nevent.source, 100, "Parent message resolved contact propagated through message_attachment_join.", alias=md.get("parent_resolved_contact"), context_only=context_only)
            add_entity_link(nevent, parent_person, "contact", 100, "message_attachment_join")
        parent_device = registry.examined_device(nevent.timestamp, nevent.event_id, context_only=context_only)
        add_entity_link(nevent, parent_device, "device", 100, "message_attachment_join")
    chat_value = md.get("chat_identifier") or md.get("chat_rowid")
    if nevent.source == "sms.db attachment":
        chat_value = chat_value or md.get("parent_chat_identifier") or md.get("parent_chat_rowid")
    if chat_value:
        chat_conf = 100 if nevent.source == "sms.db attachment" else 85
        chat_basis = "Parent chat propagated through message_attachment_join." if nevent.source == "sms.db attachment" else "Chat identifier recorded by messaging artifact."
        chat = registry.register("chat", chat_value, chat_value, nevent.timestamp, nevent.event_id, nevent.source, chat_conf, chat_basis, context_only=context_only)
        add_entity_link(nevent, chat, "conversation", chat_conf, "message_attachment_join" if nevent.source == "sms.db attachment" else "chat metadata")
    if nevent.source == "sms.db attachment" and md.get("parent_message_rowid"):
        parent_msg = registry.register("message", md.get("parent_message_rowid"), f"message_rowid={md.get('parent_message_rowid')}", nevent.timestamp, nevent.event_id, nevent.source, 100, "Parent message ROWID propagated through message_attachment_join.", context_only=context_only)
        add_entity_link(nevent, parent_msg, "parent_message", 100, "message_attachment_join")
    if nevent.filename:
        attrs = {"sha256": nevent.sha256} if nevent.sha256 else {}
        file_entity = registry.register("attachment" if "attachment" in nevent.event_type else "file", nevent.filename, Path(nevent.filename).name, nevent.timestamp, nevent.event_id, nevent.source_artifact, 80 if nevent.sha256 else 60, "File entity uses SHA-256 when available; same names are not merged without a matching hash.", attributes=attrs, context_only=context_only)
        add_entity_link(nevent, file_entity, "attachment" if "attachment" in nevent.event_type else "file", 80 if nevent.sha256 else 60, "file metadata")
        if "attachment" in nevent.event_type:
            md["attachment_entity_id"] = file_entity.entity_id
    if nevent.sha256:
        hash_entity = registry.register("file_hash", nevent.sha256, nevent.sha256, nevent.timestamp, nevent.event_id, nevent.source_artifact, 95, "Cryptographic hash recorded or calculated for file artifact.", context_only=context_only)
        add_entity_link(nevent, hash_entity, "file_hash", 95, "file hash metadata")
        md["file_hash_entity_id"] = hash_entity.entity_id
    if nevent.url:
        url_entity = registry.register("url", nevent.url, nevent.url, nevent.timestamp, nevent.event_id, nevent.source, 90, "URL recorded in browser or artifact metadata.", context_only=context_only)
        add_entity_link(nevent, url_entity, "visited_resource", 90, "URL metadata")
    if nevent.domain:
        domain_entity = registry.register("domain", nevent.domain, nevent.domain, nevent.timestamp, nevent.event_id, nevent.source, 85, "Domain parsed from URL or recorded hostname.", context_only=context_only)
        add_entity_link(nevent, domain_entity, "domain", 85, "domain metadata")
    if nevent.bundle_id or nevent.application:
        app_value = nevent.bundle_id or nevent.application
        app = registry.register("application", app_value, nevent.application or nevent.bundle_id, nevent.timestamp, nevent.event_id, nevent.source, 80, "Application or bundle identifier recorded in artifact metadata.", context_only=context_only)
        add_entity_link(nevent, app, "application", 80, "application metadata")
    if nevent.ssid:
        wifi = registry.register("wifi_network", nevent.ssid, nevent.ssid, nevent.timestamp, nevent.event_id, nevent.source, 75, "SSID recorded as network name; not proof of ownership.", context_only=context_only)
        add_entity_link(nevent, wifi, "network", 75, "SSID metadata")
    if nevent.bssid:
        ap = registry.register("wifi_access_point", nevent.bssid, nevent.bssid, nevent.timestamp, nevent.event_id, nevent.source, 75, "BSSID recorded as local wireless access point identifier; ownership is not inferred.", context_only=context_only)
        add_entity_link(nevent, ap, "access_point", 75, "BSSID metadata")
    if nevent.bluetooth_name or nevent.bluetooth_address:
        bt_value = nevent.bluetooth_address or nevent.bluetooth_name
        bt = registry.register("bluetooth_device", bt_value, nevent.bluetooth_name or nevent.bluetooth_address, nevent.timestamp, nevent.event_id, nevent.source, 70, "Bluetooth identifier/name recorded; paired records are not treated as active connections.", context_only=context_only)
        add_entity_link(nevent, bt, "device", 70, "Bluetooth metadata")
    for ip_value, role in ((nevent.local_ip, "endpoint"), (nevent.remote_ip, "endpoint")):
        if ip_value:
            ip_entity = registry.register("ip_address", ip_value, ip_value, nevent.timestamp, nevent.event_id, nevent.source, 75, "IP value validated locally; no geolocation or ownership inference.", attributes={"classification": classify_ip(ip_value)}, context_only=context_only)
            add_entity_link(nevent, ip_entity, role, 75, "IP metadata")
    if nevent.latitude and nevent.longitude:
        loc_value = f"{nevent.latitude},{nevent.longitude}"
        loc = registry.register("location", loc_value, loc_value, nevent.timestamp, nevent.event_id, nevent.source, 75, "Latitude/longitude recorded in artifact metadata.", context_only=context_only)
        add_entity_link(nevent, loc, "location", 75, "location metadata")


def derive_relationships_from_normalized_events(events: List[NormalizedEvent]) -> List[Relationship]:
    relationships: List[Relationship] = []

    def add(source_id: str, rel_type: str, target_id: str, event: NormalizedEvent, basis: str) -> None:
        if not source_id or not target_id or source_id == target_id:
            return
        stable = "|".join([source_id, rel_type, target_id, event.event_id])
        relationships.append(
            Relationship(
                relationship_id="rel_" + hashlib.sha1(stable.encode("utf-8")).hexdigest()[:16],
                source_entity_id=source_id,
                relationship_type=rel_type,
                target_entity_id=target_id,
                timestamp=event.timestamp,
                normalized_event_id=event.event_id,
                source_artifact=event.source_artifact,
                confidence_score=event.confidence_score,
                confidence_basis=basis,
                provenance={"source": event.source, "event_type": event.event_type},
            )
        )

    for event in events:
        links = event.entity_links
        by_role: Dict[str, List[str]] = {}
        for link in links:
            by_role.setdefault(str(link.get("role")), []).append(str(link.get("entity_id")))
        device_ids = by_role.get("sender", []) + by_role.get("recipient", [])
        chat_ids = by_role.get("conversation", [])
        attachments = by_role.get("attachment", [])
        message_ids = by_role.get("message", []) + by_role.get("parent_message", [])
        if event.event_type in {"incoming_message", "outgoing_message", "message"}:
            participants = by_role.get("sender", []) + by_role.get("recipient", [])
            for src in participants:
                for tgt in participants:
                    add(src, "MESSAGED", tgt, event, "Participant roles recorded by message artifact.")
            for participant in participants:
                for chat in chat_ids:
                    add(participant, "PARTICIPATED_IN", chat, event, "Message links participant to chat identifier.")
                    add(participant, "BELONGS_TO_CHAT", chat, event, "Chat association recorded by sms.db metadata.")
            for attachment in attachments:
                rel = direction_attachment_relationship(event.direction)
                if rel == "INCLUDED_ATTACHMENT":
                    for message_id in message_ids:
                        add(message_id, "INCLUDED_ATTACHMENT", attachment, event, "Attachment linked to parent message through message_attachment_join.")
                else:
                    add("examined_device:backup_subject", rel, attachment, event, "Parent message direction controls attachment relationship classification.")
        if event.event_type in {"incoming_call", "outgoing_call", "call"}:
            participants = by_role.get("sender", []) + by_role.get("recipient", [])
            for src in participants:
                for tgt in participants:
                    add(src, "CALLED", tgt, event, "Participant roles recorded by call artifact.")
        for participant in device_ids:
            for attachment in attachments:
                rel = direction_attachment_relationship(event.direction) if event.event_type == "message_attachment" else "INCLUDED_ATTACHMENT"
                add(participant, rel, attachment, event, "Attachment/file metadata linked to normalized event.")
        for file_id in attachments:
            for hash_id in by_role.get("file_hash", []):
                if hash_id.startswith("file_hash:"):
                    add(file_id, "HASHED_AS", hash_id, event, "Hash metadata recorded for file artifact.")
        for url_id in by_role.get("visited_resource", []):
            for domain_id in by_role.get("domain", []):
                add(url_id, "VISITED", domain_id, event, "Browser URL/domain relationship.")
        for app_id in by_role.get("application", []):
            for device_id in device_ids or ["examined_device:backup_subject"]:
                add(device_id, "USED_APPLICATION", app_id, event, "Application or bundle identifier recorded in event metadata.")
        for network_id in by_role.get("network", []):
            add("examined_device:backup_subject", "RECORDED_WIFI_NETWORK", network_id, event, "SSID was recorded by a network artifact.")
        for ap_id in by_role.get("access_point", []):
            add("examined_device:backup_subject", "OBSERVED_ACCESS_POINT", ap_id, event, "BSSID was recorded by a network artifact.")
        for bt_id in by_role.get("device", []):
            add("examined_device:backup_subject", "RECORDED_BLUETOOTH_DEVICE", bt_id, event, "Bluetooth identifier/name was recorded by an artifact.")
        for endpoint_id in by_role.get("endpoint", []):
            add("examined_device:backup_subject", "ASSOCIATED_WITH_IP", endpoint_id, event, "IP value recorded by an artifact.")
        for loc_id in by_role.get("location", []):
            add("examined_device:backup_subject", "LOCATED_AT", loc_id, event, "Location coordinates recorded by an artifact.")
    unique: Dict[str, Relationship] = {}
    for rel in relationships:
        unique.setdefault(rel.relationship_id, rel)
    return sorted(unique.values(), key=lambda item: (item.timestamp or datetime.max, item.relationship_id))


def build_case_knowledge(
    ctx: CaseContext,
    all_events: List[Event],
    clusters: List[Dict[str, Any]],
    coverage_records: List[CoverageRecord],
    app_coverage_records: List[AppCoverageRecord],
    hypotheses: List[Dict[str, Any]],
) -> Dict[str, Any]:
    link_message_attachments(all_events)
    coverage_lookup = build_coverage_lookup(coverage_records)
    registry = EntityRegistry()
    window_events = sorted(window_event_subset(ctx, all_events), key=lambda e: (e.timestamp or datetime.max, e.source, e.event_type))
    context_events = [
        event
        for event in all_events
        if event.timestamp and ctx.context_start <= event.timestamp <= ctx.context_end and not in_range(event.timestamp, ctx.start, ctx.end)
    ]
    normalized_events: List[NormalizedEvent] = []
    event_id_by_stable: Dict[str, str] = {}
    normalized_by_id: Dict[str, NormalizedEvent] = {}
    original_by_id: Dict[str, Event] = {}
    for event in window_events:
        nevent = normalize_event(ctx, event, coverage_lookup)
        link_entities_for_normalized_event(registry, nevent, event, context_only=False)
        normalized_events.append(nevent)
        event_id_by_stable[event_stable_id(event)] = nevent.event_id
        normalized_by_id[nevent.event_id] = nevent
        original_by_id[nevent.event_id] = event
        event.metadata["normalized_event_id"] = nevent.event_id
        event.metadata["normalized_event_category"] = nevent.event_category
        event.metadata["normalized_event_type"] = nevent.event_type
        event.metadata["normalized_coverage_status"] = nevent.coverage_status
        event.metadata["normalized_entity_links"] = nevent.entity_links
    for event in context_events:
        nevent = normalize_event(ctx, event, coverage_lookup)
        link_entities_for_normalized_event(registry, nevent, event, context_only=True)
    link_message_attachments(all_events)
    parent_by_rowid: Dict[str, NormalizedEvent] = {}
    attachment_by_rowid: Dict[str, List[NormalizedEvent]] = {}
    for nevent in normalized_events:
        original = original_by_id.get(nevent.event_id)
        md = original.metadata if original else {}
        if nevent.source == "sms.db" and md.get("rowid") not in (None, ""):
            parent_by_rowid[str(md.get("rowid"))] = nevent
        if nevent.source == "sms.db attachment" and md.get("message_rowid") not in (None, ""):
            attachment_by_rowid.setdefault(str(md.get("message_rowid")), []).append(nevent)
    for rowid, attachment_nevents in attachment_by_rowid.items():
        parent = parent_by_rowid.get(rowid)
        if not parent:
            continue
        for attachment_nevent in attachment_nevents:
            attachment_nevent.parent_message_event_id = parent.event_id
            attachment_nevent.parent_message_rowid = rowid
            original = original_by_id.get(attachment_nevent.event_id)
            if original:
                original.metadata["parent_message_event_id"] = parent.event_id
            for link in attachment_nevent.entity_links:
                if isinstance(link, dict) and link.get("role") == "attachment":
                    propagated = dict(link)
                    propagated["confidence"] = 100
                    propagated["provenance"] = "message_attachment_join"
                    if propagated not in parent.entity_links:
                        parent.entity_links.append(propagated)
        parent.attachment_count = len(attachment_nevents)
        parent.attachments = []
        parent_original = original_by_id.get(parent.event_id)
        parent_md = parent_original.metadata if parent_original else {}
        for attachment_nevent in sorted(attachment_nevents, key=lambda item: item.source_rowid):
            original = original_by_id.get(attachment_nevent.event_id)
            summary = attachment_metadata_summary(original) if original else {}
            summary["attachment_event_id"] = attachment_nevent.event_id
            summary["normalized_event_id"] = attachment_nevent.event_id
            parent.attachments.append(summary)
        if parent_original:
            parent_md["linked_attachments"] = parent.attachments
            parent_md["linked_attachment_count"] = len(parent.attachments)
    normalized_clusters: List[Dict[str, Any]] = []
    for cluster in clusters:
        ids = [
            event_id_by_stable.get(event_stable_id(event))
            for event in cluster.get("events", [])
            if event_id_by_stable.get(event_stable_id(event))
        ]
        if not ids:
            continue
        shared_counts: Dict[str, int] = {}
        for event_id in ids:
            for link in normalized_by_id[event_id].entity_links:
                entity_id = str(link.get("entity_id"))
                shared_counts[entity_id] = shared_counts.get(entity_id, 0) + 1
        shared_ids = sorted(entity_id for entity_id, count in shared_counts.items() if count > 1)
        cluster_id = str(cluster.get("cluster_id") or "cluster_" + hashlib.sha1("|".join(ids).encode("utf-8")).hexdigest()[:12])
        for event_id in ids:
            if cluster_id not in normalized_by_id[event_id].correlation_cluster_ids:
                normalized_by_id[event_id].correlation_cluster_ids.append(cluster_id)
            if event_id in original_by_id:
                existing_ids = original_by_id[event_id].metadata.setdefault("normalized_correlation_cluster_ids", [])
                if cluster_id not in existing_ids:
                    existing_ids.append(cluster_id)
        normalized_clusters.append(
            {
                "cluster_id": cluster_id,
                "normalized_event_ids": sorted(ids),
                "shared_entity_ids": shared_ids,
                "source_count": len(cluster.get("sources", [])),
                "score": cluster.get("score", 0),
                "start": format_dt(cluster.get("start") or cluster.get("central_timestamp")),
                "end": format_dt(cluster.get("end") or cluster.get("central_timestamp")),
                "cautious_interpretation": "correlated activity cluster for examiner review; temporal/entity correlation does not establish causation or malicious activity.",
            }
        )
    relationships = derive_relationships_from_normalized_events(normalized_events)
    relationships_by_event: Dict[str, List[str]] = {}
    for rel in relationships:
        relationships_by_event.setdefault(rel.normalized_event_id, []).append(rel.relationship_id)
    for event_id, event in original_by_id.items():
        event.metadata["normalized_relationship_ids"] = sorted(relationships_by_event.get(event_id, []))
    rels_by_attachment_entity: Dict[str, List[str]] = {}
    for rel in relationships:
        if rel.relationship_type in {"SENT_ATTACHMENT", "RECEIVED_ATTACHMENT", "INCLUDED_ATTACHMENT"}:
            rels_by_attachment_entity.setdefault(rel.target_entity_id, []).append(rel.relationship_id)
    for nevent in normalized_events:
        if nevent.source != "sms.db attachment":
            continue
        original = original_by_id.get(nevent.event_id)
        if not original:
            continue
        amd = original.metadata
        attachment_entity_id = str(amd.get("attachment_entity_id") or "")
        parent_ids = sorted(rels_by_attachment_entity.get(attachment_entity_id, []))
        if parent_ids:
            merged = sorted(set((amd.get("normalized_relationship_ids") or []) + parent_ids))
            amd["normalized_relationship_ids"] = merged
    for parent in normalized_events:
        if parent.source != "sms.db":
            continue
        parent_original = original_by_id.get(parent.event_id)
        if not parent_original:
            continue
        refreshed = []
        for item in parent.attachments:
            attachment_id = item.get("attachment_event_id") or item.get("normalized_event_id")
            original = original_by_id.get(str(attachment_id))
            if original:
                refreshed.append(attachment_metadata_summary(original))
            else:
                refreshed.append(item)
        parent.attachments = refreshed
        parent.attachment_count = len(refreshed)
        parent_original.metadata["linked_attachments"] = refreshed
        parent_original.metadata["linked_attachment_count"] = len(refreshed)
    coverage_scores = build_evidence_coverage_score(ctx, coverage_records, app_coverage_records, window_events) if coverage_records else {}
    confidence_results = [item.as_dict() for item in assess_finding_confidence(ctx, coverage_records, app_coverage_records, window_events)] if coverage_records else []
    cov_summary = coverage_summary(coverage_records, app_coverage_records) if coverage_records else {}
    finding_ids = list(dict.fromkeys((ctx.hypotheses or []) + ["silent_sms", "normal_communications", "network_activity", "unusual_network_transmission", "command_activity", "malware_or_compromise"]))
    finding_completeness = {
        finding_id: assess_finding_completeness(ctx, finding_id, coverage_records, app_coverage_records).as_dict()
        for finding_id in finding_ids
    }
    return {
        "case": {
            "case_name": ctx.case_name or ctx.case_dir.name,
            "start": format_dt(ctx.start),
            "end": format_dt(ctx.end),
            "context_start": format_dt(ctx.context_start),
            "context_end": format_dt(ctx.context_end),
            "window_only": bool(ctx.window_only),
            "acquisition_type": "encrypted iPhone backup",
        },
        "coverage_summary": cov_summary,
        "coverage_scores": coverage_scores,
        "finding_confidence": confidence_results,
        "finding_completeness": finding_completeness,
        "examination_status": {
            "supported_examination_status": cov_summary.get("supported_examination_status", "UNKNOWN"),
            "examination_gaps": cov_summary.get("examination_gaps", []),
        },
        "acquisition_status": {
            "acquisition_type": "encrypted_iphone_backup",
            "acquisition_sufficiency_by_finding": {
                finding_id: result.get("acquisition_sufficiency_status", "UNKNOWN")
                for finding_id, result in finding_completeness.items()
            },
            "acquisition_limitations": cov_summary.get("acquisition_limitations", []),
            "evidence_not_collected": cov_summary.get("not_collected_sources", []),
        },
        "events": [event.as_dict() for event in normalized_events],
        "entities": registry.as_list(),
        "relationships": [rel.as_dict() for rel in relationships],
        "correlation_clusters": normalized_clusters,
        "hypotheses": hypotheses,
        "blind_spots": build_forensic_blind_spots(coverage_records, app_coverage_records) if coverage_records else [],
        "evidence_recommendations": build_additional_evidence_recommendations(coverage_records, app_coverage_records) if coverage_records else [],
        "additional_evidence_recommendations": build_additional_evidence_recommendations(coverage_records, app_coverage_records) if coverage_records else [],
        "limitations": [
            "Normalized evidence is derived from parsed backup artifacts and is not a raw database dump.",
            "Outside-window events are excluded as primary normalized events; they may contribute context-only aliases/provenance.",
            "Coverage percentages describe parsing/acquisition coverage, not probabilities.",
            "Temporal/entity correlation does not establish causation, malicious activity, Silent SMS, or command activity.",
        ],
        "unresolved_identifiers": registry.unresolved_identifiers,
        "entity_merge_warnings": registry.merge_warnings,
    }


def write_case_knowledge(path: Path, knowledge: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2, default=str)


def write_normalized_evidence_summary(handle: Any, knowledge: Optional[Dict[str, Any]]) -> None:
    if not knowledge:
        handle.write("Case knowledge export was not requested for this run.\n\n")
        return
    entities = knowledge.get("entities", [])
    counts: Dict[str, int] = {}
    for entity in entities:
        etype = str(entity.get("entity_type") or "unknown")
        counts[etype] = counts.get(etype, 0) + 1
    handle.write(f"- Normalized event count: {len(knowledge.get('events', []))}\n")
    handle.write(f"- Relationship count: {len(knowledge.get('relationships', []))}\n")
    handle.write(f"- Correlation cluster count: {len(knowledge.get('correlation_clusters', []))}\n")
    if counts:
        handle.write("- Entity count by type: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) + "\n")
    else:
        handle.write("- Entity count by type: none\n")
    unresolved = knowledge.get("unresolved_identifiers", [])
    warnings = knowledge.get("entity_merge_warnings", [])
    handle.write(f"- Unresolved identifiers: {len(unresolved)}\n")
    for item in unresolved[:10]:
        handle.write(f"  - {item}\n")
    handle.write(f"- Entity merge warnings: {len(warnings)}\n")
    for item in warnings[:10]:
        handle.write(f"  - {item}\n")
    handle.write("\n")


def evaluate_hypotheses(ctx: CaseContext, events: List[Event]) -> List[Dict[str, Any]]:
    results = []
    summary = coverage_summary(ctx.coverage_records, ctx.app_coverage_records) if ctx.coverage_records else {
        "completeness_level": "UNKNOWN",
        "supported_examination_status": "UNKNOWN",
        "material_coverage_gaps": [],
        "examination_gaps": [],
        "acquisition_limitations": [],
        "not_collected_sources": [],
    }
    unsupported = [
        record.artifact_name for record in ctx.coverage_records
        if record.coverage_status in {"PRESENT_UNSUPPORTED", "PRESENT_UNKNOWN_SCHEMA", "PRESENT_PARTIALLY_PARSED"}
    ][:25]
    failures = [
        record.artifact_name for record in ctx.coverage_records
        if record.coverage_status == "PRESENT_PARSE_FAILED"
    ][:25]
    for hypothesis in ctx.hypotheses:
        h = hypothesis.lower()
        completeness = assess_finding_completeness(ctx, h, ctx.coverage_records, ctx.app_coverage_records)
        supporting: List[str] = []
        contrary: List[str] = []
        unavailable: List[str] = []
        required: List[str] = []
        confidence = "LOW"
        basis = "Assessment is based only on normalized backup artifacts."
        if h == "silent_sms":
            no_text = [event for event in events if event.source == "sms.db" and "<NO TEXT CONTENT>" in event.details]
            if no_text:
                contrary.append("No-text sms.db rows were present, but those rows are not proof of Silent SMS.")
            else:
                contrary.append("No no-text sms.db rows were identified in the normalized events.")
            unavailable.append("Carrier signaling records and baseband/sysdiagnose evidence were not available in normalized backup events.")
            required.append("Carrier records, baseband diagnostics, CommCenter/CoreTelephony logs, or sysdiagnose material.")
            basis = "A standard handset backup generally cannot confirm Silent SMS."
            telephony_ok = any(
                record.parser_name == "cellular_telephony"
                and is_record_covered(record)
                and record.coverage_status != "PRESENT_PARSE_FAILED"
                for record in ctx.coverage_records
            )
            required_sources_available = all(
                any(token in (record.artifact_name + " " + record.parser_name).lower() and is_record_covered(record) for record in ctx.coverage_records)
                for token in ("commcenter", "coretelephony")
            )
            confidence = "MODERATE" if telephony_ok and required_sources_available and completeness.supported_examination_status not in {"EXAMINATION_GAPS_PRESENT", "INSUFFICIENT_EXAMINATION"} else "LOW"
            basis += " A standard iTunes backup alone never produces HIGH confidence for confirming or excluding Silent SMS."
        elif h == "normal_communications":
            comms = [event for event in events if event.source in {"sms.db", "CallHistory", "sms.db attachment"}]
            supporting = [event_summary(event) for event in comms[:20]]
            contrary.append("Normal communications cannot exclude other activity without additional evidence.")
            confidence = "HIGH" if comms else "LOW"
            basis = "Calls, messages, and ordinary attachments are consistent with normal communication activity."
        elif h == "unauthorized_device_activity":
            supporting.append("No normalized event type in this tool directly establishes unauthorized device activity by itself.")
            contrary.append("Communications, notifications, browser visits, and filesystem timestamps are not by themselves unauthorized access indicators.")
            unavailable.append("Authentication records, device unlock context, MDM/security logs, and direct unauthorized access indicators.")
            required.append("Corroborated access logs, account/device security alerts, or forensic artifacts showing unauthorized access.")
            confidence = "LOW"
        elif h == "malware_or_compromise":
            supporting.append("No normalized event type in this tool directly establishes malware or compromise by itself.")
            contrary.append("Absence of malware indicators in a backup does not prove absence of compromise.")
            unavailable.append("Process execution, persistence, exploit telemetry, full filesystem, sysdiagnose, and security product findings.")
            required.append("Malware sample, persistence artifact, exploit trace, unauthorized process/configuration change, or corroborating system evidence.")
            confidence = "LOW"
        elif h == "attachment_exchange":
            attachments = [event for event in events if event.source == "sms.db attachment"]
            supporting = [event_summary(event) for event in attachments[:20]]
            contrary.append("Attachment metadata does not establish intent or content interpretation without examiner review.")
            confidence = "HIGH" if attachments else "LOW"
            basis = "Attachment records and recovered file metadata support whether attachments were exchanged."
        elif h == "network_activity":
            net = [event for event in events if event.metadata.get("network_event")]
            supporting = [event_summary(event) for event in net[:20]]
            contrary.append("Network configuration artifacts are not proof of active network use without timestamped state or usage records.")
            unavailable.append("Complete packet captures and full connection history are generally unavailable in a standard backup.")
            required.append("Packet capture, sysdiagnose, network equipment logs, carrier records, or timestamped operational artifacts.")
            confidence = "MEDIUM" if net else "LOW"
            basis = "Assessment distinguishes recorded configuration from timestamped network-context records."
        elif h == "bluetooth_activity":
            bt = [event for event in events if event.source == "Bluetooth"]
            supporting = [event_summary(event) for event in bt[:20]]
            contrary.append("A paired Bluetooth device record is not proof of connection during the requested window.")
            required.append("Timestamped Bluetooth connection-state records or corroborating system logs.")
            confidence = "MEDIUM" if any(event.timestamp and "connection" in event.event_type.lower() for event in bt) else "LOW"
            basis = "Bluetooth artifacts were evaluated as paired/configuration records versus connection-state records."
        elif h == "airdrop_activity":
            ad = [event for event in events if event.source == "AirDrop/Nearby"]
            supporting = [event_summary(event) for event in ad if "airdrop transfer" in event.event_type.lower()][:20]
            contrary.append("Nearby or sharing path hits are not proof of AirDrop transfer.")
            required.append("Structured AirDrop transfer record, notification, receiving artifact, or corroborating logs.")
            confidence = "MEDIUM" if supporting else "LOW"
            basis = "Only structured AirDrop transfer content supports AirDrop activity."
        elif h == "unusual_network_transmission":
            direct = [
                event for event in events
                if event.source == "Data Usage" or event.metadata.get("remote_ip") or "session" in event.event_type.lower()
            ]
            supporting = [event_summary(event) for event in direct[:20]]
            contrary.append("Wi-Fi, Bluetooth, cellular, or configuration artifacts alone do not support unusual network transmission.")
            unavailable.append("Packet-level evidence and complete connection history were not identified from normalized events.")
            required.append("Structured operational records, direct byte/session data, packet capture, or corroborated unusual activity evidence.")
            has_explicit_network = bool(direct)
            confidence = "MODERATE" if has_explicit_network else "LOW"
            basis = "The rule requires direct session/byte evidence or corroborated unusual activity; configuration-only evidence is insufficient."
        else:
            unavailable.append(f"No deterministic rule is implemented for hypothesis '{hypothesis}'.")
            required.append("Define explicit evidence rules for this hypothesis.")
        if completeness.supported_examination_status in {"EXAMINATION_GAPS_PRESENT", "INSUFFICIENT_EXAMINATION"} and confidence == "HIGH" and not supporting:
            confidence = "MEDIUM"
            basis += " Negative assessment confidence was downgraded because examination gaps exist."
        deprecated = (
            "EXAMINATION_GAPS_PRESENT"
            if completeness.examination_gaps
            else completeness.acquisition_sufficiency_status
            if completeness.acquisition_sufficiency_status == "LIMITED_BY_ACQUISITION_TYPE"
            else completeness.supported_examination_status
        )
        results.append(
            {
                "hypothesis": hypothesis,
                "evidence_supporting": supporting,
                "evidence_not_supporting_or_contrary": contrary,
                "evidence_unavailable": unavailable,
                "unparsed_evidence": unsupported,
                "unsupported_evidence": unsupported,
                "parser_failures": failures,
                "supported_examination_status": completeness.supported_examination_status,
                "acquisition_sufficiency_status": completeness.acquisition_sufficiency_status,
                "examination_gaps": completeness.examination_gaps,
                "acquisition_limitations": completeness.acquisition_limitations,
                "evidence_not_collected": completeness.evidence_not_collected,
                "additional_evidence_that_could_increase_confidence": completeness.supplemental_evidence_recommended,
                "finding_completeness": completeness.as_dict(),
                "answer_completeness": deprecated,
                "required_additional_evidence": required,
                "confidence_in_assessment": confidence,
                "basis": basis,
                "coverage_basis": coverage_aware_absence_statement(hypothesis, hypothesis, ctx.coverage_records) if ctx.coverage_records else "Coverage audit was not available.",
            }
        )
    return results


def event_summary(event: Event) -> str:
    return f"{format_dt(event.timestamp)} | {event.source} | {event.event_type} | {event.details[:220]}"


def finding_ids_for_question(question: str) -> List[str]:
    q = question.lower()
    findings: List[str] = []
    if "silent sms" in q:
        findings.append("silent_sms")
    if "command" in q:
        findings.append("command_activity")
    if "unusual" in q and "network" in q:
        findings.append("unusual_network_transmission")
    elif "network" in q or "wifi" in q or "wi-fi" in q or "bluetooth" in q or "cellular" in q:
        findings.append("network_activity")
    if "message" in q or "call" in q or "communicat" in q:
        findings.append("normal_communications")
    return list(dict.fromkeys(findings)) or ["normal_communications"]


def answer_question(ctx: CaseContext, events: List[Event], clusters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not ctx.question:
        return None
    q = ctx.question.lower()
    support: List[Event] = []
    non_supporting: List[str] = []
    limitations: List[str] = ["Answer is derived from normalized events, not raw database re-querying."]
    needed: List[str] = []
    answer = "The question was evaluated against normalized events."
    times = [parse_time_from_question(ctx, ctx.question)]
    times.extend(ctx.allegation_times)
    times = [t for t in times if t]
    if "what" in q and ("happened" in q or "occurred" in q) and times:
        answer = "Normalized events near the referenced time(s) are listed below."
        support = events_near_times(events, times, timedelta(minutes=max(ctx.correlation_window_minutes, 3)))
    if "who communicated" in q:
        support = [event for event in events if event.source in {"sms.db", "CallHistory", "Mail"}]
        answer = "Communication participants are represented by the supporting message, call, or mail events."
    if "attachments" in q:
        support.extend([event for event in events if event.source == "sms.db attachment"])
        answer = "Attachment exchange is supported only where normalized attachment records are present."
    if "calls active" in q or "were calls" in q:
        support.extend([event for event in events if event.source == "CallHistory"])
    if "safari" in q:
        support.extend([event for event in events if event.source == "Safari"])
    if "photos" in q:
        support.extend([event for event in events if event.source == "Photos"])
    if "notifications" in q:
        support.extend([event for event in events if event.source == "Notifications"])
    if "correlated" in q and times:
        support.extend(events_near_times(events, times, timedelta(minutes=ctx.correlation_window_minutes)))
    if "silent sms" in q:
        answer += " The handset backup alone generally cannot confirm Silent SMS."
        non_supporting.append("No-text sms.db or attachment-only rows are not proof of Silent SMS.")
        needed.append("Carrier signaling records, baseband diagnostics, CommCenter/CoreTelephony logs, or sysdiagnose evidence.")
    if "command activity" in q:
        non_supporting.append("Normalized events in this report do not by themselves establish command activity.")
        needed.append("Direct command execution, remote access, process, persistence, or diagnostic evidence.")
    if any(term in q for term in ("wi-fi", "wifi", "network", "bluetooth", "airdrop", "nearby", "ip-address", "ip address", "data-usage", "data usage", "cellular", "vpn")):
        net_events = [event for event in events if event.metadata.get("network_event")]
        if times:
            support.extend(events_near_times(net_events, times, timedelta(minutes=max(ctx.correlation_window_minutes, 3))))
        if "wi-fi" in q or "wifi" in q or "network" in q:
            support.extend([event for event in net_events if event.source in {"Wi-Fi", "Network Configuration"}][:30])
        if "bluetooth" in q:
            support.extend([event for event in net_events if event.source == "Bluetooth"][:30])
            non_supporting.append("Paired Bluetooth records are distinguished from confirmed connection-state records.")
        if "airdrop" in q:
            support.extend([event for event in net_events if event.source == "AirDrop/Nearby" and "airdrop" in event.event_type.lower()][:30])
            non_supporting.append("Path-only AirDrop/Nearby artifacts are not treated as proof of AirDrop use.")
        if "nearby" in q:
            support.extend([event for event in net_events if event.source == "AirDrop/Nearby"][:30])
        if "ip-address" in q or "ip address" in q:
            support.extend([event for event in net_events if event.metadata.get("local_ip") or event.metadata.get("remote_ip")][:30])
        if "data-usage" in q or "data usage" in q or "sent or received" in q:
            support.extend([event for event in net_events if event.source == "Data Usage"][:30])
            non_supporting.append("Cumulative counters are not treated as window-specific transmission volume without valid delta evidence.")
        if "cellular" in q:
            support.extend([event for event in net_events if event.source == "Cellular/Telephony"][:30])
            non_supporting.append("Ordinary cellular/carrier records are not evidence of Silent SMS.")
        if "vpn" in q:
            support.extend([event for event in net_events if "vpn" in event.event_type.lower()][:30])
        answer += " Network answers distinguish configuration, paired-device records, state records, direct counters, filesystem-only evidence, and unavailable packet evidence."
        needed.append("Packet captures, sysdiagnose, router/access point logs, carrier records, or other independent network telemetry for complete transmission reconstruction.")
    support = dedupe_event_refs(support)
    coverage = coverage_summary(ctx.coverage_records, ctx.app_coverage_records) if ctx.coverage_records else {
        "completeness_level": "UNKNOWN",
        "material_coverage_gaps": [],
    }
    unsupported_sources = [
        record.artifact_name for record in ctx.coverage_records
        if record.coverage_status in {"PRESENT_UNSUPPORTED", "PRESENT_UNKNOWN_SCHEMA", "PRESENT_PARTIALLY_PARSED"}
    ][:25]
    parser_failures = [
        record.artifact_name for record in ctx.coverage_records
        if record.coverage_status == "PRESENT_PARSE_FAILED"
    ][:25]
    if not support:
        non_supporting.append("No normalized events matching the deterministic question criteria were found.")
    question_findings = finding_ids_for_question(ctx.question)
    completeness_results = [
        assess_finding_completeness(ctx, finding_id, ctx.coverage_records, ctx.app_coverage_records).as_dict()
        for finding_id in question_findings
    ]
    primary_completeness = completeness_results[0] if completeness_results else {}
    examination_gaps = sorted(set(item for result in completeness_results for item in result.get("examination_gaps", [])))
    acquisition_limitations = sorted(set(item for result in completeness_results for item in result.get("acquisition_limitations", [])))
    evidence_not_collected = sorted(set(item for result in completeness_results for item in result.get("evidence_not_collected", [])))
    supplemental = sorted(set(item for result in completeness_results for item in result.get("supplemental_evidence_recommended", [])))
    return {
        "question": ctx.question,
        "answer": answer,
        "evidence_reviewed": f"{len(events)} normalized event(s) plus {len(ctx.coverage_records)} coverage record(s).",
        "coverage_status": primary_completeness.get("supported_examination_status", coverage.get("completeness_level", "UNKNOWN")),
        "supported_examination_status": primary_completeness.get("supported_examination_status", "UNKNOWN"),
        "acquisition_sufficiency_status": primary_completeness.get("acquisition_sufficiency_status", "UNKNOWN"),
        "finding_completeness": completeness_results,
        "examination_gaps": examination_gaps,
        "supporting_events": support[:50],
        "evidence_identified": [event_summary(event) for event in support[:50]],
        "evidence_not_identified": non_supporting,
        "unparsed_or_unsupported_sources": unsupported_sources,
        "parser_failures": parser_failures,
        "acquisition_limitations": acquisition_limitations,
        "evidence_not_collected": evidence_not_collected,
        "additional_evidence_that_could_increase_confidence": supplemental,
        "contradictory_or_non_supporting": non_supporting,
        "limitations": limitations,
        "additional_evidence_needed": needed or ["Independent corroborating evidence may be needed for stronger conclusions."],
        "confidence_in_answer_completeness": primary_completeness.get("supported_examination_status", coverage.get("completeness_level", "UNKNOWN")),
        "examiner_confidence_in_examination_completeness": primary_completeness.get("examiner_confidence_in_examination", "UNKNOWN"),
    }


def parse_time_from_question(ctx: CaseContext, question: str) -> Optional[datetime]:
    match = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", question, re.IGNORECASE)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    suffix = (match.group(3) or "").lower()
    if suffix == "pm" and hour < 12:
        hour += 12
    if suffix == "am" and hour == 12:
        hour = 0
    return ctx.start.replace(hour=hour, minute=minute, second=0, microsecond=0)


def events_near_times(events: List[Event], times: List[datetime], window: timedelta) -> List[Event]:
    out = []
    for event in events:
        if event.timestamp and any(abs(event.timestamp - time) <= window for time in times):
            out.append(event)
    return sorted(out, key=lambda e: (e.timestamp or datetime.max, e.source))


def dedupe_event_refs(events: List[Event]) -> List[Event]:
    seen = set()
    out = []
    for event in events:
        key = (format_dt(event.timestamp), event.source, event.event_type, event.details)
        if key not in seen:
            seen.add(key)
            out.append(event)
    return out


def write_outputs(ctx: CaseContext, events: List[Event]) -> Tuple[Path, Path, Path]:
    out_dir = ctx.case_dir / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "window_investigator_events.csv"
    md_path = out_dir / "window_investigator_report.md"
    error_path = out_dir / "window_investigator_errors.log"
    buckets_path = out_dir / "window_investigator_scored_buckets.csv"
    relationships_path = out_dir / "window_investigator_relationships.csv"
    graphml_path = out_dir / "window_investigator_graph.graphml"
    mermaid_path = out_dir / "window_investigator_graph.mmd"
    entity_corr_path = out_dir / "window_investigator_entity_correlations.csv"
    hypotheses_path = out_dir / "window_investigator_hypotheses.json"
    network_events_path = out_dir / "window_investigator_network_events.csv"
    network_indicators_path = out_dir / "window_investigator_network_indicators.csv"
    network_summary_path = out_dir / "window_investigator_network_summary.json"
    coverage_json_path = out_dir / "window_investigator_coverage.json"
    coverage_csv_path = out_dir / "window_investigator_coverage.csv"
    app_coverage_path = out_dir / "window_investigator_app_coverage.csv"
    sqlite_coverage_path = out_dir / "window_investigator_sqlite_coverage.csv"
    unparsed_artifacts_path = out_dir / "window_investigator_unparsed_artifacts.csv"

    sorted_events = sorted(events, key=lambda e: (e.timestamp or datetime.max, e.source, e.event_type))
    apply_confidence(sorted_events)
    coverage_records, app_coverage_records = build_coverage_audit(ctx, sorted_events)
    inventory = build_artifact_inventory(ctx, sorted_events)
    correlations = build_correlation_clusters(ctx, sorted_events)
    buckets = build_scored_buckets(ctx, sorted_events)
    entity_correlations = build_entity_correlations(ctx, sorted_events)
    network_events = [event for event in sorted_events if event.metadata.get("network_event")]
    network_indicators = build_network_indicators(network_events)
    network_summary = build_network_summary(ctx, network_events, network_indicators, inventory)
    hypotheses = evaluate_hypotheses(ctx, sorted_events)
    question_answer = answer_question(ctx, sorted_events, correlations)
    attachment_index = link_message_attachments(sorted_events)
    edges = relationship_edges(sorted_events)
    case_knowledge = build_case_knowledge(ctx, sorted_events, correlations, coverage_records, app_coverage_records, hypotheses)
    ctx.case_knowledge = case_knowledge
    attachment_index = link_message_attachments(sorted_events)
    if ctx.export_case_knowledge:
        write_case_knowledge(out_dir / "window_investigator_case_knowledge.json", case_knowledge)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for event in sorted_events:
            writer.writerow(event.as_row(ctx.start, ctx.end))

    write_scored_buckets_csv(buckets_path, buckets)
    write_relationship_outputs(relationships_path, graphml_path, mermaid_path, edges)
    write_entity_correlations_csv(entity_corr_path, entity_correlations)
    write_network_events_csv(network_events_path, ctx, network_events)
    write_network_indicators_csv(network_indicators_path, network_indicators)
    with network_summary_path.open("w", encoding="utf-8") as f:
        json.dump(network_summary, f, ensure_ascii=False, indent=2, default=str)
    write_coverage_outputs(
        coverage_json_path,
        coverage_csv_path,
        app_coverage_path,
        sqlite_coverage_path,
        unparsed_artifacts_path,
        out_dir / "window_investigator_coverage_scores.json",
        out_dir / "window_investigator_finding_confidence.csv",
        out_dir / "window_investigator_forensic_blind_spots.csv",
        out_dir / "window_investigator_evidence_recommendations.csv",
        ctx,
        coverage_records,
        app_coverage_records,
        sorted_events,
    )
    with hypotheses_path.open("w", encoding="utf-8") as f:
        json.dump(hypotheses, f, ensure_ascii=False, indent=2, default=str)
    if question_answer:
        question_path = ctx.question_output or (out_dir / "window_investigator_question.md")
        write_question_answer(question_path, question_answer)
        ctx.question_output = question_path
    if ctx.ai_summary:
        ctx.ai_summary_path = out_dir / "window_investigator_ai_summary.md"
        write_ai_summary(ctx, ctx.ai_summary_path, sorted_events, inventory, buckets, correlations, hypotheses)

    ctx.errors.write(error_path)
    write_markdown(
        md_path,
        ctx,
        sorted_events,
        error_path,
        inventory,
        correlations,
        buckets,
        entity_correlations,
        network_events,
        network_indicators,
        network_summary,
        coverage_records,
        app_coverage_records,
        hypotheses,
        question_answer,
        edges,
        case_knowledge,
    )
    return csv_path, md_path, error_path


def write_scored_buckets_csv(path: Path, buckets: List[Dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["bucket_start", "bucket_end", "score", "event_count", "sources", "bonuses"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for bucket in buckets:
            writer.writerow(
                {
                    "bucket_start": format_dt(bucket["start"]),
                    "bucket_end": format_dt(bucket["end"]),
                    "score": bucket["score"],
                    "event_count": len(bucket["events"]),
                    "sources": ";".join(sorted({event.source for event in bucket["events"]})),
                    "bonuses": ";".join(bucket.get("bonuses", [])),
                }
            )


def write_entity_correlations_csv(path: Path, correlations: List[Dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["entity", "entity_type", "source_count", "first_seen", "last_seen", "total_event_count", "confidence"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in correlations:
            writer.writerow(
                {
                    "entity": item["entity"],
                    "entity_type": item["entity_type"],
                    "source_count": item["source_count"],
                    "first_seen": format_dt(item["first_seen"]),
                    "last_seen": format_dt(item["last_seen"]),
                    "total_event_count": item["total_event_count"],
                    "confidence": item["confidence"],
                }
            )


def xml_escape(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write_relationship_outputs(csv_path: Path, graphml_path: Path, mermaid_path: Path, edges: List[Dict[str, Any]]) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "source_id",
            "source_type",
            "source_label",
            "target_id",
            "target_type",
            "target_label",
            "relationship",
            "timestamp",
            "event_source",
            "event_type",
            "confidence_score",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(edges)
    nodes: Dict[str, str] = {"device:examined_iphone": "Examined iPhone"}
    for edge in edges:
        nodes[edge["source_id"]] = edge["source_label"]
        nodes[edge["target_id"]] = edge["target_label"]
    with graphml_path.open("w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        f.write('<key id="label" for="node" attr.name="label" attr.type="string"/>\n')
        f.write('<key id="relationship" for="edge" attr.name="relationship" attr.type="string"/>\n')
        f.write('<key id="provenance" for="edge" attr.name="provenance" attr.type="string"/>\n<graph edgedefault="directed">\n')
        for node_id, label in nodes.items():
            f.write(f'<node id="{xml_escape(node_id)}"><data key="label">{xml_escape(label)}</data></node>\n')
        for index, edge in enumerate(edges):
            provenance = f"{edge['timestamp']} | {edge['event_source']} | {edge['event_type']} | confidence={edge['confidence_score']}"
            f.write(f'<edge id="e{index}" source="{xml_escape(edge["source_id"])}" target="{xml_escape(edge["target_id"])}">')
            f.write(f'<data key="relationship">{xml_escape(edge["relationship"])}</data>')
            f.write(f'<data key="provenance">{xml_escape(provenance)}</data></edge>\n')
        f.write("</graph>\n</graphml>\n")
    with mermaid_path.open("w", encoding="utf-8") as f:
        f.write("graph TD\n")
        for index, edge in enumerate(edges[:200]):
            source = f"N{abs(hash(edge['source_id']))}"
            target = f"N{abs(hash(edge['target_id']))}"
            f.write(f'  {source}["{edge["source_label"]}"] -->|{edge["relationship"]}| {target}["{edge["target_label"]}"]\n')
        if len(edges) > 200:
            f.write(f"  MORE[\"{len(edges) - 200} additional edges omitted\"]\n")


def write_question_answer(path: Path, answer: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Investigator Question Answer\n\n")
        f.write(f"Question: {answer['question']}\n\n")
        f.write("## Answer\n\n")
        f.write(f"{answer['answer']}\n\n")
        f.write("## Supporting Events\n\n")
        for event in answer["supporting_events"]:
            f.write(f"- {event_summary(event)}\n")
        if not answer["supporting_events"]:
            f.write("- None identified by deterministic rules.\n")
        f.write("\n## Contradictory or Non-supporting Evidence\n\n")
        for item in answer["contradictory_or_non_supporting"]:
            f.write(f"- {item}\n")
        f.write("\n## Limitations\n\n")
        for item in answer["limitations"]:
            f.write(f"- {item}\n")
        f.write("\n## Additional Evidence Needed\n\n")
        for item in answer["additional_evidence_needed"]:
            f.write(f"- {item}\n")


def build_network_indicators(network_events: List[Event]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for event in network_events:
        md = event.metadata
        candidates = []
        for key in ("local_ip", "remote_ip"):
            if md.get(key):
                candidates.append(("ip", md[key], classify_ip(md[key]), key))
        for key in ("hostname", "domain"):
            if md.get(key):
                candidates.append(("domain", str(md[key]).lower(), "hostname/domain", key))
        for key, cls in (("bssid", "BSSID / Wi-Fi access point MAC"), ("bluetooth_address", "Bluetooth device address")):
            if md.get(key):
                candidates.append(("mac", md[key], cls, key))
        for key in ("ssid",):
            if md.get(key):
                candidates.append(("ssid", md[key], "Wi-Fi network name", key))
        for indicator_type, value, classification, notes in candidates:
            if not value:
                continue
            item = grouped.setdefault(
                (indicator_type, str(value)),
                {
                    "indicator_type": indicator_type,
                    "normalized_value": str(value),
                    "classification": classification,
                    "first_seen": event.timestamp,
                    "last_seen": event.timestamp,
                    "event_count": 0,
                    "sources": set(),
                    "confidence": 0,
                    "notes": notes,
                },
            )
            item["event_count"] += 1
            item["sources"].add(event.source)
            item["confidence"] = max(item["confidence"], event.confidence_score)
            if event.timestamp:
                item["first_seen"] = min([t for t in (item["first_seen"], event.timestamp) if t])
                item["last_seen"] = max([t for t in (item["last_seen"], event.timestamp) if t])
    out = []
    for item in grouped.values():
        item["sources"] = sorted(item["sources"])
        out.append(item)
    return sorted(out, key=lambda x: (x["indicator_type"], x["normalized_value"]))


def build_network_summary(
    ctx: CaseContext,
    network_events: List[Event],
    indicators: List[Dict[str, Any]],
    inventory: List[Dict[str, Any]],
) -> Dict[str, Any]:
    def count_source(source: str) -> int:
        return sum(1 for event in network_events if event.source == source)

    exact = []
    for allegation in ctx.allegation_times:
        exact.extend([event_summary(event) for event in network_events if event.timestamp and abs(event.timestamp - allegation) <= timedelta(seconds=30)])
    ssids = sorted({str(event.metadata.get("ssid")) for event in network_events if event.metadata.get("ssid")})
    bssids = sorted({str(event.metadata.get("bssid")) for event in network_events if event.metadata.get("bssid")})
    bt_devices = sorted({str(event.metadata.get("bluetooth_name") or event.metadata.get("bluetooth_address")) for event in network_events if event.source == "Bluetooth" and (event.metadata.get("bluetooth_name") or event.metadata.get("bluetooth_address"))})
    ips = [item for item in indicators if item["indicator_type"] == "ip"]
    domains = [item for item in indicators if item["indicator_type"] == "domain"]
    return {
        "artifact_coverage": [item for item in inventory if any(token in item["artifact"].lower() for token in ("wi-fi", "wifi", "bluetooth", "airdrop", "nearby", "network", "vpn", "cellular", "data usage", "dns", "packet", "sysdiagnose", "wireless", "corecapture", "unified"))],
        "wifi_summary": {"event_count": count_source("Wi-Fi"), "known_ssids": ssids, "bssids": bssids, "timestamped_state_events": sum(1 for e in network_events if e.source == "Wi-Fi" and e.timestamp and "connection-state" in e.event_type.lower())},
        "bluetooth_summary": {"event_count": count_source("Bluetooth"), "devices": bt_devices, "timestamped_state_events": sum(1 for e in network_events if e.source == "Bluetooth" and e.timestamp and "connection-state" in e.event_type.lower())},
        "airdrop_nearby_summary": {"event_count": count_source("AirDrop/Nearby"), "airdrop_records": sum(1 for e in network_events if "airdrop" in e.event_type.lower()), "nearby_records": sum(1 for e in network_events if "nearby" in e.event_type.lower())},
        "cellular_summary": {"event_count": count_source("Cellular/Telephony"), "operational_records": sum(1 for e in network_events if e.source == "Cellular/Telephony" and e.timestamp)},
        "vpn_summary": {"event_count": sum(1 for e in network_events if "vpn" in e.event_type.lower())},
        "ip_summary": {"count": len(ips), "indicators": ips[:50]},
        "domain_summary": {"count": len(domains), "indicators": domains[:50]},
        "data_usage_summary": {"event_count": count_source("Data Usage"), "byte_counter_records": sum(1 for e in network_events if e.source == "Data Usage")},
        "exact_network_events_near_allegation_times": exact,
        "packet_capture_evidence": [short_path(p, ctx.case_dir) for p in ctx.find_path_tokens(("pcap", "packet"), suffixes=(".pcap", ".pcapng", ".cap"))],
        "limitations": [
            "The examined backup did not contain packet-capture evidence sufficient to reconstruct complete network transmissions unless packet files are explicitly listed.",
            "IP addresses or byte counters are reported only where explicitly present in recovered artifacts.",
            "MAC addresses in Wi-Fi and Bluetooth artifacts represent local-network or accessory identifiers and should not be interpreted as remote internet endpoints.",
            "Configuration artifacts are not treated as proof of active use without a timestamped state or usage record.",
        ],
    }


def write_network_events_csv(path: Path, ctx: CaseContext, events: List[Event]) -> None:
    fields = [
        "timestamp",
        "section",
        "source",
        "event_type",
        "confidence_score",
        "evidence_strength",
        "interface_type",
        "interface_name",
        "protocol",
        "local_ip",
        "remote_ip",
        "local_port",
        "remote_port",
        "hostname",
        "domain",
        "ssid",
        "bssid",
        "bluetooth_name",
        "bluetooth_address",
        "connection_state",
        "bytes_sent",
        "bytes_received",
        "details",
        "provenance",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for event in events:
            md = event.metadata
            writer.writerow(
                {
                    "timestamp": format_dt(event.timestamp),
                    "section": section_for(event.timestamp, ctx.start, ctx.end),
                    "source": event.source,
                    "event_type": event.event_type,
                    "confidence_score": event.confidence_score,
                    "evidence_strength": event.evidence_strength,
                    "interface_type": md.get("interface_type", ""),
                    "interface_name": md.get("interface_name", ""),
                    "protocol": md.get("protocol", ""),
                    "local_ip": md.get("local_ip", ""),
                    "remote_ip": md.get("remote_ip", ""),
                    "local_port": md.get("local_port", ""),
                    "remote_port": md.get("remote_port", ""),
                    "hostname": md.get("hostname", ""),
                    "domain": md.get("domain", ""),
                    "ssid": md.get("ssid", ""),
                    "bssid": md.get("bssid", ""),
                    "bluetooth_name": md.get("bluetooth_name", ""),
                    "bluetooth_address": md.get("bluetooth_address", ""),
                    "connection_state": md.get("connection_state", ""),
                    "bytes_sent": md.get("bytes_sent", ""),
                    "bytes_received": md.get("bytes_received", ""),
                    "details": event.details,
                    "provenance": md.get("source_artifact", ""),
                }
            )


def write_network_indicators_csv(path: Path, indicators: List[Dict[str, Any]]) -> None:
    fields = ["indicator_type", "normalized_value", "classification", "first_seen", "last_seen", "event_count", "sources", "confidence", "notes"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in indicators:
            writer.writerow(
                {
                    "indicator_type": item["indicator_type"],
                    "normalized_value": item["normalized_value"],
                    "classification": item["classification"],
                    "first_seen": format_dt(item["first_seen"]),
                    "last_seen": format_dt(item["last_seen"]),
                    "event_count": item["event_count"],
                    "sources": ";".join(item["sources"]),
                    "confidence": item["confidence"],
                    "notes": item["notes"],
                }
            )


def write_coverage_outputs(
    json_path: Path,
    coverage_csv_path: Path,
    app_coverage_path: Path,
    sqlite_coverage_path: Path,
    unparsed_artifacts_path: Path,
    coverage_scores_path: Path,
    finding_confidence_path: Path,
    blind_spots_path: Path,
    recommendations_path: Path,
    ctx: CaseContext,
    records: List[CoverageRecord],
    app_records: List[AppCoverageRecord],
    events: List[Event],
) -> None:
    summary = coverage_summary(records, app_records)
    score = build_evidence_coverage_score(ctx, records, app_records, events)
    confidence = assess_finding_confidence(ctx, records, app_records, events)
    blind_spots = build_forensic_blind_spots(records, app_records)
    recommendations = build_additional_evidence_recommendations(records, app_records)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": summary,
                "evidence_coverage_score": score,
                "finding_confidence": [item.as_dict() for item in confidence],
                "forensic_blind_spots": blind_spots,
                "additional_evidence_recommendations": recommendations,
                "coverage_records": [record.as_dict() for record in records],
                "app_coverage": [record.as_dict() for record in app_records],
            },
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    coverage_fields = list(CoverageRecord().as_dict().keys())
    with coverage_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=coverage_fields)
        writer.writeheader()
        for record in records:
            writer.writerow(record.as_dict())
    app_fields = list(AppCoverageRecord().as_dict().keys())
    with app_coverage_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=app_fields)
        writer.writeheader()
        for record in app_records:
            writer.writerow(record.as_dict())
    with sqlite_coverage_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=coverage_fields)
        writer.writeheader()
        for record in records:
            if record.file_type == "sqlite":
                writer.writerow(record.as_dict())
    with unparsed_artifacts_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=coverage_fields)
        writer.writeheader()
        for record in records:
            if record.coverage_status in {
                "PRESENT_UNSUPPORTED",
                "PRESENT_PARSER_DISABLED",
                "PRESENT_PARSE_FAILED",
                "PRESENT_PARTIALLY_PARSED",
                "PRESENT_ONLY_WAL_SHM",
                "PRESENT_ENCRYPTED_OR_INACCESSIBLE",
                "PRESENT_UNKNOWN_SCHEMA",
                "NOT_COLLECTED",
                "OUTSIDE_ACQUISITION_SCOPE",
            }:
                writer.writerow(record.as_dict())
    with coverage_scores_path.open("w", encoding="utf-8") as f:
        json.dump(score, f, ensure_ascii=False, indent=2, default=str)
    with finding_confidence_path.open("w", newline="", encoding="utf-8") as f:
        fields = list(FindingConfidenceResult("", "", "", "", "", 0, 0, "", "").as_dict().keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in confidence:
            writer.writerow(item.as_dict())
    with blind_spots_path.open("w", newline="", encoding="utf-8") as f:
        fields = ["source", "category", "coverage_status", "blind_spot_type", "disposition", "severity", "basis"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(blind_spots)
    with recommendations_path.open("w", newline="", encoding="utf-8") as f:
        fields = ["priority", "recommendation", "basis"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(recommendations)


def write_ai_summary(
    ctx: CaseContext,
    path: Path,
    events: List[Event],
    inventory: List[Dict[str, Any]],
    buckets: List[Dict[str, Any]],
    correlations: List[Dict[str, Any]],
    hypotheses: List[Dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": ctx.ollama_model,
        "stream": False,
        "prompt": build_ai_prompt(ctx, events, inventory, buckets, correlations, hypotheses),
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(ctx.ollama_url, data=data, headers={"Content-Type": "application/json"})
        with urlrequest.urlopen(req, timeout=ctx.ollama_timeout) as resp:
            result = json.loads(resp.read().decode("utf-8", errors="replace"))
        text = result.get("response") or json_dumps(result)
    except Exception as exc:
        ctx.errors.log("ai_summary", ctx.ollama_url, exc, "ollama generate")
        text = f"AI summary was requested, but Ollama was unavailable, timed out, or returned an error after up to {ctx.ollama_timeout} seconds. See the error log."
    with path.open("w", encoding="utf-8") as f:
        f.write("# Window Investigator AI Summary\n\n")
        f.write(
            "This optional AI output is derived only from normalized evidence supplied by the tool. "
            "It requires examiner validation and is not independent evidence.\n\n"
        )
        f.write(text)
        f.write("\n")


def build_ai_prompt(
    ctx: CaseContext,
    events: List[Event],
    inventory: List[Dict[str, Any]],
    buckets: List[Dict[str, Any]],
    correlations: List[Dict[str, Any]],
    hypotheses: List[Dict[str, Any]],
) -> str:
    knowledge = ctx.case_knowledge or {}
    normalized_events = knowledge.get("events", [])[: ctx.ai_top_events] if knowledge else []
    normalized_entities = knowledge.get("entities", [])[:100] if knowledge else []
    normalized_relationships = knowledge.get("relationships", [])[:150] if knowledge else []
    normalized_clusters = knowledge.get("correlation_clusters", [])[:20] if knowledge else []
    cov_summary = coverage_summary(ctx.coverage_records, ctx.app_coverage_records) if ctx.coverage_records else {"completeness_level": "UNKNOWN", "material_coverage_gaps": []}
    cov_score = build_evidence_coverage_score(ctx, ctx.coverage_records, ctx.app_coverage_records, events) if ctx.coverage_records else {}
    finding_confidence = [item.as_dict() for item in assess_finding_confidence(ctx, ctx.coverage_records, ctx.app_coverage_records, events)] if ctx.coverage_records else []
    evidence = {
        "time_window": {"start": format_dt(ctx.start), "end": format_dt(ctx.end)},
        "normalized_events": normalized_events,
        "entity_summaries": normalized_entities,
        "relationships": normalized_relationships,
        "correlation_clusters": normalized_clusters,
        "top_scored_buckets": [
            {
                "start": format_dt(bucket["start"]),
                "end": format_dt(bucket["end"]),
                "score": bucket["score"],
                "sources": sorted({event.source for event in bucket["events"]}),
            }
            for bucket in buckets[:10]
        ],
        "artifact_inventory_summary": inventory,
        "hypothesis_results": hypotheses,
        "network_limitations": [
            "Distinguish configuration from use.",
            "Distinguish local MAC identifiers from remote internet endpoints.",
            "Do not claim transmission volume unless directly recorded.",
            "Do not claim malicious network activity.",
            "Explain missing packet-level evidence.",
        ],
        "coverage_summary": cov_summary,
        "coverage_score": cov_score,
        "finding_confidence": finding_confidence,
        "finding_completeness": knowledge.get("finding_completeness", {}),
        "examination_status": knowledge.get("examination_status", {}),
        "acquisition_status": knowledge.get("acquisition_status", {}),
        "forensic_blind_spots": build_forensic_blind_spots(ctx.coverage_records, ctx.app_coverage_records)[:50] if ctx.coverage_records else [],
        "additional_evidence_recommendations": build_additional_evidence_recommendations(ctx.coverage_records, ctx.app_coverage_records) if ctx.coverage_records else [],
        "unsupported_artifacts": [r.as_dict() for r in ctx.coverage_records if r.coverage_status in {"PRESENT_UNSUPPORTED", "PRESENT_UNKNOWN_SCHEMA", "PRESENT_PARTIALLY_PARSED"}][:50],
        "parser_failures": [r.as_dict() for r in ctx.coverage_records if r.coverage_status == "PRESENT_PARSE_FAILED"][:50],
    }
    return (
        "You are assisting a forensic examiner. Use only the normalized evidence supplied. "
        "Every factual statement must be traceable to a normalized_event_id or relationship_id. "
        "Do not infer identity from aliases unless a direct relationship links them. "
        "Distinguish facts from interpretation. Do not invent facts. Do not claim Silent SMS, "
        "command activity, hacking, malicious intent, or causation. Identify limitations and additional "
        "evidence needed. For network evidence, distinguish configuration from active use, local identifiers "
        "from remote endpoints, and byte counters from packet contents. You must never interpret absence of "
        "normalized records as absence of underlying evidence unless the relevant artifact was present, supported, "
        "successfully parsed, and covered the requested time window. When coverage is incomplete, explicitly say "
        "the answer is incomplete. Distinguish no relevant parsed record, artifact absent, artifact unsupported, "
        "parser failed, acquisition did not include the source, and evidence unavailable. Do not use the phrase "
        "'no evidence' without a coverage qualification. Do not raise confidence above deterministic finding_confidence "
        "ceilings supplied in the JSON. Use cautious wording.\n\n"
        "Do not describe an acquisition limitation as a parser failure. "
        "Do not describe evidence that is ordinarily absent from an encrypted iPhone backup as unexpectedly missing. "
        "Distinguish complete examination of supplied supported evidence from whether the acquisition type is sufficient to answer the question. "
        "An answer may be COMPLETE_FOR_SUPPORTED_ARTIFACTS and simultaneously LIMITED_BY_ACQUISITION_TYPE. "
        "Do not turn recommended additional evidence into an allegation that the current examination was defective. "
        "Do not describe an attachment as sent or received unless the parent message direction supports that classification.\n\n"
        f"Evidence JSON:\n{json_dumps(evidence)}"
    )


def write_markdown(
    path: Path,
    ctx: CaseContext,
    events: List[Event],
    error_path: Path,
    inventory: List[Dict[str, Any]],
    correlations: List[Dict[str, Any]],
    buckets: List[Dict[str, Any]],
    entity_correlations: List[Dict[str, Any]],
    network_events: List[Event],
    network_indicators: List[Dict[str, Any]],
    network_summary: Dict[str, Any],
    coverage_records: List[CoverageRecord],
    app_coverage_records: List[AppCoverageRecord],
    hypotheses: List[Dict[str, Any]],
    question_answer: Optional[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    case_knowledge: Optional[Dict[str, Any]],
) -> None:
    counts: Dict[str, int] = {}
    sections: Dict[str, List[Event]] = {"before": [], "during": [], "after": [], "undated": []}
    for event in events:
        counts[event.source] = counts.get(event.source, 0) + 1
        sections.setdefault(section_for(event.timestamp, ctx.start, ctx.end), []).append(event)
    conversations = build_conversation_context(ctx, events)

    with path.open("w", encoding="utf-8") as f:
        f.write("# Window Investigator Report\n\n")
        f.write("## Time Window\n\n")
        f.write(f"Requested window: `{format_dt(ctx.start)}` to `{format_dt(ctx.end)}`\n\n")
        f.write(
            f"Context collected: `{format_dt(ctx.context_start)}` to "
            f"`{format_dt(ctx.context_end)}` ({ctx.context_minutes} minutes on each side)\n\n"
        )

        f.write("## Limitations\n\n")
        f.write(
            "This report summarizes handset-side artifacts recovered from the supplied decrypted backup. "
            "The presence, absence, or timing of a record should be interpreted with caution because iOS "
            "databases vary by version, retention policy, sync state, backup method, and application behavior. "
            "This report does not prove Silent SMS, command activity, intentional access, or causation. "
            "Network-level findings generally require carrier records, device diagnostic material, or other "
            "independent evidence.\n\n"
        )
        f.write(
            "Events labeled CONTEXT are outside the requested window but inside the configured context interval. "
            "LOW significance file timestamps may indicate only file system modification time and not user activity.\n\n"
        )
        f.write(
            "Confidence scores estimate confidence in the artifact record and parser interpretation, "
            "not confidence in any allegation, intent, causation, or unsupported conclusion.\n\n"
        )

        f.write("## Findings Summary\n\n")
        write_findings_summary(f, ctx, events, counts, inventory, correlations, buckets, hypotheses)

        f.write("## Artifact Inventory\n\n")
        f.write(
            "This inventory records whether expected artifact paths were present in the decrypted backup. "
            "Keyword or path matches are inventory observations only and should not be interpreted as proof of use.\n\n"
        )
        write_artifact_inventory(f, inventory)

        f.write("## Network Context Summary\n\n")
        write_network_context_summary(f, network_summary, network_events, network_indicators)

        f.write("## Hypothesis Testing\n\n")
        write_hypotheses(f, hypotheses)

        f.write("## Investigator Question Answer\n\n")
        write_question_answer_section(f, question_answer)

        f.write("## Source Counts\n\n")
        if counts:
            for source, count in sorted(counts.items()):
                f.write(f"- {source}: {count}\n")
        else:
            f.write("- No events found\n")
        f.write("\n")

        f.write("## Conversation Context\n\n")
        write_conversation_context(f, conversations)

        f.write("## Scored Activity Windows\n\n")
        write_scored_activity_windows(f, buckets)

        f.write("## Correlated Activity Clusters\n\n")
        write_correlation_clusters(f, correlations, ctx)

        f.write("## Cross-Artifact Entity Correlations\n\n")
        write_entity_correlations_section(f, entity_correlations)

        f.write("## Relationship Graph Summary\n\n")
        f.write(
            f"Relationship outputs were written to `window_investigator_relationships.csv`, "
            f"`window_investigator_graph.graphml`, and `window_investigator_graph.mmd`. "
            f"Graph edge count: {len(edges)}. Relationships are derived from normalized evidence and do not infer identity beyond recorded values.\n\n"
        )

        f.write("## Normalized Evidence Summary\n\n")
        write_normalized_evidence_summary(f, case_knowledge)

        for section in ("before", "during", "after"):
            title = {"before": "Before Window", "during": "During Window", "after": "After Window"}[section]
            f.write(f"## {title}\n\n")
            write_event_list(f, sections.get(section, []), ctx)

        if sections.get("undated"):
            f.write("## Undated\n\n")
            write_event_list(f, sections["undated"], ctx)

        f.write("## Chronological Reconstruction\n\n")
        write_event_list(f, events, ctx, include_section=True)

        f.write("## AI Summary Reference\n\n")
        if ctx.ai_summary and ctx.ai_summary_path:
            f.write(
                f"Optional AI output was written to `{ctx.ai_summary_path}`. "
                "AI output requires examiner validation and must not be treated as independent evidence.\n\n"
            )
        else:
            f.write("AI summary was not enabled for this run.\n\n")

        f.write("## Error Log\n\n")
        f.write(f"Errors and parser exceptions were written to `{error_path}`.\n")


def write_artifact_inventory(handle: Any, inventory: List[Dict[str, Any]]) -> None:
    handle.write("| Artifact | Found | File Count | Parser Enabled | Parsed Successfully | Events Produced | Configuration Only | Operational Records | Parser Errors | Example Paths |\n")
    handle.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n")
    for item in inventory:
        paths = "<br>".join(str(path) for path in item.get("paths", [])) or ""
        handle.write(
            f"| {item['artifact']} | {item['found']} | {item['file_count']} | "
            f"{item['parser_enabled']} | {item['parsed_successfully']} | "
            f"{item['event_count']} | {item.get('configuration_only', 0)} | "
            f"{item.get('operational_records', 0)} | {item['errors']} | {paths} |\n"
        )
    handle.write("\n")


def write_findings_summary(
    handle: Any,
    ctx: CaseContext,
    events: List[Event],
    counts: Dict[str, int],
    inventory: List[Dict[str, Any]],
    correlations: List[Dict[str, Any]],
    buckets: List[Dict[str, Any]],
    hypotheses: List[Dict[str, Any]],
) -> None:
    during = [event for event in events if in_range(event.timestamp, ctx.start, ctx.end)]
    context = [event for event in events if event.timestamp and not in_range(event.timestamp, ctx.start, ctx.end)]
    no_text = [event for event in events if event.source == "sms.db" and "<NO TEXT CONTENT>" in event.details]
    attachments = [event for event in events if event.source == "sms.db attachment"]
    highest = buckets[0] if buckets else None
    found_artifacts = sum(1 for item in inventory if item.get("found") == "YES")
    parser_errors = sum(int(item.get("errors", 0)) for item in inventory)
    exact_hits = []
    for allegation in ctx.allegation_times:
        exact_hits.extend([event for event in events if event.timestamp and abs(event.timestamp - allegation) <= timedelta(seconds=30)])
    normal_comm_near = events_near_times(
        [event for event in events if event.source in {"sms.db", "CallHistory", "sms.db attachment"}],
        ctx.allegation_times,
        timedelta(minutes=max(ctx.correlation_window_minutes, 3)),
    ) if ctx.allegation_times else []
    handle.write(f"- Total normalized events: {len(events)}\n")
    handle.write(f"- Events during requested window: {len(during)}\n")
    handle.write(f"- Context events: {len(context)}\n")
    handle.write(f"- Calls: {counts.get('CallHistory', 0)}\n")
    handle.write(f"- Messages: {counts.get('sms.db', 0)}\n")
    handle.write(f"- No-text messages: {len(no_text)}\n")
    handle.write(f"- Attachments: {len(attachments)}\n")
    handle.write(f"- Safari events: {counts.get('Safari', 0)}\n")
    handle.write(f"- Photos events: {counts.get('Photos', 0)}\n")
    handle.write(f"- Notifications: {counts.get('Notifications', 0)}\n")
    handle.write(f"- Correlations: {len(correlations)}\n")
    handle.write(f"- Scored buckets: {len(buckets)}\n")
    if highest:
        handle.write(f"- Highest scored bucket: {format_dt(highest['start'])} score={highest['score']}\n")
    handle.write(f"- Hypotheses assessed: {', '.join(item['hypothesis'] for item in hypotheses) or 'none'}\n")
    handle.write(f"- Artifact coverage: {found_artifacts}/{len(inventory)} inventory items found\n")
    handle.write(f"- Parser errors recorded in inventory: {parser_errors}\n\n")
    if ctx.allegation_times:
        handle.write(
            f"Direct normalized handset events within 30 seconds of supplied allegation time(s): {len(exact_hits)}. "
            "This count reflects artifact timing only and is not an assessment of causation.\n\n"
        )
        handle.write(
            f"Normal communication events within the configured review window around allegation time(s): {len(normal_comm_near)}.\n\n"
        )
    handle.write(
        "Direct evidence confirming Silent SMS was not identified by this normalized-event workflow. "
        "Going further generally requires carrier signaling records, baseband diagnostics, CommCenter/CoreTelephony logs, sysdiagnose material, or other independent evidence.\n\n"
    )


def write_hypotheses(handle: Any, hypotheses: List[Dict[str, Any]]) -> None:
    if not hypotheses:
        handle.write("No hypotheses were requested.\n\n")
        return
    for item in hypotheses:
        handle.write(f"### {item['hypothesis']}\n\n")
        handle.write(f"Confidence in Assessment: {item['confidence_in_assessment']}\n\n")
        handle.write(f"Supported examination status: {item.get('supported_examination_status', 'UNKNOWN')}\n\n")
        handle.write(f"Acquisition sufficiency status: {item.get('acquisition_sufficiency_status', 'UNKNOWN')}\n\n")
        handle.write(f"Basis: {item['basis']}\n\n")
        for title, key in (
            ("Evidence Supporting", "evidence_supporting"),
            ("Evidence Not Supporting / Contrary", "evidence_not_supporting_or_contrary"),
            ("Evidence Unavailable", "evidence_unavailable"),
            ("Unparsed Evidence", "unparsed_evidence"),
            ("Unsupported Evidence", "unsupported_evidence"),
            ("Parser Failures", "parser_failures"),
            ("Examination Gaps", "examination_gaps"),
            ("Acquisition Limitations", "acquisition_limitations"),
            ("Evidence Not Collected", "evidence_not_collected"),
            ("Additional Evidence That Could Increase Confidence", "additional_evidence_that_could_increase_confidence"),
            ("Required Additional Evidence", "required_additional_evidence"),
        ):
            handle.write(f"#### {title}\n\n")
            values = item.get(key) or ["None identified by deterministic rules."]
            for value in values:
                handle.write(f"- {value}\n")
            handle.write("\n")
        if item.get("answer_completeness"):
            handle.write(f"Answer completeness: {item['answer_completeness']}\n\n")
        if item.get("coverage_basis"):
            handle.write(f"Coverage basis: {item['coverage_basis']}\n\n")


def write_network_context_summary(
    handle: Any,
    summary: Dict[str, Any],
    network_events: List[Event],
    indicators: List[Dict[str, Any]],
) -> None:
    wifi = summary.get("wifi_summary", {})
    bluetooth = summary.get("bluetooth_summary", {})
    nearby = summary.get("airdrop_nearby_summary", {})
    cellular = summary.get("cellular_summary", {})
    vpn = summary.get("vpn_summary", {})
    data_usage = summary.get("data_usage_summary", {})
    handle.write(f"- Wi-Fi artifacts/events found: {wifi.get('event_count', 0)}\n")
    handle.write(f"- Known SSIDs: {', '.join(wifi.get('known_ssids', [])[:20]) or 'none identified'}\n")
    handle.write(f"- BSSIDs: {', '.join(wifi.get('bssids', [])[:20]) or 'none identified'}\n")
    handle.write(f"- Timestamped Wi-Fi state events: {wifi.get('timestamped_state_events', 0)}\n")
    handle.write(f"- Bluetooth devices found: {', '.join(bluetooth.get('devices', [])[:20]) or 'none identified'}\n")
    handle.write(f"- Timestamped Bluetooth state events: {bluetooth.get('timestamped_state_events', 0)}\n")
    handle.write(f"- AirDrop records: {nearby.get('airdrop_records', 0)}\n")
    handle.write(f"- Nearby/Continuity records: {nearby.get('nearby_records', 0)}\n")
    handle.write(f"- Cellular/telephony operational records: {cellular.get('operational_records', 0)}\n")
    handle.write(f"- VPN configurations or state records: {vpn.get('event_count', 0)}\n")
    handle.write(f"- IP addresses found: {summary.get('ip_summary', {}).get('count', 0)}\n")
    handle.write(f"- Hostnames/domains found: {summary.get('domain_summary', {}).get('count', 0)}\n")
    handle.write(f"- Data usage records: {data_usage.get('event_count', 0)}\n")
    handle.write(f"- Byte counters found: {data_usage.get('byte_counter_records', 0)}\n")
    handle.write(f"- Exact network events aligned with allegation times: {len(summary.get('exact_network_events_near_allegation_times', []))}\n")
    handle.write(f"- Packet capture files listed in backup: {len(summary.get('packet_capture_evidence', []))}\n\n")
    handle.write(
        "The examined backup did not contain packet-capture evidence sufficient to reconstruct complete network transmissions "
        "unless packet capture files are explicitly listed above. IP addresses or byte counters are reported only where explicitly "
        "present in recovered artifacts. MAC addresses in Wi-Fi and Bluetooth artifacts represent local-network or accessory "
        "identifiers and should not be interpreted as remote internet endpoints.\n\n"
    )
    if indicators:
        handle.write("Top network indicators:\n")
        for item in indicators[:20]:
            handle.write(f"- {item['indicator_type']} `{item['normalized_value']}` | {item['classification']} | events={item['event_count']} | sources={', '.join(item['sources'])}\n")
        handle.write("\n")
    handle.write("Network event outputs were written to `window_investigator_network_events.csv`, `window_investigator_network_indicators.csv`, and `window_investigator_network_summary.json`.\n\n")


def write_question_answer_section(handle: Any, answer: Optional[Dict[str, Any]]) -> None:
    if not answer:
        handle.write("No investigator question was supplied.\n\n")
        return
    handle.write(f"Question: {answer['question']}\n\n")
    handle.write(f"Answer: {answer['answer']}\n\n")
    handle.write("Supporting Events:\n")
    if answer["supporting_events"]:
        for event in answer["supporting_events"][:20]:
            handle.write(f"- {event_summary(event)}\n")
    else:
        handle.write("- None identified by deterministic rules.\n")
    handle.write("\nContradictory or Non-supporting Evidence:\n")
    for item in answer["contradictory_or_non_supporting"]:
        handle.write(f"- {item}\n")
    handle.write("\nLimitations:\n")
    for item in answer["limitations"]:
        handle.write(f"- {item}\n")
    handle.write("\nAdditional Evidence Needed:\n")
    for item in answer["additional_evidence_needed"]:
        handle.write(f"- {item}\n")
    handle.write("\n")


def write_scored_activity_windows(handle: Any, buckets: List[Dict[str, Any]]) -> None:
    if not buckets:
        handle.write("No higher-priority review windows met the configured score threshold.\n\n")
        return
    for bucket in buckets[:25]:
        sources = ", ".join(sorted({event.source for event in bucket["events"]}))
        bonuses = ", ".join(bucket.get("bonuses", [])) or "none"
        handle.write(f"### {format_dt(bucket['start'])} to {format_dt(bucket['end'])} - score {bucket['score']}\n\n")
        handle.write(f"Sources: {sources} | Event count: {len(bucket['events'])} | Bonuses: {bonuses}\n\n")
        for event in sorted(bucket["events"], key=lambda e: (e.timestamp or datetime.max, e.source))[:10]:
            handle.write(f"- {concise_event(event)}\n")
        handle.write("\n")


def write_entity_correlations_section(handle: Any, correlations: List[Dict[str, Any]]) -> None:
    if not correlations:
        handle.write("No cross-artifact entity correlations met the reporting threshold.\n\n")
        return
    for item in correlations[:50]:
        handle.write(
            f"- {item['entity_type']} `{item['entity']}` | sources={item['source_count']} | "
            f"events={item['total_event_count']} | first={format_dt(item['first_seen'])} | "
            f"last={format_dt(item['last_seen'])} | confidence={item['confidence']}\n"
        )
    handle.write("\n")


def write_conversation_context(handle: Any, conversations: List[Dict[str, Any]]) -> None:
    if not conversations:
        handle.write("No sms.db conversations with messages inside the requested window were reconstructed.\n\n")
        return
    for conversation in conversations:
        label = (
            conversation.get("chat_display_name")
            or conversation.get("chat_identifier")
            or f"chat ROWID {conversation.get('chat_rowid')}"
        )
        handle.write(f"### {label}\n\n")
        handle.write(
            f"chat_rowid={conversation.get('chat_rowid')} | "
            f"window_message_count={conversation.get('window_message_count')}\n\n"
        )
        for message in conversation.get("messages", []):
            marker = " [WINDOW]" if message.get("section") == "during" else ""
            handle.write(
                f"- `{message.get('timestamp')}`{marker} | {message.get('direction')} | "
                f"contact={message.get('contact')} | service={message.get('service')} | "
                f"attachments={message.get('attachment_summary')} | guid={message.get('guid')} | "
                f"text={message.get('text')}\n"
            )
        handle.write("\n")


def write_correlation_clusters(handle: Any, clusters: List[Dict[str, Any]], ctx: CaseContext) -> None:
    if not clusters:
        handle.write(
            "No correlated activity clusters met the configured threshold. "
            "This is not evidence that related activity did or did not occur.\n\n"
        )
        return
    handle.write(
        f"Clusters use normalized events within +/- {ctx.correlation_window_minutes} minutes "
        f"and require score >= {ctx.min_correlation_score}. These are correlated activity clusters, "
        "not findings of causation.\n\n"
    )
    for cluster in clusters:
        central = format_dt(cluster.get("central_timestamp"))
        sources = ", ".join(cluster.get("sources", []))
        events = cluster.get("events", [])
        handle.write(f"### {central} - score {cluster.get('score')}\n\n")
        handle.write(f"Involved sources: {sources} | Event count: {len(events)}\n\n")
        for event in events[:12]:
            handle.write(f"- {concise_event(event)}\n")
        if len(events) > 12:
            handle.write(f"- ... {len(events) - 12} additional event(s) omitted from this cluster summary\n")
        handle.write("\n")


def concise_event(event: Event) -> str:
    details = event.details.replace("\n", " ")
    if len(details) > 180:
        details = details[:177] + "..."
    return (
        f"`{format_dt(event.timestamp)}` | {event.source} | "
        f"{event.event_type} | {event.significance} | {details}"
    )


def write_event_list(handle: Any, events: List[Event], ctx: CaseContext, include_section: bool = False) -> None:
    if not events:
        handle.write("No events recorded in this section.\n\n")
        return
    for event in events:
        heading = f"{format_dt(event.timestamp) or 'UNDATED'} - {event.source} - {event.event_type} - {event.significance}"
        if include_section:
            heading += f" - {section_for(event.timestamp, ctx.start, ctx.end).upper()}"
        handle.write(f"### {heading}\n\n")
        handle.write(f"{event.details}\n\n")
        if event.metadata:
            handle.write("<details><summary>Normalized metadata</summary>\n\n")
            handle.write("```json\n")
            handle.write(json_dumps(event.metadata))
            handle.write("\n```\n\n</details>\n\n")


def copy_outputs_if_needed(paths: Sequence[Path], output_dir: Optional[Path]) -> None:
    if not output_dir:
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        target = output_dir / path.name
        if path.resolve() == target.resolve():
            continue
        target.write_bytes(path.read_bytes())


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a forensic event timeline for a decrypted iPhone backup window.")
    parser.add_argument("--case", default="birch", help="Case name under ~/cases when --case-dir is not supplied.")
    parser.add_argument("--case-dir", help="Case directory containing a decrypted/ backup tree.")
    parser.add_argument("--start", required=True, help="Window start, e.g. '2026-07-09 14:00:00'.")
    parser.add_argument("--end", required=True, help="Window end, e.g. '2026-07-09 15:00:00'.")
    parser.add_argument("--context-minutes", type=int, default=5, help="Minutes to collect before and after the window.")
    parser.add_argument(
        "--conversation-context-count",
        type=int,
        default=10,
        help="Number of messages before and after each in-window message to include per conversation.",
    )
    parser.add_argument(
        "--correlation-window-minutes",
        type=int,
        default=3,
        help="Minutes on each side of an in-window event to use for correlation clusters.",
    )
    parser.add_argument(
        "--min-correlation-score",
        type=int,
        default=6,
        help="Minimum score required to report a correlated activity cluster.",
    )
    parser.add_argument("--question", help="Optional deterministic investigator question to answer from normalized events.")
    parser.add_argument(
        "--question-output",
        default="reports/window_investigator_question.md",
        help="Markdown output path for the deterministic question answer.",
    )
    parser.add_argument("--score-bucket-minutes", type=int, default=5, help="Minutes per scored activity bucket.")
    parser.add_argument("--min-bucket-score", type=int, default=5, help="Minimum scored bucket value to report.")
    parser.add_argument(
        "--allegation-time",
        action="append",
        default=[],
        help="Allegation/reference timestamp. May be supplied multiple times.",
    )
    parser.add_argument(
        "--hypothesis",
        action="append",
        default=[],
        help="Hypothesis to evaluate deterministically. May be supplied multiple times.",
    )
    parser.add_argument("--ai-summary", action="store_true", help="Generate an optional AI summary via local Ollama.")
    parser.add_argument("--ollama-url", default="http://172.29.128.1:11434/api/generate", help="Ollama generate endpoint.")
    parser.add_argument("--ollama-model", default="qwen3:14b", help="Ollama model name.")
    parser.add_argument("--ollama-timeout", type=int, default=600, help="Ollama request timeout in seconds.")
    parser.add_argument("--ai-top-events", type=int, default=50, help="Number of ranked normalized events to include in AI prompt.")
    parser.add_argument("--single-report", action="store_true", help="Write only one consolidated examiner-facing Markdown report plus the error log.")
    parser.add_argument("--window-only", action="store_true", help="In single-report mode, show only events whose primary timestamp is inside the requested window.")
    parser.add_argument("--coverage-hash-all", action="store_true", help="Hash every inventoried file for coverage reporting.")
    parser.add_argument("--coverage-hash-max-size-mb", type=int, default=100, help="Maximum file size to hash for default coverage hashing.")
    parser.add_argument("--coverage-inventory-only", action="store_true", help="Build coverage inventory outputs without running artifact parsers.")
    parser.add_argument("--export-coverage-files", action="store_true", help="In single-report mode, also write machine-readable coverage CSV/JSON files.")
    parser.add_argument("--export-case-knowledge", action="store_true", help="Write reports/window_investigator_case_knowledge.json with normalized events, entities, relationships, coverage, and clusters.")
    parser.add_argument("--report-audience", default="attorney", help="Audience for generated client report; default attorney.")
    parser.add_argument("--no-technical-appendix", action="store_true", help="Skip report_technical_appendix outputs.")
    parser.add_argument("--include-full-unsupported-inventory", action="store_true", help="Allow full unsupported inventory details in generated report outputs.")
    parser.add_argument("--include-relationship-ids", action="store_true", help="Include relationship IDs in client-facing report where applicable.")
    parser.add_argument("--include-normalized-event-ids", action="store_true", help="Include normalized event IDs in client-facing report where applicable.")
    parser.add_argument("--include-hashes-in-main-report", action="store_true", help="Include hashes in the client-facing main report.")
    parser.add_argument("--max-client-context-messages", type=int, default=5, help="Maximum context messages to include in client report.")
    parser.add_argument("--max-client-correlated-events", type=int, default=5, help="Maximum correlated events to include in client report.")
    parser.add_argument("--redact-personal-data", action="store_true", help="Redact personal data in client-facing report where supported.")
    parser.add_argument(
        "--copy-output-dir",
        help="Optional directory to receive copies of the generated report, CSV, and error log.",
    )
    parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="List enabled plugins and exit without scanning.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    enabled = plugins()
    if args.list_plugins:
        for plugin in enabled:
            print(plugin.name)
        return 0

    start = parse_dt(args.start)
    end = parse_dt(args.end)
    if end < start:
        parser.error("--end must be later than or equal to --start")

    case_dir = Path(args.case_dir).expanduser() if args.case_dir else Path.home() / "cases" / args.case
    ctx = CaseContext(
        case_dir,
        start,
        end,
        args.context_minutes,
        args.conversation_context_count,
        args.correlation_window_minutes,
        args.min_correlation_score,
    )
    ctx.hypotheses = args.hypothesis
    ctx.allegation_times = [parse_dt(value) for value in args.allegation_time]
    ctx.question = args.question
    ctx.question_output = (ctx.case_dir / args.question_output) if args.question_output and not Path(args.question_output).is_absolute() else (Path(args.question_output) if args.question_output else None)
    ctx.score_bucket_minutes = args.score_bucket_minutes
    ctx.min_bucket_score = args.min_bucket_score
    ctx.ai_summary = args.ai_summary
    ctx.ollama_url = args.ollama_url
    ctx.ollama_model = args.ollama_model
    ctx.ollama_timeout = args.ollama_timeout
    ctx.ai_top_events = args.ai_top_events
    ctx.case_name = args.case
    ctx.single_report = args.single_report
    ctx.window_only = args.window_only
    ctx.coverage_hash_all = args.coverage_hash_all
    ctx.coverage_hash_max_size_mb = args.coverage_hash_max_size_mb
    ctx.coverage_inventory_only = args.coverage_inventory_only
    ctx.export_coverage_files = args.export_coverage_files
    ctx.export_case_knowledge = args.export_case_knowledge
    ctx.report_config = ReportConfig(
        audience=args.report_audience,
        include_technical_appendix=not args.no_technical_appendix,
        include_full_unsupported_inventory=args.include_full_unsupported_inventory,
        include_relationship_ids=args.include_relationship_ids,
        include_normalized_event_ids=args.include_normalized_event_ids,
        include_hashes_in_main_report=args.include_hashes_in_main_report,
        max_context_messages=args.max_client_context_messages,
        max_correlated_events=args.max_client_correlated_events,
        redact_personal_data=args.redact_personal_data,
    )

    all_events: List[Event] = []
    if not ctx.coverage_inventory_only:
        for plugin in enabled:
            error_count_before = len(ctx.errors.records)
            before_count = len(all_events)
            all_events.extend(plugin.safe_collect(ctx))
            produced = len(all_events) - before_count
            ctx.plugin_stats[plugin.name] = {
                "events": produced,
                "errors": len(ctx.errors.records) - error_count_before,
            }
            print(f"[+] {plugin.name}: {produced} events")
    else:
        print("[+] Coverage inventory only: artifact parsers were not run")

    all_events = dedupe_events(all_events)
    apply_confidence(all_events)
    link_message_attachments(all_events)
    if ctx.single_report:
        md_path, error_path = write_single_report_outputs(ctx, all_events)
        print(f"[+] Events found: {len(all_events)}")
        print(f"[+] Final report: {md_path}")
        print(f"[+] Errors: {error_path}")
        return 0

    csv_path, md_path, error_path = write_outputs(ctx, all_events)
    copy_outputs_if_needed([csv_path, md_path, error_path], Path(args.copy_output_dir).expanduser() if args.copy_output_dir else None)

    print(f"[+] Events found: {len(all_events)}")
    print(f"[+] CSV: {csv_path}")
    print(f"[+] Report: {md_path}")
    print(f"[+] Errors: {error_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
