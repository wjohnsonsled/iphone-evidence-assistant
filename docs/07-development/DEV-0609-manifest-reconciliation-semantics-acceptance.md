# DEV-0609 — Duplicate, Orphan, Reconciliation, and Absence Semantics

- Status: COMPLETE — candidate-only infrastructure
- Decisions: DEC-0073; DEC-0074
- Profile: FOR-019
- Validation: QMS-018
- Support effect: none

| ID | Acceptance criterion | Requirements | Result |
|---|---|---|---|
| AC-01 | Repeated row locator, raw TEXT fileID, canonical fileID, and domain/path tuple remain separate pattern types. | DEV-0609 authorization; FOR-019 | PASS |
| AC-02 | Inputs require compatible versioned profiles and complete tenant/case/source/artifact/run/locator provenance. | FOR-PROV-001; SEC-ISO-001 | PASS |
| AC-03 | Raw BLOB identifiers are not textualized; lexical/canonical repetition is not content or physical identity. | DEC-0063; FOR-014 | PASS |
| AC-04 | Duplicate, orphan, missing-object, and absence conclusions are always `NOT_ESTABLISHED`. | AGENTS.md; FOR-019 | PASS |
| AC-05 | Physical inventory and comparison-universe completeness remain false with explicit permanent blockers. | FOR-019; RSK-0034 | PASS |
| AC-06 | Zero patterns is distinct from failure/partial/cancellation and does not establish absence. | FOR-ERR-001; COV-GOV-002 | PASS |
| AC-07 | Positive caller row/group/member/byte/memory/time limits and cancellation preserve completed work and add blockers. | SEC-RES-001 | PASS |
| AC-08 | Cross-scope and incompatible-profile inputs fail closed. | SEC-ISO-001; FOR-MAN-004 through FOR-MAN-006 | PASS |
| AC-09 | No filesystem, physical inventory/resolution, hashing, parser, API, persistence, migration, real evidence, or support behavior exists. | ARC-002; DEC-0073 | PASS |
| AC-10 | Focused, integration, regression, compilation, dependency, migration, and hygiene checks pass. | QMS-TRC-001 | PASS |
