# DEV-0305 — Evidence-Source Tenant and Case Linkage

- Status: COMPLETE — WP-0300 package review pending
- Dependencies: DEV-0203 and DEV-0303 complete
- Scope: evidence-source identity and enforced tenant/case relationship
- Migration: deferred to DEV-0308
- Evidence/support effect: none

| ID | Acceptance criterion |
|---|---|
| AC-01 | Evidence source has stable UUIDv4 identity distinct from content hash |
| AC-02 | Factory derives both tenant and case identifiers from a SecurityCase |
| AC-03 | Source type and locator are nonempty, trimmed, and bounded |
| AC-04 | Registration actor/time and positive version are retained immutably |
| AC-05 | ORM contract references tenant and uses a composite tenant/case foreign key |
| AC-06 | Cross-tenant case/source combinations fail at the relational boundary |
| AC-07 | Existing WP-0250 evidence source IDs remain compatible and no duplicate registry is created |
| AC-08 | No path access, hashing, validation, parser, API, migration, authorization, or support effect |

## Validation results

- Focused source/case suite: 14 passed.
- Full backend regression: 198 passed with the accepted TestClient warning.
- Legacy characterization: 5 passed.
- Python compilation and diff check: passed.
- Cross-tenant composite foreign-key denial: passed.
- No migration was created; AC-01 through AC-08 pass.
