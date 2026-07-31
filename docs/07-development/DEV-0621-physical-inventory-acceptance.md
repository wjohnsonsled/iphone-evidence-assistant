# DEV-0621 — Physical Inventory Profile, Confinement, Types, and Locators

- Status: COMPLETE — candidate-only
- Decisions: DEC-0081; DEC-0082
- Profile: FOR-022
- Support effect: none

| ID | Criterion | Result |
|---|---|---|
| AC-01 | Exact tenant/case/source/run authorization and validated-root prerequisites fail closed. | PASS |
| AC-02 | Root and observed entries remain read-only; no sidecar/index/permission/timestamp mutation occurs. | PASS |
| AC-03 | V1 observes only root plus exact lowercase two-hex prefix directories; unexpected directories are preserved and not traversed. | PASS |
| AC-04 | Regular, directory, symlink, reparse, other special, inaccessible, and indeterminate states remain distinct; unsafe types are never followed. | PASS |
| AC-05 | Candidate names require exact lowercase 40-hex syntax and matching two-character prefix; uppercase, extensions, malformed and mismatched forms remain noncandidates. | PASS |
| AC-06 | Stable immutable locators are relative, exact-case, source/run/profile-bound, deterministic, and contain no host path. | PASS |
| AC-07 | Every required caller ceiling is positive; v1 depth is fixed at two; termination/cancellation preserve completed observations. | PASS |
| AC-08 | Unknown/unexpected entries remain observations without corruption, maliciousness, artifact, content, existence, or support inference. | PASS |
| AC-09 | Focused, compilation, backend, legacy, dependency, migration, and hygiene gates pass. | PASS |
| AC-10 | No migration, real evidence, parser, API, content interpretation, registry/store entry, or support promotion exists. | PASS |

