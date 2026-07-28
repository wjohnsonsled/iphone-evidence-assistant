"""Principal and membership ORM contracts; migration is owned by DEV-0308."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PrincipalModel(Base):
    __tablename__ = "security_principals"
    __table_args__ = (
        UniqueConstraint(
            "identity_provider",
            "external_subject",
            name="uq_security_principal_external_identity",
        ),
        CheckConstraint("version > 0", name="ck_security_principals_version_positive"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    kind: Mapped[str] = mapped_column(String(32))
    identity_provider: Mapped[str] = mapped_column(String(128))
    external_subject: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by_actor_id: Mapped[UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class TenantMembershipModel(Base):
    __tablename__ = "security_tenant_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "principal_id",
            "role_key",
            name="uq_security_membership_tenant_principal_role",
        ),
        CheckConstraint("version > 0", name="ck_security_memberships_version_positive"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("security_tenants.id", ondelete="RESTRICT"),
        index=True,
    )
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("security_principals.id", ondelete="RESTRICT"),
        index=True,
    )
    role_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by_actor_id: Mapped[UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
