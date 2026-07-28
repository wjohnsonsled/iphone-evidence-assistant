"""Read-only filesystem adapter for an Apple backup input candidate.

DEV-0201 intentionally stops before Apple backup structure validation. A ready
result means only that the filesystem boundary inspection completed and the
candidate may be passed to DEV-0202.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from app.intake.resource_limits import IntakeResourcePolicy, ResourceLimitExceeded


ADAPTER_NAME = "apple_local_backup_input"
ADAPTER_VERSION = "1.0.0"
UNASSESSED_LIMITATIONS = (
    "Apple backup structure is unassessed pending DEV-0202.",
    "Backup encryption state is unassessed pending DEV-0203.",
    "Source hashing is not performed by DEV-0201.",
    "This adapter result is not an input-support determination.",
)

Clock = Callable[[], datetime]
EntryCounter = Callable[[Path], int]
LinkDetector = Callable[[Path], bool]


class InputAdapterStatus(str, Enum):
    """Closed DEV-0201 filesystem-adapter outcomes."""

    READY_FOR_STRUCTURE_VALIDATION = "READY_FOR_STRUCTURE_VALIDATION"
    READY_ZERO_RESULTS = "READY_ZERO_RESULTS"
    MISSING = "MISSING"
    UNSUPPORTED_INPUT = "UNSUPPORTED_INPUT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PROCESSING_FAILED = "PROCESSING_FAILED"


@dataclass(frozen=True, slots=True)
class InputInspectionIssue:
    """Structured, non-evidentiary adapter issue."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class InputInspectionResult:
    """Immutable adapter result with source-boundary provenance."""

    status: InputAdapterStatus
    original_path: str
    resolved_path: str | None
    evidence_root: str | None
    source_locator: str | None
    inspected_at: datetime
    correlation_id: UUID
    adapter_name: str
    adapter_version: str
    observed_entry_count: int | None
    issues: tuple[InputInspectionIssue, ...]
    unassessed_limitations: tuple[str, ...]

    @property
    def is_ready(self) -> bool:
        """Return whether DEV-0202 may inspect this candidate."""

        return self.status in {
            InputAdapterStatus.READY_FOR_STRUCTURE_VALIDATION,
            InputAdapterStatus.READY_ZERO_RESULTS,
        }

    def to_audit_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible adapter audit data."""

        data = asdict(self)
        data["status"] = self.status.value
        data["inspected_at"] = self.inspected_at.isoformat()
        data["correlation_id"] = str(self.correlation_id)
        data["issues"] = [asdict(issue) for issue in self.issues]
        data["unassessed_limitations"] = list(self.unassessed_limitations)
        return data


class AppleBackupInputAdapter:
    """Inspect an evidence-root-confined directory without reading its files."""

    def __init__(
        self,
        evidence_roots: Iterable[Path],
        *,
        resource_policy: IntakeResourcePolicy,
        clock: Clock | None = None,
        entry_counter: EntryCounter | None = None,
        link_detector: LinkDetector | None = None,
    ) -> None:
        self._clock = clock or _utcnow
        self._resource_policy = resource_policy
        self._entry_counter = entry_counter or _count_top_level_entries
        self._link_detector = link_detector or _is_link_or_reparse
        self._evidence_roots = self._validate_roots(evidence_roots)

    @property
    def evidence_roots(self) -> tuple[Path, ...]:
        """Return validated roots in deterministic matching order."""

        return self._evidence_roots

    def inspect(self, submitted_path: str | os.PathLike[str], *, correlation_id: UUID) -> InputInspectionResult:
        """Inspect a candidate path and return a closed structured outcome."""

        original_path = os.fspath(submitted_path)
        inspected_at = self._inspection_time()
        if not original_path.strip():
            return self._result(
                InputAdapterStatus.VALIDATION_FAILED,
                original_path,
                inspected_at,
                correlation_id,
                issue=InputInspectionIssue("empty_input_path", "Input path must not be empty."),
            )

        try:
            lexical_path = Path(os.path.abspath(os.path.expanduser(original_path)))
            resolved_path = lexical_path.resolve(strict=False)
            self._resource_policy.check_path(lexical_path)
        except ResourceLimitExceeded:
            return self._result(
                InputAdapterStatus.VALIDATION_FAILED,
                original_path,
                inspected_at,
                correlation_id,
                issue=InputInspectionIssue(
                    "resource_limit_exceeded",
                    "Configured intake resource limit was exceeded.",
                ),
            )
        except (OSError, RuntimeError, ValueError):
            return self._result(
                InputAdapterStatus.VALIDATION_FAILED,
                original_path,
                inspected_at,
                correlation_id,
                issue=InputInspectionIssue("invalid_input_path", "Input path could not be safely resolved."),
            )

        matched_root = _most_specific_root(resolved_path, self._evidence_roots)
        if matched_root is None or not _is_relative_to(lexical_path, matched_root):
            return self._result(
                InputAdapterStatus.VALIDATION_FAILED,
                original_path,
                inspected_at,
                correlation_id,
                resolved_path=resolved_path,
                issue=InputInspectionIssue(
                    "input_outside_evidence_root",
                    "Input path is outside the configured evidence roots.",
                ),
            )

        try:
            self._resource_policy.check_path(lexical_path, relative_to=matched_root)
        except ResourceLimitExceeded:
            return self._result(
                InputAdapterStatus.VALIDATION_FAILED,
                original_path,
                inspected_at,
                correlation_id,
                resolved_path=resolved_path,
                evidence_root=matched_root,
                issue=InputInspectionIssue(
                    "resource_limit_exceeded",
                    "Configured intake resource limit was exceeded.",
                ),
            )

        try:
            if self._contains_link_boundary(lexical_path, matched_root):
                return self._result(
                    InputAdapterStatus.VALIDATION_FAILED,
                    original_path,
                    inspected_at,
                    correlation_id,
                    resolved_path=resolved_path,
                    evidence_root=matched_root,
                    issue=InputInspectionIssue(
                        "input_link_boundary_rejected",
                        "Input path contains a symlink or reparse-point boundary.",
                    ),
                )
            source_stat = lexical_path.lstat()
        except FileNotFoundError:
            return self._result(
                InputAdapterStatus.MISSING,
                original_path,
                inspected_at,
                correlation_id,
                resolved_path=resolved_path,
                evidence_root=matched_root,
                issue=InputInspectionIssue("input_missing", "Input path was not found."),
            )
        except OSError:
            return self._result(
                InputAdapterStatus.PROCESSING_FAILED,
                original_path,
                inspected_at,
                correlation_id,
                resolved_path=resolved_path,
                evidence_root=matched_root,
                issue=InputInspectionIssue(
                    "input_metadata_unavailable",
                    "Input path metadata could not be inspected.",
                ),
            )

        if not stat.S_ISDIR(source_stat.st_mode):
            return self._result(
                InputAdapterStatus.UNSUPPORTED_INPUT,
                original_path,
                inspected_at,
                correlation_id,
                resolved_path=resolved_path,
                evidence_root=matched_root,
                issue=InputInspectionIssue(
                    "input_not_directory",
                    "DEV-0201 accepts directory candidates only.",
                ),
            )

        try:
            entry_count = (
                self._entry_counter(resolved_path)
                if self._entry_counter is not _count_top_level_entries
                else self._resource_policy.count_directory(resolved_path)
            )
            if entry_count > self._resource_policy.max_directory_entries:
                raise ResourceLimitExceeded("directory_entries")
        except ResourceLimitExceeded:
            return self._result(
                InputAdapterStatus.VALIDATION_FAILED,
                original_path,
                inspected_at,
                correlation_id,
                resolved_path=resolved_path,
                evidence_root=matched_root,
                issue=InputInspectionIssue(
                    "resource_limit_exceeded",
                    "Configured intake resource limit was exceeded.",
                ),
            )
        except OSError:
            return self._result(
                InputAdapterStatus.PROCESSING_FAILED,
                original_path,
                inspected_at,
                correlation_id,
                resolved_path=resolved_path,
                evidence_root=matched_root,
                issue=InputInspectionIssue(
                    "input_enumeration_failed",
                    "Top-level input entries could not be enumerated.",
                ),
            )

        status = (
            InputAdapterStatus.READY_ZERO_RESULTS
            if entry_count == 0
            else InputAdapterStatus.READY_FOR_STRUCTURE_VALIDATION
        )
        return self._result(
            status,
            original_path,
            inspected_at,
            correlation_id,
            resolved_path=resolved_path,
            evidence_root=matched_root,
            observed_entry_count=entry_count,
        )

    def _validate_roots(self, evidence_roots: Iterable[Path]) -> tuple[Path, ...]:
        roots: set[Path] = set()
        for supplied_root in evidence_roots:
            try:
                lexical_root = Path(os.path.abspath(os.path.expanduser(os.fspath(supplied_root))))
                if _contains_link_or_reparse(lexical_root, self._link_detector):
                    raise ValueError("Evidence roots must not contain symlink or reparse boundaries.")
                resolved_root = lexical_root.resolve(strict=True)
                root_stat = lexical_root.lstat()
            except (FileNotFoundError, OSError, RuntimeError, TypeError, ValueError) as exc:
                raise ValueError("Each evidence root must be an accessible, link-free directory.") from exc
            if not stat.S_ISDIR(root_stat.st_mode):
                raise ValueError("Each evidence root must be an accessible, link-free directory.")
            roots.add(resolved_root)
        if not roots:
            raise ValueError("At least one evidence root is required.")
        return tuple(sorted(roots, key=lambda path: (-len(path.parts), os.path.normcase(str(path)))))

    def _contains_link_boundary(self, candidate: Path, evidence_root: Path) -> bool:
        relative = candidate.relative_to(evidence_root)
        current = evidence_root
        for part in relative.parts:
            current = current / part
            try:
                if self._link_detector(current):
                    return True
            except FileNotFoundError:
                return False
        return False

    def _inspection_time(self) -> datetime:
        inspected_at = self._clock()
        if inspected_at.tzinfo is None or inspected_at.utcoffset() is None:
            raise ValueError("Inspection clock must return a timezone-aware datetime.")
        return inspected_at.astimezone(timezone.utc)

    @staticmethod
    def _result(
        status: InputAdapterStatus,
        original_path: str,
        inspected_at: datetime,
        correlation_id: UUID,
        *,
        resolved_path: Path | None = None,
        evidence_root: Path | None = None,
        observed_entry_count: int | None = None,
        issue: InputInspectionIssue | None = None,
    ) -> InputInspectionResult:
        locator = None
        if resolved_path is not None and evidence_root is not None and _is_relative_to(resolved_path, evidence_root):
            relative = resolved_path.relative_to(evidence_root)
            locator = "." if not relative.parts else relative.as_posix()
        return InputInspectionResult(
            status=status,
            original_path=original_path,
            resolved_path=str(resolved_path) if resolved_path is not None else None,
            evidence_root=str(evidence_root) if evidence_root is not None else None,
            source_locator=locator,
            inspected_at=inspected_at,
            correlation_id=correlation_id,
            adapter_name=ADAPTER_NAME,
            adapter_version=ADAPTER_VERSION,
            observed_entry_count=observed_entry_count,
            issues=(issue,) if issue is not None else (),
            unassessed_limitations=UNASSESSED_LIMITATIONS,
        )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _count_top_level_entries(path: Path) -> int:
    return sum(1 for _ in path.iterdir())


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _most_specific_root(path: Path, roots: tuple[Path, ...]) -> Path | None:
    return next((root for root in roots if _is_relative_to(path, root)), None)


def _contains_link_or_reparse(path: Path, detector: LinkDetector) -> bool:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if detector(current):
            return True
    return False


def _is_link_or_reparse(path: Path) -> bool:
    path_stat = path.lstat()
    if stat.S_ISLNK(path_stat.st_mode):
        return True
    file_attributes = getattr(path_stat, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(file_attributes & reparse_attribute)
