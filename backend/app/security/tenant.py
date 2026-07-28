"""Neutral tenant identity contract for server-side isolation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4


_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


@dataclass(frozen=True, slots=True)
class Tenant:
    tenant_id: UUID
    slug: str
    display_name: str
    created_at: datetime
    created_by_actor_id: UUID
    version: int = 1

    def __post_init__(self) -> None:
        if self.tenant_id.version != 4:
            raise ValueError("Tenant identity must be UUIDv4.")
        if not _SLUG.fullmatch(self.slug):
            raise ValueError("Tenant slug is not canonical.")
        if not self.display_name.strip() or self.display_name != self.display_name.strip():
            raise ValueError("Tenant display name must be nonempty and trimmed.")
        if len(self.display_name) > 255:
            raise ValueError("Tenant display name exceeds 255 characters.")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("Tenant creation time must be timezone-aware.")
        if self.version < 1:
            raise ValueError("Tenant version must be positive.")


def create_tenant(
    *,
    slug: str,
    display_name: str,
    created_by_actor_id: UUID,
    tenant_id: UUID | None = None,
    created_at: datetime | None = None,
) -> Tenant:
    """Create an immutable neutral tenant identity."""

    observed_at = created_at or datetime.now(timezone.utc)
    return Tenant(
        tenant_id=tenant_id or uuid4(),
        slug=slug,
        display_name=display_name,
        created_at=observed_at.astimezone(timezone.utc)
        if observed_at.tzinfo is not None and observed_at.utcoffset() is not None
        else observed_at,
        created_by_actor_id=created_by_actor_id,
    )
