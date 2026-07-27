# WP-0250 — Evidence Integrity Infrastructure Acceptance

- Status: VALIDATION_PENDING — OWNER PACKAGE REVIEW
- Tasks: DEV-0251 through DEV-0265
- Architecture: ARC-001 and authorized additive ARC-002 contract
- Implementation: relational MVP; application-level coordination controls
- Support/API effect: none

## Task and acceptance matrix

| Task | Acceptance criteria |
|---|---|
| DEV-0251 | Typed tenant/case-scoped evidence object rejects missing identity and prohibited mutable content |
| DEV-0252 | Application UUIDv4 is stable, globally unique, path/content independent; equal content may have distinct UUIDs |
| DEV-0253 | Published transition table is exhaustive; invalid/terminal/quarantine transitions fail atomically and audit |
| DEV-0254 | SHA-256 streaming produces immutable success/failure observations with purpose, role, actor, version, size, and time |
| DEV-0255 | Verification distinguishes verified, mismatch, unstable, missing, and operational failure without overwriting history |
| DEV-0256 | Application locks allow only approved intents; conflicts, stale locks, releases, and prohibited writes fail closed |
| DEV-0257 | Custody events are immutable, tenant scoped, ordered, prior-linked, actor-attributed, and hash-reference capable |
| DEV-0258 | Closed audit taxonomy and append-only service record success/failure without sensitive evidence content |
| DEV-0259 | Relational provenance nodes/edges preserve tenant, case, source locator, parser identity/version where required |
| DEV-0260 | Validation detects missing nodes, dangling edges, cross-tenant edges, invalid derivation cycles, and broken citation paths |
| DEV-0261 | Mutation checkpoints preserve prior hashes, set integrity state, audit mismatch/instability, and never infer cause |
| DEV-0262 | Policy permits only verified, locked, provenance-valid, nonlegacy, approved-controlled candidate inputs |
| DEV-0263 | Typed parser contract declares identity/version/family/profiles plus validation, parse, provenance, coverage, limitations, self-test |
| DEV-0264 | Harness rejects writes, missing provenance/version/coverage, silent omissions, unsupported profiles, integrity bypass, legacy/support claims |
| DEV-0265 | Deterministic synthetic end-to-end validation and full regressions pass; relational migration is additive/reversible; no support change |

## Common controls

- Synthetic fixtures only.
- SHA-256 required; observations append-only.
- Evidence UUID is not a content hash.
- Complete tenant/case scope is required.
- Source write operations are absent from approved services.
- No graph database, external service, signature, nonrepudiation, API, parser
  promotion, real evidence, deployment, or remote Git operation.

## Validation result

All DEV-0251 through DEV-0265 criteria pass against deterministic synthetic
fixtures. Focused 11/11, backend 82/82, characterization 5/5, compilation,
single-head migration upgrade/downgrade generation, and diff checks pass. The
package remains candidate infrastructure pending owner review.
