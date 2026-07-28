# DEV-1101 — Supported Parser Registry

- Status: COMPLETE
- Owner readiness decision: 2026-07-28
- Dependencies: WP-0400, DEV-0262, DEV-0263, DEV-0264 — COMPLETE
- Reused implementation: DEV-0304 supported registry
- Support effect: none; production registry entries remain zero

## Scope

Adopt the DEV-0304 fail-closed registry as the sole registry for the future
supported processing pipeline and complete its permanent promotion-traceability
contract. No parser is executed or promoted.

## Acceptance criteria

| ID | Criterion | Requirements | Result |
|---|---|---|---|
| AC-01 | Production composition returns a versioned registry with exactly zero entries | ARC-001; ARC-002; DEV-0304-R02 | PASS |
| AC-02 | An entry permanently requires Owner Decision ID, Validation Package ID, Acceptance Record IDs, Promotion Date, and Current Support Status | QMS-SUP-001 | PASS |
| AC-03 | Missing promotion metadata, empty profiles, duplicates, premature use, retired use, identity mismatch, and schema mismatch fail closed | QMS-SUP-001; DEV-0304-R03/R04 | PASS |
| AC-04 | Only the exact controlled current status `SUPPORTED` is registry-admissible | FOR-004; all-or-nothing rule | PASS |
| AC-05 | Registry ordering and acceptance-record ordering are deterministic and registry authorization is instance-bound | ARC-002; QMS-TST-002 | PASS |
| AC-06 | Supported store remains empty and no legacy import, parser execution, evidence read, migration, API, or support promotion occurs | ARC-001; FOR-006; DEC-0049 | PASS |

## Validation and limitations

Validation uses synthetic metadata only. A synthetic registry entry demonstrates
the fail-closed mechanism and is not an approval record. Registry metadata is
an application contract, not a cryptographic owner signature. Persistent
owner-controlled configuration and immutable audit binding remain required
before any real entry can be composed.

Focused validation: 32 passed. Full backend regression: 316 passed with the
accepted TestClient deprecation warning. Legacy characterization: 5 passed.
Compilation, dependency-lock validation, installed-package consistency, and
diff checks passed.
