"""Schema-neutral controlled copies for read-only SQLite processing.

First validated under DEV-0202 Stage A and adopted as the general candidate
service by DEV-0205, this module contains no Apple schema or compatibility
rules. It copies a main SQLite file and exact-name companions, verifies source
stability and copied bytes, permits limited read-only structural observation,
and records cleanup.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID


COMPANION_SUFFIXES = ("-wal", "-shm", "-journal")
Clock = Callable[[], datetime]
Hasher = Callable[[Path], str]
Copier = Callable[[Path, Path], None]
Cleanup = Callable[[Path], None]
WorkspaceCreator = Callable[[Path | None], Path]
LinkDetector = Callable[[Path], bool]


class CleanupStatus(str, Enum):
    """Controlled workspace cleanup outcomes."""

    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RETAINED_FOR_TEST = "RETAINED_FOR_TEST"


@dataclass(frozen=True, slots=True)
class ControlledFileRecord:
    """Hash and path record for one controlled file."""

    role: str
    source_path: str
    working_path: str
    size: int
    source_sha256_before: str
    copied_sha256: str
    source_sha256_after: str


@dataclass(frozen=True, slots=True)
class SQLiteStructuralObservation:
    """Schema-neutral SQLite observations from a controlled copy."""

    integrity_rows: tuple[str, ...]
    table_names: tuple[str, ...]
    user_version: int
    application_id: int


@dataclass(slots=True)
class ControlledCopyAudit:
    """Mutable lifecycle record retained after context exit."""

    correlation_id: UUID
    created_at: datetime
    evidence_source_root: str
    source_main_path: str
    workspace_path: str | None = None
    companion_names_before: tuple[str, ...] = ()
    companion_names_after: tuple[str, ...] = ()
    files: tuple[ControlledFileRecord, ...] = ()
    verification_status: str = "PENDING"
    sqlite_access_mode: str = "NOT_OPENED"
    cleanup_status: CleanupStatus = CleanupStatus.PENDING
    failure_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible audit data."""

        data = asdict(self)
        data["correlation_id"] = str(self.correlation_id)
        data["created_at"] = self.created_at.isoformat()
        data["cleanup_status"] = self.cleanup_status.value
        data["files"] = [asdict(record) for record in self.files]
        return data

    def canonical_json(self) -> str:
        """Return canonical audit JSON for deterministic comparison."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class ControlledCopyError(RuntimeError):
    """Safe structured controlled-copy failure."""

    def __init__(self, code: str, message: str, audit: ControlledCopyAudit) -> None:
        super().__init__(message)
        self.code = code
        self.audit = audit


class ControlledSQLiteCopy:
    """Context-managed verified copy and structural SQLite observer."""

    def __init__(
        self,
        *,
        audit: ControlledCopyAudit,
        main_working_path: Path,
        hasher: Hasher,
        cleanup: Cleanup,
        retain_for_testing: bool,
    ) -> None:
        self.audit = audit
        self.main_working_path = main_working_path
        self._hasher = hasher
        self._cleanup = cleanup
        self._retain_for_testing = retain_for_testing
        self._closed = False

    @property
    def workspace_path(self) -> Path:
        """Return the controlled workspace path."""

        if self.audit.workspace_path is None:
            raise RuntimeError("Controlled workspace was not created.")
        return Path(self.audit.workspace_path)

    @property
    def read_only_uri(self) -> str:
        """Return the frozen-copy read-only SQLite URI."""

        return f"file:{quote(self.main_working_path.as_posix(), safe='/:')}?mode=ro&immutable=1&cache=private"

    def inspect_sqlite_structure(self) -> SQLiteStructuralObservation:
        """Run schema-neutral read-only SQLite structural checks."""

        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self.read_only_uri, uri=True)
            connection.execute("PRAGMA query_only = ON")
            integrity_rows = tuple(str(row[0]) for row in connection.execute("PRAGMA integrity_check"))
            table_names = tuple(
                sorted(
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_schema "
                        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
                    )
                )
            )
            user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
            self.audit.sqlite_access_mode = "READ_ONLY_QUERY_ONLY_IMMUTABLE_PRIVATE"
        except sqlite3.Error as exc:
            self.audit.sqlite_access_mode = "READ_ONLY_FAILED"
            self.audit.failure_code = "sqlite_validation_failed"
            raise ControlledCopyError(
                "sqlite_validation_failed",
                "Controlled SQLite structural validation failed.",
                self.audit,
            ) from exc
        finally:
            if connection is not None:
                connection.close()

        self.verify_working_files()
        return SQLiteStructuralObservation(
            integrity_rows=integrity_rows,
            table_names=table_names,
            user_version=user_version,
            application_id=application_id,
        )

    def verify_working_files(self) -> None:
        """Verify that controlled files still match their copied hashes."""

        for record in self.audit.files:
            try:
                current_hash = self._hasher(Path(record.working_path))
            except OSError as exc:
                self.audit.verification_status = "FAILED"
                self.audit.failure_code = "working_copy_verification_failed"
                raise ControlledCopyError(
                    "working_copy_verification_failed",
                    "A controlled file could not be re-verified.",
                    self.audit,
                ) from exc
            if current_hash != record.copied_sha256:
                self.audit.verification_status = "FAILED"
                self.audit.failure_code = "working_copy_changed"
                raise ControlledCopyError(
                    "working_copy_changed",
                    "A controlled file changed after copying.",
                    self.audit,
                )
        self.audit.verification_status = "VERIFIED"

    def close(self) -> None:
        """Verify and clean up the controlled workspace."""

        if self._closed:
            return
        self._closed = True
        verification_error: ControlledCopyError | None = None
        try:
            self.verify_working_files()
        except ControlledCopyError as exc:
            verification_error = exc

        cleanup_error = self._finish_cleanup()
        if verification_error is not None:
            raise verification_error
        if cleanup_error is not None:
            raise cleanup_error

    def _finish_cleanup(self) -> ControlledCopyError | None:
        if self._retain_for_testing:
            self.audit.cleanup_status = CleanupStatus.RETAINED_FOR_TEST
            return None
        try:
            self._cleanup(self.workspace_path)
            self.audit.cleanup_status = CleanupStatus.SUCCEEDED
            return None
        except OSError as exc:
            self.audit.cleanup_status = CleanupStatus.FAILED
            self.audit.failure_code = "working_copy_cleanup_failed"
            return ControlledCopyError(
                "working_copy_cleanup_failed",
                "Controlled workspace cleanup failed.",
                self.audit,
            )

    def __enter__(self) -> ControlledSQLiteCopy:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            self.close()
        except ControlledCopyError:
            if exc_value is None:
                raise
        return False


class ControlledCopyManager:
    """Create fail-closed verified SQLite working copies."""

    def __init__(
        self,
        *,
        workspace_root: Path | None = None,
        clock: Clock | None = None,
        hasher: Hasher | None = None,
        copier: Copier | None = None,
        cleanup: Cleanup | None = None,
        workspace_creator: WorkspaceCreator | None = None,
        link_detector: LinkDetector | None = None,
    ) -> None:
        self._workspace_root = workspace_root.resolve(strict=True) if workspace_root else None
        if self._workspace_root is not None and not self._workspace_root.is_dir():
            raise ValueError("Workspace root must be a directory.")
        self._clock = clock or _utcnow
        self._hasher = hasher or _sha256
        self._copier = copier or shutil.copyfile
        self._cleanup = cleanup or shutil.rmtree
        self._workspace_creator = workspace_creator or _create_workspace
        self._link_detector = link_detector or _is_link_or_reparse

    def create(
        self,
        main_database: Path,
        *,
        evidence_source_root: Path,
        correlation_id: UUID,
        retain_for_testing: bool = False,
    ) -> ControlledSQLiteCopy:
        """Create and verify a controlled main/companion copy."""

        created_at = _normalize_utc(self._clock())
        audit = ControlledCopyAudit(
            correlation_id=correlation_id,
            created_at=created_at,
            evidence_source_root=str(evidence_source_root.resolve(strict=False)),
            source_main_path=str(main_database.resolve(strict=False)),
        )

        try:
            source_root = evidence_source_root.resolve(strict=True)
            source_main = main_database.resolve(strict=True)
            audit.evidence_source_root = str(source_root)
            audit.source_main_path = str(source_main)
            root_stat = source_root.lstat()
            if not stat.S_ISDIR(root_stat.st_mode) or self._link_detector(source_root):
                raise ValueError("Evidence source root must be a link-free directory.")
            self._validate_source_file(source_main, source_root)
            sources_before = self._source_set(source_main, source_root)
            audit.companion_names_before = tuple(path.name for path in sources_before[1:])
            before_hashes = {path: self._hasher(path) for path in sources_before}
            before_sizes = {path: path.stat().st_size for path in sources_before}

            workspace = self._workspace_creator(self._workspace_root)
            audit.workspace_path = str(workspace.resolve(strict=True))
            self._validate_workspace(workspace, source_root)

            copied_hashes: dict[Path, str] = {}
            working_paths: dict[Path, Path] = {}
            for source_path in sources_before:
                working_path = workspace / source_path.name
                self._copier(source_path, working_path)
                working_paths[source_path] = working_path
                copied_hashes[source_path] = self._hasher(working_path)

            sources_after = self._source_set(source_main, source_root)
            audit.companion_names_after = tuple(path.name for path in sources_after[1:])
            if tuple(path.name for path in sources_before) != tuple(path.name for path in sources_after):
                raise ControlledCopyError(
                    "source_companion_set_changed",
                    "SQLite companion set changed during controlled copying.",
                    audit,
                )

            after_hashes = {path: self._hasher(path) for path in sources_after}
            records: list[ControlledFileRecord] = []
            for index, source_path in enumerate(sources_before):
                if not (
                    before_hashes[source_path]
                    == copied_hashes[source_path]
                    == after_hashes[source_path]
                ):
                    raise ControlledCopyError(
                        "source_changed_during_copy",
                        "A source file changed or did not copy exactly.",
                        audit,
                    )
                records.append(
                    ControlledFileRecord(
                        role="main" if index == 0 else source_path.name.removeprefix(source_main.name),
                        source_path=str(source_path),
                        working_path=str(working_paths[source_path]),
                        size=before_sizes[source_path],
                        source_sha256_before=before_hashes[source_path],
                        copied_sha256=copied_hashes[source_path],
                        source_sha256_after=after_hashes[source_path],
                    )
                )

            audit.files = tuple(records)
            audit.verification_status = "VERIFIED"
            return ControlledSQLiteCopy(
                audit=audit,
                main_working_path=workspace / source_main.name,
                hasher=self._hasher,
                cleanup=self._cleanup,
                retain_for_testing=retain_for_testing,
            )
        except ControlledCopyError as exc:
            audit.failure_code = exc.code
            self._cleanup_failed_creation(audit)
            raise exc
        except (OSError, RuntimeError, ValueError) as exc:
            audit.failure_code = "controlled_copy_creation_failed"
            self._cleanup_failed_creation(audit)
            raise ControlledCopyError(
                "controlled_copy_creation_failed",
                "Controlled workspace could not be created safely.",
                audit,
            ) from exc

    def _source_set(self, main_database: Path, evidence_source_root: Path) -> tuple[Path, ...]:
        source_paths = [main_database]
        for suffix in COMPANION_SUFFIXES:
            companion = main_database.with_name(f"{main_database.name}{suffix}")
            if companion.exists():
                self._validate_source_file(companion, evidence_source_root)
                source_paths.append(companion)
        return tuple(source_paths)

    def _validate_source_file(self, path: Path, evidence_source_root: Path) -> None:
        if not _is_relative_to(path, evidence_source_root):
            raise ValueError("Controlled-copy source is outside the evidence source.")
        relative = path.relative_to(evidence_source_root)
        current = evidence_source_root
        for part in relative.parts:
            current = current / part
            if self._link_detector(current):
                raise ValueError("Controlled-copy source contains a link boundary.")
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("Controlled-copy source must be a regular file.")

    @staticmethod
    def _validate_workspace(workspace: Path, evidence_source_root: Path) -> None:
        resolved_workspace = workspace.resolve(strict=True)
        if not resolved_workspace.is_dir():
            raise ValueError("Controlled workspace must be a directory.")
        if _is_relative_to(resolved_workspace, evidence_source_root):
            raise ValueError("Controlled workspace must be outside the evidence source.")
        if any(resolved_workspace.iterdir()):
            raise ValueError("Controlled workspace must be empty.")

    def _cleanup_failed_creation(self, audit: ControlledCopyAudit) -> None:
        if audit.workspace_path is None:
            audit.cleanup_status = CleanupStatus.SUCCEEDED
            return
        workspace = Path(audit.workspace_path)
        try:
            if workspace.exists():
                self._cleanup(workspace)
            audit.cleanup_status = CleanupStatus.SUCCEEDED
        except OSError:
            audit.cleanup_status = CleanupStatus.FAILED
            audit.failure_code = audit.failure_code or "working_copy_cleanup_failed"


def _create_workspace(root: Path | None) -> Path:
    return Path(tempfile.mkdtemp(prefix="iphone-evidence-validation-", dir=root))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Controlled-copy clock must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_link_or_reparse(path: Path) -> bool:
    path_stat = path.lstat()
    if stat.S_ISLNK(path_stat.st_mode):
        return True
    file_attributes = getattr(path_stat, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(file_attributes & reparse_attribute)
