"""Persistence mapping and deduplication tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import Case
from app.services.evidence_persistence import EvidenceEngineResult, EvidencePersistenceService, derive_event_fingerprint


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        yield db


def sample_result() -> EvidenceEngineResult:
    return EvidenceEngineResult(
        normalized_events=[
            {
                "event_id": "evt-1",
                "event_type": "message",
                "event_category": "communications",
                "timestamp": datetime(2026, 6, 25, 16, 32, tzinfo=timezone.utc),
                "description": "Incoming message",
                "source_artifact": "sms",
                "source_database": "sms.db",
                "source_table": "message",
                "source_rowid": "1",
                "confidence_score": 90,
                "confidence_basis": "Direct database record with timestamp",
                "raw_values": {"body": "redacted fixture"},
                "conversation_key": "chat-1",
                "contact_key": "+15551234567",
            }
        ],
        coverage_records=[],
    )


def test_persist_result_inserts_events_and_skips_duplicates(session: Session) -> None:
    case = Case(name="Test")
    session.add(case)
    session.commit()

    service = EvidencePersistenceService()
    first = service.persist_result(session, case.id, None, sample_result())
    session.commit()
    second = service.persist_result(session, case.id, None, sample_result())
    session.commit()

    assert first.inserted_events == 1
    assert second.inserted_events == 0
    assert second.skipped_duplicate_events == 1


def test_fingerprint_is_deterministic() -> None:
    case_id = uuid4()
    event = {
        "source_database": "sms.db",
        "source_table": "message",
        "source_rowid": "1",
        "event_type": "message",
        "timestamp": "2026-06-25T16:32:00Z",
    }

    assert derive_event_fingerprint(case_id, event) == derive_event_fingerprint(case_id, event)


def test_persistence_rolls_back_on_invalid_record(session: Session) -> None:
    case = Case(name="Test")
    session.add(case)
    session.commit()
    result = EvidenceEngineResult(normalized_events=[{"timestamp": "2026-06-25T16:32:00Z"}])

    with pytest.raises(ValueError):
        EvidencePersistenceService().persist_result(session, case.id, None, result)
