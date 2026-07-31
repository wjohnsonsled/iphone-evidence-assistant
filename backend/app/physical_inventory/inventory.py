"""Read-only, root-confined candidate Apple backup physical inventory v1."""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from time import monotonic
from uuid import UUID, uuid5

INVENTORY_PROFILE_ID = "apple-local-backup-physical-inventory"
INVENTORY_PROFILE_VERSION = "1"
LOCATOR_PROFILE_ID = "apple-backup-physical-object-locator"
LOCATOR_PROFILE_VERSION = "1"
IMPLEMENTATION_ID = "apple-backup-physical-inventory-reader"
IMPLEMENTATION_VERSION = "1"
_NAMESPACE = UUID("06210000-0000-4000-8000-000000000001")
_HEX2 = re.compile(r"^[0-9a-f]{2}$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_TOP_LEVEL_METADATA = frozenset(
    {"Info.plist", "Manifest.db", "Manifest.plist", "Status.plist"}
)

LIMITATIONS = (
    "The v1 layout is provisional and synthetically characterized, not Apple-authoritative.",
    "A physical observation does not prove device existence, authenticity, artifact type, deletion, tampering, relevance, or backup completeness.",
    "Filename syntax and fileID-shaped names do not verify content or Apple fileID semantics.",
    "Inventory completion describes only the governed requested filesystem universe.",
    "No parser, artifact, input, workflow, or capability is Supported.",
)


class FileSystemObjectType(str, Enum):
    REGULAR_FILE = "REGULAR_FILE"
    DIRECTORY = "DIRECTORY"
    SYMBOLIC_LINK = "SYMBOLIC_LINK"
    WINDOWS_REPARSE_POINT = "WINDOWS_REPARSE_POINT"
    OTHER_SPECIAL_OBJECT = "OTHER_SPECIAL_OBJECT"
    INACCESSIBLE = "INACCESSIBLE"
    TYPE_INDETERMINATE = "TYPE_INDETERMINATE"


class LayoutClassification(str, Enum):
    CANDIDATE_PHYSICAL_OBJECT = "CANDIDATE_PHYSICAL_OBJECT"
    TOP_LEVEL_METADATA = "TOP_LEVEL_METADATA"
    EXPECTED_PREFIX_DIRECTORY = "EXPECTED_PREFIX_DIRECTORY"
    UNEXPECTED_FILE = "UNEXPECTED_FILE"
    UNEXPECTED_DIRECTORY = "UNEXPECTED_DIRECTORY"
    UNSUPPORTED_OBJECT = "UNSUPPORTED_OBJECT"
    INACCESSIBLE_OBJECT = "INACCESSIBLE_OBJECT"
    INDETERMINATE = "INDETERMINATE"


class InventoryCompletion(str, Enum):
    COMPLETE = "INVENTORY_COMPLETE"
    PARTIAL = "INVENTORY_PARTIAL"
    CANCELLED = "INVENTORY_CANCELLED"
    RESOURCE_TERMINATED = "INVENTORY_RESOURCE_TERMINATED"
    MUTATION_TERMINATED = "INVENTORY_MUTATION_TERMINATED"
    FAILED = "INVENTORY_FAILED"
    INDETERMINATE = "INVENTORY_INDETERMINATE"


class TerminationReason(str, Enum):
    COMPLETED = "COMPLETED"
    ENTRY_LIMIT = "ENTRY_LIMIT"
    REGULAR_FILE_LIMIT = "REGULAR_FILE_LIMIT"
    DIRECTORY_LIMIT = "DIRECTORY_LIMIT"
    PATH_LENGTH_LIMIT = "PATH_LENGTH_LIMIT"
    MEMORY_ESTIMATE_LIMIT = "MEMORY_ESTIMATE_LIMIT"
    WALL_CLOCK_LIMIT = "WALL_CLOCK_LIMIT"
    UNRESOLVED_OBJECT_LIMIT = "UNRESOLVED_OBJECT_LIMIT"
    CANCELLED = "CANCELLED"
    ROOT_NOT_AUTHORIZED = "ROOT_NOT_AUTHORIZED"
    ROOT_NOT_VALIDATED = "ROOT_NOT_VALIDATED"
    ROOT_INVALID = "ROOT_INVALID"
    ROOT_LINK_UNSAFE = "ROOT_LINK_UNSAFE"
    ROOT_ACCESS_FAILED = "ROOT_ACCESS_FAILED"
    SOURCE_SCOPE_MISMATCH = "SOURCE_SCOPE_MISMATCH"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class InventoryResourcePolicy:
    max_directory_entries: int
    max_regular_files: int
    max_directories: int
    max_path_depth: int
    max_pathname_length: int
    max_individual_hash_bytes: int
    max_total_hash_bytes: int
    max_memory_estimate_bytes: int
    max_elapsed_seconds: float
    max_concurrent_hash_operations: int
    max_unresolved_objects: int

    def __post_init__(self) -> None:
        values = tuple(asdict(self).values())
        if any(isinstance(value, bool) or value <= 0 for value in values):
            raise ValueError("physical_inventory_resource_policy_must_be_positive")
        if self.max_path_depth != 2:
            raise ValueError("physical_inventory_v1_depth_must_equal_two")


@dataclass(frozen=True, slots=True)
class AuthorizedInventoryContext:
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    controlled_source_id: UUID
    processing_run_id: UUID
    authorized_scope: tuple[UUID, UUID, UUID, UUID]
    root_authorized: bool
    root_validated: bool
    observed_at: datetime

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("physical_inventory_time_invalid")


@dataclass(frozen=True, slots=True)
class PhysicalObjectLocator:
    locator_id: UUID
    profile_id: str
    profile_version: str
    inventory_profile_id: str
    inventory_profile_version: str
    evidence_source_id: UUID
    processing_run_id: UUID
    relative_components: tuple[str, ...]

    @property
    def relative_display(self) -> str:
        return "/".join(self.relative_components)


@dataclass(frozen=True, slots=True)
class FilenameObservation:
    raw_name: str
    character_length: int
    utf8_byte_length: int
    ascii_only: bool
    lexical_syntax: str
    canonical_comparison: str | None


@dataclass(frozen=True, slots=True)
class PhysicalEntryObservation:
    observation_id: UUID
    tenant_id: UUID
    case_id: UUID
    evidence_source_id: UUID
    controlled_source_id: UUID
    processing_run_id: UUID
    locator: PhysicalObjectLocator
    filename: FilenameObservation
    object_type: FileSystemObjectType
    layout_classification: LayoutClassification
    size_bytes: int | None
    modified_time_ns: int | None
    object_identity: tuple[int, int] | None
    accessible: bool
    eligible_candidate_object: bool
    observed_at: datetime
    reason_code: str
    limitations: tuple[str, ...] = LIMITATIONS


@dataclass(frozen=True, slots=True)
class PhysicalInventoryResult:
    inventory_id: UUID
    context: AuthorizedInventoryContext
    profile_id: str
    profile_version: str
    locator_profile_id: str
    locator_profile_version: str
    completion: InventoryCompletion
    termination_reason: TerminationReason
    observations: tuple[PhysicalEntryObservation, ...]
    entries_observed: int
    regular_files_observed: int
    directories_observed: int
    candidate_objects_observed: int
    inaccessible_objects: int
    unsupported_objects: int
    unresolved_objects: int
    last_safe_locator: PhysicalObjectLocator | None
    continuation_available: bool
    resource_limit: str | None
    observed_usage: int | float | None
    implementation_id: str
    implementation_version: str
    limitations: tuple[str, ...] = LIMITATIONS


CancelCheck = Callable[[], bool]
Clock = Callable[[], float]


def _locator(context: AuthorizedInventoryContext, components: tuple[str, ...]) -> PhysicalObjectLocator:
    text = "|".join((str(context.evidence_source_id), str(context.processing_run_id), *components))
    return PhysicalObjectLocator(
        uuid5(_NAMESPACE, text), LOCATOR_PROFILE_ID, LOCATOR_PROFILE_VERSION,
        INVENTORY_PROFILE_ID, INVENTORY_PROFILE_VERSION,
        context.evidence_source_id, context.processing_run_id, components,
    )


def _name_observation(name: str, components: tuple[str, ...]) -> FilenameObservation:
    ascii_only = name.isascii()
    syntax = "OTHER"
    canonical = None
    if len(components) == 1 and name in _TOP_LEVEL_METADATA:
        syntax = "RECOGNIZED_TOP_LEVEL_METADATA_NAME"
    elif len(components) == 1 and _HEX2.fullmatch(name):
        syntax = "LOWERCASE_HEX_PREFIX_DIRECTORY"
    elif len(components) == 2 and _HEX40.fullmatch(name):
        syntax = "LOWERCASE_HEX40_FILENAME"
        canonical = name
    elif len(components) == 2 and re.fullmatch(r"^[0-9A-F]{40}$", name):
        syntax = "UPPERCASE_HEX40_FILENAME_NONCANONICAL"
    elif len(components) == 2 and re.fullmatch(r"^[0-9A-Fa-f]{40}$", name):
        syntax = "MIXED_CASE_HEX40_FILENAME_NONCANONICAL"
    return FilenameObservation(name, len(name), len(name.encode("utf-8")), ascii_only, syntax, canonical)


def _entry_type(entry: os.DirEntry[str]) -> tuple[FileSystemObjectType, os.stat_result | None, str]:
    try:
        if entry.is_symlink():
            return FileSystemObjectType.SYMBOLIC_LINK, None, "symbolic_link_not_followed"
        details = entry.stat(follow_symlinks=False)
        if getattr(details, "st_file_attributes", 0) & 0x400:
            return FileSystemObjectType.WINDOWS_REPARSE_POINT, details, "reparse_point_not_followed"
        mode = details.st_mode
        if stat.S_ISREG(mode):
            return FileSystemObjectType.REGULAR_FILE, details, "regular_file_observed"
        if stat.S_ISDIR(mode):
            return FileSystemObjectType.DIRECTORY, details, "directory_observed"
        return FileSystemObjectType.OTHER_SPECIAL_OBJECT, details, "special_object_not_supported"
    except PermissionError:
        return FileSystemObjectType.INACCESSIBLE, None, "object_inaccessible"
    except OSError:
        return FileSystemObjectType.TYPE_INDETERMINATE, None, "object_type_indeterminate"


def _classification(
    components: tuple[str, ...], object_type: FileSystemObjectType
) -> tuple[LayoutClassification, bool]:
    if object_type is FileSystemObjectType.INACCESSIBLE:
        return LayoutClassification.INACCESSIBLE_OBJECT, False
    if object_type not in {FileSystemObjectType.REGULAR_FILE, FileSystemObjectType.DIRECTORY}:
        return LayoutClassification.UNSUPPORTED_OBJECT, False
    name = components[-1]
    if len(components) == 1:
        if object_type is FileSystemObjectType.REGULAR_FILE and name in _TOP_LEVEL_METADATA:
            return LayoutClassification.TOP_LEVEL_METADATA, False
        if object_type is FileSystemObjectType.DIRECTORY and _HEX2.fullmatch(name):
            return LayoutClassification.EXPECTED_PREFIX_DIRECTORY, False
        return (
            LayoutClassification.UNEXPECTED_DIRECTORY
            if object_type is FileSystemObjectType.DIRECTORY
            else LayoutClassification.UNEXPECTED_FILE,
            False,
        )
    if (
        object_type is FileSystemObjectType.REGULAR_FILE
        and _HEX2.fullmatch(components[0])
        and _HEX40.fullmatch(name)
        and name[:2] == components[0]
    ):
        return LayoutClassification.CANDIDATE_PHYSICAL_OBJECT, True
    return (
        LayoutClassification.UNEXPECTED_DIRECTORY
        if object_type is FileSystemObjectType.DIRECTORY
        else LayoutClassification.UNEXPECTED_FILE,
        False,
    )


def inventory_backup_root(
    root: Path,
    context: AuthorizedInventoryContext,
    policy: InventoryResourcePolicy,
    *,
    cancel_check: CancelCheck = lambda: False,
    clock: Clock = monotonic,
) -> PhysicalInventoryResult:
    """Observe the exact v1 depth-two universe without following links."""

    expected_scope = (
        context.tenant_id, context.case_id, context.evidence_source_id,
        context.processing_run_id,
    )
    if context.authorized_scope != expected_scope:
        return _empty_result(context, InventoryCompletion.FAILED, TerminationReason.SOURCE_SCOPE_MISMATCH)
    if not context.root_authorized:
        return _empty_result(context, InventoryCompletion.FAILED, TerminationReason.ROOT_NOT_AUTHORIZED)
    if not context.root_validated:
        return _empty_result(context, InventoryCompletion.FAILED, TerminationReason.ROOT_NOT_VALIDATED)
    try:
        if root.is_symlink():
            return _empty_result(context, InventoryCompletion.FAILED, TerminationReason.ROOT_LINK_UNSAFE)
        resolved_root = root.resolve(strict=True)
        if not resolved_root.is_dir():
            return _empty_result(context, InventoryCompletion.FAILED, TerminationReason.ROOT_INVALID)
    except OSError:
        return _empty_result(context, InventoryCompletion.FAILED, TerminationReason.ROOT_ACCESS_FAILED)

    started = clock()
    observations: list[PhysicalEntryObservation] = []
    counts = {"entries": 0, "files": 0, "directories": 0, "unresolved": 0}
    termination = TerminationReason.COMPLETED
    resource_limit: str | None = None
    usage: int | float | None = None

    def limit(reason: TerminationReason, name: str, value: int | float) -> bool:
        nonlocal termination, resource_limit, usage
        termination, resource_limit, usage = reason, name, value
        return False

    def observe(entry: os.DirEntry[str], components: tuple[str, ...]) -> bool:
        nonlocal termination, resource_limit, usage
        if cancel_check():
            termination = TerminationReason.CANCELLED
            return False
        elapsed = clock() - started
        if elapsed >= policy.max_elapsed_seconds:
            return limit(TerminationReason.WALL_CLOCK_LIMIT, "max_elapsed_seconds", elapsed)
        if counts["entries"] >= policy.max_directory_entries:
            return limit(TerminationReason.ENTRY_LIMIT, "max_directory_entries", counts["entries"])
        if len("/".join(components)) > policy.max_pathname_length:
            return limit(TerminationReason.PATH_LENGTH_LIMIT, "max_pathname_length", len("/".join(components)))
        estimated = (counts["entries"] + 1) * 512 + sum(len(value.encode("utf-8")) for value in components)
        if estimated > policy.max_memory_estimate_bytes:
            return limit(TerminationReason.MEMORY_ESTIMATE_LIMIT, "max_memory_estimate_bytes", estimated)
        object_type, details, reason = _entry_type(entry)
        if object_type is FileSystemObjectType.REGULAR_FILE and counts["files"] >= policy.max_regular_files:
            return limit(TerminationReason.REGULAR_FILE_LIMIT, "max_regular_files", counts["files"])
        if object_type is FileSystemObjectType.DIRECTORY and counts["directories"] >= policy.max_directories:
            return limit(TerminationReason.DIRECTORY_LIMIT, "max_directories", counts["directories"])
        classification, eligible = _classification(components, object_type)
        unresolved = classification in {
            LayoutClassification.UNEXPECTED_FILE,
            LayoutClassification.UNEXPECTED_DIRECTORY,
            LayoutClassification.UNSUPPORTED_OBJECT,
            LayoutClassification.INACCESSIBLE_OBJECT,
            LayoutClassification.INDETERMINATE,
        }
        if unresolved and counts["unresolved"] >= policy.max_unresolved_objects:
            return limit(TerminationReason.UNRESOLVED_OBJECT_LIMIT, "max_unresolved_objects", counts["unresolved"])
        locator = _locator(context, components)
        identity = (
            (int(details.st_dev), int(details.st_ino))
            if details is not None and hasattr(details, "st_dev") else None
        )
        observation_id = uuid5(_NAMESPACE, f"{locator.locator_id}|{object_type.value}|{classification.value}")
        observations.append(PhysicalEntryObservation(
            observation_id, context.tenant_id, context.case_id,
            context.evidence_source_id, context.controlled_source_id,
            context.processing_run_id, locator, _name_observation(entry.name, components),
            object_type, classification, int(details.st_size) if details else None,
            int(details.st_mtime_ns) if details else None, identity,
            object_type not in {FileSystemObjectType.INACCESSIBLE, FileSystemObjectType.TYPE_INDETERMINATE},
            eligible, context.observed_at, reason,
        ))
        counts["entries"] += 1
        counts["files"] += object_type is FileSystemObjectType.REGULAR_FILE
        counts["directories"] += object_type is FileSystemObjectType.DIRECTORY
        counts["unresolved"] += unresolved
        return True

    try:
        with os.scandir(resolved_root) as iterator:
            top = sorted(tuple(iterator), key=lambda item: item.name)
        for entry in top:
            if not observe(entry, (entry.name,)):
                break
            if observations[-1].layout_classification is LayoutClassification.EXPECTED_PREFIX_DIRECTORY:
                directory_path = resolved_root / entry.name
                if directory_path.resolve(strict=True).parent != resolved_root:
                    termination = TerminationReason.ROOT_LINK_UNSAFE
                    break
                with os.scandir(directory_path) as iterator:
                    children = sorted(tuple(iterator), key=lambda item: item.name)
                for child in children:
                    if not observe(child, (entry.name, child.name)):
                        break
                if termination is not TerminationReason.COMPLETED:
                    break
    except (OSError, RuntimeError):
        termination = TerminationReason.ROOT_ACCESS_FAILED

    if termination is TerminationReason.COMPLETED:
        completion = InventoryCompletion.COMPLETE
    elif termination is TerminationReason.CANCELLED:
        completion = InventoryCompletion.CANCELLED
    elif termination in {
        TerminationReason.ENTRY_LIMIT, TerminationReason.REGULAR_FILE_LIMIT,
        TerminationReason.DIRECTORY_LIMIT, TerminationReason.PATH_LENGTH_LIMIT,
        TerminationReason.MEMORY_ESTIMATE_LIMIT, TerminationReason.WALL_CLOCK_LIMIT,
        TerminationReason.UNRESOLVED_OBJECT_LIMIT,
    }:
        completion = InventoryCompletion.RESOURCE_TERMINATED
    else:
        completion = InventoryCompletion.FAILED
    last = observations[-1].locator if observations else None
    identity_text = "|".join((str(context.evidence_source_id), str(context.processing_run_id), completion.value, termination.value, str(len(observations))))
    return PhysicalInventoryResult(
        uuid5(_NAMESPACE, identity_text), context, INVENTORY_PROFILE_ID,
        INVENTORY_PROFILE_VERSION, LOCATOR_PROFILE_ID, LOCATOR_PROFILE_VERSION,
        completion, termination, tuple(observations), counts["entries"],
        counts["files"], counts["directories"],
        sum(item.eligible_candidate_object for item in observations),
        sum(item.object_type is FileSystemObjectType.INACCESSIBLE for item in observations),
        sum(item.layout_classification is LayoutClassification.UNSUPPORTED_OBJECT for item in observations),
        counts["unresolved"], last, completion is not InventoryCompletion.COMPLETE,
        resource_limit, usage, IMPLEMENTATION_ID, IMPLEMENTATION_VERSION,
    )


def _empty_result(
    context: AuthorizedInventoryContext,
    completion: InventoryCompletion,
    termination: TerminationReason,
) -> PhysicalInventoryResult:
    identity = uuid5(_NAMESPACE, f"{context.evidence_source_id}|{context.processing_run_id}|{termination.value}")
    return PhysicalInventoryResult(
        identity, context, INVENTORY_PROFILE_ID, INVENTORY_PROFILE_VERSION,
        LOCATOR_PROFILE_ID, LOCATOR_PROFILE_VERSION, completion, termination,
        (), 0, 0, 0, 0, 0, 0, 0, None, False, None, None,
        IMPLEMENTATION_ID, IMPLEMENTATION_VERSION,
    )

