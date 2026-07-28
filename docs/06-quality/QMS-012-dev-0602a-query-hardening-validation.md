# QMS-012 — DEV-0602A Query Hardening Validation

## Scope

This package validates candidate `manifestdb-files-query` v2 and
`manifestdb-query-resource-controls` v1 under DEC-0061. It does not revalidate
or modify the COMPLETE version 1 profile.

## Results

The synthetic suite validates explicit v2 selection, bounded default BLOB
projection, internal authorization denial, raw dynamic SQLite storage classes,
NULL/empty distinctions, ascending ROWID pagination, exact retrieval,
cross-scope/profile token denial, projected-byte and fixed-memory estimates,
controlled monotonic timeout, cancellation, hierarchical concurrency denial,
WITHOUT ROWID denial, source immutability, and zero registry/store entries.

Validation completed:

- DEV-0602A focused: 13 passed;
- combined schema/query suite: 40 passed;
- backend regression: 447 passed with the previously accepted TestClient
  deprecation warning;
- legacy characterization: 5 passed;
- compilation: passed;
- exact dependency-lock validation and `pip check`: passed;
- Alembic head `0005_processing_idempotency`, history, and offline upgrade SQL:
  passed;
- repository hygiene and diff checks: passed.

## Limitations

- Fixtures are synthetic and not Apple-produced.
- Deterministic memory is a query-layer estimate, not process memory.
- Wall-clock and concurrency outcomes are operational and environment-sensitive.
- Concurrency is application-level and not distributed.
- Production ceilings, workload performance, live PostgreSQL, public API,
  persistence, deployment, and real-evidence behavior are unvalidated.
- Internal raw BLOB availability is not decoding, interpretation, or support.
- DEV-0607 remains the mandatory BLOB-interpretation gate.
- No parser, artifact, input, workflow, API, Apple compatibility, or capability
  is Supported.
