# DEV-0601 — Manifest.db Schema Profile Compatibility Framework

- Status: COMPLETE
- Dependencies: WP-0200, WP-0400, DEV-0263, DEV-0264 — COMPLETE
- Owner decision: DEC-0059
- Support effect: none

| ID | Acceptance criterion |
|---|---|
| AC-01 | Immutable profile `apple-manifestdb-schema` v1 contains the complete approved candidate table, column-affinity, constraint, fingerprint, limitation, and basis contract. |
| AC-02 | Validation accepts only a DEV-0205 verified controlled copy, uses read-only/query-only SQLite access, verifies header/page size/schema/integrity preconditions, and performs no row reads or writes. |
| AC-03 | Every required table and column receives a separate closed-state observation; optional and unknown elements are preserved. |
| AC-04 | Missing required elements, type mismatches, unknown schemas, invalid/non-SQLite/corrupt inputs, duplicate observations, non-evaluation, and indeterminacy remain distinct and fail closed. |
| AC-05 | Extra tables and columns produce compatible-with-unknown-optional-elements without being ignored or treated as support. |
| AC-06 | Canonical UTF-8 JSON and SHA-256 fingerprinting include only schema/profile data approved by DEC-0008/DEC-0059 and produce a DEV-0405 algorithm-qualified observation. |
| AC-07 | Tenant, case, source, artifact, database, run, reader, profile, timestamp, and limitations are retained; scope mismatches fail closed and diagnostics contain no paths, secrets, traces, or evidence values. |
| AC-08 | Synthetic tests cover perfect, missing table/column, extra table/column, unknown, corrupt, non-SQLite, empty, duplicate-model, type-mismatch, and mixed additions deterministically. |
| AC-09 | No rows, Properties, blobs, fileIDs, paths, domains, artifacts, or user content are inspected; no parser/API/migration/registry/store/support behavior is added. |
| AC-10 | Focused, integration, regression, legacy, compilation, dependency, migration, and hygiene checks pass. |

The profile basis is DEC-0008 and the repository’s approved synthetic
Manifest fixtures. TEXT/TEXT/TEXT/INTEGER/BLOB affinity expectations are
candidate rules, not authoritative Apple documentation. Recognition means only
that the observed schema matches this software profile.

## Validation record

All AC-01 through AC-10 pass using synthetic SQLite databases only.

- focused DEV-0601 tests: 16 passed;
- controlled-copy, validator, fingerprint, and resource integration: 68 passed;
- full backend regression: 423 passed with the accepted TestClient warning;
- legacy characterization: 5 passed;
- compilation, dependency lock, package consistency, Alembic single-head and
  offline SQL, repository hygiene, and diff checks: passed.

No migration was added. No database row or user-content value was read by the
schema validator. The Supported Parser Registry and supported normalized store
remain empty.
