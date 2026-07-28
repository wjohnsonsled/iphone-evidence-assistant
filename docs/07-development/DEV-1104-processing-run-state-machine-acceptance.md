# DEV-1104 — Processing-Run State Machine

- Status: COMPLETE
- Dependency: DEV-0401 — COMPLETE
- Support effect: none

Immutable observations implement the closed sequence `REQUESTED → AUTHORIZED →
RUNNING` with explicit `COMPLETED`, `COMPLETED_ZERO_RECORDS`, `PARTIAL`,
`FAILED`, and `CANCELLED` terminal outcomes. Pre-execution failure/cancellation
is permitted; skipped authorization, blank reasons, naive timestamps, and every
transition from a terminal state fail closed. Each event retains tenant, case,
and processing-run identity.

Focused lifecycle tests pass for every terminal outcome, transition denial,
pre-execution termination, and required reason. No migration, repository,
parser, evidence access, API, or support effect is introduced.

Limitation: lifecycle observations are in memory and are not yet bound to
pipeline audit events or durable transactions.

Validation: focused 7 passed; full backend 331 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation and diff
checks passed.
