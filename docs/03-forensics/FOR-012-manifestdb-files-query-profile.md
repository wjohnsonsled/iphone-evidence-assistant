# FOR-012 — Candidate Manifest.db Files Query Profile

## Profiles

- Query: `manifestdb-files-query` version 1
- Locator: `manifestdb-row-locator` version 1
- Owner decision: DEC-0060
- Status: candidate raw-observation infrastructure
- Support effect: none

DEV-0602 treats each Files row as an immutable raw source observation. It is
not an artifact parser and makes no evidentiary interpretation.

## Authorized operations

Version 1 permits only:

- enumerate rows;
- retrieve one row by exact ROWID locator;
- deterministic ascending-ROWID ordering;
- locator-based continuation strictly after the last successful ROWID;
- projection of `fileID`, `domain`, `relativePath`, `flags`, and `file`.

There are no joins, aggregations, offset paging, temporary tables, schema
operations, writes, modification PRAGMAs, repair, replay, checkpoint, vacuum,
reindex, optimize, reconstruction, or decoding.

## Locator and continuation

`ROW_LOCATOR_V1` contains the locator type/value/version/confidence, source
table, and processing-run identity. ROWID is stable only for the controlled
input during that processing run. It is not an acquisition identity or
cross-run universal identifier.

WITHOUT ROWID produces `ROW_LOCATOR_UNAVAILABLE`; no key is synthesized.
Duplicate or nonmonotonic locators produce `ROW_LOCATOR_DUPLICATE` and stop
enumeration. A continuation token contains only the last locator, query-profile
version, and processing-run identity—never evidence values or row content.

## Raw typed observations

Each approved column independently records:

- `VALUE_PRESENT`;
- `VALUE_NULL`;
- `VALUE_EMPTY`;
- `TYPE_MISMATCH`;
- `NOT_PROJECTED`;
- `NOT_AVAILABLE`;
- `READ_FAILURE`.

No coercion occurs. In particular, the `file` BLOB remains raw bytes and is not
decoded or interpreted. DEV-0607 remains the separate metadata-blob
characterization task.

## Control and failure behavior

Execution requires an exact compatible DEV-0601 result for the same
tenant/case/source/artifact/database/run and a verified DEV-0205 controlled
copy. SQLite uses immutable private read-only/query-only access. Caller-supplied
positive page, per-operation row, and SQLite-work ceilings are mandatory; no
production ceiling is implicit.

Cancellation and failures preserve prior immutable row observations. Schema,
scope, controlled-copy, read, resource, locator, and cancellation outcomes are
explicit and safe.

## Limitations

Enumeration does not establish inventory, backup, acquisition, artifact, or
evidentiary completeness. Raw values do not establish file existence,
authenticity, meaning, or support. The implementation and synthetic fixtures
do not authorize a parser, registry entry, supported record, production use,
real evidence, API, deployment, or support promotion.

## Immutable version and successor boundary

DEC-0061 confirms that version 1 remains immutable and COMPLETE under
DEC-0060. Its raw `file` BLOB bytes may exist only as an in-memory immutable
observation: no decoding, interpretation, persistence, logging, hashing,
public API, or user-content conclusion is authorized. The separately selected
candidate version 2 behavior is defined in FOR-013 and cannot be silently
substituted for version 1.
