# DEV-0407 — Timestamp Provenance Observation Model

DEC-0044 controls observation, interpretation, timezone, ambiguity, precision,
numeric-epoch, and conversion envelope semantics.

| ID | Acceptance criterion |
|---|---|
| AC-01 | All approved controlled vocabularies are exact and closed. |
| AC-02 | Raw DEV-0406 value, category, precision, source/run/parser/time/locator provenance, and limitations are preserved. |
| AC-03 | Timezone source, offset, named zone, ruleset, and derivation remain independent. |
| AC-04 | Inferred timezone requires complete method/basis/run/limitations provenance. |
| AC-05 | Ambiguous and nonexistent local times remain distinct and unresolved. |
| AC-06 | Numeric epochs require explicit origin/unit/profile/method metadata. |
| AC-07 | Conversion status is independent; derived results and explicit failures are validated. |
| AC-08 | No parsing, conversion algorithm, Apple profile, display/timeline/AI/report behavior, API, migration, or support change. |

## Validation record

All AC-01 through AC-08 pass. Focused: 9 passed. Backend: 263 passed with
the accepted warning. Compilation and diff checks pass. No timestamp parsing,
timezone/epoch/conversion algorithm, ORM migration, API, real evidence, or
support behavior was added.
