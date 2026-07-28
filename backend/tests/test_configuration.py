"""DEV-0103 deterministic configuration validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Environment, LogLevel, Settings, get_settings


def settings(tmp_path: Path, **changes) -> Settings:
    values = {
        "DATABASE_URL": "postgresql+psycopg://user:synthetic-secret@db:5432/evidence",
        "EVIDENCE_ROOT": str(tmp_path.resolve()),
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "INFO",
    }
    values.update(changes)
    return Settings(_env_file=None, **values)


def test_closed_environment_and_log_level_normalize(tmp_path):
    configured = settings(tmp_path, ENVIRONMENT="  TEST ", LOG_LEVEL=" warning ")
    assert configured.environment is Environment.TEST
    assert configured.log_level is LogLevel.WARNING
    with pytest.raises(ValidationError):
        settings(tmp_path, ENVIRONMENT="demo")
    with pytest.raises(ValidationError):
        settings(tmp_path, LOG_LEVEL="TRACE")


@pytest.mark.parametrize("database_url", ["", "not a url", "mysql://db/evidence"])
def test_database_url_fails_closed(database_url, tmp_path):
    with pytest.raises(ValidationError):
        settings(tmp_path, DATABASE_URL=database_url)


def test_sqlite_is_test_only(tmp_path):
    test_settings = settings(
        tmp_path,
        ENVIRONMENT="test",
        DATABASE_URL="sqlite+pysqlite:///:memory:",
    )
    assert test_settings.safe_summary()["database_driver"] == "sqlite+pysqlite"
    with pytest.raises(ValidationError, match="not permitted"):
        settings(tmp_path, DATABASE_URL="sqlite+pysqlite:///:memory:")


def test_evidence_roots_are_absolute_normalized_and_unique(tmp_path):
    first = tmp_path / "one"
    second = tmp_path / "two"
    configured = settings(tmp_path, EVIDENCE_ROOT=f"{first};{second}")
    assert configured.evidence_roots == [first, second]
    for invalid in ("relative", f"{first};;{second}", f"{first};{first}"):
        with pytest.raises(ValidationError):
            settings(tmp_path, EVIDENCE_ROOT=invalid)


def test_production_rejects_documented_development_password(tmp_path):
    with pytest.raises(ValidationError, match="development database password"):
        settings(
            tmp_path,
            ENVIRONMENT="production",
            DATABASE_URL=(
                "postgresql+psycopg://evidence:evidence_dev_password@db:5432/evidence"
            ),
        )


def test_diagnostics_do_not_expose_credentials_or_full_url(tmp_path):
    configured = settings(tmp_path)
    rendered = repr(configured)
    summary = configured.safe_summary()
    assert "synthetic-secret" not in rendered
    assert "synthetic-secret" not in repr(summary)
    assert "DATABASE_URL" not in summary
    assert summary["database_host"] == "db"


def test_environment_aliases_load_and_settings_cache_can_be_cleared(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:synthetic-secret@db:5432/evidence",
    )
    monkeypatch.setenv("EVIDENCE_ROOT", str(tmp_path.resolve()))
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "error")
    get_settings.cache_clear()
    loaded = get_settings()
    assert loaded.environment is Environment.TEST
    assert loaded.log_level is LogLevel.ERROR
    get_settings.cache_clear()
    assert get_settings.cache_info().currsize == 0
