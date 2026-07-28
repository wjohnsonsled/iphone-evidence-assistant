# DEV-0602A — Files-Table Query Hardening and Resource-Control Profile

- Status: VALIDATION_PENDING
- Dependency: DEV-0602 — COMPLETE
- Owner decision: DEC-0061
- Validation package: QMS-012
- Support effect: none

| ID | Acceptance criterion | Requirement mapping | Result |
|---|---|---|---|
| AC-01 | Preserve query v1 and locator v1 unchanged; require explicit selection of candidate query v2. | FOR-MAN-002; FOR-MAN-003 | PASS |
| AC-02 | Default v2 BLOB observation exposes only state, length, storage class, and bounded availability; raw bytes require explicit internal authorization and remain nonpersistent and uninterpreted. | FOR-MAN-003 | PASS |
| AC-03 | Preserve raw SQLite values, declared affinity, observed storage class, NULL, and empty states independently without coercion. | FOR-MAN-003; EVID-VAL-001 | PASS |
| AC-04 | Keep completion, termination, row state, and resource state as separate closed dimensions. | FOR-MAN-003; FAIL-OBS-001 | PASS |
| AC-05 | Deterministically account exact projected bytes and the documented fixed-overhead memory estimate; stop before adding an over-limit row. | FOR-MAN-003; SEC-RES-001 | PASS |
| AC-06 | Use monotonic wall-clock safety measurement and preserve finalized rows, last locator, audit times, usage, reason, continuation, and limitations. | FOR-MAN-003; SEC-RES-001 | PASS |
| AC-07 | Enforce process → tenant → case → evidence-source → processing-run concurrency acquisition and deny safely without observations or workload disclosure. | FOR-MAN-003; SEC-AUTH-001 | PASS |
| AC-08 | Preserve ascending ROWID keyset pagination, exact single retrieval, run/source/profile-bound continuation, and fail-closed locator behavior. | FOR-MAN-002; FOR-MAN-003 | PASS |
| AC-09 | Detect controlled-copy change, preserve prior finalized observations, and never repair, retry, coerce, skip, or switch copies. | EVID-INT-001; FOR-MAN-003 | PASS |
| AC-10 | Use synthetic fixtures only; add no API, migration, persistence, parser, registry entry, supported record, decoding, physical resolution, or support promotion. | QMS-TST-001; QMS-ACC-001; QMS-SUP-001 | PASS |
| AC-11 | Focused, integrated, regression, legacy, compilation, dependency, migration, and hygiene validation passes. | QMS-TST-002; QMS-TRC-001 | PASS |

## Validation record

The implementation is candidate query-hardening infrastructure only. Query
profile `manifestdb-files-query` v2 uses resource profile
`manifestdb-query-resource-controls` v1 and the unchanged locator profile
`manifestdb-row-locator` v1. The profile is not active by default and cannot be
silently substituted for v1.

No migration was added. No real or Apple-produced evidence was used. No BLOB
was decoded, interpreted, persisted, logged, hashed, or publicly exposed.
Supported registry entries and supported normalized records remain zero.

Validation results:

- DEV-0602A focused: 13 passed;
- combined DEV-0601/DEV-0602/DEV-0602A: 40 passed;
- backend regression: 447 passed with the accepted TestClient warning;
- legacy characterization: 5 passed;
- compilation, dependency lock, package consistency, Alembic single-head,
  history/offline SQL, repository hygiene, and diff checks: passed.
