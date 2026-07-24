# DEV-0201 — Apple Backup Input Adapter Acceptance Criteria

## 1. Document control

- Task: DEV-0201
- Date: 2026-07-24
- Status: complete
- Owner approval: DEC-0004, 2026-07-24
- Dependencies: DEV-0003, DEV-0004, DEV-0101
- Governing requirements: PRD-IN-001 through PRD-IN-006, FOR-INT-001,
  FOR-INT-002, FOR-PROV-001, FOR-FAIL-001, FOR-FAIL-002, SEC-INP-001,
  QMS-TST-001, QMS-TST-002, ARC-001 §§5.2, 6, and 11
- Artifact/input support effect: none
- Database migration authorization: none required

## 2. Exact scope

Implement a supported-boundary filesystem adapter that inspects a submitted
directory path without modifying or parsing its contents and returns a typed,
immutable, provenance-bearing result for DEV-0202 structure validation.

The adapter performs only:

- configured evidence-root validation;
- lexical and resolved path boundary checks;
- symlink/reparse-point rejection;
- existence and directory-type checks;
- non-recursive top-level entry counting; and
- construction of deterministic structured outcome and audit data.

It does not establish that a directory is an Apple backup.

## 3. Explicit exclusions

DEV-0201 does not:

- validate `Manifest.db`, `Manifest.plist`, `Info.plist`, `Status.plist`, or
  hashed backup file layout;
- classify incomplete, malformed, or corrupted backup structures;
- detect or decrypt encryption;
- hash source files;
- create working copies;
- open SQLite;
- inventory backup contents recursively;
- use any legacy parser, registry, runner, or normalized output;
- persist database records or add a migration;
- expose intake through the default API; or
- declare an input, parser, artifact, or workflow supported.

Those behaviors remain assigned to DEV-0202 through DEV-0210 or later approved
tasks.

## 4. Task-specific requirements

| Requirement ID | Requirement |
|---|---|
| DEV-0201-R01 | Implement the adapter in the supported backend boundary with no import or runtime dependency on legacy processing |
| DEV-0201-R02 | Validate configured evidence roots at adapter construction and fail closed for absent, non-directory, symlink, or reparse-point roots |
| DEV-0201-R03 | Return exactly the controlled outcomes `READY_FOR_STRUCTURE_VALIDATION`, `READY_ZERO_RESULTS`, `MISSING`, `UNSUPPORTED_INPUT`, `VALIDATION_FAILED`, and `PROCESSING_FAILED` |
| DEV-0201-R04 | Preserve the original submitted path and record the resolved path, matched evidence root, root-relative locator, injected UTC inspection time, correlation ID, adapter name/version, and observed entry count where available |
| DEV-0201-R05 | Reject lexical/resolved root escape and symlink/reparse-point input components as `VALIDATION_FAILED` |
| DEV-0201-R06 | Perform no file creation, deletion, mutation, parsing, hashing, or recursive traversal |
| DEV-0201-R07 | Return `MISSING` for an absent in-root path and `UNSUPPORTED_INPUT` for an existing non-directory input |
| DEV-0201-R08 | Return `READY_ZERO_RESULTS` after successful inspection of an empty directory and never treat it as failure or proof of an Apple backup |
| DEV-0201-R09 | Convert filesystem inspection errors into structured `PROCESSING_FAILED` results without exposing exception text as an evidentiary conclusion |
| DEV-0201-R10 | Produce deterministic results when filesystem state, correlation ID, and injected clock are fixed |
| DEV-0201-R11 | State explicitly in every ready result that structure, encryption, hashing, and support remain unassessed |
| DEV-0201-R12 | Use only synthetic temporary-directory fixtures and leave their contents byte-for-byte unchanged |

## 5. Acceptance-criteria traceability

| Acceptance criterion | Requirement IDs |
|---|---|
| AC-01 — controlled outcome enum is exact and closed | DEV-0201-R03; FOR-FAIL-001; FOR-FAIL-002 |
| AC-02 — valid nonempty in-root directory returns `READY_FOR_STRUCTURE_VALIDATION` | DEV-0201-R02; DEV-0201-R04; SEC-INP-001 |
| AC-03 — valid empty directory returns `READY_ZERO_RESULTS` | DEV-0201-R08; FOR-FAIL-002 |
| AC-04 — missing in-root path returns `MISSING` | DEV-0201-R07; FOR-FAIL-001 |
| AC-05 — existing file returns `UNSUPPORTED_INPUT` | DEV-0201-R07; PRD-IN-006 |
| AC-06 — root escape and symlink/reparse input return `VALIDATION_FAILED` | DEV-0201-R05; SEC-INP-001 |
| AC-07 — enumeration error returns `PROCESSING_FAILED` | DEV-0201-R09; FOR-FAIL-001 |
| AC-08 — result preserves complete DEV-0201 provenance and limitations | DEV-0201-R04; DEV-0201-R11; FOR-PROV-001 |
| AC-09 — repeated fixed-input inspection is deterministic | DEV-0201-R10; QMS-TST-002 |
| AC-10 — before/after fixture hashes and directory state are identical | DEV-0201-R06; DEV-0201-R12; FOR-INT-001 |
| AC-11 — supported-boundary source has no legacy imports | DEV-0201-R01; FOR-QTN-003 |
| AC-12 — configured invalid evidence roots fail closed | DEV-0201-R02; SEC-INP-001 |
| AC-13 — backend and evidence-engine regression suites pass | DEV-0201-R12; QMS-TST-001; QMS-TST-002 |
| AC-14 — no migration, default API route, recursive inventory, hash, encryption, parser, or support-status change is introduced | DEV-0201-R06; DEV-0201-R11; PRD-IN-001; PRD-IN-004 |

## 6. Deterministic test fixtures

Tests may create only temporary synthetic directories and small synthetic text
files. No repository `dev-evidence`, private sample, client, Apple backup, or
real evidence path may be used.

The filesystem-error test must use an injected or monkeypatched adapter
boundary rather than changing operating-system permissions on user data.

## 7. Completion rule

DEV-0201 may be marked `COMPLETE` only when AC-01 through AC-14 pass, DOC-002
contains every DEV-0201 requirement and criterion mapping, documentation is
updated, and the task ledger records the results.

Completion validates only this adapter contract. The result remains an
unvalidated input candidate until DEV-0202 and DEV-0203 complete their separate
structure and encryption contracts and a later owner review approves any input
support claim.

## 8. Validation results

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | Exact six-member `InputAdapterStatus` assertion |
| AC-02 | PASS | Synthetic nonempty in-root directory test |
| AC-03 | PASS | Synthetic empty-directory zero-result test |
| AC-04 | PASS | Missing in-root path test |
| AC-05 | PASS | Existing synthetic file test |
| AC-06 | PASS | Root-escape and injected link-boundary tests |
| AC-07 | PASS | Injected enumeration failure test |
| AC-08 | PASS | Immutable result provenance and limitation assertions |
| AC-09 | PASS | Repeated fixed-clock/fixed-correlation equality and audit-data assertions |
| AC-10 | PASS | Before/after SHA-256 and directory-state assertions over a synthetic fixture |
| AC-11 | PASS | Static import and prohibited content-operation test |
| AC-12 | PASS | Missing, file, and injected link/reparse evidence-root tests |
| AC-13 | PASS | Backend 26/26; evidence-engine characterization 5/5 |
| AC-14 | PASS | No migration, API route, parser, hash, encryption, or support-status change |

## 9. Implementation and test record

- Implementation: standalone `backend/app/intake/apple_backup.py`
- API exposure: none
- Legacy dependency: none
- Test data: temporary synthetic directories and small synthetic files only
- Real evidence accessed: no
- Database migrations added: none
- Focused adapter tests: 14 passed
- Full backend tests: 26 passed; accepted third-party TestClient warning remains
- Evidence-engine characterization tests: 5 passed
- Source mutation: none; synthetic before/after content hash and directory
  state matched
- Packaging: editable backend package metadata refreshed after adding the
  intake module

Commands run:

- `.venv\Scripts\python.exe -m pytest
  backend\tests\test_apple_backup_input_adapter.py -q
  --basetemp=tmp\pytest-dev0201-focused`
- `.venv\Scripts\python.exe -m pytest backend\tests -q
  --basetemp=tmp\pytest-dev0201-full`
- `.venv\Scripts\python.exe -m unittest discover -s tests`
- `.venv\Scripts\python.exe -m pip install -e backend --no-deps`

## 10. Limitations and residual risks

- Apple backup structure and encryption remain unassessed.
- No source hashing, immutable intake storage, evidence-source persistence, or
  controlled working copy exists.
- The adapter performs a non-recursive directory entry count only.
- The adapter is not routed through the API or authorized to process a case.
- Filesystem time-of-check/time-of-use risk remains and is tracked as RSK-0003.
- Neither ready outcome establishes input support.
