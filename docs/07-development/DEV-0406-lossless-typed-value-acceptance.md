# DEV-0406 — Lossless Typed-Value Observation Model

DEC-0043 controls storage-envelope semantics.

| ID | Acceptance criterion |
|---|---|
| AC-01 | Raw representation is required, immutable, typed, serialized explicitly, and independently addressable. |
| AC-02 | Normalized representation is separate and never overwrites raw. |
| AC-03 | NULL, MISSING, EMPTY, FALSE, ZERO, UNKNOWN, UNSUPPORTED, and UNREPRESENTABLE remain distinct. |
| AC-04 | Unsupported/unrepresentable require explicit failure codes; invalid coercions fail. |
| AC-05 | Normalized values require complete method/version/run/parser/time/limitations provenance. |
| AC-06 | Observation retains artifact/run/optional-parser/time provenance. |
| AC-07 | No normalization algorithm, parser behavior, support, display, redaction, AI, or report behavior is defined. |
| AC-08 | ORM metadata is additive; migration remains DEV-0410; all tests pass. |

## Validation record

All AC-01 through AC-08 pass. Focused: 14 passed. Backend: 254 passed with
the accepted warning. Compilation and diff checks pass. No transformation
algorithm, parser, migration, API, evidence, display, AI, report, or support
behavior was added.
