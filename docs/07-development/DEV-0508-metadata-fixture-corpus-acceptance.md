# DEV-0508 — Metadata Fixture Corpus

- Status: COMPLETE
- Dependencies: DEV-0502 through DEV-0506 — COMPLETE
- Support effect: none

| ID | Acceptance criterion |
|---|---|
| AC-01 | The corpus is explicitly synthetic, repository-local, deterministic, documented, and contains no client or real-device evidence. |
| AC-02 | Cases cover unencrypted/encrypted observations, whitespace and leading zeros, missing fields/files, unsupported typed values, and malformed plist input. |
| AC-03 | Every case declares stable expected discovery, normalization, and coverage observations without claiming Apple compatibility or support. |
| AC-04 | A root-confined test loader materializes only declared top-level files and validates the corpus schema and unique IDs. |
| AC-05 | Corpus tests exercise DEV-0501 through DEV-0507 behavior and preserve immutable fixture definitions. |
| AC-06 | Focused and regression validation passes with no migration, API, parser, production path, real evidence, registry/store population, or support promotion. |

## Validation record

All AC-01 through AC-06 pass. Corpus-focused: 4 passed. Full backend: 407
passed with the accepted TestClient warning. Legacy characterization: 5
passed. Compilation and diff checks passed. The six cases and all identifiers
are explicitly synthetic. No migration or support-state change occurred.
