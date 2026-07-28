# DEV-0602 — Controlled Files-Table Query Layer

- Status: COMPLETE
- Dependency: DEV-0601 — COMPLETE
- Owner decision: DEC-0060
- Support effect: none

| ID | Acceptance criterion |
|---|---|
| AC-01 | Immutable query profile `manifestdb-files-query` v1 permits only enumeration, single-ROWID retrieval, locator pagination/order, and the five approved raw projections. |
| AC-02 | Immutable locator profile `manifestdb-row-locator` v1 uses ROWID only, binds locator/run/table/profile, and never depends on order/page/cursor/memory. |
| AC-03 | Only a verified DEV-0205 controlled copy with a compatible DEV-0601 result and exact scope may execute; access remains read-only/query-only and fail closed. |
| AC-04 | ROWID ordering is ascending; continuation resumes strictly after the last successful locator and tokens contain no evidence values. |
| AC-05 | WITHOUT ROWID and duplicate/nonmonotonic locators fail closed with the approved outcomes; no locator is synthesized. |
| AC-06 | Each projected `fileID`, `domain`, `relativePath`, `flags`, and `file` value is preserved raw with a distinct closed typed state and no coercion or interpretation. |
| AC-07 | Caller-supplied positive query ceilings and cancellation are mandatory; limit/cancellation/read failures preserve prior immutable observations and explicit outcome. |
| AC-08 | Results retain tenant/case/source/artifact/database/run/schema/query/locator/reader/time/limitations provenance without paths, secrets, traces, or unrelated content. |
| AC-09 | No joins, aggregation, offset pagination, writes, PRAGMA modification, temporary/schema operations, repair/replay, decoding, reconstruction, parser, API, persistence, registry/store, or support behavior exists. |
| AC-10 | Synthetic focused/integration/regression, legacy, compilation, dependency, migration, and hygiene validation passes. |

## Validation record

All AC-01 through AC-10 pass using synthetic Files rows only.

- focused DEV-0602 tests: 11 passed;
- controlled-copy/schema/query integration: 47 passed;
- full backend regression: 434 passed with the accepted TestClient warning;
- legacy characterization: 5 passed;
- compilation, dependency lock, package consistency, Alembic single-head and
  offline SQL, repository hygiene, and diff checks: passed.

No migration was added. No value was interpreted, decoded, normalized, or
persisted. Registry entries and supported normalized records remain zero.

## DEC-0061 immutable-profile clarification

DEV-0602 remains COMPLETE under DEC-0060. Query profile
`manifestdb-files-query` v1 and locator profile `manifestdb-row-locator` v1
remain immutable. Version 1 returns exact raw projected values, including raw
`file` BLOB bytes, but never decodes, interprets, persists, logs, hashes, or
publicly exposes those bytes. Its existing outcome codes remain authoritative.
Its determinism claim applies to logical query behavior; operational timing can
vary by environment. Expanded resource controls are separately tracked by
DEV-0602A and do not retroactively change this acceptance record.
