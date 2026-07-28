# DEV-0205 — Controlled SQLite Working-Copy Service Acceptance

- Status: COMPLETE — WP-0200 package review pending
- Dependency: DEV-0204 complete
- Architecture: ARC-001 §5.3; ARC-002; DEC-0011
- Implementation: shared `app.intake.controlled_copy` service first validated
  under the limited DEV-0202 Stage-A authorization
- Support effect: none

## Scope reconciliation

DEV-0205 adopts the existing schema-neutral controlled-copy implementation as
the general candidate intake service. It does not create a second copy manager.
Its embedded pre/copy/post digests are copy-verification manifest fields, not a
competing evidence hash registry; durable evidence hash observations remain
solely owned by WP-0250.

## Requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0205-R01 | Copy a caller-selected SQLite main file with exact present companions | AC-01 main-only and `-wal`, `-shm`, `-journal` sets retain exact basenames in one workspace |
| DEV-0205-R02 | Preserve the immutable source boundary | AC-02 regular link-free files must remain inside the source root; outside, missing, directory, and link inputs fail closed |
| DEV-0205-R03 | Detect source or companion-set instability | AC-03 pre/copy/post SHA-256 values must match and the companion set must remain stable |
| DEV-0205-R04 | Isolate controlled material | AC-04 workspace is empty, outside the source, and uses an approved OS or caller-controlled temporary root |
| DEV-0205-R05 | Open SQLite read-only from the copy only | AC-05 URI uses read-only, immutable, private-cache semantics; query-only is enabled and writes fail |
| DEV-0205-R06 | Verify after use | AC-06 every controlled file is rehashed after inspection and change fails closed |
| DEV-0205-R07 | Make cleanup explicit | AC-07 success, failure, and synthetic-test retention are distinct; creation failures attempt cleanup |
| DEV-0205-R08 | Return safe deterministic records | AC-08 paths, roles, sizes, hashes, correlation, UTC creation time, access mode, verification, failures, and cleanup serialize canonically |
| DEV-0205-R09 | Remain schema-neutral and quarantined from legacy | AC-09 no Apple schema/version assumption or legacy import exists |
| DEV-0205-R10 | Preserve support boundaries | AC-10 synthetic fixtures only; no API, parser, artifact processing, real evidence, migration, or support promotion |

## Validation record

| Criterion | Result | Objective evidence |
|---|---|---|
| AC-01 | PASS | Main-only and all-companion tests |
| AC-02 | PASS | Missing/outside/non-file/link and workspace-inside-source tests |
| AC-03 | PASS | Injected source mutation and companion-set mutation tests |
| AC-04 | PASS | Workspace boundary and empty-workspace validation |
| AC-05 | PASS | Structural observation succeeds and schema write is rejected as read-only |
| AC-06 | PASS | Post-inspection verification and changed-copy failure tests |
| AC-07 | PASS | Normal cleanup, injected cleanup failure, creation cleanup, and test-retention tests |
| AC-08 | PASS | Fixed clock/correlation canonical audit comparison |
| AC-09 | PASS | AST/static boundary test |
| AC-10 | PASS | Diff review and supported/legacy regressions |

## Limitations and risks

- Application copying cannot guarantee a point-in-time snapshot of a source
  changing outside the process; detected changes fail closed (RSK-0005).
- Cleanup failure can leave controlled material and is surfaced rather than
  hidden (RSK-0006). Startup scavenging and production retention policy remain
  future work.
- This service has no persistence or multi-process transaction adapter.
- Structural SQLite readability does not establish Apple compatibility,
  evidentiary completeness, artifact correctness, or support.

## Commands and results

- `python -m pytest backend/tests/test_controlled_copy.py backend/tests/test_backup_validator.py -q`
  — 39 passed.
- `python -m pytest backend/tests -q` — 135 passed with the previously accepted
  third-party TestClient deprecation warning.
- `python -m unittest discover -s tests -q` — 5 passed.
- `python -m compileall -q backend/app backend/tests` — passed.
- `git diff --check` — passed.
