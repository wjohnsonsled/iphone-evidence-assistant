# Owner Review Checklist

Use this checklist at every Codex stop.

---

## 1. Repository State

- [ ] Correct branch: `mvp-development`
- [ ] Working tree clean
- [ ] Nothing pushed
- [ ] Commit hashes provided
- [ ] No evidence or secrets committed

## 2. Scope

- [ ] Work matches the approved task
- [ ] No unrelated refactor
- [ ] No excluded artifact or workflow added
- [ ] No support claim was silently expanded

## 3. Evidence Integrity

- [ ] Source evidence remains immutable
- [ ] Controlled copies used where required
- [ ] Hashes and provenance recorded where required
- [ ] Failures and omissions are explicit
- [ ] No direct unsafe SQLite access

## 4. Security

- [ ] Tenant isolation preserved
- [ ] Authorization boundaries preserved
- [ ] Legacy routes remain isolated
- [ ] Logs do not leak evidence content or secrets
- [ ] No external credentials or services used

## 5. Testing

- [ ] Task-specific acceptance criteria exist
- [ ] Focused tests passed
- [ ] Regression tests passed
- [ ] Negative and failure tests exist
- [ ] Synthetic fixtures only
- [ ] Migration and compilation checks passed

## 6. Documentation

- [ ] Task ledger updated
- [ ] Traceability matrix updated
- [ ] Risk register updated
- [ ] Decision log updated when required
- [ ] Limitations documented

## 7. Decision

Choose one:

- [ ] Approve task/package
- [ ] Approve with conditions
- [ ] Request revisions
- [ ] Reject
- [ ] Defer

Approval language:

```text
I approve [TASK OR WORK PACKAGE ID] as complete.

This approval does not promote any parser, artifact family, input type, workflow,
report, API, or production capability to supported status unless explicitly
stated below.

Approved support promotions:
- None.

Record this decision in the decision log and task ledger.
Proceed to the next unblocked task under BACKLOG.md and CODEX_AUTONOMY_CHARTER.md.
Stop at the next mandatory owner-review gate.
```
