# DEV-0405 — Schema-Fingerprint Observation Model

DEC-0042 requires algorithm/profile-qualified observations and prohibits a
universal cross-artifact canonicalization algorithm.

| ID | Acceptance criterion |
|---|---|
| AC-01 | Profile ID/version and canonical input reference are explicit. |
| AC-02 | SHA-256, artifact/run/optional-parser provenance, and aware time are required. |
| AC-03 | Limitations are mandatory. |
| AC-04 | No compatibility, equivalence, parse-success, or support conclusion exists. |
| AC-05 | No canonicalization algorithm is implemented; DEC-0008 remains profile-specific. |
| AC-06 | ORM metadata is additive; migration remains DEV-0410. |
| AC-07 | Malformed inputs fail closed and regressions pass. |
| AC-08 | No parser execution, compatibility, support, API, or real evidence use occurs. |

## Validation record

All AC-01 through AC-08 pass. Focused: 7 passed. Backend: 240 passed with
the accepted warning. Compilation and diff checks pass. No canonicalization,
parser execution, compatibility, migration, API, evidence, or support change.
