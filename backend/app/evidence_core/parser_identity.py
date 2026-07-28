"""Persistent candidate parser identity; registration is not support approval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.integrity.parser_contract import ParserRegistryState

_ID = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")


@dataclass(frozen=True, slots=True)
class ParserIdentity:
    parser_identity_id: UUID
    parser_id: str
    parser_version: str
    artifact_family: str
    contract_version: str
    registry_state: ParserRegistryState
    declaration_reference: str
    version: int = 1

    def __post_init__(self) -> None:
        if self.parser_identity_id.version != 4:
            raise ValueError("Parser identity must be UUIDv4.")
        if not _ID.fullmatch(self.parser_id) or not _ID.fullmatch(self.artifact_family):
            raise ValueError("Parser and artifact-family identifiers must be canonical.")
        for value, field, maximum in (
            (self.parser_version, "parser_version", 64),
            (self.contract_version, "contract_version", 64),
            (self.declaration_reference, "declaration_reference", 255),
        ):
            if not value.strip() or value != value.strip() or len(value) > maximum:
                raise ValueError(f"{field}_invalid")
        if self.registry_state is ParserRegistryState.SUPPORTED:
            raise ValueError("Supported identity requires the separate owner promotion gate.")
        if self.version < 1:
            raise ValueError("Identity version must be positive.")


def register_candidate_parser_identity(
    *,
    parser_id: str,
    parser_version: str,
    artifact_family: str,
    contract_version: str,
    declaration_reference: str,
) -> ParserIdentity:
    return ParserIdentity(
        uuid4(), parser_id, parser_version, artifact_family, contract_version,
        ParserRegistryState.CANDIDATE, declaration_reference,
    )
