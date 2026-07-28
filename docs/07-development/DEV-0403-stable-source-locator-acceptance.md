# DEV-0403 — Stable Source-Locator Model

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | Locator uses immutable UUIDv4 internal identity scoped to tenant, case, and source artifact. |
| AC-02 | Raw and normalized values remain separate and unchanged. |
| AC-03 | Locator kind and normalization method are explicit canonical keys. |
| AC-04 | Empty, oversized, or NUL-containing values fail closed. |
| AC-05 | Contract performs no filesystem access and expresses no presence, readability, completeness, or support claim. |
| AC-06 | Additive ORM metadata remains separate; migration is deferred to DEV-0410. |
| AC-07 | Synthetic focused/full regressions pass without API, parser, evidence access, or support change. |

DEV-0403-R01 through R07 map one-to-one to these criteria under AGENTS.md raw
value and provenance rules, ARC-001, ARC-002, and WP-0400.

## Validation record

All AC-01 through AC-07 pass. Focused: 8 passed. Backend: 228 passed with
the accepted warning. Compilation and diff checks pass. No filesystem access,
parser, API, migration, or support change occurred.
