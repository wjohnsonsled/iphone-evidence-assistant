# Codex Prompt — Integrate and Execute WP-0250

```text
The owner authorizes insertion of WP-0250 — Evidence Integrity Infrastructure.

Before changing the repository:

1. Verify branch mvp-development.
2. Verify the working tree is clean.
3. Read:
   - AGENTS.md
   - BACKLOG.md
   - CODEX_AUTONOMY_CHARTER.md
   - WP-0250-evidence-integrity-infrastructure.md
   - ARC-002-evidence-integrity-and-parser-contract.md
   - BACKLOG-WP-0250-PATCH.md
   - DOC-002 requirements traceability matrix
   - DOC-003 decision log
   - DOC-004 risk register
   - DEV-009 task ledger
   - ARC-001 approved system architecture
   - DEV-0202 acceptance and completion records

First determine whether DEV-0202 has been explicitly approved COMPLETE.

If DEV-0202 is not COMPLETE:
- integrate the WP-0250 planning documents and backlog entries;
- mark WP-0250 blocked by DEV-0202;
- do not begin implementation;
- stop only if the existing governance requires owner completion approval.

If DEV-0202 is COMPLETE:
- integrate WP-0250 into BACKLOG.md and DEV-009;
- reconcile overlap with existing DEV-0203 through DEV-0207 tasks;
- preserve all existing task IDs, decisions, completed work, and audit history;
- do not create duplicate evidence registration, hashing, audit, or provenance
  implementations;
- update dependencies for the supported evidence store, processing pipeline,
  artifact parsers, search, AI, reports, and exports;
- record the planning decision in DOC-003;
- update DOC-002 and DOC-004;
- create task-specific acceptance criteria;
- proceed autonomously through DEV-0251 to DEV-0265.

Implementation constraints:

- relational implementation for MVP;
- no graph database;
- application-level lock controls only;
- SHA-256 required;
- hash observations immutable;
- evidence UUID distinct from content hash;
- source evidence immutable;
- controlled inputs only;
- append-only custody and audit records through services;
- complete tenant-scoped provenance;
- no digital-signature or nonrepudiation claim;
- no production API;
- no real evidence;
- no support promotion;
- no push, merge, or deployment.

Common supported-parser contract:

Every future supported parser must declare identity, version, artifact family,
schema profiles, validation behavior, parse behavior, provenance, coverage,
limitations, and self-test behavior.

A parser implementing the contract remains CANDIDATE until its artifact package
passes a separate owner support-promotion gate.

Autonomous execution:

- continue through all unblocked WP-0250 tasks;
- create local commits;
- keep the working tree clean between tasks;
- do not ask for routine implementation approval;
- stop at the WP-0250 owner-review gate or a genuine mandatory stop condition.

At the final stop, provide:
- task and acceptance matrix;
- migrations;
- lifecycle transition table;
- hash policy;
- audit taxonomy;
- chain-of-custody specification;
- provenance model;
- parser contract;
- conformance results;
- all test results;
- risks and limitations;
- local commit hashes;
- clean working-tree confirmation;
- explicit confirmation that no support status changed.
```
