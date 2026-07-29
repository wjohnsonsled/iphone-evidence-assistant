# DEV-0603 — Canonical Identifier Framework and Manifest fileID Profile

- Status: COMPLETE — candidate-only infrastructure
- Implementation decision: DEC-0063
- Completion decision: DEC-0064
- Dependencies: DEV-0602 and DEV-0602A — COMPLETE
- Validation package: QMS-013
- Support effect: none

| ID | Acceptance criterion | Requirements | Result |
|---|---|---|---|
| AC-01 | A reusable immutable, profile-driven generic identifier framework has controlled classes, storage classes, outcomes, transformations, comparison modes, serialization, lineage, and limitations. | DEC-0063; DEV-0406-R01 | PASS |
| AC-02 | Only proven query v1/v2 `Files.fileID` observations enter through production adapters; complete scope/query/locator/raw provenance is required. | FOR-MAN-002 through FOR-MAN-004 | PASS |
| AC-03 | Profile v1 recognizes only exactly 40 ASCII hex characters and canonicalizes only recognized values to lowercase without repair. | DEC-0063; FOR-014 | PASS |
| AC-04 | TEXT/BLOB/NULL/INTEGER/REAL and all required unavailable/failure states remain lossless and distinct. | DEV-0406-R01; FOR-MAN-004 | PASS |
| AC-05 | Authorized BLOBs use strict ASCII only; arbitrary 20-byte BLOBs are not hex-expanded, hashed, decoded with replacement, or interpreted. | DEC-0063; FOR-014 | PASS |
| AC-06 | Ordered transformation provenance contains only NONE, strict ASCII decode, and case canonicalization when performed. | FOR-PROV-001; FOR-MAN-004 | PASS |
| AC-07 | Explicit raw/canonical/not-comparable modes enforce profile and tenant/case compatibility with bounded equality language and no fallback. | SEC-AUTH-001; FOR-MAN-004 | PASS |
| AC-08 | Deterministic serialization is BLOB-safe and immutable reruns create new run-bound observations with prior lineage. | QMS-TST-002; DEC-0052 | PASS |
| AC-09 | Caller-supplied batch ceilings and cancellation preserve completed normalization/comparison observations. | SEC-RES-001; FOR-MAN-004 | PASS |
| AC-10 | The 40-case synthetic corpus and query v1/v2 integrations cover success, malformed, storage, comparison, scope, provenance, rerun, resource, and boundary behavior. | QMS-TST-001; QMS-TST-002 | PASS |
| AC-11 | No hash, physical resolution, file-existence, domain/path/flags/blob interpretation, duplicate/orphan/absence, API, migration, parser, supported record, real evidence, or support behavior exists. | AGENTS.md; DEC-0063 | PASS |
| AC-12 | Focused, combined, backend, legacy, compilation, dependency, migration, and hygiene validation passes. | QMS-TRC-001 | PASS |

Final validation results are recorded in QMS-013. DEC-0064 records the
authorized autonomous candidate-level review. Nothing is promoted to Supported.
