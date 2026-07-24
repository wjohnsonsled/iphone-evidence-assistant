\# DEV-001 — Master Implementation Plan



\## Phase 0 — Repository and requirements baseline



\- DEV-0001: Inspect repository and document current state.

\- DEV-0002: Confirm MVP scope.

\- DEV-0003: Establish requirements traceability.

\- DEV-0004: Establish development, test, and documentation conventions.

\- DEV-0005: Identify unresolved architectural decisions.



Exit criteria:



\- Repository baseline approved.

\- MVP boundaries documented.

\- Initial architecture decision recorded.

\- No production feature implementation has begun using unresolved assumptions.

\### Phase 0 reconciliation controls

\- DEV-0001 records the pre-existing implementation as baseline inventory.

\- DEV-0002 limits the initial MVP to unencrypted-first Apple local backups and
the artifact candidates in PRD-003 and FOR-004.

\- Existing evidence-engine and backend code is implemented-but-unvalidated and
does not satisfy a downstream task merely because it exists.

\- FOR-006 requires a separate approved production parser registry and
quarantine of legacy, experimental, deferred, and unsupported parser output.

\- Runtime quarantine is not implemented by DEV-0002 and must be assigned an
approved implementation task after traceability, architecture, and acceptance
criteria are established.



\## Phase 1 — Application foundation



\- DEV-0101: Establish backend application scaffold.

\- DEV-0102: Establish database and migrations.

\- DEV-0103: Establish case and evidence-source models.

\- DEV-0104: Establish structured logging.

\- DEV-0105: Establish error and status models.

\- DEV-0106: Establish test framework.

\- DEV-0107: Establish local Docker development environment.

\- DEV-0108: Establish CI quality checks.

Phase 1 must evaluate the pre-existing scaffold before reuse. Authentication,
authorization, tenant isolation, evidence-source boundaries, and audit records
must be designed before the scaffold can be accepted for a shared deployment.



\## Phase 2 — Apple backup intake



\- DEV-0201: Define Apple backup input adapter.

\- DEV-0202: Validate required backup structure.

\- DEV-0203: Detect encrypted versus unencrypted backups.

\- DEV-0204: Parse backup metadata plists.

\- DEV-0205: Parse supported Manifest.db schemas.

\- DEV-0206: Build deterministic backup inventory.

\- DEV-0207: Generate source hashes.

\- DEV-0208: Reconcile manifest entries to stored files.

\- DEV-0209: Produce intake coverage report.

\- DEV-0210: Persist processing errors and omissions.

Phase 2 input order:

1\. Validated unencrypted Apple local backup.

2\. Encrypted-backup detection and explicit reporting only.

Encrypted-backup decryption, password handling, extracted-directory support,
physical/full-filesystem acquisition, and third-party extraction ingestion are
not included without separate approval.



\## Phase 3 — Evidence normalization and provenance



\- DEV-0301: Define normalized artifact envelope.

\- DEV-0302: Define source locator model.

\- DEV-0303: Define parser execution records.

\- DEV-0304: Define artifact support-status model.

\- DEV-0305: Implement raw and normalized value preservation.

\- DEV-0306: Implement timestamp provenance model.



\## Phase 4 — First supported artifact



Implement one artifact family completely before beginning the next.



Recommended order:



1\. Backup metadata and inventory

2\. Messages

3\. Message attachments

4\. Calls

5\. Contacts



Each parser requires:



\- schema detection;

\- read-only controlled working copy;

\- deterministic extraction;

\- source provenance;

\- explicit error behavior;

\- synthetic fixtures;

\- expected-result fixtures;

\- unit tests;

\- integration tests;

\- validation review;

\- support-matrix update.

Only the approved production registry may execute in the supported path.
Legacy compatibility, experimental, deferred, and unsupported parser output
must be excluded from supported stores, search, AI, reports, citations, and
coverage calculations.



\## Phase 5 — Search and evidence review



\- Structured artifact search

\- Filters

\- Pagination

\- Source inspection

\- Provenance display

\- Processing-coverage display



\## Phase 6 — Evidence-grounded AI



\- Retrieval boundary

\- Artifact ranking

\- Citation generation

\- Citation resolver

\- Fact-versus-interpretation formatting

\- Limitations enforcement

\- Evaluation dataset

\- Unsupported-question handling



\## Phase 7 — Reporting



\- Scope

\- Evidence sources

\- Methodology

\- Coverage

\- Findings

\- Citations

\- Limitations

\- Export validation



\## Phase 8 — Security and SaaS readiness



\- Authentication

\- Authorization

\- Tenant isolation

\- Encryption

\- Retention and deletion

\- Audit logging

\- Rate limiting

\- Upload hardening

\- Backup and recovery

\- Security testing



\## Phase execution rule



Codex must implement one approved task at a time.



Codex must not continue automatically to the next task after completing the

current task.

Implementation presence is not task completion or support evidence. Every task
requires its own approved acceptance criteria, traceability, tests, validation,
documentation, and completion review.

