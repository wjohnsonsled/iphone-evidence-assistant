# DEV-0103 — Configuration Model and Environment Validation

- Status: COMPLETE — owner approved in DEC-0019
- Dependency: DEV-0102 complete under DEC-0014
- Scope: backend application configuration only
- Runtime/API/support effect: no new route, evidence workflow, or support status

## Requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0103-R01 | Use closed environment and log-level vocabularies | AC-01 accepted values normalize deterministically; unknown values fail |
| DEV-0103-R02 | Require a parseable database URL and restrict SQLite to tests | AC-02 missing/malformed URLs fail; development/staging/production require PostgreSQL; test permits SQLite |
| DEV-0103-R03 | Validate every configured evidence root | AC-03 roots are nonempty, absolute, normalized, and duplicate-free |
| DEV-0103-R04 | Fail closed for unsafe production development credentials | AC-04 production rejects the documented development password |
| DEV-0103-R05 | Prevent credentials from configuration diagnostics | AC-05 settings representation and safe summary contain no password or full URL |
| DEV-0103-R06 | Preserve deterministic environment loading and cache control | AC-06 environment aliases load predictably and tests can clear cached settings |
| DEV-0103-R07 | Preserve supported/legacy composition and database behavior | AC-07 default health-only and legacy regressions pass |
| DEV-0103-R08 | Add no evidence access, API, migration, external service, or support promotion | AC-08 static boundary and diff review pass |

The task validates configuration values only. It does not create directories,
connect to a database, inspect evidence roots, load secrets from an external
manager, or establish production readiness.

## Validation record

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | Closed enum normalization and rejection tests |
| AC-02 | PASS | Missing/malformed/driver-policy and SQLite test-only matrix |
| AC-03 | PASS | Absolute, empty-segment, relative, and duplicate root tests |
| AC-04 | PASS | Production development-password rejection test |
| AC-05 | PASS | Settings representation and safe-summary credential assertions |
| AC-06 | PASS | Environment alias loading and cache-clear test |
| AC-07 | PASS | Focused 13/13; backend 113/113; legacy 5/5 |
| AC-08 | PASS | No route, migration, evidence access, external service, or support change |

Commands: focused and full pytest with repository-local `--basetemp`; legacy
unittest discovery; compileall; dependency-lock validation; `pip check`; and
`git diff --check`.

Limitations: validation does not confirm database reachability, filesystem
existence/permissions, external secret-manager integration, or production
readiness. Rejecting the documented development password is a narrow guard, not
general credential-strength validation. The accepted TestClient warning remains.
