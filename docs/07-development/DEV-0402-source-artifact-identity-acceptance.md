# DEV-0402 — Source-Artifact Identity Model

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | Source artifact has immutable UUIDv4 identity distinct from evidence UUID and content hash. |
| AC-02 | Tenant, case, evidence source, processing run, and WP-0250 evidence UUID are explicit. |
| AC-03 | Registration requires exact authorization and matching run/source/case scope. |
| AC-04 | Actor/time and authorization policy identity/version are retained. |
| AC-05 | Artifact-family key is canonical; source locator is deferred to DEV-0403. |
| AC-06 | Registration contains no support status and cannot promote file presence to support. |
| AC-07 | Additive ORM metadata is separate from legacy models; migration remains DEV-0410. |
| AC-08 | Synthetic focused/full regressions pass with no evidence access, parsing, API, or support change. |

Requirements DEV-0402-R01 through R08 map one-to-one to these criteria under
ARC-001, ARC-002, WP-0250 identity rules, DEC-0037, and AGENTS.md.

## Validation record

All AC-01 through AC-08 pass. Focused: 9 passed. Backend: 223 passed with
the accepted warning. Compilation and diff checks pass. No source filesystem,
parser, API, migration, or support status was used or changed.
