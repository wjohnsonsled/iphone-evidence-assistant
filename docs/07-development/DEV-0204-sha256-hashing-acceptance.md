# DEV-0204 — SHA-256 Hashing Service Acceptance

- Status: COMPLETE — WP-0200 package review pending
- Dependency: DEV-0203 complete under DEC-0014
- Architecture: ARC-001, ARC-002, DEC-0011
- Implementation authority: shared WP-0250 `HashRegistry`
- Support effect: none

## Scope reconciliation

DEV-0204 adopts and validates the owner-approved WP-0250 hashing contract for
intake. DEC-0011 and BACKLOG.md make WP-0250 the sole authority for hash
observations. This task therefore must not create a competing intake hash
implementation.

Hashing is limited to caller-controlled file paths. Evidence-root registration,
path selection, immutable storage enforcement, working-copy lifecycle,
persistence adapters, and package orchestration remain separate tasks.

## Requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0204-R01 | Reuse the sole approved hash authority | AC-01 intake validation imports and exercises `HashRegistry`; no second SHA-256 service is introduced |
| DEV-0204-R02 | Compute complete SHA-256 deterministically | AC-02 known, empty, and multi-chunk synthetic files produce the standard digest and exact byte length |
| DEV-0204-R03 | Preserve immutable observation history | AC-03 each attempt appends a distinct frozen observation and prior observations remain unchanged |
| DEV-0204-R04 | Retain complete hash provenance | AC-04 success records tenant, case, evidence UUID, purpose, role, actor, component/version, UTC time, algorithm, digest, and byte length |
| DEV-0204-R05 | Fail closed and explicitly | AC-05 unreadable or missing input appends `hash_failed`; detected source instability appends `source_unstable`; neither produces a digest |
| DEV-0204-R06 | Audit every attempt and verification | AC-06 success, failure, verified, mismatch, instability, and verification failure remain distinct and produce typed audit events |
| DEV-0204-R07 | Preserve source bytes | AC-07 hashing opens the synthetic source read-only and before/after bytes and modification metadata are unchanged |
| DEV-0204-R08 | Preserve forensic and support boundaries | AC-08 tests use synthetic files only; no API, parser, artifact parsing, real evidence, or support status is introduced |

## Validation record

| Criterion | Result | Objective evidence |
|---|---|---|
| AC-01 | PASS | Task-specific test imports `app.integrity.services.HashRegistry`; repository search confirms no intake hash engine |
| AC-02 | PASS | Known-content task test plus WP-0250 empty and multi-chunk tests |
| AC-03 | PASS | Distinct observation IDs, tuple history, and frozen-dataclass mutation denial |
| AC-04 | PASS | Task-specific complete metadata assertions |
| AC-05 | PASS | Missing-file failure test and WP-0250 instability characterization |
| AC-06 | PASS | Typed success/failure audit assertions and WP-0250 verification-state tests |
| AC-07 | PASS | Synthetic source byte, size, and modification-time comparison |
| AC-08 | PASS | Static scope review and full supported/legacy regression suites |

## Limitations and risks

- The approved service is an in-memory reference implementation pending a
  repository/transaction adapter.
- A hash observation proves the bytes read at observation time; it does not
  prove acquisition authenticity or pre-intake history.
- Application stat comparisons reduce but cannot eliminate filesystem
  time-of-check/time-of-use risk (RSK-0003).
- DEV-0204 does not select paths or establish that a candidate is an Apple
  backup. It grants no input or artifact support.

## Commands and results

- `python -m pytest backend/tests/test_intake_hashing.py backend/tests/test_integrity_infrastructure.py -q`
  — 13 passed.
- `python -m pytest backend/tests -q` — 134 passed with the previously accepted
  third-party TestClient deprecation warning.
- `python -m unittest discover -s tests -v` — 5 passed.
- `python -m compileall -q backend/app backend/tests` — passed.
- `git diff --check` — passed.
