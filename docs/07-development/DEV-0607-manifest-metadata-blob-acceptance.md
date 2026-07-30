# DEV-0607 — Manifest Metadata-BLOB Characterization

- Status: COMPLETE — candidate-only infrastructure
- Decisions: DEC-0071; DEC-0072
- Profile: FOR-018
- Validation: QMS-017
- Support effect: none

| ID | Acceptance criterion | Requirements | Result |
|---|---|---|---|
| AC-01 | Exact raw-BLOB/source/query/locator/scope/run provenance and explicit internal authorization are required. | FOR-PROV-001; FOR-013 | PASS |
| AC-02 | Raw observation, format recognition, syntactic decoding, typed scalar/reference nodes, and interpretation/support state remain separate. | DEV-0607 authorization; FOR-018 | PASS |
| AC-03 | Only exact `bplist00` is decoded by an iterative bounded scanner; unknown/malformed/unsupported structures fail closed. | FOR-018; SEC-VAL-001 | PASS |
| AC-04 | No native deserialization, dynamic loading, arbitrary class/object instantiation, or `plistlib` exists in the implementation. | SEC-EXEC-001 | PASS |
| AC-05 | Caller supplies positive BLOB/object/depth/string/collection/memory/time ceilings and cancellation; completed nodes survive termination. | SEC-RES-001 | PASS |
| AC-06 | Object references are range checked; graph cycles and depth excess fail closed. | SEC-VAL-001 | PASS |
| AC-07 | DATA bytes and raw source BLOBs are not serialized; UID/class/key/scalar meaning remains uninterpreted. | SEC-DATA-001; FOR-018 | PASS |
| AC-08 | Empty, unknown format, malformed, NULL/type mismatch, unavailable/failure, cancelled, and resource states remain distinct. | FOR-ERR-001 | PASS |
| AC-09 | Query v1 and explicitly raw-BLOB-authorized query v2 adapters retain scope and provenance. | FOR-MAN-002; FOR-MAN-003 | PASS |
| AC-10 | No filesystem, physical conclusion, parser, API, persistence, migration, real evidence, artifact/support behavior exists. | ARC-002; DEC-0071 | PASS |
| AC-11 | Focused, integration, regression, compilation, dependency, migration, and hygiene checks pass. | QMS-TRC-001 | PASS |
