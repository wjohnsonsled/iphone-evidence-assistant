# DEV-0404 — Parser Identity and Version Model

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | Parser metadata has immutable UUIDv4 identity and exact parser/version pair. |
| AC-02 | Artifact family, parser-contract version, and declaration reference are explicit. |
| AC-03 | Identifiers are canonical and malformed metadata fails closed. |
| AC-04 | Candidate registration always yields CANDIDATE and cannot create SUPPORTED state. |
| AC-05 | DEV-0304 supported registry remains separate and empty. |
| AC-06 | ORM uniqueness prevents duplicate parser/version identities; migration remains DEV-0410. |
| AC-07 | No parser execution, evidence access, API, support promotion, or legacy dependency occurs. |

DEV-0404-R01 through R07 map to these criteria under ARC-002, DEV-0263,
DEV-0304, DEC-0037, AGENTS.md, and WP-0400.

## Validation record

All AC-01 through AC-07 pass. Focused: 35 passed using the documented
repository-local pytest temp workaround. Backend: 233 passed with the accepted
TestClient warning. Compilation and diff checks pass. The supported registry
remains empty; no parser execution, migration, evidence, API, or support change.
