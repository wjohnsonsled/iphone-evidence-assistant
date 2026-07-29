# DEV-0604 — Manifest Domain Grammar and Interpretation

- Status: COMPLETE — candidate-only infrastructure
- Implementation decision: DEC-0065
- Completion decision: DEC-0066
- Dependencies: DEV-0602 and DEV-0603 — COMPLETE
- Validation package: QMS-014
- Profile: FOR-015
- Support effect: none

| ID | Acceptance criterion | Requirements | Result |
|---|---|---|---|
| AC-01 | Versioned immutable observations preserve exact raw value, SQLite storage class, and complete query/locator/scope provenance. | FOR-PROV-001; DEV-0406-R01 | PASS |
| AC-02 | Only proven query v1/v2 `Files.domain` observations enter through production adapters. | FOR-MAN-002; FOR-MAN-003 | PASS |
| AC-03 | Exact literal and prefixed candidate grammar is case sensitive, deterministic, and performs no implicit transformation. | DEC-0065; FOR-015 | PASS |
| AC-04 | Raw observation, lexical/grammar outcome, canonical representation, family, and opaque application/group/plugin components remain separate. | DEV-0604; FOR-015 | PASS |
| AC-05 | Unknown, malformed, empty, NULL, dynamic-type, unavailable, failure, unevaluated, and indeterminate states remain explicit and fail closed. | FOR-ERR-001; DEV-0406-R01 | PASS |
| AC-06 | No trimming, repair, case folding, Unicode normalization, broad coercion, or invented semantics occurs. | AGENTS.md; FOR-015 | PASS |
| AC-07 | Deterministic serialization does not expose raw BLOB bytes or host paths. | SEC-DATA-001; QMS-TST-002 | PASS |
| AC-08 | Tests cover literal/prefixed/unknown/malformed/storage/failure/provenance/determinism and query v1/v2 integration. | QMS-TST-001; QMS-TST-002 | PASS |
| AC-09 | No installation, execution, activity, ownership, existence, completeness, compatibility, artifact, parser, or support conclusion is produced. | AGENTS.md; DEC-0065 | PASS |
| AC-10 | No filesystem, hash, API, migration, persistence, legacy parser, registry, supported-record, or real-evidence behavior exists. | ARC-002; DEC-0065 | PASS |
| AC-11 | Full focused, integration, regression, compilation, dependency, migration, and hygiene matrix passes. | QMS-TRC-001 | PASS |

QMS-014 records the complete validation matrix. DEC-0066 records authorized
candidate-level completion. Candidate completion does not change support status.
