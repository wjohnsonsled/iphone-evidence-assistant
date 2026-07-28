# DEV-0507 — Metadata Coverage and Limitation Reporting

- Status: COMPLETE
- Dependencies: DEV-0505 — COMPLETE
- Support effect: none

| ID | Acceptance criterion |
|---|---|
| AC-01 | A closed, versioned metadata measurable set covers only the approved backup-root and plist fields. |
| AC-02 | Every expected item has exactly one factual state; observed-normalized, observed-raw-only, missing-field, source-absent, inaccessible, malformed, unsupported, failed, and indeterminate remain distinct. |
| AC-03 | Counts reconcile exactly to the named denominator and output ordering is deterministic. |
| AC-04 | Entries retain tenant, case, evidence-source, artifact, run, source-file, source-field, reader, and normalization references where applicable. |
| AC-05 | Limitations prohibit device/backup completeness, evidence absence, deletion, concealment, compatibility, parser support, and support inferences. |
| AC-06 | Missing/duplicate/extra/cross-scope normalized observations fail closed. |
| AC-07 | Synthetic focused and regression tests pass; no migration, API, parser, evidence access, registry/store change, or support promotion occurs. |

## Validation record

All AC-01 through AC-07 pass. Focused: 5 passed. Full backend: 403 passed
with the accepted TestClient warning. Legacy characterization: 5 passed.
Compilation and diff checks passed. No migration, evidence access, parser,
API, persistence, registry/store population, or support promotion occurred.
