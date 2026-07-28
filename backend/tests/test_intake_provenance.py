from __future__ import annotations

from uuid import uuid4

import pytest

from app.integrity.domain import (
    ProvenanceEdge,
    ProvenanceNode,
    ProvenanceNodeType,
    ProvenanceRelationship,
)
from app.integrity.services import ProvenanceService


def _node(tenant_id, case_id, node_type, locator):
    return ProvenanceNode(uuid4(), tenant_id, case_id, node_type, locator)


def test_controlled_copy_resolves_to_registered_intake_source():
    tenant_id, case_id = uuid4(), uuid4()
    source = _node(
        tenant_id,
        case_id,
        ProvenanceNodeType.EVIDENCE_SOURCE,
        "evidence-source:synthetic-candidate",
    )
    artifact = _node(
        tenant_id,
        case_id,
        ProvenanceNodeType.SOURCE_ARTIFACT,
        "source:Manifest.db",
    )
    controlled = _node(
        tenant_id,
        case_id,
        ProvenanceNodeType.CONTROLLED_COPY,
        "working-copy:run-1/Manifest.db",
    )
    service = ProvenanceService()
    for node in (source, artifact, controlled):
        service.add_node(node)
    belongs = ProvenanceEdge(
        uuid4(),
        tenant_id,
        case_id,
        artifact.node_id,
        source.node_id,
        ProvenanceRelationship.BELONGS_TO,
    )
    copied = ProvenanceEdge(
        uuid4(),
        tenant_id,
        case_id,
        controlled.node_id,
        artifact.node_id,
        ProvenanceRelationship.COPIED_FROM,
    )
    service.add_edge(belongs)
    service.add_edge(copied)

    assert service.edges == [belongs, copied]
    assert service.validate_path(controlled.node_id, source.node_id).valid
    assert source.stable_locator == "evidence-source:synthetic-candidate"
    assert artifact.stable_locator == "source:Manifest.db"
    assert controlled.stable_locator == "working-copy:run-1/Manifest.db"


def test_intake_provenance_rejects_scope_crossing_dangling_and_cycles():
    tenant_id, case_id = uuid4(), uuid4()
    source = _node(tenant_id, case_id, ProvenanceNodeType.EVIDENCE_SOURCE, "source")
    controlled = _node(
        tenant_id,
        case_id,
        ProvenanceNodeType.CONTROLLED_COPY,
        "copy",
    )
    foreign_tenant = _node(
        uuid4(),
        case_id,
        ProvenanceNodeType.SOURCE_ARTIFACT,
        "foreign-tenant",
    )
    foreign_case = _node(
        tenant_id,
        uuid4(),
        ProvenanceNodeType.SOURCE_ARTIFACT,
        "foreign-case",
    )
    service = ProvenanceService()
    for node in (source, controlled, foreign_tenant, foreign_case):
        service.add_node(node)

    for target in (foreign_tenant, foreign_case):
        with pytest.raises(PermissionError):
            service.add_edge(
                ProvenanceEdge(
                    uuid4(),
                    tenant_id,
                    case_id,
                    controlled.node_id,
                    target.node_id,
                    ProvenanceRelationship.COPIED_FROM,
                )
            )
    with pytest.raises(ValueError):
        service.add_edge(
            ProvenanceEdge(
                uuid4(),
                tenant_id,
                case_id,
                controlled.node_id,
                uuid4(),
                ProvenanceRelationship.COPIED_FROM,
            )
        )
    assert not service.validate_path(controlled.node_id, source.node_id).valid

    service.add_edge(
        ProvenanceEdge(
            uuid4(),
            tenant_id,
            case_id,
            controlled.node_id,
            source.node_id,
            ProvenanceRelationship.COPIED_FROM,
        )
    )
    with pytest.raises(ValueError):
        service.add_edge(
            ProvenanceEdge(
                uuid4(),
                tenant_id,
                case_id,
                source.node_id,
                controlled.node_id,
                ProvenanceRelationship.DERIVED_FROM,
            )
        )

