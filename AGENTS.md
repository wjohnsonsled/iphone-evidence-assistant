\# AGENTS.md



\## Project



This repository contains the AI-Powered iPhone Evidence Assistant.



The product accepts supported Apple local iPhone backups, processes approved

forensic artifacts, and allows authorized users to search, review, cite,

summarize, and report on evidence using natural language.



The product is not intended to replace forensic acquisition tools. It is an

evidence-understanding and review platform.



\## Governing priorities



In descending order:



1\. Evidence integrity

2\. Accurate and traceable results

3\. Explicit support boundaries

4\. Security and tenant isolation

5\. Explainable AI

6\. Attorney-friendly workflows

7\. Maintainable architecture

8\. Development speed



Do not trade a higher priority for a lower priority without explicit approval.



\## Mandatory forensic rules



\- Never modify submitted source evidence.

\- Treat source evidence as immutable.

\- Separate source evidence from all derived data.

\- Generate and retain SHA-256 hashes for source and material derived files.

\- Every normalized record must retain provenance to its source artifact.

\- Every displayed evidentiary assertion must be traceable to source records.

\- Preserve original values in addition to normalized values.

\- Do not silently discard unreadable, malformed, unknown, or unsupported data.

\- Record processing failures and coverage limitations explicitly.

\- Do not infer intent, motive, legal responsibility, or identity from technical

&#x20; artifacts alone.

\- Do not fabricate evidence, records, relationships, timestamps, or conclusions.

\- Absence of a record is not proof that an event did not occur.

\- A local Apple backup is not a complete physical image of an iPhone.

\- Do not represent backup contents as everything that existed on the device.



\## Input scope



The initial product supports Apple local iPhone backups.



The application must distinguish between:



\- unencrypted Apple local backups;

\- encrypted Apple local backups;

\- malformed or incomplete backup packages;

\- unsupported input formats.



The MVP should prioritize artifact families available in ordinary Apple local

backups. It must not require encrypted backups unless an implemented feature

depends on encrypted-only material.



Encrypted-only artifact families such as Health or keychain-derived credentials

are outside the initial MVP unless separately approved, implemented, validated,

and documented.



\## All-or-nothing support rule



A feature, parser, artifact type, workflow, schema version, or conclusion is not

supported until its complete declared behavior is:



\- implemented;

\- validated;

\- tested;

\- documented;

\- provenance-aware;

\- failure-aware;

\- and covered by explicit acceptance criteria.



Partial support must be classified as unsupported or experimental.



Do not label partially implemented functionality as supported.

Every capability promoted to Supported must permanently reference:

- Owner Decision ID;
- Validation Package ID;
- Acceptance Record IDs;
- Promotion Date; and
- Current Support Status.

Support promotion must be fully traceable through repository documentation.



\## Artifact support statuses



Use only controlled statuses such as:



\- SUPPORTED\_COMPLETE

\- SUPPORTED\_NO\_RECORDS

\- UNSUPPORTED

\- INACCESSIBLE

\- CORRUPTED

\- FAILED

\- EXCLUDED



Do not treat file presence as proof of parser support.



\## AI rules



\- AI answers must be grounded only in records available to the authorized case.

\- Material factual claims must cite supporting artifact records.

\- Citations must resolve to stable internal record identifiers.

\- The UI must allow the user to inspect the underlying source record.

\- AI must distinguish artifact facts from interpretations.

\- AI must state material uncertainty and limitations.

\- AI must not use unsupported artifacts as validated evidence.

\- AI must not claim that missing evidence proves an event did not occur.

\- Model output is derived work product and must never overwrite evidence data.



\## Time handling



\- Preserve the original timestamp value.

\- Preserve the original timestamp format and source field.

\- Record the conversion method.

\- Normalize timestamps to UTC for comparison.

\- Display local time only when the applicable timezone is known or explicitly

&#x20; selected.

\- Never silently assume a timezone.

\- Record timestamp precision and known limitations.



\## SQLite handling



\- Treat SQLite main databases, WAL files, and rollback journals as potentially

&#x20; related evidence.

\- Never open source databases in writable mode.

\- Perform analysis on controlled working copies.

\- Document whether WAL or journal files were present.

\- Do not claim byte-for-byte identity between a backup database and its

&#x20; on-device source.

\- Distinguish logical backup records from physical or deleted-data recovery.



\## Security rules



\- Never commit client evidence.

\- Never commit credentials, passwords, API keys, tokens, or production secrets.

\- Never log backup passwords or decrypted secret values.

\- Do not expose one tenant's case data to another tenant.

\- Enforce authorization server-side.

\- Validate uploaded files and paths.

\- Prevent path traversal, archive traversal, and unsafe file execution.

\- Use secure defaults.

\- Treat evidence filenames and artifact content as untrusted input.



\## Development method



Before editing code:



1\. Read the relevant documentation under `docs/`.

2\. Inspect the existing implementation.

3\. Identify the applicable requirement and task IDs.

4\. State assumptions and unresolved questions.

5\. Avoid inventing requirements.



For each implementation task:



1\. Work on only the approved task.

2\. Make the smallest coherent change.

3\. Add or update tests.

4\. Run relevant tests and quality checks.

5\. Compare results against every acceptance criterion.

6\. Update documentation when behavior changes.

7\. Update the requirements traceability matrix.

8\. Update the task ledger.

9\. Report files changed, tests run, results, and remaining limitations.

10\. Stop before beginning the next task unless explicitly instructed.



\## Coding standards



\- Prefer modular, typed, testable code.

\- Keep evidence-processing logic separate from API and UI code.

\- Keep vendor-specific parsers behind defined interfaces.

\- Use database migrations for schema changes.

\- Do not introduce a framework or dependency without documenting the reason.

\- Avoid duplicate implementations.

\- Use structured error types rather than silent exception handling.

\- Do not catch broad exceptions unless they are logged and converted into an

&#x20; explicit processing failure.

\- Add comments for forensic assumptions and non-obvious transformations.

\- Do not leave placeholder implementations that appear functional.



\## Testing requirements



At minimum, include:



\- unit tests;

\- malformed-input tests;

\- deterministic-output tests;

\- provenance tests;

\- timestamp tests;

\- parser fixture tests;

\- authorization tests where applicable;

\- regression tests for defects.



Use synthetic or lawfully distributable test data only.



Tests must verify both successful behavior and explicit failure behavior.



\## Completion reporting



At the end of each task, report:



\- task ID;

\- summary;

\- files changed;

\- migrations added;

\- tests added or changed;

\- commands run;

\- test results;

\- acceptance criteria status;

\- forensic limitations;

\- security implications;

\- documentation updated;

\- unresolved issues;

\- recommended next task.



Do not claim completion when tests fail or acceptance criteria remain unmet.

# AGENTS.md Addendum — Autonomous MVP Execution

Add the following section to the repository's existing `AGENTS.md`. Do not replace existing instructions.

---

## Autonomous MVP Execution

The repository root files `BACKLOG.md` and `CODEX_AUTONOMY_CHARTER.md` govern task sequencing and autonomous execution.

Before starting work, the agent must read:

- `BACKLOG.md`
- `CODEX_AUTONOMY_CHARTER.md`
- the decision log;
- the task ledger;
- the risk register;
- the requirements traceability matrix;
- the approved architecture.

The agent must automatically select the first `READY` task in plan order and may continue through all unblocked tasks in the current work package without routine owner approval.

The agent must stop only at:

- a mandatory stop condition in `CODEX_AUTONOMY_CHARTER.md`;
- a work-package owner-review gate;
- an artifact-support promotion gate;
- a release gate.

Repository-specific approved decisions override generic backlog wording.

No agent may infer support status from implementation presence.

No unsupported or legacy output may enter supported stores, retrieval, AI, citations, reports, coverage calculations, or production claims.
