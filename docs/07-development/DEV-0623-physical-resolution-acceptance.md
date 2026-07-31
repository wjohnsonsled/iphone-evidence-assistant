# DEV-0623 — Manifest fileID Physical Resolution Acceptance

| ID | Criterion | Result |
|---|---|---|
| AC-01 | Same-scope DEV-0603 canonical identifiers only | PASS |
| AC-02 | Exact provisional prefix/filename rule is deterministic | PASS |
| AC-03 | Single, multiple, complete-no-match, partial-no-match, inaccessible, unsupported, incompatible, invalid, and scope outcomes remain distinct | PASS |
| AC-04 | Stable identifiers and complete source/run/locator provenance are retained | PASS |
| AC-05 | No content, deletion, Apple compatibility, artifact, parser, or support inference | PASS |
| AC-06 | Focused, integration, regression, compilation, and diff gates pass | PASS |

Focused tests: 4 passed. Integration tests: 64 passed, 2 host-dependent link
fixture skips. Only project-original synthetic files were used.

Complete regression: 800 backend passed, 2 skipped, 1 accepted warning; 5
legacy passed. Compilation and `git diff --check` passed.
