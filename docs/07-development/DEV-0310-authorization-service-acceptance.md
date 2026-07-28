# DEV-0310 — Authorization Service and Policy Enforcement

## Scope and assumptions

Implement a framework-neutral, fail-closed authorization boundary using an
explicit caller-supplied, versioned policy snapshot. No role permissions,
production policy, authentication provider, repository, API, or default grant
is established.

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | Policy identity/version and the evaluated principal, tenant, action, and result are retained in every decision. |
| AC-02 | Only an exact canonical role/action grant permits access; empty, absent, malformed, or mismatched grants deny closed. |
| AC-03 | Actor tenant must equal case tenant before policy evaluation can grant. |
| AC-04 | An evidence source must match both the requested tenant and case. |
| AC-05 | Enforcement raises a safe stable denial reason without evidence-derived detail. |
| AC-06 | Tests cover grants, empty policy, wrong role/action, malformed action, cross-tenant and cross-case denial. |
| AC-07 | No implicit production policy, API, repository, evidence processing, parser activation, or support promotion is added. |

## Validation record

All AC-01 through AC-07 pass. Focused tests: 25 passed. Full backend: 211
passed with the accepted TestClient warning. Compilation and diff checks pass.
No production role/action vocabulary or policy is supplied.
