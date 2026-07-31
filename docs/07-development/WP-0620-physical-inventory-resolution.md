# WP-0620 — Physical Apple Backup Object Inventory and Resolution

## Status and scope

- Status: IN_PROGRESS
- Decision: DEC-0081
- Tasks: DEV-0621 through DEV-0626
- Migration policy: none; head remains `0005_processing_idempotency`
- Support effect: none

WP-0620 implements immutable candidate observations for root-confined physical
filesystem entries, regular-object SHA-256 and instability, exact provisional
fileID resolution, separate physical coverage/reconciliation, synthetic
fixtures, and an internal validation report. It performs no content parsing or
artifact interpretation.

## Task sequence

1. DEV-0621 — physical profile, authorized-root confinement, filesystem type,
   deterministic locator, ordering, and caller resource policy.
2. DEV-0622 — streaming SHA-256, pre/post stat mutation detection, immutable
   provenance, and operational failure distinctions.
3. DEV-0623 — exact v1 synthetic layout resolution with all required outcomes.
4. DEV-0624 — separate physical/Manifest universes, factual coverage, and
   duplicate/orphan/absence blockers.
5. DEV-0625 — at least 50 project-original deterministic scenarios and package
   integration.
6. DEV-0626 — candidate validation report and final work-package review.

## Permanent boundaries

- Physical observation is not device existence, authenticity, artifact type,
  deletion, concealment, tampering, relevance, or backup completeness.
- fileID-to-name equality is not content verification or an Apple guarantee.
- SHA-256 does not prove pre-intake authenticity and never replaces evidence
  identity.
- No match is not deletion; unmatched is not automatically orphaned.
- Synthetic characterization is not Apple-produced validation.
- No capability is Supported.

