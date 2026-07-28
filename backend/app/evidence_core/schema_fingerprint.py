"""Algorithm-qualified schema fingerprint observations, never compatibility claims."""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
_KEY = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True, slots=True)
class SchemaFingerprintObservation:
    observation_id: UUID
    source_artifact_id: UUID
    processing_run_id: UUID
    parser_identity_id: UUID | None
    profile_id: str
    profile_version: str
    canonical_input_reference: str
    sha256_digest: str
    observed_at: datetime
    limitations: tuple[str, ...]
    version: int = 1
    def __post_init__(self) -> None:
        if self.observation_id.version != 4: raise ValueError("observation_id_invalid")
        if not _KEY.fullmatch(self.profile_id): raise ValueError("profile_id_invalid")
        if any(not v.strip() for v in (self.profile_version, self.canonical_input_reference)): raise ValueError("profile_reference_invalid")
        if not _SHA256.fullmatch(self.sha256_digest): raise ValueError("sha256_invalid")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise ValueError("observed_at_invalid")
        if not self.limitations or any(not v.strip() for v in self.limitations): raise ValueError("limitations_required")
        if self.version < 1: raise ValueError("version_invalid")

def record_schema_fingerprint(**values: object) -> SchemaFingerprintObservation:
    return SchemaFingerprintObservation(observation_id=uuid4(), **values)  # type: ignore[arg-type]
