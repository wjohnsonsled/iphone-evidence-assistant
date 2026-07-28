# DEV-0304 — Artifact Support-Status Model and Parser Quarantine Enforcement

- Status: COMPLETE — owner approved in DEC-0014
- Dependencies: DEV-0003 and DEV-0004 complete
- Governing scope: DEV-009, FOR-004, FOR-006, ARC-001, ARC-002
- Support effect: none; the supported registry remains empty

## Requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0304-R01 | Model FOR-004 lifecycle and processing-result statuses separately | AC-01 exact closed enums are deterministic and cannot conflate lifecycle with results |
| DEV-0304-R02 | Provide a separate, versioned supported registry with no legacy dependency | AC-02 default composition is empty and static import tests find no legacy registry or parser import |
| DEV-0304-R03 | Disable unknown, candidate, legacy, experimental, compatibility, excluded, and mismatched parser/profile requests | AC-03 each disposition and identity/profile mismatch fails closed before parser execution |
| DEV-0304-R04 | Require complete approval and validation metadata for any future registry entry | AC-04 malformed entries and duplicate identities are rejected deterministically |
| DEV-0304-R05 | Admit output only through an authorization issued by the exact registry and only for supported success statuses | AC-05 counterfeit/cross-registry authorization, failure statuses, incomplete provenance, and unreconciled coverage are rejected |
| DEV-0304-R06 | Keep no-record success distinct from failure and prohibit records on no-record success | AC-06 zero-record and failure matrices pass |
| DEV-0304-R07 | Preserve default API and legacy compatibility behavior without crossing boundaries | AC-07 default health-only, legacy characterization, and full regressions pass |
| DEV-0304-R08 | Add no parser execution, evidence parsing, migration, production API, real evidence, or support promotion | AC-08 diff and boundary tests pass |

Only synthetic metadata and in-memory records may be used. A synthetic
authorized-entry fixture tests the mechanism; it is not a repository approval
record and cannot promote a parser or artifact.

## Validation record

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | Exact lifecycle and processing-result enum test |
| AC-02 | PASS | Empty `supported-registry-v0-empty`; AST import-boundary test |
| AC-03 | PASS | Six nonapproved dispositions plus identity/profile/date denial matrix |
| AC-04 | PASS | Required approval metadata and duplicate-entry tests |
| AC-05 | PASS | Registry-instance authorization and output admission matrix |
| AC-06 | PASS | Zero-result, record-bearing success, and failed result remain distinct |
| AC-07 | PASS | Backend 104/104; legacy characterization 5/5 |
| AC-08 | PASS | No executor, evidence fixture, migration, API, registry entry, or support change |

Commands: focused and full pytest with the documented repository-local
`--basetemp` workaround; legacy unittest discovery; compileall; lock validator;
`pip check`; and `git diff --check`.

Limitation: approval metadata is an application contract, not a cryptographic
owner authorization. Before a nonempty registry is permitted, a later approved
task must bind registry snapshots to authorized persistent configuration and
immutable audit. The TestClient deprecation warning remains accepted debt.
