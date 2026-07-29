"""Fail-closed candidate grammar for Manifest.db Files.domain observations."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid5

from app.manifest.files_query import FilesQueryContext, FilesRowObservation
from app.manifest.files_query_v2 import V2RowObservation
from app.manifest.identifier_normalization import StorageClass

PROFILE_ID = "manifestdb-domain-grammar"
PROFILE_VERSION = "1"
IMPLEMENTATION_ID = "manifestdb-domain-normalizer"
IMPLEMENTATION_VERSION = "1"
SOURCE_TABLE = "Files"
SOURCE_COLUMN = "domain"
_NAMESPACE = UUID("06040000-0000-4000-8000-000000000001")
_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]*$")

LIMITATIONS = (
    "Recognized domain grammar does not establish application installation, execution, ownership, or user activity.",
    "A domain observation does not establish container, file, artifact, or physical-object existence.",
    "Domain family labels are structural candidate observations, not artifact or parser support.",
    "Unknown and malformed forms remain uninterpreted; backup completeness and absence are not evaluated.",
    "No capability is Supported by this candidate profile.",
)


class DomainFamily(str, Enum):
    HOME = "HOME"
    WIRELESS = "WIRELESS"
    ROOT = "ROOT"
    SYSTEM_PREFERENCES = "SYSTEM_PREFERENCES"
    MANAGED_PREFERENCES = "MANAGED_PREFERENCES"
    MEDIA = "MEDIA"
    CAMERA_ROLL = "CAMERA_ROLL"
    APPLICATION = "APPLICATION"
    APPLICATION_GROUP = "APPLICATION_GROUP"
    APPLICATION_PLUGIN = "APPLICATION_PLUGIN"
    SYSTEM_CONTAINER = "SYSTEM_CONTAINER"
    SYSTEM_SHARED_CONTAINER = "SYSTEM_SHARED_CONTAINER"
    UNKNOWN = "UNKNOWN"


class DomainStructure(str, Enum):
    RECOGNIZED_LITERAL = "RECOGNIZED_LITERAL"
    RECOGNIZED_PREFIXED = "RECOGNIZED_PREFIXED"
    UNKNOWN_STRUCTURE = "UNKNOWN_STRUCTURE"
    MALFORMED_STRUCTURE = "MALFORMED_STRUCTURE"
    NULL = "NULL"
    EMPTY = "EMPTY"
    UNSUPPORTED_STORAGE_CLASS = "UNSUPPORTED_STORAGE_CLASS"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    READ_FAILURE = "READ_FAILURE"
    NOT_EVALUATED = "NOT_EVALUATED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class DomainSourceObservation:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    source_artifact_id: UUID
    controlled_copy_identity_id: UUID
    database_identity_id: UUID
    processing_run_id: UUID
    row_locator: int
    query_profile_id: str
    query_profile_version: str
    locator_profile_id: str
    locator_profile_version: str
    source_table: str
    source_column: str
    storage_class: StorageClass
    upstream_value_state: str
    raw_value: str | int | float | bytes | None
    observed_at: datetime
    synthetic_fixture: bool = False

    def __post_init__(self) -> None:
        identities = (
            self.tenant_id,
            self.case_id,
            self.evidence_source_id,
            self.source_artifact_id,
            self.controlled_copy_identity_id,
            self.database_identity_id,
            self.processing_run_id,
        )
        if any(not isinstance(item, UUID) for item in identities):
            raise ValueError("domain_provenance_incomplete")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("domain_time_invalid")
        if (self.source_table, self.source_column) != (SOURCE_TABLE, SOURCE_COLUMN):
            raise ValueError("domain_source_invalid")
        if (
            self.query_profile_id != "manifestdb-files-query"
            or self.query_profile_version not in {"1", "2"}
            or self.locator_profile_id != "manifestdb-row-locator"
            or self.locator_profile_version != "1"
        ):
            raise ValueError("domain_upstream_profile_invalid")
        expected_types = {
            StorageClass.NULL: type(None),
            StorageClass.INTEGER: int,
            StorageClass.REAL: float,
            StorageClass.TEXT: str,
            StorageClass.BLOB: bytes,
        }
        expected_type = expected_types[self.storage_class]
        if type(self.raw_value) is not expected_type:
            if self.upstream_value_state not in {
                "NOT_AVAILABLE",
                "NOT_PROJECTED",
                "READ_FAILURE",
                "NOT_EVALUATED",
                "INDETERMINATE",
            } or self.raw_value is not None:
                raise ValueError("domain_storage_value_mismatch")


@dataclass(frozen=True, slots=True)
class DomainObservation:
    observation_id: UUID
    source: DomainSourceObservation
    profile_id: str
    profile_version: str
    structure: DomainStructure
    domain_family: DomainFamily
    canonical_representation: str | None
    application_identifier_component: str | None
    group_identifier_component: str | None
    plugin_identifier_component: str | None
    raw_character_length: int | None
    raw_utf8_byte_length: int | None
    implementation_id: str
    implementation_version: str
    observed_at: datetime
    limitations: tuple[str, ...] = LIMITATIONS

    def canonical_json(self) -> str:
        source = asdict(self.source)
        for key in (
            "tenant_id",
            "case_id",
            "evidence_source_id",
            "source_artifact_id",
            "controlled_copy_identity_id",
            "database_identity_id",
            "processing_run_id",
        ):
            source[key] = str(source[key])
        source["storage_class"] = self.source.storage_class.value
        source["observed_at"] = self.source.observed_at.isoformat()
        if isinstance(self.source.raw_value, bytes):
            source["raw_value"] = {
                "representation": "BLOB_NOT_SERIALIZED",
                "byte_length": len(self.source.raw_value),
            }
        payload = {
            "observation_id": str(self.observation_id),
            "source": source,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "structure": self.structure.value,
            "domain_family": self.domain_family.value,
            "canonical_representation": self.canonical_representation,
            "application_identifier_component": self.application_identifier_component,
            "group_identifier_component": self.group_identifier_component,
            "plugin_identifier_component": self.plugin_identifier_component,
            "raw_character_length": self.raw_character_length,
            "raw_utf8_byte_length": self.raw_utf8_byte_length,
            "implementation_id": self.implementation_id,
            "implementation_version": self.implementation_version,
            "observed_at": self.observed_at.isoformat(),
            "limitations": list(self.limitations),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


_LITERALS = {
    "HomeDomain": DomainFamily.HOME,
    "WirelessDomain": DomainFamily.WIRELESS,
    "RootDomain": DomainFamily.ROOT,
    "SystemPreferencesDomain": DomainFamily.SYSTEM_PREFERENCES,
    "ManagedPreferencesDomain": DomainFamily.MANAGED_PREFERENCES,
    "MediaDomain": DomainFamily.MEDIA,
    "CameraRollDomain": DomainFamily.CAMERA_ROLL,
}
_PREFIXES = {
    "AppDomain-": (DomainFamily.APPLICATION, "application"),
    "AppDomainGroup-": (DomainFamily.APPLICATION_GROUP, "group"),
    "AppDomainPlugin-": (DomainFamily.APPLICATION_PLUGIN, "plugin"),
    "SysContainerDomain-": (DomainFamily.SYSTEM_CONTAINER, "application"),
    "SysSharedContainerDomain-": (DomainFamily.SYSTEM_SHARED_CONTAINER, "group"),
}


def _stable_id(source: DomainSourceObservation) -> UUID:
    return uuid5(
        _NAMESPACE,
        "|".join(
            (
                str(source.tenant_id),
                str(source.case_id),
                str(source.source_artifact_id),
                str(source.controlled_copy_identity_id),
                str(source.processing_run_id),
                str(source.row_locator),
                source.storage_class.value,
                repr(source.raw_value),
                PROFILE_ID,
                PROFILE_VERSION,
            )
        ),
    )


def normalize_manifest_domain(source: DomainSourceObservation) -> DomainObservation:
    structure = DomainStructure.INDETERMINATE
    family = DomainFamily.UNKNOWN
    canonical: str | None = None
    application: str | None = None
    group: str | None = None
    plugin: str | None = None
    characters: int | None = None
    byte_length: int | None = None
    state = source.upstream_value_state

    if state == "READ_FAILURE":
        structure = DomainStructure.READ_FAILURE
    elif state in {"NOT_AVAILABLE", "NOT_PROJECTED"}:
        structure = DomainStructure.SOURCE_UNAVAILABLE
    elif state == "NOT_EVALUATED":
        structure = DomainStructure.NOT_EVALUATED
    elif state == "INDETERMINATE":
        structure = DomainStructure.INDETERMINATE
    elif source.storage_class is StorageClass.NULL:
        structure = DomainStructure.NULL
    elif source.storage_class is not StorageClass.TEXT:
        structure = DomainStructure.UNSUPPORTED_STORAGE_CLASS
    elif not isinstance(source.raw_value, str):
        structure = DomainStructure.INDETERMINATE
    else:
        raw = source.raw_value
        characters = len(raw)
        byte_length = len(raw.encode("utf-8"))
        if raw == "":
            structure = DomainStructure.EMPTY
        elif not raw.isascii() or any(character.isspace() for character in raw):
            structure = DomainStructure.MALFORMED_STRUCTURE
        elif raw in _LITERALS:
            structure = DomainStructure.RECOGNIZED_LITERAL
            family = _LITERALS[raw]
            canonical = raw
        else:
            for prefix, (candidate_family, component_type) in _PREFIXES.items():
                if raw.startswith(prefix):
                    component = raw[len(prefix) :]
                    if not component or not _COMPONENT.fullmatch(component):
                        structure = DomainStructure.MALFORMED_STRUCTURE
                    else:
                        structure = DomainStructure.RECOGNIZED_PREFIXED
                        family = candidate_family
                        canonical = raw
                        if component_type == "application":
                            application = component
                        elif component_type == "group":
                            group = component
                        else:
                            plugin = component
                    break
            else:
                structure = DomainStructure.UNKNOWN_STRUCTURE

    return DomainObservation(
        _stable_id(source),
        source,
        PROFILE_ID,
        PROFILE_VERSION,
        structure,
        family,
        canonical,
        application,
        group,
        plugin,
        characters,
        byte_length,
        IMPLEMENTATION_ID,
        IMPLEMENTATION_VERSION,
        source.observed_at,
    )


def _storage_from_v1(name: str) -> StorageClass:
    return StorageClass(
        {
            "NoneType": "NULL",
            "int": "INTEGER",
            "float": "REAL",
            "str": "TEXT",
            "bytes": "BLOB",
        }[name]
    )


def _context_valid(context: FilesQueryContext) -> bool:
    return (
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.processing_run_id,
    ) == context.authorized_scope


def source_from_v1(
    row: FilesRowObservation,
    context: FilesQueryContext,
    controlled_copy_identity_id: UUID,
) -> DomainSourceObservation:
    if (
        not _context_valid(context)
        or row.processing_run_id != context.processing_run_id
        or row.source_artifact_id != context.source_artifact_id
        or row.database_identity_id != context.database_identity_id
    ):
        raise ValueError("domain_v1_scope_mismatch")
    value = next(
        (item for item in row.projected_values if item.column_name == SOURCE_COLUMN),
        None,
    )
    if value is None:
        raise ValueError("domain_value_not_projected")
    return DomainSourceObservation(
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.source_artifact_id,
        controlled_copy_identity_id,
        context.database_identity_id,
        context.processing_run_id,
        row.row_locator.locator_value,
        row.query_profile_id,
        row.query_profile_version,
        "manifestdb-row-locator",
        row.row_locator.locator_version,
        SOURCE_TABLE,
        SOURCE_COLUMN,
        _storage_from_v1(value.observed_sqlite_type),
        value.state.value,
        value.raw_value,
        row.queried_at,
    )


def source_from_v2(
    row: V2RowObservation,
    context: FilesQueryContext,
    controlled_copy_identity_id: UUID,
) -> DomainSourceObservation:
    if (
        not _context_valid(context)
        or row.processing_run_id != context.processing_run_id
        or row.source_artifact_id != context.source_artifact_id
        or row.database_identity_id != context.database_identity_id
    ):
        raise ValueError("domain_v2_scope_mismatch")
    value = next(
        (item for item in row.projected_values if item.column_name == SOURCE_COLUMN),
        None,
    )
    if value is None:
        raise ValueError("domain_value_not_projected")
    return DomainSourceObservation(
        context.tenant_id,
        context.case_id,
        context.evidence_source_id,
        context.source_artifact_id,
        controlled_copy_identity_id,
        context.database_identity_id,
        context.processing_run_id,
        row.row_locator.locator_value,
        row.query_profile_id,
        row.query_profile_version,
        "manifestdb-row-locator",
        row.row_locator.locator_version,
        SOURCE_TABLE,
        SOURCE_COLUMN,
        StorageClass(value.observed_storage_class),
        value.state.value,
        value.raw_value,
        row.observed_at,
    )


def synthetic_source(
    value: str | int | float | bytes | None,
    storage_class: StorageClass,
    *,
    state: str = "VALUE_PRESENT",
    seed: int = 1,
) -> DomainSourceObservation:
    def uid(n: int) -> UUID:
        return UUID(f"06040000-0000-4000-8000-{n:012d}")

    return DomainSourceObservation(
        uid(1),
        uid(2),
        uid(3),
        uid(4),
        uid(5),
        uid(6),
        uid(7),
        seed,
        "manifestdb-files-query",
        "2",
        "manifestdb-row-locator",
        "1",
        SOURCE_TABLE,
        SOURCE_COLUMN,
        storage_class,
        state,
        value,
        datetime(2026, 7, 29, tzinfo=timezone.utc),
        True,
    )
