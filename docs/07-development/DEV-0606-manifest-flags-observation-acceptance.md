# DEV-0606 — Flags and File Metadata Normalization

- Status: COMPLETE — candidate-only infrastructure
- Decisions: DEC-0069; DEC-0070
- Profile: FOR-017
- Validation: QMS-016
- Support effect: none

| ID | Acceptance criterion | Requirements | Result |
|---|---|---|---|
| AC-01 | Exact raw value, SQLite storage/value state, and complete query/locator/scope provenance remain immutable. | FOR-PROV-001; DEV-0406-R01 | PASS |
| AC-02 | INTEGER representation, bit width, set-bit positions, profile version, and limitations remain separate. | DEV-0606 authorization; FOR-017 | PASS |
| AC-03 | Because no meaning is approved, known meanings remain empty and all set bits remain explicitly unknown. | Autonomous Manifest authorization; FOR-017 | PASS |
| AC-04 | Zero, negative, NULL, non-INTEGER, unavailable, failure, unevaluated, indeterminate, and resource states remain distinct. | FOR-ERR-001 | PASS |
| AC-05 | Caller supplies a positive bounded bit-width policy; excess fails closed before bit enumeration. | SEC-RES-001 | PASS |
| AC-06 | Deterministic serialization excludes raw BLOB bytes and preserves limitations. | SEC-DATA-001; QMS-TST-002 | PASS |
| AC-07 | Query v1/v2 adapters enforce source scope and complete provenance. | FOR-MAN-002; FOR-MAN-003 | PASS |
| AC-08 | No file/deletion/tampering/corruption/physical/support inference, BLOB decoding, filesystem, parser, API, persistence, migration, or support behavior exists. | ARC-002; DEC-0069 | PASS |
| AC-09 | Focused, integration, regression, compilation, dependency, migration, and hygiene checks pass. | QMS-TRC-001 | PASS |
