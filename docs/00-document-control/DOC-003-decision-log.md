# DOC-003 — Decision Log

## DEC-0001 — Approve DEV-0002 MVP scope reconciliation

- Date: 2026-07-24
- Status: APPROVED
- Owner: Project owner
- Task: DEV-0002
- Decision source: Explicit owner approval recorded in the controlled
  development task on 2026-07-24
- Governing document: PRD-007

### Decision

The owner approved the DEV-0002 scope reconciliation in PRD-007:

- unencrypted Apple local backups are the first supported-input target;
- encrypted Apple local backups are detection-and-reporting-only and are not
  decrypted in the initial MVP;
- backup metadata, `Manifest.db` inventory, SMS/iMessage records, message
  attachments, call history, and contacts are the only initial MVP artifact
  candidates;
- candidate status does not confer support;
- all existing legacy parsers remain quarantined and unsupported unless
  individually validated and promoted through a separate owner-review gate;
- unsupported or quarantined output is prohibited from supported evidence
  storage, AI retrieval, attorney-facing reports, supported coverage
  calculations, and production claims;
- the excluded inputs and artifact families listed in PRD-007 remain outside
  the initial supported path; and
- existing implementation may be retained for compatibility,
  characterization, or future validation without being represented as
  supported.

### Consequences

- DEV-0002 may be marked `COMPLETE`.
- DEV-0003 and DEV-0004 are unblocked and must proceed in approved plan order.
- No artifact, parser, schema, workflow, or conclusion is promoted to supported
  status by this decision.
- Each parser promotion requires a separate owner-review gate after all
  all-or-nothing requirements are satisfied.

## DEC-0002 — Approve DEV-0004 system architecture

- Date: 2026-07-24
- Status: APPROVED
- Owner: Project owner
- Task: DEV-0004
- Decision source: Explicit owner approval recorded in the controlled
  development task on 2026-07-24
- Governing document: ARC-001

### Decision

The owner approved ARC-001 as the architectural basis for the MVP:

- use an incremental modular monolith with enforceable module boundaries;
- treat source evidence as immutable and process supported SQLite artifacts
  only from controlled, hashed working copies with required companions;
- separate source evidence, working copies, supported normalized evidence,
  legacy/experimental output, and derived AI/reporting work product;
- introduce tenant, user, case, authorization, evidence-source,
  processing-run, provenance, coverage, failure, and audit entities;
- separate supported and legacy registries, composition roots, execution
  paths, stores, and retrieval paths;
- exclude legacy and unsupported output from every supported or
  attorney-facing product path;
- require supported processing to fail closed with distinct controlled
  outcomes;
- require complete raw/normalized values, source identity and locator, parser
  and schema identity, processing-run identity, timestamp provenance, and
  applicable hashes for supported records;
- restrict search, AI, citations, and reports to supported records; and
- use additive and reversible MVP migrations unless a later owner decision
  approves destructive or data-rewriting behavior.

### Consequences

- DEV-0004 may be marked `COMPLETE`.
- ARC-001 becomes an approved architecture source for downstream task
  requirements and acceptance criteria.
- DEV-0101 is unblocked after its task-specific requirements and measurable
  acceptance criteria are defined.
- No parser, artifact family, input type, schema, workflow, or conclusion is
  promoted to supported status.

## DEC-0003 — Approve DEV-0101 backend scaffold

- Date: 2026-07-24
- Status: APPROVED
- Owner: Project owner
- Task: DEV-0101
- Decision source: Explicit owner approval recorded in the controlled
  development task on 2026-07-24
- Governing document: DEV-0101 backend scaffold acceptance criteria

### Decision

The owner approved DEV-0101 as complete:

- the default FastAPI composition root exposes only the approved scaffold
  surface;
- legacy case, evidence, summary, and processing routes remain isolated behind
  the explicit legacy compatibility application;
- legacy processing remains unavailable from the default composition root;
- the scaffold-boundary tests and recorded passing results are accepted as the
  validation record;
- use of a repository-local ignored pytest temporary directory is accepted as
  a documented development-environment workaround;
- the third-party TestClient deprecation warning is accepted as tracked
  technical debt; and
- the explicit legacy application must not be deployed, exposed, or included
  in the supported SaaS surface.

### Consequences

- DEV-0101 remains `COMPLETE`.
- DEV-0201 may begin after task-specific measurable acceptance criteria and
  DOC-002 mappings are created.
- RSK-0001 and RSK-0002 track the accepted residual risks.
- No parser, artifact family, input type, workflow, or production capability is
  promoted to supported status.
