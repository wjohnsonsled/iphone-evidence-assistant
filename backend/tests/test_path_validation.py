"""Path validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.errors import ApiError
from app.services.case_processing import LocalBackupPathValidator, appears_supported_backup


def test_path_validation_accepts_supported_backup_under_root(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    backup = root / "backup"
    backup.mkdir(parents=True)
    (backup / "Manifest.db").write_text("", encoding="utf-8")

    resolved = LocalBackupPathValidator([root]).validate(str(backup))

    assert resolved == backup.resolve()
    assert appears_supported_backup(backup)


def test_path_validation_rejects_path_traversal_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "Manifest.db").write_text("", encoding="utf-8")

    with pytest.raises(ApiError) as exc:
        LocalBackupPathValidator([root]).validate(str(outside))

    assert exc.value.code == "backup_path_outside_evidence_root"
