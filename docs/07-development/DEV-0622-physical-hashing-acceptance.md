# DEV-0622 — Physical-Object Hashing, Mutation, and Provenance Acceptance

## Scope

Add a candidate-only adapter from an eligible DEV-0621 inventory observation to
the existing WP-0250 SHA-256 integrity registry. The adapter does not discover
files, interpret content, establish authenticity, or promote support.

## Acceptance results

| ID | Criterion | Evidence | Result |
|---|---|---|---|
| AC-01 | Hash only eligible, root-confined inventory observations in the same tenant/case/source scope. | Scope, eligibility, and resolved depth-two confinement tests. | PASS |
| AC-02 | Use SHA-256 through the existing append-only integrity registry and retain its observation identity. | Registry integration and audit-event assertions. | PASS |
| AC-03 | Preserve source, controlled source, run, locator profile, byte count, algorithm, digest, and observation time. | Complete-provenance focused test. | PASS |
| AC-04 | Compare pre/post size, nanosecond mtime, device, and inode; distinguish source instability from operational failure. | Mutation-after-inventory and registry failure paths. | PASS |
| AC-05 | Enforce caller-supplied individual and aggregate byte ceilings and cancellation before reading. | Resource and cancellation focused tests. | PASS |
| AC-06 | State permanent limitations and make no authenticity, Apple compatibility, artifact, parser, or support claim. | Frozen observation limitations and governance review. | PASS |
| AC-07 | Focused, integration, compilation, regression, and diff checks pass. | Recorded commands below. | PASS |

## Commands and results

- `pytest backend/tests/test_physical_inventory_hashing.py -q`: 3 passed.
- Physical inventory/hash focused suite: 20 passed, 2 skipped.
- Inventory/integrity integration suite: 33 passed, 2 skipped.
- Complete backend regression: 796 passed, 2 skipped, 1 accepted warning.
- Legacy regression: 5 passed.
- Compilation and `git diff --check`: passed.
- Skips are live Windows symlink fixture creation denied by the host; deterministic
  symlink and reparse-point denial tests pass.

## Limitations

- The physical layout and locator profiles remain provisional and synthetic.
- Filesystem metadata cannot prove uninterrupted source stability outside the
  bounded observation interval.
- A digest identifies observed bytes only. It proves neither authenticity nor
  artifact meaning, compatibility, completeness, or Supported status.
- No real or Apple-produced evidence was used.
