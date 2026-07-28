# DEV-0210 — Intake Package Integration Tests

- Status: VALIDATION_PENDING — WP-0200 owner review required
- Dependencies: DEV-0203 through DEV-0209 complete
- Scope: synthetic candidate integration only
- Support effect: none

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | A root-confined synthetic candidate passes adapter handoff without implying support |
| AC-02 | Evidence receives a stable UUID distinct from content hashes |
| AC-03 | Source `Manifest.db` has immutable before/after WP-0250 SHA-256 observations that verify |
| AC-04 | SQLite processing occurs only through a hashed, verified controlled copy with cleanup success |
| AC-05 | Unencrypted and encrypted candidate outcomes remain detection/classification results only |
| AC-06 | Audit events retain tenant, case, evidence, actor, correlation, ordered success, and typed outcome |
| AC-07 | Controlled-copy provenance resolves through source artifact to evidence source |
| AC-08 | Source fixture files remain byte-for-byte unchanged |
| AC-09 | successful zero-result, missing input, and resource denial remain distinct |
| AC-10 | Resource denial uses safe validation failure and does not create a forensic classification |
| AC-11 | Supported registry remains empty throughout the integration suite |
| AC-12 | No API, parser, artifact content, persistence, real evidence, or support promotion is introduced |

## Results

All acceptance criteria pass against synthetic temporary fixtures. The
integration is intentionally test-only; no production composition root or
workflow endpoint was added.

## Limitations

- The Apple compatibility profile remains candidate-only and validated only
  with synthetic fixtures.
- Evidence, audit, hash, custody, and provenance services remain in-memory
  reference implementations.
- Resource ceilings in tests are synthetic and do not establish production
  capacity.
- No artifact rows are parsed and no supported evidence record is created.

## Commands and results

- DEV-0210 focused integration — 3 passed.
- WP-0200/intake/integrity/quarantine package suite — 102 passed.
- Full backend regression — 156 passed with the previously accepted third-party
  TestClient deprecation warning.
- Legacy characterization — 5 passed.
- Python compilation and `git diff --check` — passed.
- No migration was created.
