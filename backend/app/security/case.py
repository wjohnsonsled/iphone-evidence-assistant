"""Tenant-scoped supported-boundary case identity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class SecurityCase:
    case_id: UUID
    tenant_id: UUID
    name: str
    created_at: datetime
    created_by_actor_id: UUID
    version: int = 1

    def __post_init__(self) -> None:
        if self.case_id.version != 4:
            raise ValueError("Case identity must be UUIDv4.")
        if not self.name.strip() or self.name != self.name.strip():
            raise ValueError("Case name must be nonempty and trimmed.")
        if len(self.name) > 255:
            raise ValueError("Case name exceeds 255 characters.")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("Case creation time must be timezone-aware.")
        if self.version < 1:
            raise ValueError("Case version must be positive.")


def create_case(
    *,
    tenant_id: UUID,
    name: str,
    created_by_actor_id: UUID,
    created_at: datetime | None = None,
) -> SecurityCase:
    return SecurityCase(
        case_id=uuid4(),
        tenant_id=tenant_id,
        name=name,
        created_at=created_at or datetime.now(timezone.utc),
        created_by_actor_id=created_by_actor_id,
    )
