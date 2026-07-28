# DEV-0309 — Security Package Integration Tests

## Acceptance matrix

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| AC-01 | Tenant, principal/membership, case, and source contracts compose with exact tenant scope | PASS | Model and focused security suites |
| AC-02 | Authorization denies closed unless an explicit versioned grant and all resource scopes match | PASS | DEV-0310 tests and adversarial DEV-0307 tests |
| AC-03 | Sensitive audit attribution uses the principal and cross-tenant attempts append nothing | PASS | Audit attribution and isolation tests |
| AC-04 | Supported registry remains empty and legacy paths remain quarantined | PASS | Registry/scaffold regression tests |
| AC-05 | The additive migration is single-head and reversible offline | PASS | Alembic head/history and offline upgrade/downgrade |
| AC-06 | Full backend and legacy regressions, compilation, and diff checks pass | PASS | 214 backend; 5 legacy; compilation/diff clean |
| AC-07 | No production API, policy, authentication provider, real evidence, deployment, or support promotion occurs | PASS | Boundary and diff review |

## Limitations

- No live PostgreSQL migration or database-enforced integration test was run.
- No production authorization policy, role/action vocabulary, policy
  persistence, authentication provider, or repository exists.
- There is intentionally no supported production evidence API. Therefore the
  WP-0300 wording requiring authorization at an API boundary is not yet
  operationally validated; it remains a mandatory condition before any such
  API is exposed.
- The accepted pytest temp-directory workaround and TestClient warning remain.

Status: `COMPLETE` — owner approved candidate foundation infrastructure in
DEC-0037 with every limitation above retained.
