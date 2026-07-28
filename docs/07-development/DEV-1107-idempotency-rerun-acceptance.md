# DEV-1107 — Idempotency and Forensic Rerun Model

- Status: COMPLETE
- Owner decision: DEC-0052
- Dependency: DEV-1104 — COMPLETE
- Profile: `processing-request-canonical-json-sha256` version `1`
- Support effect: none

## Acceptance summary

The immutable logical request is distinct from every execution attempt.
Canonical sorted JSON includes tenant, case, evidence source, source artifact,
parser identity and exact version, parser-contract version, artifact family,
schema profile, processing profile and version, operation, controlled-input
digest, authorization reference, and idempotency profile/version. SHA-256
produces the key and canonical-input digest.

An atomic repository claim has one winner. Exact duplicates create no run
before execution, reference the running run, return the completed run, or
require explicit retry after unsuccessful outcomes. Every actual attempt has a
new UUID and monotonic attempt number. Retry and rerun relationships preserve
prior immutable outcomes. Changed governed inputs create a new request/key.
Expired claims may be safely reacquired. Same bytes never replace tenant,
case, evidence-source, or source-artifact scope.

Migration 0005 adds separate logical-request, execution-attempt, and
run-relationship tables with exact active-claim uniqueness, scoped foreign
keys, monotonic attempt uniqueness, cycle/self-link checks, and no seed data.
The application service depends on atomic repository behavior; the in-memory
repository is synthetic test infrastructure only.

## Limitations

No checkpoint resumption, cross-run output merging, production repository,
live PostgreSQL, API, parser activation, real evidence, support, or deployment
is included. Application metadata is not nonrepudiation.

Validation: focused 9 passed; full backend 353 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation, lock,
package consistency, migration single-head, offline upgrade/downgrade, and diff
checks passed.
