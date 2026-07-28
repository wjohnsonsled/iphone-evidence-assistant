# DEV-1106 — Failure Aggregation

- Status: COMPLETE
- Dependency: DEV-0409 — COMPLETE
- Support effect: none

The reducer produces deterministic same-run counts by closed issue category and
severity, stable issue/partial identities, and explicit fatal issue identities.
It does not reproduce descriptions or create evidentiary conclusions. Duplicate
or cross-run observations and partial observations with missing contributing
issues fail closed.

No persistence, API, parser, evidence read, or support change is introduced.

Validation: focused 2 passed; full backend 336 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation and diff
checks passed.
