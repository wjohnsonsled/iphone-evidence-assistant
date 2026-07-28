"""Application configuration."""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Environment-backed application settings."""

    database_url: str = Field(..., alias="DATABASE_URL", repr=False)
    evidence_root: str = Field("/evidence", alias="EVIDENCE_ROOT")
    log_level: LogLevel = Field(LogLevel.INFO, alias="LOG_LEVEL")
    environment: Environment = Field(Environment.DEVELOPMENT, alias="ENVIRONMENT")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: Any) -> Any:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: Any) -> Any:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DATABASE_URL must not be empty")
        try:
            parsed = make_url(value)
        except ArgumentError as exc:
            raise ValueError("DATABASE_URL must be a parseable SQLAlchemy URL") from exc
        if not parsed.drivername:
            raise ValueError("DATABASE_URL must declare a database driver")
        return value

    @field_validator("evidence_root")
    @classmethod
    def validate_evidence_root(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("EVIDENCE_ROOT must not be empty")
        raw_items = value.split(";")
        if any(not item.strip() for item in raw_items):
            raise ValueError("EVIDENCE_ROOT contains an empty root")
        normalized: list[str] = []
        identities: set[str] = set()
        for raw in raw_items:
            path = Path(raw.strip()).expanduser()
            if not path.is_absolute():
                raise ValueError("EVIDENCE_ROOT entries must be absolute")
            text = os.path.normpath(str(path))
            identity = os.path.normcase(text)
            if identity in identities:
                raise ValueError("EVIDENCE_ROOT entries must be unique")
            identities.add(identity)
            normalized.append(text)
        return ";".join(normalized)

    @model_validator(mode="after")
    def validate_environment_policy(self) -> Settings:
        parsed = make_url(self.database_url)
        if self.environment is Environment.TEST:
            permitted = {"sqlite", "sqlite+pysqlite", "postgresql+psycopg"}
        else:
            permitted = {"postgresql+psycopg"}
        if parsed.drivername not in permitted:
            raise ValueError(
                f"DATABASE_URL driver {parsed.drivername!r} is not permitted "
                f"for {self.environment.value}"
            )
        if (
            self.environment is Environment.PRODUCTION
            and parsed.password == "evidence_dev_password"
        ):
            raise ValueError("production must not use the documented development database password")
        return self

    @property
    def evidence_roots(self) -> list[Path]:
        """Return configured evidence roots as paths."""

        return [Path(item) for item in self.evidence_root.split(";")]

    def safe_summary(self) -> dict[str, Any]:
        """Return non-secret configuration metadata suitable for diagnostics."""

        parsed = make_url(self.database_url)
        return {
            "environment": self.environment.value,
            "log_level": self.log_level.value,
            "database_driver": parsed.drivername,
            "database_host": parsed.host,
            "database_name": parsed.database,
            "evidence_roots": tuple(str(path) for path in self.evidence_roots),
        }


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()
