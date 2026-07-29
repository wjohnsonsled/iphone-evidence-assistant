# QMS-015 — DEV-0605 Relative-Path Validation

Candidate validation of `manifestdb-relative-path-lexical` version 1 with
synthetic fixtures only.

Validation results:

- focused lexical and query-integration suite: 23 passed;
- combined Manifest suite: 136 passed;
- backend regression: 543 passed with the unchanged accepted TestClient warning;
- legacy characterization: 5 passed;
- compilation, exact dependency lock, `pip check`, Alembic single
  head/history/offline SQL, hygiene, and diff checks: passed;
- migration head: `0005_processing_idempotency`; new migrations: none.

Permanent limitations are recorded in FOR-016. No filesystem lookup, path
joining, symlink resolution, physical inventory, evidence hashing, parser,
registry entry, supported record, API, real evidence, deployment, or support
promotion exists. Supported registry/store counts remain zero.
