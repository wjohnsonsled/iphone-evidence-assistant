# DEV-0505 — Identifier and Product-Version Normalization

- Status: COMPLETE
- Dependencies: DEV-0502 through DEV-0504 — COMPLETE
- Owner decision: DEC-0056
- Support effect: none

| ID | Acceptance criterion | Controlling requirements |
|---|---|---|
| AC-01 | Two immutable versioned profiles implement only the approved identifier and dotted-numeric product-version transformations. | DEC-0056 §§1–5, 10–13 |
| AC-02 | Raw, missing, null, empty, malformed, unsupported, ambiguous, and failed values remain distinct and raw observations are never overwritten. | DEC-0056 §§1, 4, 10, 21; DEV-0406 |
| AC-03 | Identifier classes and recognized syntaxes remain explicit; backup-root names are non-authoritative and no class conversion, attribution, fuzzy matching, or repair occurs. | DEC-0056 §§3, 5–9 |
| AC-04 | Product versions preserve component text, count, numeric values, and leading-zero observations without padding, suffix removal, or compatibility inference. | DEC-0056 §§10–16 |
| AC-05 | Exact comparison modes and conflict outcomes are deterministic, class-aware, fail closed when not comparable, and preserve every source value. | DEC-0056 §§13, 17–19 |
| AC-06 | Every normalized result carries complete source/run/reader/profile/method/status/limitation data and DEV-0406 transformation provenance. | DEC-0056 §§1, 20, 22–23 |
| AC-07 | Tenant, case, and source scope mismatches fail closed; diagnostics are stable and safe. | DEC-0056 §§19–21, 24 |
| AC-08 | No migration, parser activation, registry insertion, supported record, API, real evidence, compatibility claim, or support promotion occurs. | DEC-0056 authorization boundary |
| AC-09 | Focused, dependent, regression, legacy, compilation, lock, package, migration, and hygiene checks pass using synthetic data only. | DEC-0056 §24 |

Normalization equality means only exact textual or component agreement under
the named profile. It does not prove physical-device identity, attribution,
authenticity, Apple compatibility, parser compatibility, or artifact support.
DEV-0601 remains authoritative for Manifest.db schema compatibility.

## Validation record

All AC-01 through AC-09 pass using synthetic observations only.

- focused DEV-0505 tests: 25 passed;
- DEV-0502 through DEV-0506 dependent tests with DEV-0505: 31 passed;
- full backend regression: 398 passed with the accepted TestClient warning;
- legacy characterization: 5 passed;
- compilation, exact dependency-lock validation, package consistency,
  Alembic single-head/offline SQL, repository hygiene, and diff checks: passed.

No migration was added. The Supported Parser Registry and supported normalized
store remain empty. No parser, artifact, workflow, input, compatibility
profile, API, or capability was promoted to Supported.
