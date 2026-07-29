# DEV-0605 — Relative-Path Canonicalization and Traversal Semantics

- Status: COMPLETE — candidate-only infrastructure
- Decisions: DEC-0067; DEC-0068
- Profile: FOR-016
- Validation: QMS-015
- Support effect: none

| ID | Acceptance criterion | Requirements | Result |
|---|---|---|---|
| AC-01 | Immutable exact raw/dynamic-type/query/locator/scope provenance is retained. | FOR-PROV-001; DEV-0406-R01 | PASS |
| AC-02 | Raw path, storage class, lexical tokens, empty, separators, absolute indicators, dot/parent segments, Unicode/encoding, canonical comparison, and safety state remain separate. | DEV-0605 authorization; FOR-016 | PASS |
| AC-03 | No unsafe path is repaired; no trimming, separator conversion, dot removal, case folding, Unicode normalization, or BLOB decoding occurs. | AGENTS.md; FOR-016 | PASS |
| AC-04 | Caller supplies positive character, byte, and segment ceilings; excess fails closed before token retention. | SEC-RES-001 | PASS |
| AC-05 | NULL, non-TEXT, unavailable, failure, unevaluated, indeterminate, and resource states remain distinct. | FOR-ERR-001 | PASS |
| AC-06 | Deterministic serialization excludes raw BLOB bytes and host paths. | SEC-DATA-001; QMS-TST-002 | PASS |
| AC-07 | Query v1/v2 adapters enforce complete scope and provenance. | FOR-MAN-002; FOR-MAN-003 | PASS |
| AC-08 | No filesystem, physical resolution/existence, artifact, parser, API, migration, persistence, or support behavior exists. | ARC-002; DEC-0067 | PASS |
| AC-09 | Focused, integration, regression, compilation, dependency, migration, and hygiene checks pass. | QMS-TRC-001 | PASS |
