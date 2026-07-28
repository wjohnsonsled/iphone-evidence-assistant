# DEV-1105 — Coverage Aggregation

- Status: COMPLETE
- Dependency: DEV-0408 — COMPLETE
- Support effect: none

The deterministic reducer aggregates only same-run factual coverage
observations, exact status counts, and known record counts. Unknown/unavailable
counts propagate as unknown rather than being treated as zero. Duplicate and
cross-run observations fail closed. The result permanently disclaims
evidentiary completeness and contains no percentage, device-completeness,
evidence-gap, or attorney-facing conclusion.

No persistence, API, parser, evidence read, or support change is introduced.

Validation: focused 3 passed; full backend 334 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation and diff
checks passed.
