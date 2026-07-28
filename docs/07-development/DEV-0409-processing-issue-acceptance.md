# DEV-0409 — Processing Issue and Partial-Processing Observation Model

DEC-0046 controls immutable safe diagnostic observations.

| ID | Acceptance criterion |
|---|---|
| AC-01 | All approved issue categories, severities, and recoverability values are closed. |
| AC-02 | Stable code, safe description, stage, scope, optional remediation, provenance, and limitations are required. |
| AC-03 | Raw exceptions, traces, paths, secrets, credentials, evidence content, and customer IDs have no storage fields. |
| AC-04 | Unsafe diagnostic patterns and multiline content fail closed. |
| AC-05 | Coverage, omission, parser, typed-value, and timestamp relationships are references only. |
| AC-06 | Partial observations identify completed, incomplete, unresolved scope and contributing records. |
| AC-07 | Records are immutable; corrections create new records with optional supersession reference. |
| AC-08 | No corruption, compatibility, support, intent, evidentiary/legal, AI, report, or production conclusion occurs. |

## Validation record

All AC-01 through AC-08 pass. Focused: 14 passed. Backend: 289 passed with
the accepted warning. Compilation and diff checks pass. No ORM migration,
parser, evidence, API, diagnostic exposure, or support behavior was added.
