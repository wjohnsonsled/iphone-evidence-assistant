# DEV-0202 — Apple Backup Validation Acceptance Criteria

## 1. Document control

- Task: DEV-0202
- Date: 2026-07-27
- Status: VALIDATION_PENDING — STAGE-B OWNER REVIEW
- Dependencies: DEV-0201, DEC-0006
- Compatibility profile: FOR-007, proposed
- Input/artifact support effect: none
- Migration authorization: none

## 2. Two-stage task gate

### Stage A — Authorized now

- prepare FOR-007 for owner review;
- implement a schema-neutral controlled-copy mechanism;
- demonstrate read-only SQLite access and integrity checking on synthetic
  SQLite fixtures;
- record hashing, companion relationships, cleanup, and audit data.

### Stage B — Authorized with one unresolved classification conflict

- implement the approved Apple identity, completeness, encryption, schema,
  version, and final classification rules using synthetic fixtures only.

Stage B must not expose the validator through an API or make an input-support
claim. DEC-0008 resolved the identity/database-validity conflict.

## 3. Controlled-copy requirements

| Requirement ID | Requirement |
|---|---|
| DEV-0202-R01 | Copy only a caller-specified SQLite main file and present exact-name `-wal`, `-shm`, and `-journal` companions |
| DEV-0202-R02 | Require the main and companions to be regular, link-free files within the declared evidence source |
| DEV-0202-R03 | Record source and working paths, sizes, pre-copy source SHA-256, copied SHA-256, and post-copy source SHA-256 |
| DEV-0202-R04 | Require all three hashes to match for every file and fail closed otherwise |
| DEV-0202-R05 | Require the companion set to remain unchanged across copying |
| DEV-0202-R06 | Create the workspace outside the evidence source in an approved temporary root |
| DEV-0202-R07 | Preserve companion basenames in a single working directory |
| DEV-0202-R08 | Open SQLite only from the controlled copy using URI read-only mode, private cache, immutable frozen-copy semantics, and query-only behavior |
| DEV-0202-R09 | Prohibit writes, schema changes, `VACUUM`, repair, checkpointing, and source SQLite access |
| DEV-0202-R10 | Verify controlled-copy hashes again after SQLite use |
| DEV-0202-R11 | Delete the workspace on context exit unless explicit test retention is enabled |
| DEV-0202-R12 | Record cleanup success, failure, or explicit test retention in deterministic audit data |
| DEV-0202-R13 | On copy, verification, SQLite-open, or cleanup failure, return/raise a structured safe failure with audit data and no unsupported conclusion |
| DEV-0202-R14 | Use no legacy code, Apple schema names, Apple version values, or production API integration |
| DEV-0202-R15 | Use synthetic fixtures only |

## 4. Measurable Stage-A acceptance criteria

| Criterion | Requirement mapping |
|---|---|
| AC-01 — main-only copy records matching pre/copy/post hashes | DEV-0202-R01; R03; R04 |
| AC-02 — all three companion types retain exact names and relationships | DEV-0202-R01; R05; R07 |
| AC-03 — links, non-files, out-of-source paths, and missing main fail closed | DEV-0202-R02; R13 |
| AC-04 — source mutation during copy is detected and copy fails closed | DEV-0202-R03; R04; R13 |
| AC-05 — companion-set mutation during copy is detected | DEV-0202-R05; R13 |
| AC-06 — workspace is outside the evidence source | DEV-0202-R06 |
| AC-07 — read-only SQLite connection reads schema/integrity but rejects writes | DEV-0202-R08; R09 |
| AC-08 — controlled-copy file hashes are unchanged after SQLite validation | DEV-0202-R10 |
| AC-09 — normal context exit deletes workspace and records success | DEV-0202-R11; R12 |
| AC-10 — injected cleanup failure is recorded and surfaced | DEV-0202-R12; R13 |
| AC-11 — explicit test retention records retained state | DEV-0202-R11; R12 |
| AC-12 — audit record is deterministic with injected clock/correlation ID | DEV-0202-R03; R12 |
| AC-13 — static boundary test finds no legacy or Apple compatibility assumptions | DEV-0202-R14 |
| AC-14 — backend and legacy characterization regression suites pass | DEV-0202-R15 |
| AC-15 — no migration, API route, parser, artifact, or input support change | DEV-0202-R14 |
| AC-16 — FOR-007 labels every rule basis and lists every unresolved owner decision | DEC-0006 |

## 5. Synthetic fixture plan

- minimal SQLite database created in a temporary directory;
- SQLite WAL fixture created through SQLite operations, with copied companion
  bytes treated only as a relationship fixture;
- synthetic `-shm` and `-journal` companion byte files where SQLite does not
  retain them deterministically;
- mutation injected only into temporary synthetic files;
- cleanup failure injected through a test cleanup function, followed by test
  cleanup;
- no Apple-produced plist, database, or backup data.

## 6. Stage-A completion gate

Stage A reaches `VALIDATION_PENDING` when AC-01 through AC-16 pass. DEV-0202
does not become `COMPLETE` until FOR-007 is approved and the separately
authorized Stage-B classifier passes its acceptance criteria.

## 7. Stage-A validation record

All AC-01 through AC-16 passed on 2026-07-27.

- `python -m pytest backend/tests/test_controlled_copy.py -q`: 12 passed.
- `python -m pytest backend/tests -q`: 38 passed, with the previously accepted
  third-party `TestClient` deprecation warning.
- `python -m unittest discover -s tests`: 5 passed.
- `python -m compileall -q backend/app`: passed.
- `python -m pip install -e backend --no-deps`: passed and refreshed package
  source metadata.
- `git diff --check`: passed before commit.

The fixtures were generated entirely in test temporary directories. No client
evidence, Apple-produced backup, legacy parser, migration, or production API
route was used or changed.

## 8. Stage-B acceptance and validation record

Stage B requires the nine approved distinct outcomes, independent plist
identity, required-file and `SnapshotState` checks, Boolean `IsEncrypted`
handling, controlled-copy-only SQLite integrity inspection,
`MANIFEST_FILES_V1`, canonical schema fingerprinting, explicit provenance,
observations and limitations, and no API/artifact parsing/support promotion.

Deterministic tests cover valid encrypted and unencrypted candidates; invalid
adapter inputs; non-Apple and indeterminate identity; every missing required
plist; malformed plists; snapshot and encryption states; invalid SQLite with
and without independent identity; integrity failure; absent `Files`; each
required column absent; compatible added tables/columns; cleanup failure;
schema-fingerprint determinism; and production/legacy boundary isolation.
Stage-A tests continue to cover source mutation, companion-set mutation, hash
mismatch, links/reparse points, path escape, and controlled-copy cleanup.

Validation on 2026-07-27:

- focused Stage-B tests: 26 passed;
- full backend suite: 64 passed with one accepted third-party deprecation
  warning;
- legacy characterization: 5 passed;
- compilation: passed;
- migrations: none.

All behavior remains synthetic characterization. A production compatibility
claim requires the separately approved Apple-produced validation package.
