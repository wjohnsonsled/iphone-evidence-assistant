# FOR-003 — Apple Local Backup Ingestion Boundaries

## 1. Status

- Scope: Phase 2 task boundaries
- Architecture: ARC-001
- Current implementation task: DEV-0210 validation pending
- Input support effect: none

## 2. Governing principle

Intake is a sequence of independently validated, fail-closed stages. Passing an
earlier stage never implies that a later stage passed and never establishes
that an input is a supported Apple local backup.

## 3. Phase 2 responsibilities

| Task | Responsibility | Explicit non-claim |
|---|---|---|
| DEV-0201 | Adapt a bounded filesystem directory into a typed inspection result | Does not validate Apple backup structure |
| DEV-0202 | Validate candidate structure and collect the sole approved encryption observation | Does not establish production compatibility or support |
| DEV-0203 | Project that observation into a typed detection/reporting state | Does not decrypt encrypted content or inspect another signal |
| DEV-0204 | Adopt the WP-0250 SHA-256 registry for intake | Does not create a competing hash authority or establish authenticity |
| DEV-0205 | Provide the general controlled SQLite working-copy service | Does not authorize direct source parsing |
| DEV-0206 | Adapt intake events to the WP-0250 audit taxonomy | Does not make operational logs immutable audit records |
| DEV-0207 | Adapt intake provenance to the WP-0250 relational model | Does not make an input or artifact supported |
| DEV-0208 | Verify cleanup and recover from intake failures | Does not silently discard cleanup failures |
| DEV-0209 | Enforce intake resource and denial-of-service limits | Does not establish production capacity |
| DEV-0210 | Validate the integrated intake package synthetically | Does not authorize real evidence or production exposure |

## 4. DEV-0201 boundary

DEV-0201 may inspect path metadata and count top-level directory entries. It
must not read file contents, recurse, parse, hash, copy, modify, or classify
Apple backup structure or encryption.

Its ready outcomes mean only that the filesystem adapter completed and may hand
the candidate to DEV-0202. An empty directory is a successful zero-result
adapter inspection but will not satisfy later Apple backup structure
validation.

The adapter must preserve the original submitted value and record resolved,
root-confined provenance. It must reject path escape and symlink/reparse
boundaries and convert operational filesystem errors into an explicit
processing-failure outcome.

## 5. Source immutability

Every intake stage is read-only against the submitted source. Future SQLite
parsing must occur only from controlled, verified working copies. A path check
is not an immutability guarantee; subsequent tasks must add evidence-source
registration, hashing, working-copy creation, and audit persistence.

## 6. Current limitations

- No input is currently supported.
- Apple backup structural validation is implemented only against synthetic
  candidate fixtures; production compatibility is unvalidated.
- Encryption detection/reporting is implemented as a non-persistent,
  non-API projection; it is not a support claim.
- Source-file hashing, controlled copies, audit, provenance, cleanup recovery,
  and resource policy have validated shared candidate implementations.
  Persistent production intake orchestration is not implemented; DEV-0210
  composition exists only in deterministic synthetic tests.
- Tenant, authorization, evidence-source, and audit persistence are not
  implemented.
- DEV-0201 adapter output is not eligible for evidence storage, search, AI,
  citations, reports, or supported coverage calculations.
- DEV-0201 path validation does not eliminate filesystem time-of-check/time-of-use
  risk; later evidence-source intake must bind processing to a registered,
  immutable source and verified working copy.
## DEV-0501 candidate discovery boundary

Profile `apple-local-backup-top-level-discovery` version 1 observes only the
authorized top-level Manifest.db and three governed plists. Manifest.db remains
pending controlled structural and DEV-0601 schema validation. Plist claims are
source-specific; field conflicts default unresolved. Root names are not device
identity. Discovery is not parsing, compatibility, completeness, or support.
