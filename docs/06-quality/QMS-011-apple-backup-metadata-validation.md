# QMS-011 — Candidate Apple Backup Metadata Validation

## Package

- Work package: WP-0500 Apple Backup Metadata
- Tasks: DEV-0501 through DEV-0509
- Status: COMPLETE candidate infrastructure
- Owner approval: DEC-0058
- Support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`
- Supported Parser Registry entries: 0
- Supported normalized records: 0

## Validated candidate behavior

The package provides:

- root-confined discovery of the four governed top-level metadata targets;
- source-specific projections for three Info.plist fields,
  `Manifest.plist.IsEncrypted`, and `Status.plist.SnapshotState`;
- exact source reconciliation with conflicts preserved;
- lossless class-specific identifier normalization profile version 1;
- lossless dotted-numeric product-version normalization profile version 1;
- exact raw, canonical-text, component-sequence, and authorized ordering
  comparisons without fuzzy repair or trailing-zero padding;
- DEV-0406 transformation provenance;
- factual six-item metadata coverage with exact state counts;
- a six-case deterministic synthetic fixture corpus.

## Validation results

- integrated WP-0500 focused suite: 52 passed;
- latest full backend regression: 407 passed with one accepted TestClient
  deprecation warning;
- legacy characterization: 5 passed;
- compilation: passed;
- exact dependency-lock validation: passed;
- installed-package consistency: passed;
- Alembic single head: `0005_processing_idempotency`;
- offline PostgreSQL migration SQL: passed;
- repository diff and hygiene checks: passed.

No migration was added by WP-0500.

## Evidence-integrity and security implications

Raw observations remain separately addressable and are never overwritten.
Every normalized value retains source artifact, field, reader, processing-run,
profile, method, timestamp, and limitations. Cross-tenant, cross-case,
cross-source, and cross-run mismatches fail closed. Discovery remains
root-confined and read-only. No production API or persistence composition was
added.

## Active limitations and unresolved risks

- The fixture corpus is synthetic and not Apple-produced.
- No real evidence was processed and no user-content artifact was parsed.
- The candidate Apple compatibility profile remains unapproved for production
  and unvalidated across Apple-produced multi-version backups.
- Manifest.db receives header presence recognition only. DEV-0601 remains the
  schema-profile compatibility gate.
- Metadata presence, `SnapshotState`, and coverage do not prove backup, device,
  acquisition, or evidentiary completeness.
- A missing value or file does not prove deletion, concealment, destruction,
  spoliation, or absence from the device.
- A backup-root name is non-authoritative and may have been renamed.
- Canonical identifier agreement does not prove physical-device identity,
  attribution, authenticity, or exclusive association.
- Product-version ordering does not establish Apple, schema, parser, or
  artifact compatibility.
- `Manifest.plist.IsEncrypted` remains the sole approved encryption signal;
  secondary indicators remain deferred to DEV-0211.
- No live PostgreSQL, production repository, production concurrency, API,
  deployment, real-evidence, or attorney-facing validation occurred.
- The accepted TestClient warning remains.

## Owner disposition and continuing boundary

DEC-0058 approves WP-0500 and DEV-0509 as COMPLETE candidate metadata
infrastructure with every limitation above retained.

This approval authorizes later candidate architectural use only. It does
not approve the Apple compatibility profile for production, classify Apple
local backups or metadata as Supported, activate a parser, populate the
Supported Parser Registry or supported normalized store, expose an API,
authorize real evidence, deploy, or promote support.

Any future support promotion requires an Apple-produced multi-version
validation package and a separate owner decision containing the permanent
promotion references required by QMS-SUP-001.

Post-approval governance revalidation on 2026-07-28: 52 integrated WP-0500
tests passed; 407 backend regression tests passed with the accepted TestClient
warning; 5 legacy characterization tests passed; compilation and repository
diff checks passed.
