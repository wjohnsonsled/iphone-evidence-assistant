"""Tenant/case-scoped evidence-source identity without evidence access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.security.case import SecurityCase


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    evidence_source_id: UUID
    tenant_id: UUID
    case_id: UUID
    source_type: str
    source_locator: str
    registered_at: datetime
    registered_by_actor_id: UUID
    version: int = 1

    def __post_init__(self) -> None:
        if self.evidence_source_id.version != 4:
            raise ValueError("Evidence-source identity must be UUIDv4.")
        for value, label, maximum in (
            (self.source_type, "Source type", 128),
            (self.source_locator, "Source locator", 2_048),
        ):
            if not value.strip() or value != value.strip() or len(value) > maximum:
                raise ValueError(f"{label} must be nonempty, trimmed, and bounded.")
        if self.registered_at.tzinfo is None or self.registered_at.utcoffset() is None:
            raise ValueError("Registration time must be timezone-aware.")
        if self.version < 1:
            raise ValueError("Evidence-source version must be positive.")


def register_evidence_source(
    *,
    case: SecurityCase,
    source_type: str,
    source_locator: str,
    registered_by_actor_id: UUID,
    registered_at: datetime | None = None,
) -> EvidenceSource:
    return EvidenceSource(
        evidence_source_id=uuid4(),
        tenant_id=case.tenant_id,
        case_id=case.case_id,
        source_type=source_type,
        source_locator=source_locator,
        registered_at=registered_at or datetime.now(timezone.utc),
        registered_by_actor_id=registered_by_actor_id,
    )
