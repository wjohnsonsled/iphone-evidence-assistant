# BACKLOG.md Patch — Insert WP-0250

This file is an insertion patch. Codex should reconcile it with the live `BACKLOG.md`, task ledger, decision log, and current DEV-0202 status.

Do not replace current task statuses with stale values.

---

## Insertion Point

Insert the following section immediately after `WP-0200 Apple Backup Intake and Validation` and before the tenancy/security work package.

```markdown
# PHASE 2.5 — EVIDENCE INTEGRITY INFRASTRUCTURE

## WP-0250 Evidence Integrity Infrastructure

**Package status:** `READY` only after DEV-0202 is approved `COMPLETE`.

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0251 | Evidence-object domain contract | NOT_STARTED | DEV-0202 | Package gate |
| DEV-0252 | Stable evidence identifier strategy | NOT_STARTED | DEV-0251 | Package gate |
| DEV-0253 | Evidence lifecycle state machine | NOT_STARTED | DEV-0251 | Package gate |
| DEV-0254 | Cryptographic hash registry | NOT_STARTED | DEV-0251, DEV-0252 | Package gate |
| DEV-0255 | Evidence integrity verification service | NOT_STARTED | DEV-0254 | Package gate |
| DEV-0256 | Evidence access and lock policy | NOT_STARTED | DEV-0253, DEV-0255 | Package gate |
| DEV-0257 | Chain-of-custody event model | NOT_STARTED | DEV-0251, DEV-0253 | Package gate |
| DEV-0258 | Evidence audit-event taxonomy | NOT_STARTED | DEV-0257 | Package gate |
| DEV-0259 | Provenance graph foundation | NOT_STARTED | DEV-0251, DEV-0258 | Package gate |
| DEV-0260 | Provenance relationship validation | NOT_STARTED | DEV-0259 | Package gate |
| DEV-0261 | Evidence mutation detector | NOT_STARTED | DEV-0254, DEV-0255 | Package gate |
| DEV-0262 | Integrity policy enforcement service | NOT_STARTED | DEV-0256, DEV-0260, DEV-0261 | Package gate |
| DEV-0263 | Common supported-parser contract | NOT_STARTED | DEV-0259, DEV-0262 | Package gate |
| DEV-0264 | Parser-contract conformance harness | NOT_STARTED | DEV-0263 | Package gate |
| DEV-0265 | End-to-end integrity validation package | NOT_STARTED | DEV-0251 through DEV-0264 | Package gate |

### WP-0250 completion criteria

- stable evidence-object IDs;
- immutable hash observations;
- explicit lifecycle state transitions;
- application-level access controls;
- append-only custody and audit events;
- complete provenance relationships;
- mutation and broken-provenance detection;
- common supported-parser contract;
- parser conformance tests;
- deterministic synthetic fixture coverage;
- no API exposure or support promotion.

**Owner-review gate:** Approve the evidence-integrity architecture, data model,
lifecycle, audit taxonomy, provenance model, and parser contract.
```

---

## Dependency Changes

After inserting WP-0250, update these dependencies in the live backlog where appropriate:

1. `DEV-0203 Evidence-source registration model`
   - Do not duplicate evidence registration if WP-0250 now owns the domain contract.
   - Reconcile the task by either:
     - moving its remaining intake-specific implementation under DEV-0251; or
     - retaining DEV-0203 as the intake adapter that creates the approved evidence object.
   - Preserve the existing task ID and decision history.

2. `WP-0400 Supported Evidence Data Model`
   - Add WP-0250 as a dependency.
   - Reuse evidence UUID, hash, lifecycle, custody, audit, and provenance structures.
   - Do not create parallel competing models.

3. `WP-1100 Supported Processing Pipeline`
   - Add DEV-0262, DEV-0263, and DEV-0264 as dependencies.

4. Every artifact parser package
   - Add DEV-0263 and DEV-0264 as dependencies.
   - Require conformance before artifact-validation completion.

5. Search, AI, reports, and exports
   - Depend on provenance validation from DEV-0260.

---

## Reconciliation Rule

When a live task already covers part of WP-0250:

- do not delete the existing task;
- do not renumber it;
- map it to the new package;
- preserve completed work;
- document the overlap;
- select one authoritative implementation location;
- avoid duplicate models and services;
- stop only if reconciliation changes approved architecture or support scope.
