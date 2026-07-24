"""FastAPI endpoint tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_session
from app.main import app
from app.models import Case, EvidenceEvent


def make_client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session():
        with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.state.test_session_local = SessionLocal
    return TestClient(app)


def test_create_get_list_detail_and_summary() -> None:
    client = make_client()
    created = client.post("/api/v1/cases", json={"name": "API case", "description": "fixture"}).json()
    case_id = created["id"]

    SessionLocal = app.state.test_session_local
    with SessionLocal() as session:
        case = session.get(Case, UUID(case_id))
        session.add(
            EvidenceEvent(
                case_id=case.id,
                event_type="message",
                category="communications",
                timestamp=datetime(2026, 6, 25, 16, 32, tzinfo=timezone.utc),
                summary="Incoming message",
                details_json={"description": "Incoming message"},
                raw_values_json={"body": "fixture"},
                source_artifact="sms",
                source_database="sms.db",
                source_record_id="1",
                confidence_score=90,
                confidence_basis_json={"basis": "Direct"},
                conversation_key="chat-1",
                contact_key="+15551234567",
            )
        )
        session.commit()

    assert client.get(f"/api/v1/cases/{case_id}").status_code == 200
    listed = client.get(f"/api/v1/cases/{case_id}/evidence?event_type=message").json()
    assert listed["total"] == 1
    evidence_id = listed["items"][0]["id"]
    detail = client.get(f"/api/v1/cases/{case_id}/evidence/{evidence_id}").json()
    assert detail["raw_values_json"]["body"] == "fixture"
    summary = client.get(f"/api/v1/cases/{case_id}/summary").json()
    assert summary["total_events"] == 1


def test_invalid_case_returns_structured_error() -> None:
    client = make_client()
    response = client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "case_not_found"
