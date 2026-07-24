"""Summary aggregation tests."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import ArtifactCoverage, Case, EvidenceEvent
from app.services.evidence_summary import EvidenceSummaryService


def test_summary_counts_are_deterministic() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as session:
        case = Case(name="Summary")
        session.add(case)
        session.flush()
        session.add_all(
            [
                EvidenceEvent(
                    case_id=case.id,
                    event_type="message",
                    category="communications",
                    timestamp=datetime(2026, 6, 25, 16, 32, tzinfo=timezone.utc),
                    source_artifact="sms",
                    details_json={},
                    raw_values_json={},
                    confidence_basis_json={},
                    conversation_key="chat-1",
                    contact_key="+15551234567",
                ),
                EvidenceEvent(
                    case_id=case.id,
                    event_type="attachment",
                    category="media",
                    timestamp=datetime(2026, 6, 25, 16, 33, tzinfo=timezone.utc),
                    source_artifact="photos",
                    details_json={},
                    raw_values_json={},
                    confidence_basis_json={},
                    conversation_key="chat-1",
                    contact_key="+15551234567",
                ),
                ArtifactCoverage(
                    case_id=case.id,
                    artifact_name="SMS",
                    coverage_status="available_and_parsed",
                    records_parsed=1,
                    warning_count=0,
                    error_count=0,
                    details_json={},
                ),
            ]
        )
        session.commit()

        summary = EvidenceSummaryService().build_summary(session, case.id)

    assert summary["total_events"] == 2
    assert summary["counts_by_event_type"]["message"] == 1
    assert summary["counts_by_artifact"]["sms"] == 1
    assert summary["top_contacts"][0]["count"] == 2
    assert summary["attachment_count"] == 1
    assert summary["coverage_statuses"]["available_and_parsed"] == 1
