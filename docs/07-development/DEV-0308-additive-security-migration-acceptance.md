# DEV-0308 — Additive Alembic Migration Baseline

## Scope

Create one linear, additive, reversible Alembic migration for the validated
DEV-0301 through DEV-0306 ORM schema. The migration must not change legacy or
WP-0250 tables, expose an API, implement authorization, process evidence, or
change support status.

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | A single revision follows `0002_evidence_integrity` without branching the migration history. |
| AC-02 | The five security tables are created in dependency order and match their ORM constraints and indexes. |
| AC-03 | Tenant/case evidence-source linkage is enforced by the composite foreign key. |
| AC-04 | Downgrade removes only the five new tables, in safe reverse dependency order. |
| AC-05 | Alembic head, history, and offline PostgreSQL upgrade and downgrade SQL generation pass. |
| AC-06 | Deterministic migration tests and all backend and legacy regressions pass. |
| AC-07 | No destructive data rewrite, production database operation, API, parser, evidence access, or support promotion occurs. |

## Validation record

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | One head directly follows `0002_evidence_integrity`. |
| AC-02 | PASS | Dependency order and ORM schema validated; focused suite: 44 passed. |
| AC-03 | PASS | Composite case/tenant foreign key is present. |
| AC-04 | PASS | Downgrade removes only the five new tables in reverse order. |
| AC-05 | PASS | Alembic head/history and offline upgrade/downgrade SQL passed. |
| AC-06 | PASS | Backend: 203 passed; legacy: 5 passed; compilation/diff checks passed. |
| AC-07 | PASS | No live database, evidence, API, parser, deployment, or support change. |

The documented repository-local `--basetemp` workaround was required. The
accepted TestClient warning remains. Live PostgreSQL validation was not run.
