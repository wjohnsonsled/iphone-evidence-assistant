# DEV-0206 — Intake Audit-Event Model Acceptance

- Status: COMPLETE — WP-0200 package review pending
- Dependency: DEV-0203 complete
- Architecture: ARC-001, ARC-002, DEC-0011
- Implementation authority: WP-0250 `AuditEventType` and
  `AppendOnlyAuditService`
- Support effect: none

## Scope reconciliation

WP-0250 is the sole audit authority. DEV-0206 adopts its closed taxonomy and
append-only service for registered intake evidence and adds no parallel event
model. Operational logs and deterministic stage-result dictionaries remain
distinct from these audit records.

## Requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0206-R01 | Reuse the closed WP-0250 taxonomy | AC-01 all required intake validation, hash, controlled-copy, lifecycle, and system-failure event types exist; no intake-only enum is introduced |
| DEV-0206-R02 | Scope every event completely | AC-02 each event records tenant, case, evidence UUID, actor, correlation, UTC time, result, and optional closed failure code |
| DEV-0206-R03 | Make service history append-only | AC-03 appends allocate ordered sequence and distinct IDs; reads return immutable tuples and records are frozen |
| DEV-0206-R04 | Record success and failure distinctly | AC-04 validation completion, validation failure, controlled-copy verification, cleanup failure, hash success, and hash failure remain typed and distinguishable |
| DEV-0206-R05 | Preserve tenant/case association | AC-05 events use the registered evidence object's tenant/case/evidence identifiers rather than caller-supplied substitutes |
| DEV-0206-R06 | Avoid sensitive diagnostic storage | AC-06 the model accepts a controlled failure code, not raw exception or evidence-content fields |
| DEV-0206-R07 | Preserve boundaries | AC-07 synthetic objects only; no API, parser, persistence, real evidence, or support promotion |

## Validation record

All seven criteria pass in `backend/tests/test_intake_audit.py` and the existing
WP-0250 integrity suite. The task-specific suite verifies the complete intake
taxonomy subset, immutable ordered history, evidence-derived scoping,
correlation, timezone-aware timestamps, and distinct success/failure records.

## Limitations

- This is an in-memory application reference service, not durable,
  transactional, storage-media-immutable audit persistence.
- It makes no legal chain-of-custody, digital-signature, sealing, or
  nonrepudiation claim (RSK-0009).
- Actor authorization and database-enforced tenant isolation remain Phase 3
  work.

## Commands and results

- `python -m pytest backend/tests/test_intake_audit.py backend/tests/test_integrity_infrastructure.py -q`
  — 13 passed.
- `python -m pytest backend/tests -q` — 137 passed with the previously accepted
  third-party TestClient deprecation warning.
- `python -m unittest discover -s tests -q` — 5 passed.
- `python -m compileall -q backend/app backend/tests` — passed.
- `git diff --check` — passed.
