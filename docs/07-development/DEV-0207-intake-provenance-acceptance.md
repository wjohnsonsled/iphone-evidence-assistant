# DEV-0207 — Intake Provenance Model Acceptance

- Status: COMPLETE — WP-0200 package review pending
- Dependency: DEV-0203 complete
- Architecture: ARC-001, ARC-002, DEC-0011
- Implementation authority: WP-0250 relational `ProvenanceService`
- Support effect: none

## Scope reconciliation

WP-0250 is the sole provenance authority. DEV-0207 adopts its relational nodes,
relationships, and validation service for intake and creates no intake-specific
graph or store.

The minimum intake path is:

`CONTROLLED_COPY --COPIED_FROM--> SOURCE_ARTIFACT --BELONGS_TO--> EVIDENCE_SOURCE`

This relationship direction permits a derived controlled copy to resolve
deterministically back to the submitted evidence source.

## Requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0207-R01 | Reuse WP-0250 provenance contracts | AC-01 intake uses `ProvenanceNode`, `ProvenanceEdge`, and `ProvenanceService`; no competing model is introduced |
| DEV-0207-R02 | Represent the complete minimum intake path | AC-02 tenant/case-scoped evidence-source, source-artifact, and controlled-copy nodes link with `BELONGS_TO` and `COPIED_FROM` |
| DEV-0207-R03 | Preserve stable source locators | AC-03 nodes retain caller-controlled stable locators for the source root, source-relative artifact, and controlled copy |
| DEV-0207-R04 | Resolve lineage deterministically | AC-04 controlled copy resolves through the source artifact to the evidence source |
| DEV-0207-R05 | Fail closed on broken lineage | AC-05 missing nodes, dangling edges, unresolved paths, and derivation cycles fail |
| DEV-0207-R06 | Enforce tenant and case boundaries | AC-06 cross-tenant and cross-case edges are rejected |
| DEV-0207-R07 | Preserve boundaries | AC-07 synthetic identities only; no parser, API, persistence, graph database, real evidence, or support promotion |

## Validation record

All seven criteria pass in `backend/tests/test_intake_provenance.py` together
with the WP-0250 provenance tests. The focused suite verifies the complete
lineage path, exact relationships and locators, dangling/unresolved behavior,
cycle denial, and tenant/case isolation.

## Limitations

- This is an in-memory relational reference service pending a transactional
  repository adapter.
- Stable locator selection is the caller's responsibility until integrated
  intake orchestration binds it to a registered evidence root.
- Provenance validity proves model connectivity and scope, not authenticity,
  Apple compatibility, evidentiary completeness, or support.

## Commands and results

- `python -m pytest backend/tests/test_intake_provenance.py backend/tests/test_integrity_infrastructure.py -q`
  — 13 passed.
- `python -m pytest backend/tests -q` — 139 passed with the previously accepted
  third-party TestClient deprecation warning.
- `python -m unittest discover -s tests -q` — 5 passed.
- `python -m compileall -q backend/app backend/tests` — passed.
- `git diff --check` — passed.
