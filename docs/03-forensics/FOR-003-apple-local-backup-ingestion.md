# FOR-003 — Apple Local Backup Ingestion Boundaries

## 1. Status

- Scope: Phase 2 task boundaries
- Architecture: ARC-001
- Current implementation task: DEV-0201 complete; DEV-0202 blocked pending
  owner clarification recorded in DEC-0005
- Input support effect: none

## 2. Governing principle

Intake is a sequence of independently validated, fail-closed stages. Passing an
earlier stage never implies that a later stage passed and never establishes
that an input is a supported Apple local backup.

## 3. Phase 2 responsibilities

| Task | Responsibility | Explicit non-claim |
|---|---|---|
| DEV-0201 | Adapt a bounded filesystem directory into a typed inspection result | Does not validate Apple backup structure |
| DEV-0202 | Validate the required Apple local backup structure | Does not detect or decrypt encryption |
| DEV-0203 | Detect and report encryption state | Does not decrypt encrypted content |
| DEV-0204 | Parse approved backup metadata plist profiles | Does not authorize other plist parsing |
| DEV-0205 | Parse approved `Manifest.db` schema profiles from controlled working copies | Does not authorize unknown schemas or direct source parsing |
| DEV-0206 | Build deterministic backup inventory | Does not prove on-device completeness |
| DEV-0207 | Generate and retain required source/material hashes | Does not silently omit hash failures |
| DEV-0208 | Reconcile manifest entries to stored backup files | Does not treat missing files as no-record evidence |
| DEV-0209 | Produce explicit intake coverage | Does not convert failure into zero results |
| DEV-0210 | Persist structured processing errors and omissions | Does not expose secret or unsafe diagnostic content |

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
- Apple backup structural validation is not implemented.
- Encryption detection is not implemented.
- Source-file hashing and controlled working copies are not implemented.
- Tenant, authorization, evidence-source, and audit persistence are not
  implemented.
- DEV-0201 adapter output is not eligible for evidence storage, search, AI,
  citations, reports, or supported coverage calculations.
- DEV-0201 path validation does not eliminate filesystem time-of-check/time-of-use
  risk; later evidence-source intake must bind processing to a registered,
  immutable source and verified working copy.
