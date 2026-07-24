"""Application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    database_url: str = Field(..., alias="DATABASE_URL")
    evidence_root: str = Field("/evidence", alias="EVIDENCE_ROOT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    environment: str = Field("development", alias="ENVIRONMENT")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @field_validator("evidence_root")
    @classmethod
    def validate_evidence_root(cls, value: str) -> str:
        """Normalize configured evidence root text."""

        if not value.strip():
            raise ValueError("EVIDENCE_ROOT must not be empty")
        return value

    @property
    def evidence_roots(self) -> list[Path]:
        """Return configured evidence roots as paths."""

        return [Path(item).expanduser() for item in self.evidence_root.split(";") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()
