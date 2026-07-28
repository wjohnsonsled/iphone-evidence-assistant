# DEV-0105 — Structured Application Logging Baseline Acceptance

- Status: COMPLETE — WP-0100 package review pending
- Dependency: DEV-0103 complete
- Scope: supported-path application logging and safe compatibility formatting
- Audit effect: operational logs are not immutable audit/custody records

| ID | Requirement | Acceptance criterion |
|---|---|---|
| DEV-0105-R01 | Emit deterministic JSON log objects | AC-01 required timestamp, level, logger, and event fields parse |
| DEV-0105-R02 | Permit only allowlisted structured metadata | AC-02 unknown fields fail and known identifiers serialize |
| DEV-0105-R03 | Redact credential-shaped values | AC-03 URLs, passwords, tokens, and API keys are absent |
| DEV-0105-R04 | Do not serialize traceback or raw exception text | AC-04 exception secret text is absent while a safe failure event remains |
| DEV-0105-R05 | Retain request correlation for API failures | AC-05 error events carry request ID, code/status, and safe path |
| DEV-0105-R06 | Keep logs distinct from append-only audit records | AC-06 documentation and module contract state the distinction |
| DEV-0105-R07 | Preserve API/composition behavior | AC-07 focused and full regressions pass |
| DEV-0105-R08 | Add no evidence logging, route, migration, external service, or support promotion | AC-08 static and diff checks pass |

## Validation record

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | JSON parsing and required-field assertions |
| AC-02 | PASS | Allowlisted metadata and unknown-field denial tests |
| AC-03 | PASS | URI/password/token/API-key/secret redaction matrix |
| AC-04 | PASS | Exception content and traceback omission test |
| AC-05 | PASS | DEV-0104 correlated error-event integration |
| AC-06 | PASS | Module contract distinguishes operational logs |
| AC-07 | PASS | Focused 20/20; backend 129/129; legacy 5/5 |
| AC-08 | PASS | No evidence logging, route, migration, service, or support change |

Commands: focused/full pytest with repository-local `--basetemp`; legacy
unittest discovery; compileall; and `git diff --check`.

Limitations: operational logs are not append-only audit or custody records.
Free-form compatibility log messages are intentionally reduced to a generic
event unless migrated to `log_event`, which preserves safety but reduces legacy
diagnostic detail. Redaction patterns are defense-in-depth, not permission to
log evidence content. The accepted TestClient warning remains.
