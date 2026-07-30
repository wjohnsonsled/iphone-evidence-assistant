# DEV-0608 — Inventory Provenance and Factual Coverage

- Status: COMPLETE — candidate-only infrastructure
- Decisions: DEC-0075; DEC-0076
- Profile: FOR-020
- Validation: QMS-019
- Support effect: none

| ID | Acceptance criterion | Requirements | Result |
|---|---|---|---|
| AC-01 | Immutable observations preserve complete inventory, scope, source/copy/run, profile, locator, count, continuation, timestamp, implementation, and limitation provenance. | DEC-0075; FOR-PROV-001 | PASS |
| AC-02 | Requested, authorized, examined, completion, termination, resource, mutation, compatibility, comparison, absence, physical-inventory, and limitation dimensions remain independent. | DEV-0608 authorization; FOR-020 | PASS |
| AC-03 | Complete, successful-zero, partial, resource-terminated, cancelled, failed, mutation-terminated, and indeterminate outcomes remain distinct. | FOR-ERR-001; FOR-020 | PASS |
| AC-04 | Query/resource/row provenance, tenant, case, source, artifact, database, run, and controlled-copy identity fail closed. | SEC-TEN-001; FOR-PROV-001 | PASS |
| AC-05 | Multi-run composition requires explicit compatible identities/profiles, prior links, request-locator continuity, unique ordered components, unchanged inputs, and a complete final run. | DEC-0075; FOR-020 | PASS |
| AC-06 | Every unmet absence prerequisite records a blocker; row coverage never implies artifact, parser, physical-object, backup, normalized-record, or user-activity completeness. | AGENTS.md; FOR-020 | PASS |
| AC-07 | Resource and operational termination preserves finalized counts/locators and prohibits absence eligibility without asserting evidence loss. | SEC-RES-001; FOR-020 | PASS |
| AC-08 | Canonical serialization is deterministic and contains no host paths, temporary paths, secrets, raw BLOBs, or raw evidence values. | SEC-DATA-001; QMS-TRC-001 | PASS |
| AC-09 | At least 40 deterministic synthetic scenarios cover required states, composition, isolation, provenance, and prohibited conclusions. | DEC-0075 | PASS — 41 |
| AC-10 | No migration, persistence, physical inventory, parser activation, API, real evidence, Supported entry/record, or support promotion is introduced. | ARC-002; DEC-0075 | PASS |
| AC-11 | Focused, combined Manifest, backend, legacy, compilation, dependency, migration, and hygiene checks pass. | QMS-TRC-001 | PASS |

