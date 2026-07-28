"""Candidate parser identity ORM metadata; migration deferred to DEV-0410."""

from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ParserIdentityModel(Base):
    __tablename__ = "evidence_parser_identities"
    __table_args__ = (
        UniqueConstraint("parser_id", "parser_version", name="uq_parser_identity_version"),
        CheckConstraint("version > 0", name="ck_parser_identity_version_positive"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    parser_id: Mapped[str] = mapped_column(String(128), index=True)
    parser_version: Mapped[str] = mapped_column(String(64))
    artifact_family: Mapped[str] = mapped_column(String(128), index=True)
    contract_version: Mapped[str] = mapped_column(String(64))
    registry_state: Mapped[str] = mapped_column(String(32))
    declaration_reference: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
