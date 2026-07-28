# QMS-007 — WP-0200 Apple Backup Intake Validation Report

- Status: COMPLETE — owner approved in DEC-0027
- Owner gate: satisfied by DEC-0027 for candidate architecture only
- Support effect: none

## Package scope

WP-0200 provides candidate-only filesystem adaptation, synthetic structural
classification, single-signal encryption reporting, shared SHA-256 integrity,
controlled SQLite copies, intake audit/provenance contracts, bounded cleanup
recovery, explicit resource policy, and synthetic integration tests.

## Validation summary

| Area | Result |
|---|---|
| Adapter outcomes, root/link controls, zero versus failure | PASS |
| Candidate Apple structure/encryption classifications | PASS — synthetic profile only |
| Shared immutable SHA-256 observations | PASS |
| Main/WAL/SHM/journal controlled copy and read-only SQLite | PASS |
| Audit and provenance adoption | PASS — in-memory reference services |
| Cleanup, failure recovery, and unsafe-candidate rejection | PASS |
| Required resource configuration and denial matrix | PASS |
| Candidate end-to-end source immutability and lineage | PASS |
| Supported registry remains empty | PASS |

## Test results

- DEV-0210 focused integration: 3 passed.
- WP-0200/intake/integrity/quarantine package: 102 passed.
- Full backend regression: 156 passed with the accepted TestClient warning.
- Legacy quarantine characterization: 5 passed.
- Dependency lock validation and `pip check`: passed during DEV-0209.
- Python compilation: passed.
- Alembic single head/history and PostgreSQL offline SQL: passed during
  DEV-0209; no WP-0200 migration was added.
- Diff check: passed.

## Explicit non-authorizations

Validation does not approve the candidate Apple compatibility profile,
production capacity, deployment, real evidence, a production API, decryption,
parser execution, artifact families, supported records, search, AI, reports,
exports, or support promotion.

## Unresolved limitations and risks

- Apple-produced multi-version backup fixtures have not been validated.
- Production resource ceilings have not been selected or capacity-tested.
- Reference integrity/audit/provenance services are not durable transactional
  repositories.
- Cleanup recovery is not scheduled or persistently audited.
- Filesystem TOCTOU and changing SQLite companion-set risks remain fail-closed
  but cannot be eliminated at application level.
- The accepted TestClient third-party deprecation warning remains.

## Owner disposition

The owner accepted the reported results and limitations in DEC-0027. No
support status changed; the supported registry remains empty.
