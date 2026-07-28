# DEV-0306 — Audit-Actor Attribution Acceptance

- Status: COMPLETE — WP-0300 package review pending
- Dependencies: DEV-0302 and DEV-0206 complete
- Scope: authenticated-principal attribution boundary for WP-0250 audit events
- Authorization/support effect: none

| ID | Acceptance criterion |
|---|---|
| AC-01 | Actor context derives principal, membership, tenant, kind, and opaque role from validated domain records |
| AC-02 | Membership principal must equal the attributed principal |
| AC-03 | Audit event actor ID is always the attributed principal ID |
| AC-04 | Actor tenant must equal evidence tenant; cross-tenant attribution fails before append |
| AC-05 | Correlation, event type, result, and safe failure code remain unchanged |
| AC-06 | Actor context is immutable and has no credential or permission fields |
| AC-07 | Existing append-only audit taxonomy/service remains the sole authority |
| AC-08 | No authentication, authorization policy, API, migration, evidence processing, or support effect |

Cross-tenant authorization-denial audit orchestration remains DEV-0310 scope;
DEV-0306 only prevents false attribution to the target tenant.

## Validation results

- Focused attribution/audit/identity suite: 19 passed.
- Full backend regression: 201 passed with the accepted TestClient warning.
- Legacy characterization: 5 passed.
- Python compilation and diff check: passed.
- AC-01 through AC-08: PASS.
