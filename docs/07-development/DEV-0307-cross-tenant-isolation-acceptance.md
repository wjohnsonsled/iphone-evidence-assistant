# DEV-0307 — Cross-Tenant Isolation Tests

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | An explicit policy grant cannot override an actor/case tenant mismatch. |
| AC-02 | A source linked to a different case cannot be authorized. |
| AC-03 | Cross-tenant audit attribution fails before an audit event is appended. |
| AC-04 | Existing tenant, membership, case, source, authorization, audit, migration, backend, and legacy regressions pass. |
| AC-05 | Tests use synthetic in-memory objects only and add no runtime, API, evidence, parser, deployment, or support behavior. |

## Validation record

All AC-01 through AC-05 pass. Focused isolation/security tests: 22 passed.
Backend regressions: 214 passed with the accepted TestClient warning.
Compilation and diff checks pass. Synthetic in-memory objects only were used.
