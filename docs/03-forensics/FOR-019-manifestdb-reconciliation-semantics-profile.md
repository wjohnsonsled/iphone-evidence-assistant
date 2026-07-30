# FOR-019 — Manifest.db Reconciliation Semantics Profile

- Profile: `manifestdb-reconciliation-semantics` version 1
- Decisions: DEC-0073 implementation; DEC-0074 candidate completion
- Status: candidate-only, not Supported

Version 1 accepts caller-supplied, scope-consistent observations bound to the
approved query/locator, fileID, domain, and relative-path candidate profiles.
It separately observes repeated row locators, raw TEXT fileIDs, canonical
fileIDs, and domain/path tuples. These are repetition patterns only. Raw BLOB
fileIDs are not transformed into invented text keys.

The profile always records duplicate, orphan, missing-object, and absence
conclusions as `NOT_ESTABLISHED`. No physical-object inventory or resolution is
approved or performed, so `physical_inventory_observed` and
`comparison_universe_complete` remain false. Permanent blockers identify the
unobserved physical universe, unauthorized resolution, incomplete comparison
universe, and unapproved support. Resource, cancellation, scope, and profile
failures add explicit blockers and can never enable a conclusion.

Callers supply positive row, group, group-member, projected-byte,
deterministic-memory, and monotonic-time ceilings plus cancellation. Only
completed rows and pattern groups are retained. Zero repetition patterns is not
evidence absence. Repeated identifiers are not content or physical identity.
Fixtures are synthetic; no filesystem, hashing, parser, API, persistence,
physical inventory, real evidence, or support promotion exists.
