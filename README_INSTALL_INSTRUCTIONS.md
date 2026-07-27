# Installation Instructions for the Codex Governance Bundle

Copy these files to the repository root:

- `BACKLOG.md`
- `CODEX_AUTONOMY_CHARTER.md`
- `WORK_PACKAGE_TEMPLATE.md`
- `OWNER_REVIEW_CHECKLIST.md`
- `CODEX_START_PROMPT.md`
- `AGENTS_ADDENDUM.md`

Then:

1. Open the existing `AGENTS.md`.
2. Append the contents of `AGENTS_ADDENDUM.md`.
3. Keep `AGENTS_ADDENDUM.md` temporarily for audit history, or delete it after
   committing the integrated `AGENTS.md`.
4. Review `BACKLOG.md` against `DEV-009-task-ledger.md`.
5. Do not overwrite approved task names or IDs already present in the ledger.
6. Commit the governance bundle locally.
7. Paste the contents of `CODEX_START_PROMPT.md` into Codex.

Recommended local commit:

```text
DOC: add autonomous MVP backlog and Codex governance
```

Important:

- The backlog is a planning baseline, not authority to promote support.
- Existing approved decisions remain controlling.
- Codex must reconcile differences rather than replacing repository governance.
- Keep all work on `mvp-development`.
- Do not let Codex push or deploy.
