# DEV-0208 — Intake Cleanup and Failure Recovery Acceptance

- Status: COMPLETE — WP-0200 package review pending
- Dependency: DEV-0205 complete
- Architecture: ARC-001 §5.3
- Support effect: none

## Scope

DEV-0208 preserves the context-managed cleanup behavior in DEV-0205 and adds a
bounded recovery pass for orphaned controlled workspaces. Recovery is limited
to immediate children of one configured root whose names use the controlled
workspace prefix. It does not traverse evidence sources or arbitrary paths.

## Requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0208-R01 | Preserve normal cleanup and explicit failure | AC-01 context exit deletes controlled workspaces; cleanup failure remains surfaced and recorded |
| DEV-0208-R02 | Recover only owned stale workspaces | AC-02 only immediate prefix-matching directories older than a positive threshold are removed |
| DEV-0208-R03 | Preserve unrelated and recent paths | AC-03 unrelated entries are ignored and owned recent directories are retained with `SKIPPED_RECENT` |
| DEV-0208-R04 | Reject unsafe candidates | AC-04 prefix-matching links, root escapes, and non-directories are retained with explicit rejection outcomes |
| DEV-0208-R05 | Surface operational failure | AC-05 deletion failure records `FAILED` and `workspace_recovery_failed` without exposing raw exception text |
| DEV-0208-R06 | Produce deterministic audit data | AC-06 fixed clock, threshold, sorted paths, UTC timestamps, status, and failure code serialize canonically |
| DEV-0208-R07 | Fail closed on invalid policy | AC-07 nonexistent/non-directory/link roots and non-positive age thresholds are rejected |
| DEV-0208-R08 | Preserve boundaries | AC-08 synthetic temporary workspaces only; no API, evidence source deletion, parser, persistence, real evidence, or support promotion |

## Validation record

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | Existing normal and injected cleanup-failure tests |
| AC-02 | PASS | Stale owned directory removed |
| AC-03 | PASS | Recent owned and unrelated directories retained |
| AC-04 | PASS | Injected link and owned-file rejection tests |
| AC-05 | PASS | Injected deletion failure remains explicit and candidate remains |
| AC-06 | PASS | Fixed-clock ordered report and canonical JSON test |
| AC-07 | PASS | Constructor/threshold validation tests |
| AC-08 | PASS | Synthetic `tmp_path` fixtures and static scope review |

## Limitations and risks

- Recovery is an explicit service call, not a scheduled startup job.
- No persistent recovery ledger or multi-process coordination exists.
- A process crash during deletion can leave a partially removed workspace; a
  later pass will retry and record its outcome.
- RSK-0006 remains open until production retention, permissions, scheduling,
  persistent audit, and monitoring are implemented.

## Commands and results

- `python -m pytest backend/tests/test_intake_cleanup_recovery.py backend/tests/test_controlled_copy.py -q`
  — 17 passed.
- `python -m pytest backend/tests -q` — 143 passed with the previously accepted
  third-party TestClient deprecation warning.
- `python -m unittest discover -s tests -q` — 5 passed.
- `python -m compileall -q backend/app backend/tests` — passed.
- `git diff --check` — passed.
