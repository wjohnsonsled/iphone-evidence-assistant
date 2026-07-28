from uuid import UUID

import pytest

from app.evidence_core.parser_identity import ParserIdentity, register_candidate_parser_identity
from app.integrity.parser_contract import ParserRegistryState
from app.support.registry import create_supported_registry


def u(n: int) -> UUID:
    return UUID(f"43000000-0000-4000-8000-{n:012d}")


def test_candidate_identity_preserves_exact_identity_and_contract_version() -> None:
    identity = register_candidate_parser_identity(
        parser_id="synthetic.messages", parser_version="1.2.0",
        artifact_family="messages", contract_version="parser-contract-v1",
        declaration_reference="DEV-0404-synthetic",
    )
    assert identity.parser_identity_id.version == 4
    assert identity.registry_state is ParserRegistryState.CANDIDATE
    assert identity.parser_version == "1.2.0"


def test_supported_state_cannot_be_created_by_candidate_model() -> None:
    with pytest.raises(ValueError, match="owner promotion"):
        ParserIdentity(
            u(1), "synthetic.messages", "1.2.0", "messages",
            "parser-contract-v1", ParserRegistryState.SUPPORTED, "synthetic",
        )
    assert create_supported_registry().entries == ()


@pytest.mark.parametrize("parser_id", ["", "Synthetic.Messages", "bad/parser"])
def test_noncanonical_parser_identity_fails_closed(parser_id: str) -> None:
    with pytest.raises(ValueError):
        register_candidate_parser_identity(
            parser_id=parser_id, parser_version="1", artifact_family="messages",
            contract_version="v1", declaration_reference="synthetic",
        )
