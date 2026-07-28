# DEV-0302 — User and Role Model Acceptance

- Status: COMPLETE — WP-0300 package review pending
- Dependency: DEV-0301 complete
- Scope: neutral principal and tenant-membership identity only
- Migration: deferred to DEV-0308
- Authorization/API/support effect: none

No governing record defines production role names or permissions. DEV-0302
therefore stores a canonical opaque `role_key` and assigns no powers. DEV-0310
owns policy enforcement.

| ID | Acceptance criterion |
|---|---|
| AC-01 | Principal uses stable UUIDv4 and closed `USER`/`SERVICE` kind |
| AC-02 | Provider and subject are nonempty, bounded, and form a unique external identity |
| AC-03 | Membership always binds one principal, tenant, and canonical opaque role key |
| AC-04 | No membership represents implicit global access |
| AC-05 | Principal and membership preserve timezone-aware creation actor/time and positive version |
| AC-06 | Domain records are immutable |
| AC-07 | Additive ORM contracts define scoped uniqueness and tenant/principal foreign keys |
| AC-08 | No permission vocabulary, authorization, credentials, API, migration, evidence access, or support effect is introduced |

## Limitations

- Authentication-provider selection and subject verification remain
  owner-controlled.
- Role keys have no permissions until DEV-0310 binds an approved policy.
- Case membership and case authorization remain later tasks.

## Validation results

- Focused DEV-0301/0302 suite: 28 passed.
- Full backend regression: 184 passed with the accepted TestClient warning.
- Legacy characterization: 5 passed.
- Python compilation and diff check: passed.
- No migration was created; DEV-0308 retains migration ownership.
- AC-01 through AC-08: PASS.
