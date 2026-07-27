# Codex Extended Autonomous Execution Prompt

Paste the following into Codex after adding the governance files to the repository.

```text
Operate under the repository's approved governance documents.

Before doing any work, read:

- AGENTS.md
- BACKLOG.md
- CODEX_AUTONOMY_CHARTER.md
- OWNER_REVIEW_CHECKLIST.md
- docs/00-document-control/DOC-002-requirements-traceability-matrix.md
- docs/00-document-control/DOC-003-decision-log.md
- docs/00-document-control/DOC-004-risk-register.md
- docs/02-architecture/ARC-001-system-architecture.md
- docs/07-development/DEV-009-task-ledger.md

Execution instructions:

1. Verify the current branch is mvp-development.
2. Verify the working tree is clean.
3. Reconcile BACKLOG.md with the existing task ledger without discarding any
   approved task IDs, decisions, or completed work.
4. Preserve the existing repository as the source of truth when a backlog task
   title differs from an already-approved ledger title.
5. Select the first READY task in approved plan order.
6. Create task-specific requirements and deterministic acceptance criteria.
7. Update traceability before implementation.
8. Implement the smallest complete solution.
9. Use synthetic fixtures only.
10. Run focused and full relevant regression tests.
11. Fix failures.
12. Update documentation and risks.
13. Create local commits only.
14. Continue automatically through every unblocked task in the active work
    package.
15. Do not ask for routine approval between tasks.
16. Stop only at a mandatory stop condition in CODEX_AUTONOMY_CHARTER.md or at
    the work-package owner gate.
17. Do not push, merge, deploy, access real evidence, access external
    credentials, or promote support status.

Current known state:

- DEV-0201 is awaiting owner completion approval.
- DEV-0202 requires owner authorization for a temporary hashed controlled copy
  of Manifest.db and available SQLite companion files.
- DEV-0202 also requires preparation and separate owner approval of an Apple
  backup version/schema compatibility profile.
- Do not invent compatibility rules.

First, inspect the repository and report any inconsistency between BACKLOG.md,
the task ledger, and recorded decisions. Resolve clerical inconsistencies
automatically when the approved intent is unambiguous. Stop only if resolution
would change scope, architecture, support status, or an owner decision.

At each final stop, provide the required end-of-session report defined in
CODEX_AUTONOMY_CHARTER.md.
```
