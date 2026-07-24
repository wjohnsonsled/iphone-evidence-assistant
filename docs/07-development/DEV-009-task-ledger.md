\# DEV-009 — Task Ledger



| Task ID | Description | Status | Dependencies | Acceptance document | Completion evidence |

|---|---|---|---|---|---|

| DEV-0001 | Repository baseline inspection and reconciliation | COMPLETE | None | DEV-001; DOC-005; PRD-006; DEV-000 | Documentation review recorded through DEV-0002 authorization on 2026-07-24; baseline accepted for scope reconciliation; backend pytest limitation remains recorded in DOC-005 |

| DEV-0002 | Confirm MVP scope against baseline | COMPLETE | DEV-0001 | PRD-003; PRD-007; FOR-004; FOR-006 | Owner approved PRD-007 on 2026-07-24; approval recorded as DEC-0001; no artifact, parser, schema, workflow, or conclusion was promoted |

| DEV-0003 | Create traceability baseline | READY | DEV-0002 approval | DOC-002 | Pending; must trace pre-existing implemented-but-unvalidated code and quarantine controls |

| DEV-0004 | Architecture recommendation | READY | DEV-0002 approval | ARC-001 | Existing architecture is conditionally reusable; supported/legacy registry separation, evidence-source boundaries, security, provenance, timestamps, and working-copy architecture remain undecided |

| DEV-0101 | Backend scaffold | BLOCKED | DEV-0002, DEV-0003, DEV-0004 | To be created | Pre-existing FastAPI/SQLAlchemy/Alembic scaffold remains IMPLEMENTED_NOT_VALIDATED; evaluate for reuse under approved architecture and acceptance criteria |

| DEV-0201 | Apple backup input adapter | BLOCKED | DEV-0003, DEV-0004, DEV-0101 | To be created | Pre-existing path checks are PARTIALLY_IMPLEMENTED and unvalidated; initial target is unencrypted Apple local backup |

| DEV-0203 | Backup encryption-state detection | BLOCKED | DEV-0201, DEV-0202 | To be created | Database field exists, but detection is NOT_IMPLEMENTED; initial release is detection/reporting only |

| DEV-0304 | Artifact support-status model and parser quarantine enforcement | BLOCKED | DEV-0003, DEV-0004 | FOR-004; FOR-006; acceptance document to be created | Legacy registry exists but supported registry/quarantine enforcement is NOT_IMPLEMENTED |



\## Status definitions



\- READY

\- IN\_PROGRESS

\- BLOCKED

\- VALIDATION\_PENDING

\- COMPLETE

\- REJECTED

\- DEFERRED



Only one task may be `IN\_PROGRESS` unless parallel work is explicitly approved.

\## Reconciliation note — 2026-07-24

DEV-0001 found substantial evidence-engine and backend code that predates the
controlled task sequence. Historical task dependencies were not removed or
marked complete. Existing downstream code is inventory evidence only and must
be evaluated under its approved task, acceptance criteria, traceability, tests,
and validation.

No artifact family was promoted from Candidate or Unsupported by this
reconciliation. See `DOC-005`, `PRD-006`, and `DEV-000`.

\## Scope reconciliation note — 2026-07-24

DEV-0002 confirms that unencrypted Apple local backups are the first input
priority. Encrypted backups are detection/reporting-only for the initial
release; decryption and encrypted-only artifact claims are excluded.

The pre-existing backend, evidence engine, parsers, reports, and AI components
remain implemented-but-unvalidated or partial. FOR-006 defines their quarantine
from the future supported production path. DEV-0002 makes no runtime change and
does not complete any downstream implementation task.
