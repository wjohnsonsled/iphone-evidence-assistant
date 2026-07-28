"""Fail-closed caller-supplied resource policy for evidence intake."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


VALID_RANGES = {
    "max_directory_entries": (1, 10_000_000),
    "max_directory_depth": (1, 1_024),
    "max_pathname_length": (1, 32_767),
    "max_plist_bytes": (1, 1_073_741_824),
    "max_sqlite_main_bytes": (1, 1_099_511_627_776),
    "max_sqlite_wal_bytes": (1, 1_099_511_627_776),
    "max_sqlite_shm_bytes": (1, 1_073_741_824),
    "max_controlled_copy_bytes": (1, 2_199_023_255_552),
    "max_schema_entries": (1, 10_000_000),
    "max_sqlite_work_units": (1, 10_000_000_000),
}


class ResourceLimitExceeded(RuntimeError):
    """Safe resource-policy denial without evidentiary classification."""

    code = "resource_limit_exceeded"

    def __init__(self, resource: str) -> None:
        super().__init__("Configured intake resource limit was exceeded.")
        self.resource = resource


@dataclass(frozen=True, slots=True)
class IntakeResourcePolicy:
    """Explicit ceilings; no field has an implicit deployment value."""

    max_directory_entries: int
    max_directory_depth: int
    max_pathname_length: int
    max_plist_bytes: int
    max_sqlite_main_bytes: int
    max_sqlite_wal_bytes: int
    max_sqlite_shm_bytes: int
    max_controlled_copy_bytes: int
    max_schema_entries: int
    max_sqlite_work_units: int

    def __post_init__(self) -> None:
        for field_name, (minimum, maximum) in VALID_RANGES.items():
            value = getattr(self, field_name)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(
                    f"{field_name} must be an integer in [{minimum}, {maximum}]"
                )

    def check_path(self, path: Path, *, relative_to: Path | None = None) -> None:
        if len(str(path)) > self.max_pathname_length:
            raise ResourceLimitExceeded("pathname_length")
        if relative_to is not None:
            try:
                depth = len(path.relative_to(relative_to).parts)
            except ValueError as exc:
                raise ResourceLimitExceeded("directory_depth") from exc
            if depth > self.max_directory_depth:
                raise ResourceLimitExceeded("directory_depth")

    def count_directory(self, path: Path) -> int:
        count = 0
        for _ in path.iterdir():
            count += 1
            if count > self.max_directory_entries:
                raise ResourceLimitExceeded("directory_entries")
        return count

    def check_plist(self, path: Path) -> None:
        if path.stat().st_size > self.max_plist_bytes:
            raise ResourceLimitExceeded("plist_size")

    def check_sqlite_set(self, paths: tuple[Path, ...]) -> None:
        total = 0
        for index, path in enumerate(paths):
            size = path.stat().st_size
            suffix = path.name.removeprefix(paths[0].name) if index else ""
            ceiling = {
                "": self.max_sqlite_main_bytes,
                "-wal": self.max_sqlite_wal_bytes,
                "-shm": self.max_sqlite_shm_bytes,
                "-journal": self.max_sqlite_wal_bytes,
            }.get(suffix)
            if ceiling is None or size > ceiling:
                raise ResourceLimitExceeded(
                    "sqlite_main_size" if index == 0 else f"sqlite{suffix}_size"
                )
            total += size
            if total > self.max_controlled_copy_bytes:
                raise ResourceLimitExceeded("controlled_copy_aggregate_size")
