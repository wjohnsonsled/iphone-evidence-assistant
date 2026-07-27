# DEV-0203 — Backup Encryption-State Detection Acceptance

- Status: VALIDATION_PENDING
- Scope: project DEV-0202's sole approved `IsEncrypted` observation into a
  typed, deterministic reporting decision.
- Support effect: none
- Decryption/password handling: prohibited
- Persistence/API/migration effect: none

## Requirements

| ID | Requirement |
|---|---|
| DEV-0203-R01 | Consume only a DEV-0202 `BackupValidationResult` |
| DEV-0203-R02 | Report `ENCRYPTED`, `UNENCRYPTED`, `INDETERMINATE`, `NOT_APPLICABLE`, or `FAILED` distinctly |
| DEV-0203-R03 | Preserve the raw Boolean observation and stable source locator when present |
| DEV-0203-R04 | Allow artifact-processing eligibility only for the unencrypted outcome, without claiming support |
| DEV-0203-R05 | Encrypted results are detection/reporting-only and never eligible for decryption or parsing |
| DEV-0203-R06 | Do not accept passwords or infer state from any secondary signal |
| DEV-0203-R07 | Preserve correlation, validator provenance, limitations, and deterministic audit serialization |
| DEV-0203-R08 | Add no API, migration, legacy dependency, or support promotion |

## Acceptance criteria

- AC-01: encrypted and unencrypted validator outcomes map exactly.
- AC-02: indeterminate maps distinctly and retains no fabricated raw value.
- AC-03: validation failures map to failed; unrelated outcomes map to not
  applicable.
- AC-04: only unencrypted is processing-eligible.
- AC-05: raw Boolean, locator, correlation, provenance, and limitations survive
  projection.
- AC-06: deterministic serialization is stable.
- AC-07: static boundaries exclude passwords, decryption, secondary signals,
  API, legacy, and persistence.
- AC-08: focused and regression suites pass using synthetic fixtures only.

## Validation record

- Focused tests: 7 passed.
- Backend regression: 71 passed with one previously accepted third-party
  deprecation warning.
- Legacy characterization: 5 passed.
- Compilation and `git diff --check`: passed.
- Migrations: none.
- Fixtures: synthetic only.

All criteria pass. The pre-existing nullable database field remains unused;
persistence belongs to a later approved evidence-source/model task.
