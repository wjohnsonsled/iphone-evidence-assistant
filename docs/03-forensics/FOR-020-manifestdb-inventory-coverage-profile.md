# FOR-020 — Manifest.db Inventory Coverage Profile

## Status and boundary

- Profile: `manifestdb-inventory-coverage` version 1
- Serialization: `manifestdb-inventory-coverage-canonical-json` version 1
- Implementation: `manifestdb-inventory-coverage-observer` version 1
- Status: candidate infrastructure; not Supported
- Governing decision: DEC-0075

This profile records factual coverage of a performed, authorized examination of
the logical `Files`-table row universe. It does not establish completeness of
an Apple backup, device, physical-object set, artifact family, parser,
normalized store, metadata interpretation, or user activity.

## Independent dimensions

Every observation preserves requested scope, authorized scope, examined scope,
completion, termination reason, resource state, mutation state, profile
compatibility, comparison readiness, absence eligibility, physical-inventory
state, and limitations as separate fields. A completed query cannot overwrite
or imply any other dimension.

## Required provenance

An observation binds the inventory request, tenant, case, evidence source,
source artifact, controlled copy, source database, processing run, schema
profile and fingerprint reference, query profile, locator profile,
normalization and interpretation profiles, resource profile, run sequence,
continuation locator, prior run and observation relationship, timestamp,
implementation version, and deterministic serialization version.

Query-result scope, query/resource profiles, and every finalized row's
artifact/database/run/schema/query provenance must match. Mismatch is rejected.
Observations are frozen values. Retry or continuation creates a new run and
observation.

## Completion and termination

Normal completion, partial processing, failure, cancellation, configured
resource termination, mutation termination, and indeterminate processing remain
distinct. Row, page, byte, deterministic memory-estimate, wall-clock,
concurrency, authorization, schema, controlled-copy, locator, SQLite, and
internal outcomes retain their exact classified reason.

A successful zero-row result is complete-zero and is not parser failure.
Finalized observations and the last completed locator survive partial
termination when supplied by the governed query layer.

## Continuation composition

A computed multi-run view requires:

- the declared number of unique component runs and exact sequence;
- one tenant, case, evidence source, artifact, controlled copy, and database;
- identical schema fingerprint, schema, query, locator, normalization,
  interpretation, and resource profiles;
- explicit prior-run and prior-observation links;
- the next request to begin after the prior completed locator;
- unchanged mutation state;
- continuation on intermediate components and normal completion on the final
  component.

SQLite ROWIDs may contain legitimate numeric gaps. Continuity therefore means
that the next request records the exact prior completed locator, not that the
next returned ROWID is arithmetically adjacent. A gap or overlap in the
continuation request, changed identity/profile, missing/duplicate component, or
unresolved continuation makes composition indeterminate.

Even a valid composition states only that compatible runs form one complete
logical `Files`-row universe. It never enables an absence conclusion.

## Fail-closed absence eligibility

`ABSENCE_ELIGIBLE` is only metadata for a separately approved future workflow.
It is not an absence finding. Eligibility requires an exactly defined and fully
authorized/observed universe, normal completion, no resource/cancellation/
mutation issue, compatible profiles, all required sources and Supported
interpretation layers, any required complete physical inventory, no unresolved
continuation, and no relevant exclusion.

The current production Supported Parser Registry and supported normalized store
are empty, and DEV-0608 performs no physical inventory. Consequently
artifact-level absence and completeness remain ineligible.

## Determinism and security

Canonical JSON uses stable keys, canonical tuples, explicit versions and
bounded identifiers. It contains no host or temporary paths, secrets, raw BLOBs,
or raw evidence values. Cross-tenant, cross-case, cross-source, cross-copy, and
cross-run aggregation fails closed. No global inventory index, persistence,
API, filesystem access, physical resolution, evidence hashing, or logging is
introduced.

## Permanent limitations

- Coverage describes only the performed, authorized Manifest `Files`-table
  examination.
- Manifest-row coverage is not backup, physical-object, artifact, parser,
  metadata, normalized-record, or user-activity coverage.
- No absence, deletion, missing-object, duplicate, orphan, or completeness
  conclusion is produced.
- Structural or logical completion does not establish evidentiary completeness.
- No parser, artifact, input, workflow, or capability is Supported.

