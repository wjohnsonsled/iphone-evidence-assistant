# WP-0620 â€” Acceptance Criteria

| ID | Criterion | Requirements | Status |
|---|---|---|---|
| AC-01 | Only validated authorized tenant/case/source/run roots are inventoried; lexical and physical escape, links, reparse points, mount/special objects fail closed. | DEC-0081 Â§Â§3â€“6 | PASS |
| AC-02 | Read-only deterministic inventory preserves exact names, types, relative locators, unknown/unexpected entries, explicit limits, continuation, and limitations. | DEC-0081 Â§Â§4â€“9, 19 | PASS |
| AC-03 | Regular objects use streaming SHA-256 with pre/post stat, bytes, source/run/locator provenance, instability and operational failure states. | DEC-0081 Â§Â§14â€“15 | PASS |
| AC-04 | Exact v1 provisional synthetic layout and comparison profile implements every required resolution outcome without Apple/content/artifact inference. | DEC-0081 Â§Â§10â€“13 | PASS |
| AC-05 | Physical and Manifest coverage remain separate; complete/partial, no-match, inaccessible, unsupported, mutation, absence, duplicate, and orphan distinctions fail closed. | DEC-0081 Â§Â§16â€“18 | PASS |
| AC-06 | At least 50 project-original scenarios cover layout, types, security, hashes, mutation, resolution, coverage, isolation, determinism, and prohibited claims. | DEC-0081 Â§22 | PASS |
| AC-07 | Intake, integrity, evidence-core, metadata, Manifest, and pipeline integrations remain candidate-only and provenance-complete. | DEC-0081 Â§23 | PASS |
| AC-08 | Focused, integration, backend, legacy, compilation, dependency, Alembic, hygiene, and diff gates pass. | DEC-0081 Â§Â§23â€“24 | PASS |
| AC-09 | No migration, real/Apple/customer evidence, parser, content interpretation, API, production, registry/store entry, or support promotion exists. | DEC-0081 Â§Â§21, 24, 28 | PASS |

