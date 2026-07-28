# DEV-0452 — Artifact Coverage Engine

- Status: COMPLETE
- Dependencies: DEV-0451, DEV-0304, DEV-0408, DEV-0409, DEV-1101 through
  DEV-1106 — COMPLETE
- Support effect: none

The engine projects one explicit processing-coverage observation for every
registered source-inventory item in a named measurable set. It preserves the
closed factual status verbatim, keeps successful zero records distinct from
unsupported/not-executed/failure states, and reports exact status counts and an
explicit denominator. Missing, extra, duplicate, or cross-run observations fail
closed.

The report contains no percentage, evidence-gap classification, device
completeness, attorney conclusion, or support inference. No parser, evidence
read, persistence, migration, API, or support change is introduced.

Validation: focused 3 passed; full backend 339 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation and diff
checks passed.
