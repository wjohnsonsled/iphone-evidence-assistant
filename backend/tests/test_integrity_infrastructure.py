from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from app.core.database import Base
from app.integrity.domain import (
    AccessIntent, AuditEventType, EvidenceLifecycle, HashObservation,
    IntegrityState, ProvenanceEdge, ProvenanceNode, ProvenanceNodeType,
    ProvenanceRelationship, ProvenanceValidationReport, register_evidence,
)
from app.integrity.parser_contract import (
    ControlledParseContext, EvidenceParser, IntegrityPolicy,
    ParserConformanceHarness, ParserRegistryState, ParserResult,
)
from app.integrity.services import (
    TRANSITIONS, AppendOnlyAuditService, CustodyService, EvidenceLockService,
    HashRegistry, LifecycleService, MutationDetector, ProvenanceService,
)

NOW = datetime(2026, 7, 27, tzinfo=timezone.utc)


def evidence(**overrides):
    values = dict(
        tenant_id=uuid4(), case_id=uuid4(), evidence_source_id=uuid4(),
        evidence_kind="SOURCE", source_type="SYNTHETIC", source_locator="fixture/source",
        logical_identifier="fixture-1", intake_method="SYNTHETIC_TEST",
        registered_by_actor_id=uuid4(), registered_at=NOW,
    )
    values.update(overrides)
    return register_evidence(**values)


def test_evidence_uuid_is_stable_distinct_and_not_content_derived():
    first, second = evidence(), evidence()
    assert first.evidence_uuid != second.evidence_uuid
    assert replace(first, integrity_state=IntegrityState.VERIFIED).evidence_uuid == first.evidence_uuid
    assert first.evidence_uuid.version == 4
    with pytest.raises(ValueError):
        evidence(source_locator="")


def test_relational_models_create_additive_tables():
    import app.models  # noqa: F401 - register all relational mappings
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    names = set(__import__("sqlalchemy").inspect(engine).get_table_names())
    assert {"integrity_evidence_objects", "integrity_hash_observations", "integrity_audit_events", "integrity_custody_events", "integrity_provenance_nodes", "integrity_provenance_edges"} <= names
    assert "evidence_events" in names


def test_every_transition_and_denial_is_atomic_and_audited():
    audit, actor, correlation = AppendOnlyAuditService(), uuid4(), uuid4()
    service = LifecycleService(audit)
    for source, targets in TRANSITIONS.items():
        for target in targets:
            updated = service.transition(replace(evidence(), lifecycle_state=source), target, actor_id=actor, correlation_id=correlation)
            assert updated.lifecycle_state is target
    original = replace(evidence(), lifecycle_state=EvidenceLifecycle.ARCHIVED)
    with pytest.raises(ValueError):
        service.transition(original, EvidenceLifecycle.REGISTERED, actor_id=actor, correlation_id=correlation)
    assert original.lifecycle_state is EvidenceLifecycle.ARCHIVED
    assert audit.events[-1].event_type is AuditEventType.LIFECYCLE_TRANSITION_DENIED
    with pytest.raises(ValueError):
        service.transition(replace(evidence(), lifecycle_state=EvidenceLifecycle.QUARANTINED), EvidenceLifecycle.PROCESSING, actor_id=actor, correlation_id=correlation)


def test_sha256_empty_streaming_history_and_mismatch(tmp_path):
    audit, registry, item, actor, correlation = AppendOnlyAuditService(), None, evidence(), uuid4(), uuid4()
    registry = HashRegistry(audit)
    empty = tmp_path / "empty"; empty.write_bytes(b"")
    large = tmp_path / "large"; large.write_bytes(b"a" * (2 * 1024 * 1024 + 3))
    first = registry.compute(empty, item, purpose="registration", role="source", actor_id=actor, correlation_id=correlation)
    second = registry.compute(empty, item, purpose="verification", role="source", actor_id=actor, correlation_id=correlation)
    third = registry.compute(large, item, purpose="registration", role="source", actor_id=actor, correlation_id=correlation)
    assert first.digest == hashlib.sha256(b"").hexdigest()
    assert third.byte_length == 2 * 1024 * 1024 + 3
    assert registry.verify(first, second, item, actor_id=actor, correlation_id=correlation) is IntegrityState.VERIFIED
    changed = replace(second, observation_id=uuid4(), digest="0" * 64)
    mutated = MutationDetector(registry).evaluate(item, first, changed, actor_id=actor, correlation_id=correlation)
    assert mutated.integrity_state is IntegrityState.MISMATCH
    assert len(registry.observations) == 3
    with pytest.raises(FrozenInstanceError):
        first.digest = "changed"


def test_hash_failure_and_unstable_state_are_distinct(tmp_path):
    registry, item, actor, correlation = HashRegistry(AppendOnlyAuditService()), evidence(), uuid4(), uuid4()
    failed = registry.compute(tmp_path / "missing", item, purpose="registration", role="source", actor_id=actor, correlation_id=correlation)
    unstable = replace(failed, observation_id=uuid4(), failure_code="source_unstable")
    assert registry.verify(failed, failed, item, actor_id=actor, correlation_id=correlation) is IntegrityState.VERIFICATION_FAILED
    assert registry.verify(failed, unstable, item, actor_id=actor, correlation_id=correlation) is IntegrityState.SOURCE_UNSTABLE


def test_locks_conflict_release_owner_and_stale_policy():
    audit, service, item, actor, other, correlation = AppendOnlyAuditService(), None, evidence(), uuid4(), uuid4(), uuid4()
    service = EvidenceLockService(audit)
    locked = service.acquire(item, actor_id=actor, intent=AccessIntent.COMPUTE_HASH, correlation_id=correlation, now=NOW)
    with pytest.raises(PermissionError):
        service.acquire(item, actor_id=other, intent=AccessIntent.VERIFY_INTEGRITY, correlation_id=correlation)
    with pytest.raises(PermissionError):
        service.release(locked, actor_id=other, correlation_id=correlation)
    assert service.release(locked, actor_id=actor, correlation_id=correlation).lock_state.value == "UNLOCKED"
    locked = service.acquire(item, actor_id=actor, intent=AccessIntent.INSPECT_METADATA, correlation_id=correlation, now=NOW)
    assert service.release_stale(locked, older_than=NOW + timedelta(seconds=1), actor_id=other, correlation_id=correlation).lock_state.value == "UNLOCKED"


def test_custody_is_ordered_prior_linked_and_immutable():
    service, item, actor, correlation = CustodyService(), evidence(), uuid4(), uuid4()
    first = service.append(evidence=item, actor_id=actor, actor_type="SERVICE", action_type="REGISTER", component="test", component_version="1", environment_id="synthetic", purpose="test", result="SUCCEEDED", correlation_id=correlation)
    second = service.append(evidence=item, actor_id=actor, actor_type="SERVICE", action_type="VERIFY", component="test", component_version="1", environment_id="synthetic", purpose="test", result="FAILED", correlation_id=correlation, failure_code="synthetic")
    assert (first.sequence, second.sequence, second.prior_event_id) == (1, 2, first.event_id)
    with pytest.raises(FrozenInstanceError):
        first.result = "changed"


def test_provenance_path_cross_tenant_dangling_cycle_and_parser_link():
    tenant, case = uuid4(), uuid4()
    service = ProvenanceService()
    source = ProvenanceNode(uuid4(), tenant, case, ProvenanceNodeType.SOURCE_ARTIFACT, "source")
    record = ProvenanceNode(uuid4(), tenant, case, ProvenanceNodeType.NORMALIZED_RECORD, "record")
    service.add_node(source); service.add_node(record)
    service.add_edge(ProvenanceEdge(uuid4(), tenant, case, record.node_id, source.node_id, ProvenanceRelationship.NORMALIZED_FROM, "parser", "1"))
    assert service.validate_path(record.node_id, source.node_id).valid
    with pytest.raises(ValueError):
        service.add_edge(ProvenanceEdge(uuid4(), tenant, case, source.node_id, record.node_id, ProvenanceRelationship.DERIVED_FROM))
    with pytest.raises(ValueError):
        service.add_edge(ProvenanceEdge(uuid4(), tenant, case, uuid4(), source.node_id, ProvenanceRelationship.BELONGS_TO))
    foreign = ProvenanceNode(uuid4(), uuid4(), case, ProvenanceNodeType.SOURCE_ARTIFACT, "foreign")
    service.add_node(foreign)
    with pytest.raises(PermissionError):
        service.add_edge(ProvenanceEdge(uuid4(), tenant, case, record.node_id, foreign.node_id, ProvenanceRelationship.BELONGS_TO))


def parser_result(*, provenance=True, omissions=(), examined=1, emitted=1):
    return ParserResult(True, examined, emitted, 0, 0, 0, 0, 0, provenance, omissions, (), ("synthetic only",), ({"raw": 1},), ({"normalized": 1},))


class SyntheticParser:
    parser_id = "synthetic.parser"
    parser_version = "1.0.0"
    artifact_family = "SYNTHETIC"
    registry_state = ParserRegistryState.CANDIDATE
    def declared_schema_profiles(self): return ("SYNTHETIC_V1",)
    def validate(self, context): return parser_result()
    def parse(self, context): return parser_result()
    def report_coverage(self, context): return parser_result()
    def report_limitations(self, context): return ("synthetic only",)
    def self_test(self): return parser_result()


def context(**changes):
    values = dict(controlled_input_id="copy-1", schema_profile="SYNTHETIC_V1", integrity_state=IntegrityState.VERIFIED, provenance_report=ProvenanceValidationReport(True))
    values.update(changes)
    return ControlledParseContext(**values)


def test_parser_contract_conformance_and_integrity_policy():
    parser = SyntheticParser()
    assert isinstance(parser, EvidenceParser)
    assert ParserConformanceHarness().evaluate(parser, context()).conforming
    for changed, expected in [
        ({"source_writable": True}, "source_write_capability"),
        ({"legacy_source": True}, "legacy_input"),
        ({"integrity_state": IntegrityState.MISMATCH}, "integrity_not_verified"),
        ({"provenance_report": ProvenanceValidationReport(False, ("broken",))}, "provenance_invalid"),
        ({"schema_profile": "UNKNOWN"}, "schema_profile_not_declared"),
    ]:
        report = ParserConformanceHarness().evaluate(parser, context(**changed))
        assert not report.conforming and expected in report.failures
    assert report.support_effect == "NONE_CANDIDATE_ONLY"


def test_parser_harness_rejects_version_provenance_coverage_omission_and_registry():
    parser = SyntheticParser()
    parser.parser_version = ""
    assert "missing_parser_version" in ParserConformanceHarness().evaluate(parser, context()).failures
    parser.parser_version = "1"
    parser.registry_state = ParserRegistryState.SUPPORTED
    assert "registry_state_not_candidate" in ParserConformanceHarness().evaluate(parser, context()).failures
    parser.registry_state = ParserRegistryState.CANDIDATE
    parser.parse = lambda _: parser_result(provenance=False)
    assert "provenance_missing" in ParserConformanceHarness().evaluate(parser, context()).failures
    parser.parse = lambda _: parser_result(omissions=("omitted",))
    assert "silent_omission" in ParserConformanceHarness().evaluate(parser, context()).failures
    parser.parse = lambda _: parser_result(examined=2, emitted=1)
    assert "coverage_not_reconciled" in ParserConformanceHarness().evaluate(parser, context()).failures
