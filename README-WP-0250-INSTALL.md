# Install WP-0250 Evidence Integrity Bundle

Copy these files into the repository:

## Recommended locations

```text
BACKLOG-WP-0250-PATCH.md
CODEX-WP-0250-INTEGRATION-PROMPT.md
docs/02-architecture/ARC-002-evidence-integrity-and-parser-contract.md
docs/07-development/WP-0250-evidence-integrity-infrastructure.md
```

The ZIP contains flat filenames. Move them to the locations above before committing.

## Suggested PowerShell commands

Run from the repository root:

```powershell
New-Item -ItemType Directory -Force -Path ".\docs\02-architecture" | Out-Null
New-Item -ItemType Directory -Force -Path ".\docs\07-development" | Out-Null

Move-Item ".\ARC-002-evidence-integrity-and-parser-contract.md" `
  ".\docs\02-architecture\ARC-002-evidence-integrity-and-parser-contract.md"

Move-Item ".\WP-0250-evidence-integrity-infrastructure.md" `
  ".\docs\07-development\WP-0250-evidence-integrity-infrastructure.md"

git status
```

Review the files, then commit:

```powershell
git add BACKLOG-WP-0250-PATCH.md `
  CODEX-WP-0250-INTEGRATION-PROMPT.md `
  docs/02-architecture/ARC-002-evidence-integrity-and-parser-contract.md `
  docs/07-development/WP-0250-evidence-integrity-infrastructure.md

git commit -m "DOC: add WP-0250 evidence integrity architecture"
git status
```

Do not push.

After the working tree is clean, paste the contents of
`CODEX-WP-0250-INTEGRATION-PROMPT.md` into Codex.

## Important

The patch file instructs Codex to update the live `BACKLOG.md`. It avoids
replacing the backlog with a stale copy and preserves the repository's current
DEV-0202 status, decision history, and task numbering.
