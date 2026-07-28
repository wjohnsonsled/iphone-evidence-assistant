\# DEV-009 — Task Ledger



| Task ID | Description | Status | Dependencies | Acceptance document | Completion evidence |

|---|---|---|---|---|---|

| DEV-0001 | Repository baseline inspection and reconciliation | COMPLETE | None | DEV-001; DOC-005; PRD-006; DEV-000 | Documentation review recorded through DEV-0002 authorization on 2026-07-24; baseline accepted for scope reconciliation; backend pytest limitation remains recorded in DOC-005 |

| DEV-0002 | Confirm MVP scope against baseline | COMPLETE | DEV-0001 | PRD-003; PRD-007; FOR-004; FOR-006 | Owner approved PRD-007 on 2026-07-24; approval recorded as DEC-0001; no artifact, parser, schema, workflow, or conclusion was promoted |

| DEV-0003 | Create traceability baseline | COMPLETE | DEV-0002 approval | DOC-002 | DOC-002 traces 46 uniquely identified requirements to implementation evidence, verification evidence, and owning tasks or explicit gaps; deterministic matrix validation passed; no support status changed |

| DEV-0004 | Architecture recommendation | COMPLETE | DEV-0002 approval | ARC-001 | Owner approved ARC-001 on 2026-07-24; approval recorded as DEC-0002; architecture establishes immutable-source/working-copy boundaries, tenant authorization, provenance-complete records, supported/legacy isolation, and additive migrations without changing support status |

| DEV-0101 | Backend scaffold | COMPLETE | DEV-0002, DEV-0003, DEV-0004 | DEV-0101-backend-scaffold-acceptance | Owner approved completion on 2026-07-24 in DEC-0003; default composition is health-only and import-isolated from legacy processing; backend 12/12 and evidence-engine 5/5 tests passed; pytest temp workaround and TestClient warning recorded; no migration or support promotion |

| DEV-0102 | Dependency locking and reproducible environment | COMPLETE | DEV-0101 | DEV-0102-dependency-locking-acceptance | Owner approved in DEC-0014 with recorded Docker-build, scanning, mutable-image-tag, pytest-directory, and TestClient-warning limitations; no runtime or support-status change |
| DEV-0103 | Configuration model and environment validation | COMPLETE | DEV-0102 | DEV-0103-configuration-validation-acceptance | Closed environment/log/database/root validation, safe diagnostics, 13 focused, 113 backend, and 5 legacy tests pass; WP-0100 package review pending |
| DEV-0104 | Structured error model | COMPLETE | DEV-0103 | DEV-0104-structured-error-acceptance | Typed categories, stable safe envelopes, validation/HTTP/internal translation, 13 focused, 120 backend, and 5 legacy tests pass; WP-0100 review pending |
| DEV-0105 | Structured application logging baseline | COMPLETE | DEV-0103 | DEV-0105-structured-logging-acceptance | Safe JSON formatter, field allowlist, redaction, traceback omission, 20 focused, 129 backend, and 5 legacy tests pass; WP-0100 review pending |
| DEV-0106 | CI architecture and regression gate | READY | DEV-0102 | To be created | Unblocked by DEC-0014 approval of DEV-0102 |

| DEV-0201 | Apple backup input adapter | COMPLETE | DEV-0003, DEV-0004, DEV-0101 | DEV-0201-apple-backup-input-adapter-acceptance | Owner approved completion on 2026-07-24 in DEC-0004; additive read-only adapter implements six explicit outcomes, root/link controls, provenance, limitations, and deterministic audit data; focused 14/14, backend 26/26, and characterization 5/5 tests passed; no input support claim |

| DEV-0202 | Validate required Apple backup structure | COMPLETE | DEV-0201; DEC-0006 through DEC-0010 | DEV-0202-apple-backup-validation-acceptance; FOR-007 candidate profile | Owner approved the synthetic validation framework and controlled classification logic in DEC-0010; candidate profile still requires Apple-produced multi-version validation and separate promotion approval; no support claim |

| DEV-0203 | Backup encryption-state detection | COMPLETE | DEV-0201, DEV-0202 | DEV-0203-backup-encryption-state-acceptance | Owner approved reporting-only projection in DEC-0014; no compatibility-profile, decryption, parser, API, persistence, or support approval |

| DEV-0211 | Profile and validate secondary Apple backup encryption indicators | DEFERRED | Owner-approved signal sources and revised compatibility profile | To be created | Must source, characterize, order, and define conflicts for every candidate signal; requires synthetic and Apple-produced fixtures plus owner approval before implementation or promotion |

| DEV-0251 | Evidence-object domain contract | COMPLETE | DEV-0202; DEC-0011 | WP-0250-acceptance-criteria | Owner approved candidate infrastructure in DEC-0014; typed contract and additive relational model validated synthetically |
| DEV-0252 | Stable evidence identifier strategy | COMPLETE | DEV-0251 | WP-0250-acceptance-criteria | Owner approved in DEC-0014; UUIDv4 identity remains content/path independent |
| DEV-0253 | Evidence lifecycle state machine | COMPLETE | DEV-0251 | WP-0250-acceptance-criteria | Owner approved in DEC-0014; transition and denial matrix accepted with application-level limitations |
| DEV-0254 | Cryptographic hash registry | COMPLETE | DEV-0251, DEV-0252 | WP-0250-acceptance-criteria | Owner approved in DEC-0014; immutable streaming SHA-256 observations validated |
| DEV-0255 | Evidence integrity verification service | COMPLETE | DEV-0254 | WP-0250-acceptance-criteria | Owner approved in DEC-0014; verified/mismatch/unstable/failure states remain distinct |
| DEV-0256 | Evidence access and lock policy | COMPLETE | DEV-0253, DEV-0255 | WP-0250-acceptance-criteria | Owner approved in DEC-0014; application coordination only, not write blocking |
| DEV-0257 | Chain-of-custody event model | COMPLETE | DEV-0251, DEV-0253 | WP-0250-acceptance-criteria | Owner approved in DEC-0014; handling history makes no legal-sufficiency claim |
| DEV-0258 | Evidence audit-event taxonomy | COMPLETE | DEV-0257 | WP-0250-acceptance-criteria | Owner approved in DEC-0014; closed append-only application taxonomy |
| DEV-0259 | Provenance graph foundation | COMPLETE | DEV-0251, DEV-0258 | WP-0250-acceptance-criteria | Owner approved relational candidate model in DEC-0014 |
| DEV-0260 | Provenance relationship validation | COMPLETE | DEV-0259 | WP-0250-acceptance-criteria | Owner approved in DEC-0014 with service-boundary bypass risk retained |
| DEV-0261 | Evidence mutation detector | COMPLETE | DEV-0254, DEV-0255 | WP-0250-acceptance-criteria | Owner approved candidate mutation controls in DEC-0014 |
| DEV-0262 | Integrity policy enforcement service | COMPLETE | DEV-0256, DEV-0260, DEV-0261 | WP-0250-acceptance-criteria | Owner approved candidate policy controls in DEC-0014 |
| DEV-0263 | Common supported-parser contract | COMPLETE | DEV-0259, DEV-0262 | WP-0250-acceptance-criteria | Owner approved candidate-only contract in DEC-0014; conformance grants no support |
| DEV-0264 | Parser-contract conformance harness | COMPLETE | DEV-0263 | WP-0250-acceptance-criteria | Owner approved synthetic conformance harness in DEC-0014 |
| DEV-0265 | End-to-end integrity validation package | COMPLETE | DEV-0251 through DEV-0264 | WP-0250-acceptance-criteria | Owner approved WP-0250 candidate infrastructure with all documented limitations in DEC-0014 |

| DEV-0304 | Artifact support-status model and parser quarantine enforcement | COMPLETE | DEV-0003, DEV-0004 | DEV-0304-support-status-quarantine-acceptance; FOR-004; FOR-006 | Owner approved in DEC-0014; supported registry remains empty and no capability is promoted |
| DEV-0307 | Cross-tenant isolation tests | BLOCKED | DEV-0310, DEV-0305 | To be created | Dependency corrected by DEC-0014; implementation is not authorized until dependencies complete |
| DEV-0310 | Authorization Service and Policy Enforcement | BLOCKED | DEV-0301, DEV-0302, DEV-0303 | To be created | Reserved by DEC-0014; no implementation authorization until dependencies and task-specific acceptance record are complete |



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
