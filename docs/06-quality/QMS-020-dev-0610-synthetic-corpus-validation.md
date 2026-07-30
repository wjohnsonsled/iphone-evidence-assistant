# QMS-020 — DEV-0610 Synthetic Corpus Validation

## Scope

Candidate validation of `synthetic-characterization-corpus-governance` version
1 and `manifest-synthetic-characterization-corpus` version 1 under DEC-0077.
The package uses only project-original synthetic values.

## Corpus evidence

- Fixture/internal resource count: 60
- Candidate profile/version matrix rows: 13
- Corpus SHA-256:
  `159b01df907f56cd7c8f82c1a77cc67e479f6c87e169408b3aec5fcec38655bc`
- Source classification: `PROJECT_ORIGINAL_SYNTHETIC`
- Distribution: `ORIGINAL_PROJECT_SYNTHETIC`
- Provenance: `GENERATED_DETERMINISTICALLY`
- Synthetic status: `SYNTHETIC_CHARACTERIZED`
- Apple-produced status: `APPLE_PRODUCED_NOT_STARTED`
- Compatibility status: `COMPATIBILITY_NOT_EVALUATED`
- Support status: `SUPPORT_NOT_EVALUATED`

The focused corpus validates complete records and deterministic regeneration,
then mutates source, provenance, custody, distribution, registration, fixture
bytes, manifest bytes, generator/profile versions, and coverage to prove
fail-closed denial.

## Results

| Gate | Result |
|---|---|
| Focused corpus/governance/security suite | PASS — 80 |
| Combined Manifest suite | PASS — 322 |
| Full backend regression | PASS — 713; one accepted TestClient warning |
| Legacy characterization | PASS — 5 |
| Compilation | PASS |
| Dependency lock / pip consistency | PASS — 3 / no broken requirements |
| Alembic head/history/offline SQL | PASS — `0005_processing_idempotency` |
| Repository hygiene and final diff | PASS |

## Permanent limitations

This package characterizes only explicitly generated conditions. It does not
show that Apple produces any condition, validate an Apple/iOS/device/software
version, establish compatibility or production readiness, activate a parser,
validate an artifact, seed a supported record, or promote support. Corpus
custody is not evidence chain of custody, and fixture hashes are not evidence
hashes. A future Apple-produced package requires separate owner governance and
must remain outside Git by default.
