# DEV-0401 — Processing-Run Model

## Scope

Define immutable processing-run identity scoped to tenant, case, and evidence
source, plus authorization and request provenance. DEV-1104 owns lifecycle
states. DEV-0410 owns the coherent WP-0400 store migration.

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | Run identity is UUIDv4 and distinct from legacy `processing_jobs`. |
| AC-02 | Tenant, case, evidence source, purpose, request actor/time, and correlation are immutable and explicit. |
| AC-03 | Creation requires the exact caller-supplied `processing-run.create` grant after tenant/case/source checks. |
| AC-04 | Authorization policy identity/version is retained with the run. |
| AC-05 | Purpose and timestamps validate deterministically and fail closed. |
| AC-06 | Additive ORM metadata contains relational tenant/case/source constraints; migration is deferred to DEV-0410. |
| AC-07 | Synthetic tests and regressions pass; no parser, API, evidence access, lifecycle, persistence repository, or support promotion occurs. |

## Requirement mapping

DEV-0401-R01 through DEV-0401-R07 map one-to-one to AC-01 through AC-07 and
derive from ARC-001, ARC-002 provenance requirements, DEC-0037 authorization
requirements, AGENTS.md, and the WP-0400 completion criteria.

## Validation record

All AC-01 through AC-07 pass. Focused tests: 17 passed. Backend: 220 passed
with the accepted warning. Compilation and diff checks pass. No migration,
parser, evidence access, API, lifecycle, repository, or support change occurred.
