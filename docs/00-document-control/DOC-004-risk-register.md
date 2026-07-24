# DOC-004 — Risk Register

## Document control

- Established: 2026-07-24
- Scope: Controlled MVP development risks
- Review rule: Update in the task that identifies, changes, accepts, or closes
  a risk

| Risk ID | Risk | Impact | Current controls | Residual status | Owner decision / next action |
|---|---|---|---|---|---|
| RSK-0001 | The explicit legacy compatibility FastAPI application could be deployed or exposed mistakenly | Unsupported, unauthenticated legacy output could be treated as supported evidence or cross the SaaS boundary | Default composition is health-only; legacy composition is explicitly named and warned; deterministic import/route tests | OPEN — HIGH | Owner accepted retention for characterization in DEC-0003; add deployment/CI denial controls in a later approved task |
| RSK-0002 | FastAPI/Starlette TestClient emits a third-party deprecation warning | A future dependency update could break backend tests or mask new warnings | Warning is recorded; current tests pass deterministically | OPEN — LOW | Owner accepted as technical debt in DEC-0003; resolve during dependency/quality task without weakening tests |
