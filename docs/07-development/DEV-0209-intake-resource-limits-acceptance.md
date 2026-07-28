# DEV-0209 — Intake Resource Limits and Denial-of-Service Controls

- Status: COMPLETE — WP-0200 package review pending
- Dependency: DEV-0202 complete
- Owner authorization: DEC-0025
- Support effect: none

## Scope and requirements

DEV-0209 implements caller-supplied, fail-closed resource policy. There are no
implicit deployment ceilings. Missing or invalid policy values prevent
configuration or dependency composition.

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0209-R01 | Require every approved ceiling | AC-01 directory count/depth, pathname length, plist bytes, SQLite main/WAL/SHM bytes, aggregate copy bytes, schema entries, and SQLite work units are required |
| DEV-0209-R02 | Validate policy deterministically | AC-02 missing, malformed, Boolean, zero, negative, and above-range values fail |
| DEV-0209-R03 | Bound input adaptation | AC-03 path length/depth and bounded directory enumeration exceedance returns `VALIDATION_FAILED` with `resource_limit_exceeded` |
| DEV-0209-R04 | Bound metadata reads | AC-04 plist size is checked before opening and exceedance returns `APPLE_BACKUP_VALIDATION_FAILED` |
| DEV-0209-R05 | Bound controlled copying | AC-05 main, WAL, SHM, rollback-journal role ceiling and aggregate bytes are checked before workspace creation/copy |
| DEV-0209-R06 | Bound SQLite processing | AC-06 schema enumeration and progress-handler work budgets interrupt processing and return validation failure |
| DEV-0209-R07 | Avoid false forensic classification | AC-07 resource denial never produces corrupt, incomplete, unsupported, encrypted, or unencrypted solely because of the limit |
| DEV-0209-R08 | Return safe deterministic failure | AC-08 public message and code are fixed; raw exception/evidence content is absent |
| DEV-0209-R09 | Keep production values deployment-controlled | AC-09 example and test ceilings are explicitly non-production; safe summary reveals configuration presence, not values |
| DEV-0209-R10 | Preserve boundaries | AC-10 synthetic fixtures only; no API, parser, real evidence, compatibility approval, or support promotion |

## Valid configuration ranges

The inclusive validation ranges in `resource_limits.py` are type/operability
bounds, not production capacity values:

| Setting suffix | Valid range |
|---|---:|
| `MAX_DIRECTORY_ENTRIES` | 1–10,000,000 |
| `MAX_DIRECTORY_DEPTH` | 1–1,024 |
| `MAX_PATHNAME_LENGTH` | 1–32,767 |
| `MAX_PLIST_BYTES` | 1–1 GiB |
| `MAX_SQLITE_MAIN_BYTES` | 1–1 TiB |
| `MAX_SQLITE_WAL_BYTES` | 1–1 TiB |
| `MAX_SQLITE_SHM_BYTES` | 1–1 GiB |
| `MAX_CONTROLLED_COPY_BYTES` | 1–2 TiB |
| `MAX_SCHEMA_ENTRIES` | 1–10,000,000 |
| `MAX_SQLITE_WORK_UNITS` | 1–10,000,000,000 |

## Validation result

AC-01 through AC-10 pass using synthetic temporary files. Focused tests cover
every policy field, configuration failure, all input and validation
classifications, companion-role limits, aggregate limits, schema limits,
SQLite interruption, safe messages, and cleanup before copying.

## Limitations

- Example values are development/test fixtures, not capacity guidance.
- SQLite work units are VM progress-handler operations, not elapsed time or a
  cross-platform performance guarantee.
- Filesystem metadata can still change between checks; controlled-copy
  pre/copy/post verification remains required.
- Production monitoring, rate limiting, upload streaming, concurrency quotas,
  and capacity testing remain future deployment/API work.

## Commands and results

- Focused configuration/intake/resource suite — 72 passed.
- Full backend regression — 153 passed with the previously accepted third-party
  TestClient deprecation warning.
- Legacy characterization — 5 passed.
- Dependency lock validation and `pip check` — passed.
- Python compilation — passed.
- Alembic heads/history and PostgreSQL offline upgrade SQL — passed; one head.
- No migration was created.
