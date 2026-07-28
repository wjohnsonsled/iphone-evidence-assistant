"""Stable internal source locator with separate raw and normalized values."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.evidence_core.source_artifact import SourceArtifact

_KEY = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")


@dataclass(frozen=True, slots=True)
class SourceLocator:
    locator_id: UUID
    tenant_id: UUID
    case_id: UUID
    source_artifact_id: UUID
    locator_kind: str
    raw_value: str
    normalized_value: str
    normalization_method: str
    version: int = 1

    def __post_init__(self) -> None:
        if self.locator_id.version != 4:
            raise ValueError("Locator identity must be UUIDv4.")
        if not _KEY.fullmatch(self.locator_kind) or not _KEY.fullmatch(self.normalization_method):
            raise ValueError("Locator keys must be canonical.")
        for value in (self.raw_value, self.normalized_value):
            if not value or len(value) > 4096 or "\x00" in value:
                raise ValueError("Locator values must be nonempty, bounded, and NUL-free.")
        if self.version < 1:
            raise ValueError("Locator version must be positive.")


def create_source_locator(
    *,
    artifact: SourceArtifact,
    locator_kind: str,
    raw_value: str,
    normalized_value: str,
    normalization_method: str,
) -> SourceLocator:
    return SourceLocator(
        uuid4(), artifact.tenant_id, artifact.case_id, artifact.source_artifact_id,
        locator_kind, raw_value, normalized_value, normalization_method,
    )
