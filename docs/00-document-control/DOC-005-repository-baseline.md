# DOC-005 — Repository Baseline

## Document control

- Task: DEV-0001
- Baseline date: 2026-07-24
- Repository root: `C:\Users\wjohn\OneDrive\Business\Digital Forensics\Sales\AI-Powered iPhone Evidence Assistant\Project`
- Branch observed: `master`
- Working tree at inspection start: clean
- Scope: read, inspect, and validate the existing repository; no application-code changes
- Approval state: validation pending

## Purpose

This document records the repository state found during DEV-0001. It reconciles
the Phase 0 documentation with application code that was already present before
the controlled implementation plan and `AGENTS.md` were established.

This baseline does not approve any parser, artifact family, schema, workflow, or
conclusion as supported. Existing code is inventory evidence, not support
evidence.

## Governing documents read

The inspection read `AGENTS.md`, all populated files under `docs/`, and the
following populated root documents:

- `README.md`
- `API.md`
- `DATABASE_DESIGN.md`
- `IMPLEMENTATION_NOTES.md`
- `LOCAL_DEVELOPMENT.md`
- `REFACTOR_NOTES.md`
- `docker-compose.yml`
- `backend/Dockerfile`
- `backend/pyproject.toml`
- `backend/alembic.ini`

Only four files under `docs/` were populated before DEV-0001:

- `docs/01-product/PRD-003-mvp-scope.md`
- `docs/03-forensics/FOR-004-artifact-support-matrix.md`
- `docs/07-development/DEV-001-master-implementation-plan.md`
- `docs/07-development/DEV-009-task-ledger.md`

All other pre-existing documentation files under `docs/` were zero-byte
placeholders.

## Repository inventory

### Top-level implementation

- `evidence_engine/`: Python evidence-processing package.
- `backend/`: FastAPI, SQLAlchemy, Alembic, repositories, services, API routes,
  schemas, and tests.
- `tests/`: evidence-engine characterization and deterministic self-check tests.
- `window_investigator.py`: thin compatibility wrapper for the legacy CLI.
- `docker-compose.yml`: PostgreSQL and backend service definitions.
- `backend/Dockerfile`: Python 3.12 backend image.
- `frontend/`: empty.
- `infra/`: empty.
- `.github/`: contains no CI workflow.
- `scripts/`, `dev-evidence/`, and `outputs/`: empty.
- `references/`: third-party forensic reference PDFs; not test fixtures.
- `work/alembic_upgrade_head.sql`: generated or working SQL output, not a
  controlled migration source.

### Evidence-engine architecture

`evidence_engine/_legacy.py` is an approximately 8,700-line implementation
containing the operative models, parsers, timestamp helpers, inventory,
coverage, normalization, analysis, AI prompt construction, deterministic
question answering, and report generation.

Most files in `evidence_engine/models`, `parsers`, `normalization`, `analysis`,
`inventory`, `ai`, and `reports` re-export functions and classes from
`_legacy.py`. They provide import boundaries but are not independently
implemented modules. `evidence_engine/parsers/base.py` adds a parser protocol,
result class, and legacy adapter.

The default registry exposes parsers for SMS, calls, Safari, photos, Notes,
Mail, Calendar, Reminders, Maps/location, KnowledgeC, notifications, Wi-Fi,
Bluetooth, AirDrop/Nearby, network configuration, cellular/telephony, data
usage, plists, and system files. Several are outside the approved MVP artifact
candidate list. Their presence does not make them supported.

### Backend architecture

The backend contains:

- a FastAPI application and `/api/v1` routes;
- case, device, evidence-event, artifact-coverage, and processing-job models;
- a single initial Alembic migration;
- repositories and synchronous processing services;
- server-local path validation;
- mapping of legacy normalized events into PostgreSQL-oriented rows;
- deterministic evidence summaries; and
- tests using in-memory SQLite and mocked/synthetic data.

No authentication principal, authorization policy, tenant model, tenant key, or
audit-event model was found. Case IDs constrain evidence queries, but any caller
can supply any case ID.

## Baseline forensic observations

1. Source SQLite databases are opened with SQLite URI `mode=ro`, which reduces
   direct write risk, but no controlled working-copy process exists.
2. WAL and SHM presence is inventoried. The code relies on SQLite behavior when
   opening the source database and records a heuristic `wal_applied_by_sqlite`
   value; it does not establish a controlled copy of the main database plus WAL,
   SHM, and journal.
3. Rollback-journal handling is not implemented.
4. Source files may be hashed, but default coverage hashing is size-limited and
   `sha256()` converts any hashing error to an empty string without logging it.
5. Timestamp helpers commonly remove timezone information, call
   `datetime.fromtimestamp()` using the host timezone, and do not retain the
   source field, raw format, conversion method, precision, or timezone basis in
   a uniform model.
6. The normalized event has provenance-like fields, but many are inferred from
   broad dictionaries and may be blank. A complete, resolvable source locator is
   not enforced.
7. The backend persists `raw_values` when supplied, but `normalize_event()` does
   not populate a complete raw-value envelope. Original values are therefore not
   reliably preserved end to end.
8. Parser versions default to `"1"` or `"legacy"` and are not tied to a parser
   build, schema profile, or execution record.
9. Broad exceptions in legacy collection usually produce an error-log entry and
   an empty result, but several helper functions silently return `None`, `[]`,
   `0`, or an empty hash. This can blur no-record, unreadable, unsupported, and
   failed states.
10. `EvidenceEngineRunner` does not call `build_coverage_audit()` before
    `build_case_knowledge()`. Consequently, backend processing can persist no
    coverage rows even when parsers ran.
11. `EvidenceEngineRunner` always builds knowledge with acquisition labels
    stating an encrypted iPhone backup, without detecting the actual encryption
    state.
12. The backend path check accepts a directory when any one broad marker exists;
    it is not structural Apple-backup validation.

## Baseline security observations

- The resolved-path boundary check has a focused traversal test and is reusable.
- Docker mounts `dev-evidence` read-only, but non-Docker processing receives
  ordinary filesystem paths and has no OS-enforced immutability control.
- No upload endpoint is implemented.
- No authentication, authorization, tenant isolation, audit log, rate limiting,
  retention enforcement, or deletion workflow is implemented.
- Case and evidence endpoints are unauthenticated.
- The case table stores source paths, which may expose sensitive server layout
  through database access even though the API omits the field from case detail.
- Exception handlers return generic messages, but logs may contain source paths
  and artifact-derived exception text.
- `docker-compose.yml` uses development database credentials and refers to
  `backend/.env.example`, which does not exist. The root `.env.example` is empty.

## Documentation reconciliation

The original ledger described DEV-0101 as blocked and pending, but a backend
scaffold already exists. This is treated as pre-baseline code and classified
`IMPLEMENTED_NOT_VALIDATED`; DEV-0101 remains blocked and is not complete.

`README.md`, `API.md`, `DATABASE_DESIGN.md`, `IMPLEMENTATION_NOTES.md`,
`LOCAL_DEVELOPMENT.md`, and `REFACTOR_NOTES.md` describe implemented behavior,
while the controlled `docs/` set lacks product requirements, architecture,
forensic methods, traceability, threat model, test strategy, and acceptance
criteria. Those root documents are useful implementation notes but do not
satisfy the all-or-nothing support rule.

`FOR-004` correctly retains MVP artifacts as candidates and out-of-scope
artifacts as unsupported. DEV-0001 does not change those statuses.

## Commands and observed results

| Command | Result |
|---|---|
| `Get-Content` and `rg` repository inspections | Completed; read-only |
| Bundled `git.exe status --short --branch` | `## master`; no changes reported before documentation edits |
| Bundled `python.exe --version` | Python 3.12.13 |
| Bundled `python.exe -m unittest discover -s tests` | 5 tests passed in 0.139 seconds |
| Bundled `python.exe window_investigator.py --list-plugins --start ... --end ...` | Completed; 18 legacy plugins listed |
| Bundled `python.exe -m pytest backend/tests -q` | Not executed: `No module named pytest` |
| `Get-Command` / runtime search for Git and pytest | Bundled Git found; no runnable pytest found |

No real evidence, credentials, network services, Docker services, database
migrations, or destructive commands were used.

## Baseline conclusion

The architecture has reusable boundaries: a domain-oriented evidence engine, a
backend persistence adapter, case-scoped database relationships, repositories,
and a path validator. It is not ready to be treated as a validated MVP.

The legacy processing core should be retained for characterization, isolated
from supported workflows, and validated or replaced incrementally. The backend
scaffold is reusable as a starting point only after requirements, authentication
and tenant boundaries, evidence-source modeling, immutable intake, provenance,
timestamp handling, and controlled parser execution are defined.

DEV-0001 is placed in `VALIDATION_PENDING` because the repository baseline is
documented but requires project-owner approval, and backend tests could not be
executed in the available environment.
