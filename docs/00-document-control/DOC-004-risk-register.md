# DOC-004 — Risk Register

## Document control

- Established: 2026-07-24
- Scope: Controlled MVP development risks
- Review rule: Update in the task that identifies, changes, accepts, or closes
  a risk

| Risk ID | Risk | Impact | Current controls | Residual status | Owner decision / next action |
|---|---|---|---|---|---|
| RSK-0001 | The explicit legacy compatibility FastAPI application could be deployed or exposed mistakenly | Unsupported, unauthenticated legacy output could be treated as supported evidence or cross the SaaS boundary | Default composition is health-only; legacy composition is explicitly named and warned; deterministic import/route tests | OPEN — HIGH | Owner accepted retention for characterization in DEC-0003; add deployment/CI denial controls in a later approved task |
| RSK-0002 | FastAPI/Starlette TestClient emits a third-party deprecation warning | A future dependency update could break backend tests or mask new warnings | Warning is recorded; current tests pass deterministically | OPEN — LOW | Owner accepted as technical debt in DEC-0003; resolve during dependency/quality task without weakening tests |
| RSK-0003 | DEV-0201 path inspection cannot eliminate filesystem time-of-check/time-of-use replacement | A candidate could change after inspection if later code relies only on the returned path | Adapter is not API-exposed and performs no parsing; link/reparse and root escape fail closed; result makes no support claim | OPEN — HIGH | Evidence-source registration, immutable storage, hashing, and verified working-copy tasks must bind later processing to controlled material |
| RSK-0004 | Apple does not publicly document the internal local-backup manifest schema used by the proposed validator | Provisional rules could reject valid backups or accept incompatible structures | FOR-007 labels rule basis, uses schema characteristics rather than iOS allowlists, and blocks implementation pending owner approval and fixture evidence | OPEN — HIGH | Owner must approve/revise profile and required fixture basis before Stage B |
| RSK-0005 | A filesystem copy of main/WAL/journal files may be inconsistent if the source changes during or between reads | Integrity conclusions could be invalid despite individual hashes | DEV-0202 checks source pre/post hashes and companion-set stability and is not API-exposed; controlled source is expected immutable | OPEN — HIGH | Later general intake must bind immutable source storage/snapshot semantics; fail closed on any detected change |
| RSK-0006 | Cleanup can fail and leave hashed synthetic or future sensitive working material | Temporary derived data may persist outside retention policy | Context-managed cleanup, explicit audit state, and surfaced cleanup failure | OPEN — MEDIUM | Production working-copy subsystem needs startup scavenging, retention, permissions, and audit policy |
| RSK-0007 | Approved DEV-0202 identity and corruption rules assigned different outcomes to a present but invalid SQLite `Manifest.db` | Deterministic precedence could misclassify non-Apple input as corrupt or corrupt Apple-like input as non-Apple | DEC-0008 separates independent plist identity from database validity; deterministic conflict tests cover both branches | CLOSED | Reopen if recognized identity fields change |
| RSK-0008 | DEV-0202 required contradictory encryption-indicator handling but approved only `Manifest.plist.IsEncrypted` | A fabricated secondary signal would create an unsupported forensic classification rule | DEC-0009 removes the requirement and prohibits inference from unapproved signals; DEV-0211 is deferred | CLOSED | Reopen only through an owner-approved revised compatibility profile |
