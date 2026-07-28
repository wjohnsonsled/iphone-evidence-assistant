# DEV-0408 — Processing Coverage and Omission Observation Model

DEC-0045 controls processing facts and prohibits WP-0450 conclusions.

| ID | Acceptance criterion |
|---|---|
| AC-01 | All approved coverage, authorization, execution, count, reconciliation, and omission vocabularies are closed. |
| AC-02 | Known zero, unknown, not applicable, and failure-unavailable counts remain distinct. |
| AC-03 | Complete statuses require authorized completed execution and reconciled known counts. |
| AC-04 | Zero records cannot arise from denial, non-execution, absence, unsupported, failure, limits, or partial processing. |
| AC-05 | Partial cannot masquerade as complete because records were emitted. |
| AC-06 | Resource-limit and omission metadata are explicit and provenance complete. |
| AC-07 | Noncomplete observations require safe reason, description, governing reference, and limitations. |
| AC-08 | No device/backup completeness, deletion, concealment, spoliation, compatibility, support, legal, AI, report, or WP-0450 conclusion is represented. |

## Validation record

All AC-01 through AC-08 pass. Focused: 12 passed. Backend: 275 passed with
the accepted warning. Compilation and diff checks pass. No ORM migration,
parser, evidence, API, WP-0450 conclusion, or support behavior was added.
