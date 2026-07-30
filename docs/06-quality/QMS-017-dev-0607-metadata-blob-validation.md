# QMS-017 — DEV-0607 Metadata-BLOB Validation

Candidate validation of `manifestdb-file-bplist-syntax` version 1 using
deterministic synthetic binary plists only.

Validation results:

- focused syntactic, malformed, resource, cancellation, serialization, and
  query-integration suite: 19 passed;
- combined Manifest suite: 172 passed;
- backend regression: 579 passed with the unchanged accepted TestClient warning;
- legacy characterization: 5 passed;
- compilation, exact dependency lock, `pip check`, Alembic single
  head/history/offline SQL, hygiene, and diff checks: passed;
- migration head: `0005_processing_idempotency`; new migrations: none.

Permanent limitations are in FOR-018. No native deserializer, `plistlib`,
dynamic loading, class instantiation, filesystem access, metadata-field
meaning, parser, registry entry, supported record, API, real evidence,
deployment, or support promotion exists. Registry/store counts remain zero.
