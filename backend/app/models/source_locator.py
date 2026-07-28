"""Candidate stable-locator ORM contract; migration is deferred to DEV-0410."""

from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SupportedSourceLocatorModel(Base):
    __tablename__ = "supported_source_locators"
    __table_args__ = (CheckConstraint("version > 0", name="ck_supported_locators_version_positive"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("security_tenants.id", ondelete="RESTRICT"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("security_cases.id", ondelete="RESTRICT"), index=True)
    source_artifact_id: Mapped[UUID] = mapped_column(ForeignKey("supported_source_artifacts.id", ondelete="RESTRICT"), index=True)
    locator_kind: Mapped[str] = mapped_column(String(128))
    raw_value: Mapped[str] = mapped_column(Text)
    normalized_value: Mapped[str] = mapped_column(Text)
    normalization_method: Mapped[str] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer, default=1)
