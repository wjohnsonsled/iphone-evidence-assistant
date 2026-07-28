# DEV-0104 — Structured Error Model Acceptance

- Status: COMPLETE — WP-0100 package review pending
- Dependency: DEV-0103 complete
- Scope: API error contracts and exception translation only
- Support effect: none

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0104-R01 | Use typed error categories and validated stable codes | AC-01 invalid status/code/message fail deterministically |
| DEV-0104-R02 | Return one stable safe error envelope | AC-02 application errors include category, code, safe message, retryable flag, and server request ID |
| DEV-0104-R03 | Translate request-validation failures safely | AC-03 malformed input does not echo submitted values or validation internals |
| DEV-0104-R04 | Translate framework HTTP errors consistently | AC-04 missing routes and safe HTTP failures use the common envelope |
| DEV-0104-R05 | Hide unexpected exception content | AC-05 internal response is generic and excludes exception text |
| DEV-0104-R06 | Preserve server-side diagnostic correlation | AC-06 every response has a UUID request ID represented in logs |
| DEV-0104-R07 | Preserve existing API semantics and composition boundaries | AC-07 status/code regressions and default health-only tests pass |
| DEV-0104-R08 | Add no route, evidence behavior, migration, external service, or support promotion | AC-08 boundary and diff checks pass |

## Validation record

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | Invalid status, code, and empty-message tests |
| AC-02 | PASS | Typed application-error envelope test |
| AC-03 | PASS | Malformed request input and validation internals absent from response |
| AC-04 | PASS | Missing-route common-envelope test |
| AC-05 | PASS | Unexpected exception text absent from response |
| AC-06 | PASS | UUID request IDs validated; correlation fields asserted |
| AC-07 | PASS | Focused 13/13; backend 120/120; legacy 5/5 |
| AC-08 | PASS | No route, evidence, migration, external service, or support change |

Commands: focused/full pytest with repository-local `--basetemp`; legacy
unittest discovery; compileall; and `git diff --check`.

Limitation: this task controls API responses. Unexpected exceptions are still
logged server-side by the existing logger; evidence-safe structured logging and
redaction are DEV-0105 scope. The accepted TestClient warning remains.
