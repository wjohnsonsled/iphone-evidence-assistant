# DEV-0106 — CI Architecture and Regression Gate Acceptance

- Status: COMPLETE — WP-0100 package review pending
- Dependency: DEV-0102 complete
- Scope: repository CI definition and deterministic gate validation
- Deployment/support effect: none

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0106-R01 | Run with least GitHub token privilege and no secrets | AC-01 workflow declares read-only contents permission and no secret/evidence inputs |
| DEV-0106-R02 | Use Python 3.12.13 and the committed lock | AC-02 setup and install commands are pinned to repository policy |
| DEV-0106-R03 | Validate the lock and installed environment | AC-03 lock validator and `pip check` are mandatory |
| DEV-0106-R04 | Run backend and legacy regressions deterministically | AC-04 full pytest with controlled temp root and legacy unittest commands are mandatory |
| DEV-0106-R05 | Run compilation and migration checks | AC-05 compileall, Alembic single-head/history, and offline upgrade SQL are mandatory |
| DEV-0106-R06 | Preserve supported/legacy architecture boundaries | AC-06 full backend suite includes boundary tests and CI definition has no legacy deployment command |
| DEV-0106-R07 | Fail closed without deployment or mutation steps | AC-07 workflow has no deploy, push, migration-online, or evidence-processing step |
| DEV-0106-R08 | Validate workflow structure locally | AC-08 deterministic tests parse the workflow and assert every required gate |

## Validation record

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | Read-only permission and no-secret/evidence/deploy static test |
| AC-02 | PASS | Python 3.12.13 and locked nonisolated install assertions |
| AC-03 | PASS | Lock validator and `pip check` commands asserted and passed locally |
| AC-04 | PASS | Backend/legacy commands asserted; 132/132 and 5/5 pass locally |
| AC-05 | PASS | Compilation and PostgreSQL offline migration commands passed locally |
| AC-06 | PASS | Full suite contains supported/legacy architecture tests |
| AC-07 | PASS | No deploy, push, online migration, or processing command |
| AC-08 | PASS | Workflow parses and three deterministic gate tests pass |

Commands: focused/full pytest with repository-local `--basetemp`; legacy
unittest discovery; compileall; lock validation; `pip check`; Alembic
heads/history and PostgreSQL offline upgrade generation; YAML parse; and
`git diff --check`.

Limitations: the workflow was not executed by GitHub because no push or remote
action was authorized. Docker is unavailable. No formatter, linter, type
checker, vulnerability scanner, license scanner, secret scanner, live database,
or container build is configured in this gate. Official GitHub actions use
major-version tags rather than immutable commit SHAs. The accepted TestClient
warning remains.
