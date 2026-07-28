# QMS-009 — WP-0400 Evidence-Core Validation Report

## Recommendation

Approve with documented limitations as candidate evidence-core infrastructure
only.

Owner disposition: approved in DEC-0049. Classification:
`COMPLETE — CANDIDATE EVIDENCE-CORE INFRASTRUCTURE`.

WP-0400 implements processing-run, artifact, locator, parser identity,
fingerprint, typed-value, timestamp, coverage, issue, candidate store,
admission, supersession, and quarantine-isolation contracts. The supported
registry and normalized store remain empty.

## Permanent limitations

- No parser, artifact, input, workflow, API, report, or AI capability is Supported.
- No live PostgreSQL validation was performed.
- Migration persistence for complex DEV-0407–0409 envelopes uses relational
  scope/reference columns plus JSON observation payloads; future query/index
  requirements may require additive refinement.
- The repository implementation is candidate/in-memory and not a production repository.
- Positive admission exists only in isolated synthetic tests using an explicit
  synthetic registry and promotion reference.
- Existing TestClient warning remains accepted development debt.

Owner approval would authorize architectural use by later candidate tasks. It
would not authorize parser activation, supported records, real evidence,
production exposure, deployment, compatibility, or support promotion.

All limitations in this report remain active after approval.

## Validation results

- focused evidence-core: 94 passed;
- backend: 308 passed, one accepted warning;
- legacy characterization: 5 passed;
- Alembic single head/history and offline upgrade/downgrade: passed;
- compilation and diff checks: passed.
