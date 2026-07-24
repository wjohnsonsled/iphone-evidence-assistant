# DEV-0101 — Backend Scaffold Acceptance Criteria

## 1. Document control

- Task: DEV-0101
- Date: 2026-07-24
- Status: complete
- Dependencies: DEV-0002, DEV-0003, DEV-0004
- Architecture: ARC-001 and DEC-0002
- Artifact support effect: none
- Database migration authorization: none required

## 2. Objective

Validate and minimally remediate the pre-existing FastAPI/SQLAlchemy/Alembic
backend scaffold so that the default application is a safe supported-path
composition root and cannot accidentally expose the legacy processing,
evidence, or reporting API.

This task establishes application composition and repository safety only. It
does not implement intake, evidence-source entities, authentication, tenant
isolation, supported parsers, supported storage, or artifact workflows.

## 3. In scope

- retain the FastAPI application-factory pattern;
- make the default application expose only infrastructure-safe endpoints;
- create an explicitly named legacy compatibility composition root;
- keep existing legacy case/evidence behavior available for characterization
  tests without including it in the default application;
- ensure the default composition root has no import dependency on legacy
  processing or legacy API routes;
- retain structured error and database-session foundations;
- reconcile `.gitignore` into a valid conservative evidence/secret exclusion
  policy; and
- add deterministic scaffold and architecture-boundary tests.

## 4. Out of scope

- authentication, authorization, tenants, memberships, and audit entities;
- evidence-source, source-file, working-copy, or parser-run entities;
- Apple backup structure or encryption detection;
- parser registries or parser promotion;
- schema migrations or data rewriting;
- changing legacy parser behavior;
- production deployment or external services; and
- declaring any endpoint, input, parser, artifact, or workflow supported.

## 5. Requirements

| Requirement ID | Requirement |
|---|---|
| DEV-0101-R01 | `app.main:create_app()` is the default supported-path application factory |
| DEV-0101-R02 | The default API exposes health/readiness only and does not expose case, evidence, summary, or processing routes |
| DEV-0101-R03 | Importing the default composition root does not import legacy composition, legacy processing, or `evidence_engine._legacy` |
| DEV-0101-R04 | Legacy API routes remain available only through an explicitly named legacy compatibility factory |
| DEV-0101-R05 | The legacy compatibility factory and documentation display an unambiguous unsupported/characterization-only warning |
| DEV-0101-R06 | Existing structured errors, settings, database sessions, and Alembic scaffold remain intact |
| DEV-0101-R07 | `.gitignore` contains no merge-conflict or shell-write debris and conservatively excludes secrets, evidence, databases, companion files, archives, generated output, and local environments |
| DEV-0101-R08 | Tests are deterministic and use only synthetic in-memory data or temporary paths |
| DEV-0101-R09 | No migration, parser promotion, artifact promotion, or supported processing claim is introduced |

## 6. Measurable acceptance criteria

| Criterion | Required result |
|---|---|
| AC-01 | Default OpenAPI paths equal `{"/api/v1/health"}` |
| AC-02 | Requests to default `/api/v1/cases` and a default processing route return `404` |
| AC-03 | Static import-boundary test proves supported composition files do not import legacy composition, case/evidence routes, case processing, or `evidence_engine._legacy` |
| AC-04 | Explicit legacy factory exposes the pre-existing case, evidence, summary, and processing paths |
| AC-05 | Legacy application title or description contains `Legacy` and `unsupported` |
| AC-06 | Existing backend tests pass after being bound explicitly to the legacy factory where appropriate |
| AC-07 | `.gitignore` safety test proves required exclusions and absence of conflict markers/herestring debris |
| AC-08 | Evidence-engine characterization tests continue to pass unchanged |
| AC-09 | `git diff --check` passes and no Alembic migration is added |
| AC-10 | Documentation and DOC-002 trace the new composition boundary and its limitations |

## 7. Completion rule

DEV-0101 may be marked `COMPLETE` only if AC-01 through AC-10 pass. Completion
accepts only the backend scaffold and composition boundary. All feature,
security, intake, parser, evidence, AI, and reporting claims remain
unimplemented, unvalidated, quarantined, or unsupported according to DOC-002.

## 8. Validation results

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | Default OpenAPI path assertion |
| AC-02 | PASS | Default case and processing route-negative assertions |
| AC-03 | PASS | Static AST import-boundary test |
| AC-04 | PASS | Explicit legacy OpenAPI route assertions |
| AC-05 | PASS | Legacy title and description assertions |
| AC-06 | PASS | Backend test suite |
| AC-07 | PASS | Deterministic `.gitignore` safety assertions |
| AC-08 | PASS | Evidence-engine `unittest` characterization suite |
| AC-09 | PASS | `git diff --check`; no Alembic file added |
| AC-10 | PASS | API.md, LOCAL_DEVELOPMENT.md, README.md, DOC-002, and DEV-009 |

## 9. Test and implementation record

- Test data: synthetic in-memory records and temporary directories only
- Real evidence accessed: no
- Database migrations added: none
- First backend test attempt: 10 passed, 2 setup errors because the user-level
  pytest temporary directory was inaccessible
- Corrected backend command: repository-local ignored `--basetemp`
- Corrected backend result: 12 passed; one third-party TestClient deprecation
  warning
- Evidence-engine characterization result: 5 passed
- Security effect: default application no longer exposes unauthenticated
  legacy case/evidence/processing routes
- Evidence-integrity effect: legacy processing can no longer be reached through
  the default composition root; no source evidence was read or changed
- Limitation: authentication, tenant isolation, supported intake, controlled
  working copies, supported parser registry, and supported storage remain
  unimplemented
- Remaining risk: explicit legacy compatibility application remains callable
  by developers and must not be deployed or distributed as a supported surface

Commands run:

- bundled Python 3.12 `-m venv .venv`
- `.venv\Scripts\python.exe -m pip install -e "backend[dev]"`
- `.venv\Scripts\python.exe -m pytest backend\tests -q`
- `.venv\Scripts\python.exe -m pytest backend\tests -q
  --basetemp=tmp\pytest-dev0101`
- `.venv\Scripts\python.exe -m compileall -q backend\app`
- `.venv\Scripts\python.exe -m pytest backend\tests -q
  --basetemp=tmp\pytest-dev0101-final`
- `.venv\Scripts\python.exe -m unittest discover -s tests`
- `git diff --check`
- Git diff inspection of `backend/alembic/versions`
- repository scan for `.gitignore` conflict and shell-write debris
