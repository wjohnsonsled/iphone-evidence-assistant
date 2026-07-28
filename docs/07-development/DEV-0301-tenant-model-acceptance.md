# DEV-0301 — Tenant Model Acceptance

- Status: COMPLETE — WP-0300 package review pending
- Dependency: DEV-0103 complete
- Architecture: ARC-001 §§7, 10, 12
- Scope: neutral application tenant identity and additive ORM contract
- Migration: deferred to DEV-0308 package migration
- Support/API effect: none

## Requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0301-R01 | Define a stable tenant boundary identity | AC-01 application-generated UUIDv4 is stable and independent of name/slug |
| DEV-0301-R02 | Use a deterministic canonical locator | AC-02 slug uses a closed lowercase ASCII/hyphen grammar, 1–63 characters, and rejects malformed input |
| DEV-0301-R03 | Retain human-readable identity separately | AC-03 display name remains separate, nonempty, trimmed, and bounded |
| DEV-0301-R04 | Retain creation provenance | AC-04 timezone-aware UTC creation time and creating actor UUID are mandatory |
| DEV-0301-R05 | Make the domain contract immutable and versioned | AC-05 frozen records reject mutation and version must be positive |
| DEV-0301-R06 | Define an additive relational model | AC-06 `security_tenants` has UUID primary key, unique slug, identity/provenance fields, and positive version constraint without altering legacy tables |
| DEV-0301-R07 | Avoid premature authorization semantics | AC-07 no membership, role, user, case, authorization service, repository, route, or production tenancy policy is introduced |
| DEV-0301-R08 | Preserve quarantine and support boundaries | AC-08 no legacy import, evidence access, parser, API exposure, migration, or support promotion |

## Limitations

- The model defines an internal tenant isolation key; it does not choose a
  billing, legal-organization, deployment, or production tenancy model.
- Database persistence and constraints are not active until the additive
  WP-0300 migration in DEV-0308.
- Membership, users/roles, cases, evidence linkage, authorization enforcement,
  and cross-tenant tests remain DEV-0302 through DEV-0310.

## Validation results

- Focused tenant/integrity suite: 25 passed.
- Full backend regression: 170 passed with the accepted TestClient warning.
- Legacy characterization: 5 passed.
- Python compilation and `git diff --check`: passed.
- No migration was created; DEV-0308 remains the additive package migration.
- AC-01 through AC-08: PASS.
