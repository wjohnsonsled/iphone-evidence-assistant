# FOR-013 — Candidate Manifest.db Query Hardening Profile

## Profiles and transition

- Query: `manifestdb-files-query` version 2
- Resource controls: `manifestdb-query-resource-controls` version 1
- Locator: unchanged `manifestdb-row-locator` version 1
- Decision: DEC-0061
- Status: candidate, validation pending, not Supported

Callers explicitly select v1 or v2. There is no automatic transition,
reinterpretation, migration, or fallback between versions. Every observation
retains its exact query, schema, locator, resource, reader, source, and
processing-run identities.

## Observation model

SQLite declared affinity and observed storage class are independent. Version 2
preserves raw TEXT, INTEGER, REAL, BLOB, and NULL storage observations without
coercion, trimming, normalization, reconstruction, or inference. NULL and
zero-length TEXT/BLOB remain distinct.

Default BLOB observations contain presence state, exact SQLite `length()`,
storage class, and bounded availability state, but no bytes. An internal caller
may request raw bytes only with an explicit authorization flag. Such bytes
remain run-scoped and in-memory only and may not be decoded, interpreted,
persisted, logged, hashed, or publicly exposed. DEV-0607 remains the separate
owner gate for BLOB interpretation.

## Result dimensions

Completion is one of `QUERY_COMPLETE`, `QUERY_PARTIAL`, `QUERY_FAILED`,
`QUERY_NOT_EVALUATED`, or `QUERY_INDETERMINATE`. Termination reasons, row-value
states, and resource-control observations are recorded separately. A resource
or concurrency result never establishes corruption, loss, deletion,
tampering, incompatibility, or evidentiary absence.

## Determinism and resource accounting

Logical ordering, ROWID locators, pagination, projection, states, result
structure, and fixed-input accounting are deterministic. Wall-clock,
cancellation, process termination, memory pressure, and concurrency denial are
operational controls and are exempt from cross-hardware outcome equivalence.

Projected-byte accounting uses exact UTF-8 byte length for TEXT, exact SQLite
BLOB length, eight bytes for INTEGER/REAL, zero payload bytes for NULL, and 16
bytes per locator.

`DETERMINISTIC_QUERY_MEMORY_ESTIMATE` is not process memory. Version 1 of the
resource profile uses:

- page container: 128 bytes;
- continuation token: 96 bytes;
- row envelope: 96 bytes;
- column envelope: 40 bytes per projected column;
- locator envelope: 16 bytes;
- scalar encoding: 8 bytes;
- plus projected payload bytes.

The next row is not finalized when its projected-byte or memory estimate would
exceed the caller-supplied positive ceiling. Prior observations and a
run/source/profile-bound continuation are retained.

Wall-clock measurement uses a monotonic source and records audit start/stop
timestamps separately. Processing stops between finalized observations where
practical.

## Concurrency and security

Application-level counters acquire in the fixed hierarchy PROCESS → TENANT →
CASE → EVIDENCE_SOURCE → PROCESSING_RUN and release in reverse. Evidence-source
and processing-run ceilings are one; process, tenant, and case ceilings are
caller supplied. No production ceiling is implicit. Denial returns no row
observations and discloses only the enforcement scope.

All access requires an exactly scoped compatible schema result and verified
controlled copy. Continuations bind tenant, case, evidence source, artifact,
database identity, processing run, query ID, and query version. No host paths,
temporary paths, stacks, raw values in errors, or other workload details are
returned.

## Limitations

This profile is based solely on deterministic synthetic fixtures. It does not
establish Apple compatibility, backup or inventory completeness, artifact
meaning, parser behavior, production capacity, actual memory use, API safety,
or support. It creates no parser, registry entry, supported record,
persistence, file reconstruction, physical resolution, AI/reporting output,
deployment authority, or real-evidence authority.
