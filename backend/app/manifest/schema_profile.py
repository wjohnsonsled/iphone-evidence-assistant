"""Read-only, schema-only candidate recognition for controlled Manifest.db copies."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from app.evidence_core.schema_fingerprint import (
    SchemaFingerprintObservation,
    record_schema_fingerprint,
)
from app.intake.controlled_copy import ControlledCopyError, ControlledSQLiteCopy
from app.intake.resource_limits import IntakeResourcePolicy, ResourceLimitExceeded

PROFILE_ID = "apple-manifestdb-schema"
PROFILE_VERSION = "1"
FINGERPRINT_PROFILE_ID = "manifestdb-schema-canonical-json-sha256"
FINGERPRINT_PROFILE_VERSION = "1"
READER_ID = "sqlite-schema-only-reader"
READER_VERSION = "1"
LIMITATIONS = (
    "Schema recognition is not Apple backup, parser, artifact, or workflow support.",
    "Schema compatibility does not interpret evidence or establish evidentiary completeness.",
    "The profile is based on approved synthetic and repository-characterized structure, not authoritative Apple schema documentation.",
    "Unknown additions are preserved and do not establish future-version compatibility.",
)


class SQLiteAffinity(str, Enum):
    INTEGER = "INTEGER"
    TEXT = "TEXT"
    BLOB = "BLOB"
    REAL = "REAL"
    NUMERIC = "NUMERIC"


class TableState(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    DUPLICATE = "DUPLICATE"
    UNREADABLE = "UNREADABLE"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"
    NOT_EVALUATED = "NOT_EVALUATED"


class ColumnState(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    DUPLICATE = "DUPLICATE"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    UNKNOWN = "UNKNOWN"
    NOT_EVALUATED = "NOT_EVALUATED"


class CompatibilityOutcome(str, Enum):
    SCHEMA_COMPATIBLE = "SCHEMA_COMPATIBLE"
    SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS = "SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS"
    SCHEMA_UNKNOWN = "SCHEMA_UNKNOWN"
    SCHEMA_NOT_RECOGNIZED = "SCHEMA_NOT_RECOGNIZED"
    SCHEMA_REQUIRED_COMPONENT_MISSING = "SCHEMA_REQUIRED_COMPONENT_MISSING"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    SCHEMA_CORRUPT = "SCHEMA_CORRUPT"
    SCHEMA_NOT_EVALUATED = "SCHEMA_NOT_EVALUATED"
    SCHEMA_INDETERMINATE = "SCHEMA_INDETERMINATE"


@dataclass(frozen=True, slots=True)
class ColumnRule:
    name: str
    affinity: SQLiteAffinity
    required: bool
    primary_key_position: int | None = None
    unique_required: bool = False


@dataclass(frozen=True, slots=True)
class TableRule:
    name: str
    required: bool
    columns: tuple[ColumnRule, ...]
    foreign_keys_required: tuple[str, ...] = ()
    indexes_informational_only: bool = True


@dataclass(frozen=True, slots=True)
class ManifestSchemaProfile:
    profile_id: str
    profile_version: str
    description: str
    apple_backup_generation: str
    sqlite_characteristics: tuple[str, ...]
    required_tables: tuple[TableRule, ...]
    optional_tables: tuple[TableRule, ...]
    known_apple_notes: tuple[str, ...]
    limitations: tuple[str, ...]


FILES_RULE = TableRule(
    "Files",
    True,
    (
        ColumnRule("fileID", SQLiteAffinity.TEXT, True),
        ColumnRule("domain", SQLiteAffinity.TEXT, True),
        ColumnRule("relativePath", SQLiteAffinity.TEXT, True),
        ColumnRule("flags", SQLiteAffinity.INTEGER, True),
        ColumnRule("file", SQLiteAffinity.BLOB, True),
    ),
)
MANIFEST_SCHEMA_PROFILE = ManifestSchemaProfile(
    PROFILE_ID,
    PROFILE_VERSION,
    "Candidate Apple local-backup Manifest.db Files-table schema family.",
    "Candidate ordinary Apple local-backup Files-table generation; no iOS-version allowlist.",
    (
        "SQLite format-3 header",
        "page size 512 through 65536 in valid powers of two",
        "read format 1 or 2",
        "schema format 1 through 4",
        "read-only immutable controlled-copy access",
    ),
    (FILES_RULE,),
    (),
    (
        "DEC-0008 requires case-insensitive Files/fileID/domain/relativePath/flags/file identifiers.",
        "Affinity expectations derive from validated repository synthetic fixtures, not public Apple schema documentation.",
        "No primary-key, uniqueness, foreign-key, trigger, view, statistic, or index is required by version 1.",
    ),
    LIMITATIONS,
)


@dataclass(frozen=True, slots=True)
class SchemaValidationContext:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    database_identity_id: UUID
    processing_run_id: UUID
    authorized_scope: tuple[UUID, UUID, UUID, UUID]
    observed_at: datetime

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("schema_observation_time_invalid")


@dataclass(frozen=True, slots=True)
class RawColumn:
    name: str
    declared_type: str
    not_null: bool
    default_present: bool
    primary_key_position: int


@dataclass(frozen=True, slots=True)
class RawIndex:
    name: str
    unique: bool
    columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RawTable:
    name: str
    columns: tuple[RawColumn, ...]
    indexes: tuple[RawIndex, ...]


@dataclass(frozen=True, slots=True)
class ColumnObservation:
    table_name: str
    column_name: str
    required: bool
    state: ColumnState
    declared_type: str | None
    observed_affinity: SQLiteAffinity | None
    expected_affinity: SQLiteAffinity | None
    primary_key_position: int | None


@dataclass(frozen=True, slots=True)
class TableObservation:
    table_name: str
    required: bool
    state: TableState
    columns: tuple[ColumnObservation, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ManifestSchemaValidationResult:
    outcome: CompatibilityOutcome
    explanation: str
    context: SchemaValidationContext
    profile_id: str
    profile_version: str
    reader_id: str
    reader_version: str
    sqlite_page_size: int | None
    sqlite_read_format: int | None
    sqlite_schema_format: int | None
    tables: tuple[TableObservation, ...]
    raw_schema: tuple[RawTable, ...]
    canonical_schema_json: str | None
    fingerprint: SchemaFingerprintObservation | None
    reason_code: str
    limitations: tuple[str, ...] = LIMITATIONS


def sqlite_affinity(declared_type: str) -> SQLiteAffinity:
    normalized = declared_type.upper()
    if "INT" in normalized:
        return SQLiteAffinity.INTEGER
    if any(token in normalized for token in ("CHAR", "CLOB", "TEXT")):
        return SQLiteAffinity.TEXT
    if normalized == "" or "BLOB" in normalized:
        return SQLiteAffinity.BLOB
    if any(token in normalized for token in ("REAL", "FLOA", "DOUB")):
        return SQLiteAffinity.REAL
    return SQLiteAffinity.NUMERIC


def _scope_check(context: SchemaValidationContext) -> None:
    actual = (
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.processing_run_id,
    )
    if actual != context.authorized_scope:
        raise PermissionError("manifest_schema_scope_mismatch")


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _read_raw_schema(
    uri: str, resource_policy: IntakeResourcePolicy
) -> tuple[RawTable, ...]:
    connection = sqlite3.connect(uri, uri=True)
    work_units = 0
    interrupted = False

    def progress() -> int:
        nonlocal work_units, interrupted
        work_units += 1_000
        if work_units > resource_policy.max_sqlite_work_units:
            interrupted = True
            return 1
        return 0

    try:
        connection.execute("PRAGMA query_only=ON")
        connection.set_progress_handler(progress, 1_000)
        names = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_schema "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        if len(names) > resource_policy.max_schema_entries:
            raise ResourceLimitExceeded("schema_enumeration")
        tables: list[RawTable] = []
        schema_entries = len(names)
        for name in names:
            columns = tuple(
                RawColumn(
                    str(row[1]),
                    str(row[2] or ""),
                    bool(row[3]),
                    row[4] is not None,
                    int(row[5]),
                )
                for row in connection.execute(f"PRAGMA table_info({_quote(name)})")
            )
            index_rows = list(connection.execute(f"PRAGMA index_list({_quote(name)})"))
            indexes = tuple(
                RawIndex(
                    str(row[1]),
                    bool(row[2]),
                    tuple(
                        str(info[2])
                        for info in connection.execute(
                            f"PRAGMA index_info({_quote(str(row[1]))})"
                        )
                    ),
                )
                for row in index_rows
            )
            schema_entries += len(columns) + len(indexes)
            if schema_entries > resource_policy.max_schema_entries:
                raise ResourceLimitExceeded("schema_enumeration")
            tables.append(RawTable(name, columns, indexes))
        return tuple(tables)
    except sqlite3.OperationalError as exc:
        if interrupted:
            raise ResourceLimitExceeded("sqlite_processing_work") from exc
        raise
    finally:
        connection.set_progress_handler(None, 0)
        connection.close()


def _canonical_schema(raw_schema: tuple[RawTable, ...]) -> str:
    payload = {
        "fingerprint_profile_id": FINGERPRINT_PROFILE_ID,
        "fingerprint_profile_version": FINGERPRINT_PROFILE_VERSION,
        "schema_profile_id": PROFILE_ID,
        "schema_profile_version": PROFILE_VERSION,
        "tables": [
            {
                "name": table.name.casefold(),
                "columns": [
                    {
                        "name": column.name.casefold(),
                        "declared_type": column.declared_type.upper(),
                        "not_null": column.not_null,
                        "default_present": column.default_present,
                        "primary_key_position": column.primary_key_position,
                    }
                    for column in sorted(table.columns, key=lambda item: item.name.casefold())
                ],
                "indexes": [
                    {
                        "name": index.name.casefold(),
                        "unique": index.unique,
                        "columns": tuple(name.casefold() for name in index.columns),
                    }
                    for index in sorted(table.indexes, key=lambda item: item.name.casefold())
                ],
            }
            for table in sorted(raw_schema, key=lambda item: item.name.casefold())
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def evaluate_schema(
    raw_schema: tuple[RawTable, ...],
    context: SchemaValidationContext,
    *,
    page_size: int = 4096,
    read_format: int = 1,
    schema_format: int = 4,
) -> ManifestSchemaValidationResult:
    _scope_check(context)
    table_groups: dict[str, list[RawTable]] = {}
    for table in raw_schema:
        table_groups.setdefault(table.name.casefold(), []).append(table)

    observations: list[TableObservation] = []
    required_missing = False
    invalid = False
    unknown_elements = False
    recognized_names = {rule.name.casefold() for rule in MANIFEST_SCHEMA_PROFILE.required_tables}

    for rule in MANIFEST_SCHEMA_PROFILE.required_tables:
        matches = table_groups.get(rule.name.casefold(), [])
        if not matches:
            required_missing = True
            observations.append(
                TableObservation(rule.name, True, TableState.ABSENT, tuple(
                    ColumnObservation(
                        rule.name, column.name, column.required, ColumnState.NOT_EVALUATED,
                        None, None, column.affinity, None
                    )
                    for column in rule.columns
                ), LIMITATIONS)
            )
            continue
        if len(matches) > 1:
            invalid = True
            observations.append(
                TableObservation(rule.name, True, TableState.DUPLICATE, (), LIMITATIONS)
            )
            continue
        table = matches[0]
        column_groups: dict[str, list[RawColumn]] = {}
        for column in table.columns:
            column_groups.setdefault(column.name.casefold(), []).append(column)
        columns: list[ColumnObservation] = []
        known_columns = {column.name.casefold() for column in rule.columns}
        for column_rule in rule.columns:
            found = column_groups.get(column_rule.name.casefold(), [])
            if not found:
                required_missing = True
                columns.append(
                    ColumnObservation(
                        table.name, column_rule.name, column_rule.required,
                        ColumnState.ABSENT, None, None, column_rule.affinity, None,
                    )
                )
            elif len(found) > 1:
                invalid = True
                columns.append(
                    ColumnObservation(
                        table.name, column_rule.name, column_rule.required,
                        ColumnState.DUPLICATE, None, None, column_rule.affinity, None,
                    )
                )
            else:
                item = found[0]
                affinity = sqlite_affinity(item.declared_type)
                state = (
                    ColumnState.PRESENT
                    if affinity is column_rule.affinity
                    else ColumnState.TYPE_MISMATCH
                )
                if state is ColumnState.TYPE_MISMATCH:
                    invalid = True
                columns.append(
                    ColumnObservation(
                        table.name, item.name, column_rule.required, state,
                        item.declared_type, affinity, column_rule.affinity,
                        item.primary_key_position,
                    )
                )
        for item in sorted(table.columns, key=lambda value: value.name.casefold()):
            if item.name.casefold() not in known_columns:
                unknown_elements = True
                columns.append(
                    ColumnObservation(
                        table.name, item.name, False, ColumnState.UNKNOWN,
                        item.declared_type, sqlite_affinity(item.declared_type), None,
                        item.primary_key_position,
                    )
                )
        observations.append(
            TableObservation(table.name, True, TableState.PRESENT, tuple(columns), LIMITATIONS)
        )

    for table in sorted(raw_schema, key=lambda item: item.name.casefold()):
        if table.name.casefold() not in recognized_names:
            unknown_elements = True
            observations.append(
                TableObservation(
                    table.name,
                    False,
                    TableState.UNKNOWN,
                    tuple(
                        ColumnObservation(
                            table.name, column.name, False, ColumnState.UNKNOWN,
                            column.declared_type, sqlite_affinity(column.declared_type),
                            None, column.primary_key_position,
                        )
                        for column in sorted(table.columns, key=lambda item: item.name.casefold())
                    ),
                    LIMITATIONS,
                )
            )

    canonical = _canonical_schema(raw_schema)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    fingerprint = record_schema_fingerprint(
        source_artifact_id=context.source_artifact_id,
        processing_run_id=context.processing_run_id,
        parser_identity_id=None,
        profile_id=FINGERPRINT_PROFILE_ID,
        profile_version=FINGERPRINT_PROFILE_VERSION,
        canonical_input_reference=(
            "FOR-011 manifestdb schema canonical JSON profile version 1"
        ),
        sha256_digest=digest,
        observed_at=context.observed_at,
        limitations=LIMITATIONS,
    )

    if invalid:
        outcome = CompatibilityOutcome.SCHEMA_INVALID
        reason = "schema_component_invalid"
    elif required_missing and raw_schema:
        known_overlap = bool(set(table_groups) & recognized_names)
        outcome = (
            CompatibilityOutcome.SCHEMA_REQUIRED_COMPONENT_MISSING
            if known_overlap
            else CompatibilityOutcome.SCHEMA_UNKNOWN
        )
        reason = (
            "REQUIRED_SCHEMA_COMPONENT_MISSING"
            if known_overlap
            else "unknown_schema"
        )
    elif required_missing:
        outcome = CompatibilityOutcome.SCHEMA_REQUIRED_COMPONENT_MISSING
        reason = "REQUIRED_SCHEMA_COMPONENT_MISSING"
    elif unknown_elements:
        outcome = CompatibilityOutcome.SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS
        reason = "unknown_optional_elements_preserved"
    else:
        outcome = CompatibilityOutcome.SCHEMA_COMPATIBLE
        reason = "exact_profile_match"
    return ManifestSchemaValidationResult(
        outcome,
        "Observed schema evaluated against the candidate Manifest.db profile.",
        context,
        PROFILE_ID,
        PROFILE_VERSION,
        READER_ID,
        READER_VERSION,
        page_size,
        read_format,
        schema_format,
        tuple(observations),
        raw_schema,
        canonical,
        fingerprint,
        reason,
    )


def _early_result(
    outcome: CompatibilityOutcome,
    reason: str,
    explanation: str,
    context: SchemaValidationContext,
    *,
    page_size: int | None = None,
    read_format: int | None = None,
    schema_format: int | None = None,
) -> ManifestSchemaValidationResult:
    return ManifestSchemaValidationResult(
        outcome, explanation, context, PROFILE_ID, PROFILE_VERSION, READER_ID,
        READER_VERSION, page_size, read_format, schema_format, (), (), None,
        None, reason,
    )


def validate_controlled_manifest_schema(
    controlled: ControlledSQLiteCopy,
    context: SchemaValidationContext,
    resource_policy: IntakeResourcePolicy,
) -> ManifestSchemaValidationResult:
    _scope_check(context)
    controlled.verify_working_files()
    try:
        with controlled.main_working_path.open("rb") as stream:
            header = stream.read(100)
    except OSError:
        return _early_result(
            CompatibilityOutcome.SCHEMA_INDETERMINATE,
            "controlled_header_unreadable",
            "The controlled SQLite header could not be read.",
            context,
        )
    if len(header) < 100 or header[:16] != b"SQLite format 3\x00":
        return _early_result(
            CompatibilityOutcome.SCHEMA_NOT_RECOGNIZED,
            "sqlite_header_not_recognized",
            "The controlled file does not have a recognized SQLite format-3 header.",
            context,
        )
    raw_page_size = int.from_bytes(header[16:18], "big")
    page_size = 65536 if raw_page_size == 1 else raw_page_size
    read_format = header[19]
    schema_format = int.from_bytes(header[44:48], "big")
    valid_page_size = (
        512 <= page_size <= 65536
        and page_size & (page_size - 1) == 0
    )
    if not valid_page_size or read_format not in {1, 2} or schema_format not in {1, 2, 3, 4}:
        return _early_result(
            CompatibilityOutcome.SCHEMA_INVALID,
            "sqlite_header_characteristics_invalid",
            "SQLite header characteristics do not meet the candidate profile.",
            context,
            page_size=page_size,
            read_format=read_format,
            schema_format=schema_format,
        )
    try:
        structural = controlled.inspect_sqlite_structure()
        if structural.integrity_rows != ("ok",):
            return _early_result(
                CompatibilityOutcome.SCHEMA_CORRUPT,
                "sqlite_integrity_failed",
                "SQLite integrity preconditions failed.",
                context,
                page_size=page_size,
                read_format=read_format,
                schema_format=schema_format,
            )
        raw_schema = _read_raw_schema(controlled.read_only_uri, resource_policy)
        controlled.verify_working_files()
    except ControlledCopyError as exc:
        outcome = (
            CompatibilityOutcome.SCHEMA_CORRUPT
            if exc.code == "sqlite_validation_failed"
            else CompatibilityOutcome.SCHEMA_INDETERMINATE
        )
        return _early_result(
            outcome,
            exc.code,
            "Controlled read-only schema validation failed.",
            context,
            page_size=page_size,
            read_format=read_format,
            schema_format=schema_format,
        )
    except (sqlite3.DatabaseError, ResourceLimitExceeded):
        return _early_result(
            CompatibilityOutcome.SCHEMA_INDETERMINATE,
            "schema_read_failed",
            "Schema enumeration could not complete defensibly.",
            context,
            page_size=page_size,
            read_format=read_format,
            schema_format=schema_format,
        )
    return evaluate_schema(
        raw_schema,
        context,
        page_size=page_size,
        read_format=read_format,
        schema_format=schema_format,
    )
