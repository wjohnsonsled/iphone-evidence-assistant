# DEV-0303 — Case Model Acceptance

- Status: COMPLETE — WP-0300 package review pending
- Dependency: DEV-0301 complete
- Scope: tenant-scoped supported-boundary case identity
- Legacy effect: none; existing `cases` remains quarantined
- Migration: deferred to DEV-0308

| ID | Acceptance criterion |
|---|---|
| AC-01 | Case uses a stable application-generated UUIDv4 |
| AC-02 | Every case binds exactly one tenant UUID with no global/unscoped case |
| AC-03 | Case name is separate, nonempty, trimmed, and bounded |
| AC-04 | Creation time is timezone-aware and creating actor is retained |
| AC-05 | Domain record is immutable and positively versioned |
| AC-06 | Additive `security_cases` ORM contract has tenant foreign key and tenant/name lookup index |
| AC-07 | Existing legacy `cases` metadata remains separate and unchanged |
| AC-08 | No case lifecycle, membership, repository, authorization, route, migration, evidence access, or support effect |

## Limitations

- Case authorization and case-specific membership are not implemented.
- Existing legacy case routes and persistence remain unavailable from the
  default supported composition root.
- DEV-0308 owns the additive package migration.

## Validation results

- Focused tenant/principal/case suite: 34 passed.
- Full backend regression: 190 passed with the accepted TestClient warning.
- Legacy characterization: 5 passed.
- Python compilation and diff check: passed.
- No migration was created.
- AC-01 through AC-08: PASS.
