# FOR-008 — Evidence Integrity Infrastructure Specification

## Status and limitations

- WP-0250 implementation specification.
- Application controls only; not physical write blocking.
- Application handling history only; not a legal-sufficiency,
  digital-signature, sealing, or nonrepudiation claim.
- Relational MVP; no graph database.
- No parser, input, artifact, workflow, report, export, or API support effect.

## Evidence identity and hash policy

Evidence identity is an application-generated UUIDv4. It is stable after
registration and independent of path, filename, logical label, and bytes.
Equal content retains distinct evidence UUIDs and handling histories.

SHA-256 is required. Each attempt appends an immutable observation containing
tenant, case, evidence UUID, purpose, role, bytes, time, actor, component and
version, success/failure, and digest or failure code. Observations are never
updated. Verification compares two observations; mismatch, source instability,
missing/failed hashing, and verified content remain distinct.

## Lifecycle transition table

| From | Permitted targets |
|---|---|
| REGISTERED | VALIDATING, QUARANTINED, REJECTED, FAILED |
| VALIDATING | VALIDATED, QUARANTINED, FAILED, REJECTED |
| VALIDATED | HASH_VERIFIED, QUARANTINED, FAILED |
| HASH_VERIFIED | PROCESSING, QUARANTINED, FAILED |
| PROCESSING | DERIVED_RECORDS_CREATED, QUARANTINED, FAILED |
| DERIVED_RECORDS_CREATED | REPORTABLE, QUARANTINED, FAILED |
| REPORTABLE | ARCHIVED, QUARANTINED |
| FAILED | QUARANTINED, ARCHIVED |
| QUARANTINED | none |
| ARCHIVED | none |
| REJECTED | none |

Every permitted transition appends `LIFECYCLE_TRANSITION`. Every denial appends
`LIFECYCLE_TRANSITION_DENIED`; the original object remains unchanged.

## Access and lock policy

Approved intents are metadata inspection, hashing, controlled-copy creation and
inspection, integrity verification, controlled-copy parsing, and approved
archive. No approved service offers source modify, overwrite, rename,
truncate, repair, recovery, checkpoint, vacuum, schema change, in-root
temporary creation, deletion, or link traversal. Locks coordinate application
operations only. Conflict, non-owner release, and ineligible stale release fail
closed.

## Audit taxonomy

The closed `AuditEventType` taxonomy in
`backend/app/integrity/domain.py` contains the 28 WP-0250 families for
registration, validation, hashes, controlled copies, locks, lifecycle, parser
execution, records, provenance, policy, exports, reports, AI, archive, and
system failure. Events are immutable and append-only through the service.

## Chain-of-custody specification

Handling events record tenant, case, evidence UUID, actor/type, action,
timezone-aware UTC time, component/version, environment, purpose, result,
failure code/safe detail, correlation, before/after hash references, related
audit event, sequence, and prior event. The service exposes append and read
operations only.

## Relational provenance model

Nodes cover tenant, case, evidence source, source artifact, controlled copy,
processing run, parser execution, normalized record, timeline, citations, and
export. Edges use the ten controlled relationship types in ARC-002.
Service validation rejects dangling nodes, tenant/case crossing, parser-derived
edges without parser identity/version, and cycles for derivation, copying,
normalization, and supersession. A record/citation is eligible only when a
deterministic path resolves to its source node.

## Parser contract

Every candidate parser declares identity, version, artifact family, registry
state, schema profiles, validation, parse, coverage, limitations, and
self-test. Controlled context carries input identity, schema profile, integrity
decision, provenance report, write capability, and legacy status.

The harness rejects missing identity/version/profile, unverified integrity,
broken provenance, writable source, legacy input, unsupported profile,
non-candidate registry state, incomplete provenance, unreconciled coverage,
silent omissions, missing limitations, or failed self-test. Conformance always
reports `NONE_CANDIDATE_ONLY`; it cannot confer support.
