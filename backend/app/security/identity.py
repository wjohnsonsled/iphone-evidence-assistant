"""Neutral principal and tenant-membership contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


_KEY = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")


class PrincipalKind(str, Enum):
    USER = "USER"
    SERVICE = "SERVICE"


def _required(value: str, label: str, maximum: int) -> None:
    if not value.strip() or value != value.strip() or len(value) > maximum:
        raise ValueError(f"{label} must be nonempty, trimmed, and bounded.")


def _aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Creation time must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class Principal:
    principal_id: UUID
    kind: PrincipalKind
    identity_provider: str
    external_subject: str
    created_at: datetime
    created_by_actor_id: UUID
    version: int = 1

    def __post_init__(self) -> None:
        if self.principal_id.version != 4:
            raise ValueError("Principal identity must be UUIDv4.")
        _required(self.identity_provider, "Identity provider", 128)
        _required(self.external_subject, "External subject", 255)
        _aware(self.created_at)
        if self.version < 1:
            raise ValueError("Principal version must be positive.")


@dataclass(frozen=True, slots=True)
class TenantMembership:
    membership_id: UUID
    tenant_id: UUID
    principal_id: UUID
    role_key: str
    created_at: datetime
    created_by_actor_id: UUID
    version: int = 1

    def __post_init__(self) -> None:
        if self.membership_id.version != 4:
            raise ValueError("Membership identity must be UUIDv4.")
        if not _KEY.fullmatch(self.role_key):
            raise ValueError("Role key is not canonical.")
        _aware(self.created_at)
        if self.version < 1:
            raise ValueError("Membership version must be positive.")


def create_principal(
    *,
    kind: PrincipalKind,
    identity_provider: str,
    external_subject: str,
    created_by_actor_id: UUID,
    created_at: datetime | None = None,
) -> Principal:
    return Principal(
        uuid4(),
        kind,
        identity_provider,
        external_subject,
        created_at or datetime.now(timezone.utc),
        created_by_actor_id,
    )


def create_membership(
    *,
    tenant_id: UUID,
    principal_id: UUID,
    role_key: str,
    created_by_actor_id: UUID,
    created_at: datetime | None = None,
) -> TenantMembership:
    return TenantMembership(
        uuid4(),
        tenant_id,
        principal_id,
        role_key,
        created_at or datetime.now(timezone.utc),
        created_by_actor_id,
    )
