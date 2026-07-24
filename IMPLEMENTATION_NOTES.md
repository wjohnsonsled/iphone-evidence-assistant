# Implementation Notes

## Short Implementation Plan

1. Add a `backend/` Python project with FastAPI, SQLAlchemy 2.x models,
   Pydantic v2 schemas, repositories, services, Alembic, Docker, and tests.
2. Keep `evidence_engine` independent from SQLAlchemy. The backend will adapt
   engine domain objects into database rows through an
   `EvidencePersistenceService`.
3. Implement synchronous processing first. The processing service will expose a
   single method that can later be called by a background worker without
   changing persistence or route handlers.
4. Restrict processing to configured server-local evidence roots using resolved
   paths and simple supported-backup structure checks.
5. Preserve evidence-engine coverage distinctions in JSON details while mapping
   coverage rows into a small API-friendly status vocabulary.
6. Add deterministic summaries and tests using mocked/sanitized evidence-engine
   results so CI does not require a real iPhone backup.

## Architectural Decisions

- SQLAlchemy is used only in the backend layer. `evidence_engine` remains a
  domain/parser/reporting package.
- UUID primary keys are used for all public resources.
- Raw evidence values are only returned from the evidence-detail endpoint, not
  list or summary endpoints.
- Processing is synchronous for the MVP, but the orchestration lives in
  `CaseProcessingService` rather than in API route handlers.
- Deduplication uses a deterministic fingerprint stored in `artifact_hash`;
  no unique database constraint is added yet to avoid incorrectly merging
  distinct forensic records.

## Assumptions

- `backup_path` refers to a decrypted local backup or extracted case directory
  already present under `EVIDENCE_ROOT`.
- The first device row for a case is sufficient for this MVP.
- Full PostgreSQL integration is exercised through Docker/local development;
  unit tests use mocked engine output and repository/service boundaries.

## Limitations

- No frontend, authentication, upload workflow, queue, Redis, embeddings, or
  OpenAI integration is included.
- The refactored evidence engine still delegates most logic to
  `evidence_engine._legacy`.
- Local bundled Python in this Codex environment is missing several declared
  backend dependencies, so full API/import test execution requires installing
  `backend[dev]` or using Docker.

## Known Technical Debt

- Add private golden-file tests against sanitized real backup outputs.
- Promote frequently queried JSONB fields into typed columns as usage patterns
  settle.
- Add a real background worker only when processing duration or concurrency
  requires it.

## Recommended Next Task

Add a sanitized miniature decrypted-backup fixture and an integration test that
runs the real engine end-to-end against PostgreSQL in Docker.
