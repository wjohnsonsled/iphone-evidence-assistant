# Codex Autonomous Development Charter

**Applies to:** AI-Powered iPhone Evidence Assistant  
**Branch:** `mvp-development`  
**Purpose:** Permit extended autonomous implementation while preserving owner control over forensic, architectural, security, and support decisions.

---

## 1. Authorized Actions

Codex may perform the following without additional approval:

- read all repository files;
- create and edit files inside the repository;
- create task-specific requirements and acceptance criteria;
- update the backlog, task ledger, traceability matrix, risk register, and technical documentation;
- add or modify application code within the approved architecture;
- create synthetic fixtures;
- run linters, formatters, type checks, tests, migrations checks, and compilation checks;
- install project-local dependencies already permitted by repository configuration;
- create additive and reversible migrations;
- create local Git commits on `mvp-development`;
- continue to the next unblocked task inside the active work package.

---

## 2. Prohibited Actions

Codex must not:

- push to any remote;
- merge branches;
- force-push;
- delete branches;
- rewrite Git history;
- deploy to any environment;
- access real client evidence;
- access external credentials or secrets;
- upload repository contents to unapproved external services;
- purchase services or consume paid APIs;
- weaken authentication, authorization, audit, provenance, encryption, hashing, or evidence-integrity controls;
- promote any parser, artifact family, input type, workflow, report, or API to supported status;
- expose legacy routes through the default application;
- allow unsupported or legacy records into the supported store, search, AI, citations, reports, or coverage calculations;
- make destructive or data-rewriting migrations;
- silently invent forensic compatibility rules.

---

## 3. Default Execution Loop

For each task:

1. Verify branch is `mvp-development`.
2. Verify the working tree is clean.
3. Read governing documents.
4. Confirm the task is `READY`.
5. Create task-specific requirements.
6. Create measurable acceptance criteria.
7. Map criteria to requirement IDs.
8. Identify risks and assumptions.
9. Implement the smallest complete solution.
10. Add deterministic synthetic fixtures.
11. Run focused tests.
12. Run the full relevant regression suite.
13. Fix all failures caused by the task.
14. Run formatting, compilation, migration, and diff checks.
15. Update documentation and task status.
16. Create one or more clear local commits.
17. Confirm the working tree is clean.
18. Continue automatically when the next task is authorized.
19. Stop only at a mandatory gate.

---

## 4. Mandatory Stop Conditions

Stop and request an owner decision when:

- a work-package gate is reached;
- requirements conflict;
- architecture must change;
- support status may change;
- a compatibility profile must be approved;
- a destructive migration is needed;
- real evidence or credentials are needed;
- an external service or paid dependency is needed;
- tenant isolation cannot be demonstrated;
- a security control would be weakened;
- a production deployment or Git remote action is needed;
- evidence integrity cannot be preserved;
- a provisional forensic assumption would affect a user-facing classification;
- deterministic testing is not possible.

---

## 5. Evidence Handling Rules

- Treat all evidence sources as immutable.
- Never open source SQLite evidence in a mode that can write.
- Use controlled working copies when SQLite validation or parsing requires them.
- Preserve SQLite companion files when required.
- Hash and verify controlled copies.
- Record cleanup success or failure.
- Do not parse outside validated evidence roots.
- Reject symlinks, reparse points, path traversal, and root escapes unless an approved design explicitly handles them.
- Do not expose raw exception text as evidentiary conclusions.
- Never infer evidentiary completeness from structural validity alone.

---

## 6. Support Rules

Code presence does not equal support.

An artifact family may be promoted only after:

- an approved compatibility profile exists;
- fixture coverage is adequate;
- all-or-nothing acceptance criteria pass;
- provenance is complete;
- omissions and failures are explicit;
- regression tests pass;
- a validation report is prepared;
- the owner explicitly records promotion.

Until then, the artifact remains `CANDIDATE` or `UNSUPPORTED`.

---

## 7. Commit Rules

Codex may create local commits.

Each commit must:

- have a narrow purpose;
- reference the task ID;
- leave the repository in a testable state;
- avoid unrelated formatting churn;
- exclude secrets, evidence, temporary files, generated reports, and local environments.

Recommended format:

```text
DEV-####: concise imperative summary
```

Codex must not push.

---

## 8. Autonomous Runtime Goal

Codex should maximize useful work per session by:

- completing all unblocked tasks in the active work package;
- batching regression runs intelligently;
- reusing synthetic fixture builders;
- avoiding repeated repository-wide rediscovery;
- documenting decisions as they arise;
- continuing automatically after local commits.

Codex must not continue merely to appear busy. It should stop when proceeding would create rework or require an unapproved assumption.

---

## 9. Required End-of-Session Report

At every stop, report:

- branch and working-tree status;
- tasks completed;
- tasks still in progress;
- files created and modified;
- migrations created;
- tests and commands run;
- acceptance-criteria results;
- evidence-integrity and security implications;
- unresolved risks;
- provisional assumptions;
- local commit hashes;
- exact owner decision required;
- next task that will become unblocked.
