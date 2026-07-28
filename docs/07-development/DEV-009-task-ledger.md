\# DEV-009 — Task Ledger



| Task ID | Description | Status | Dependencies | Acceptance document | Completion evidence |

|---|---|---|---|---|---|

| DEV-0001 | Repository baseline inspection and reconciliation | COMPLETE | None | DEV-001; DOC-005; PRD-006; DEV-000 | Documentation review recorded through DEV-0002 authorization on 2026-07-24; baseline accepted for scope reconciliation; backend pytest limitation remains recorded in DOC-005 |

| DEV-0002 | Confirm MVP scope against baseline | COMPLETE | DEV-0001 | PRD-003; PRD-007; FOR-004; FOR-006 | Owner approved PRD-007 on 2026-07-24; approval recorded as DEC-0001; no artifact, parser, schema, workflow, or conclusion was promoted |

| DEV-0003 | Create traceability baseline | COMPLETE | DEV-0002 approval | DOC-002 | DOC-002 traces 46 uniquely identified requirements to implementation evidence, verification evidence, and owning tasks or explicit gaps; deterministic matrix validation passed; no support status changed |

| DEV-0004 | Architecture recommendation | COMPLETE | DEV-0002 approval | ARC-001 | Owner approved ARC-001 on 2026-07-24; approval recorded as DEC-0002; architecture establishes immutable-source/working-copy boundaries, tenant authorization, provenance-complete records, supported/legacy isolation, and additive migrations without changing support status |

| DEV-0101 | Backend scaffold | COMPLETE | DEV-0002, DEV-0003, DEV-0004 | DEV-0101-backend-scaffold-acceptance | Owner approved completion on 2026-07-24 in DEC-0003; default composition is health-only and import-isolated from legacy processing; backend 12/12 and evidence-engine 5/5 tests passed; pytest temp workaround and TestClient warning recorded; no migration or support promotion |

| DEV-0102 | Dependency locking and reproducible environment | COMPLETE | DEV-0101 | DEV-0102-dependency-locking-acceptance | Owner approved in DEC-0014 with recorded Docker-build, scanning, mutable-image-tag, pytest-directory, and TestClient-warning limitations; no runtime or support-status change |
| DEV-0103 | Configuration model and environment validation | COMPLETE | DEV-0102 | DEV-0103-configuration-validation-acceptance | Owner approved in DEC-0019 with QMS-006 and RSK-0015 limitations retained |
| DEV-0104 | Structured error model | COMPLETE | DEV-0103 | DEV-0104-structured-error-acceptance | Owner approved in DEC-0019; safe error boundary adds no production-facing API authorization |
| DEV-0105 | Structured application logging baseline | COMPLETE | DEV-0103 | DEV-0105-structured-logging-acceptance | Owner approved in DEC-0019; structured operational logs remain distinct from immutable audit records |
| DEV-0106 | CI architecture and regression gate | COMPLETE | DEV-0102 | DEV-0106-ci-regression-gate-acceptance | Owner approved in DEC-0019 with QMS-006, RSK-0017, and RSK-0018 limitations retained |

| DEV-0201 | Apple backup input adapter | COMPLETE | DEV-0003, DEV-0004, DEV-0101 | DEV-0201-apple-backup-input-adapter-acceptance | Owner approved completion on 2026-07-24 in DEC-0004; additive read-only adapter implements six explicit outcomes, root/link controls, provenance, limitations, and deterministic audit data; focused 14/14, backend 26/26, and characterization 5/5 tests passed; no input support claim |

| DEV-0202 | Validate required Apple backup structure | COMPLETE | DEV-0201; DEC-0006 through DEC-0010 | DEV-0202-apple-backup-validation-acceptance; FOR-007 candidate profile | Owner approved the synthetic validation framework and controlled classification logic in DEC-0010; candidate profile still requires Apple-produced multi-version validation and separate promotion approval; no support claim |

| DEV-0203 | Backup encryption-state detection | COMPLETE | DEV-0201, DEV-0202 | DEV-0203-backup-encryption-state-acceptance | Owner approved reporting-only projection in DEC-0014; no compatibility-profile, decryption, parser, API, persistence, or support approval |

| DEV-0204 | SHA-256 hashing service | COMPLETE | DEV-0203; DEV-0254, DEV-0255 | DEV-0204-sha256-hashing-acceptance | Adopted the owner-approved WP-0250 HashRegistry as the sole intake hash authority; focused and regression validation passed; no duplicate service, API, parser, evidence access, or support promotion |

| DEV-0205 | Controlled SQLite working-copy service | COMPLETE | DEV-0204 | DEV-0205-controlled-sqlite-working-copy-acceptance | Adopted the schema-neutral DEV-0202 mechanism as the single general candidate service; source/companion stability, isolation, read-only SQLite, verification, cleanup, and safe failures validated synthetically |

| DEV-0206 | Intake audit-event model | COMPLETE | DEV-0203; DEV-0258 | DEV-0206-intake-audit-event-acceptance | Adopted the closed WP-0250 audit taxonomy and append-only reference service; intake scope, ordering, immutability, success/failure, and correlation validated synthetically |

| DEV-0207 | Intake provenance model | COMPLETE | DEV-0203; DEV-0259, DEV-0260 | DEV-0207-intake-provenance-acceptance | Adopted the WP-0250 relational model; synthetic evidence-source, source-artifact, and controlled-copy lineage resolves deterministically and rejects broken or cross-scope relationships |

| DEV-0208 | Intake cleanup and failure recovery | COMPLETE | DEV-0205 | DEV-0208-intake-cleanup-recovery-acceptance | Context cleanup retained and bounded prefix/root/age-scoped orphan recovery added; removal, recent skip, unsafe rejection, and failure outcomes validated synthetically |

| DEV-0209 | Intake resource limits and denial-of-service controls | COMPLETE | DEV-0202; DEC-0025 | DEV-0209-intake-resource-limits-acceptance | Explicit caller-supplied policy validates ten required ceilings; adapter/copy/plist/schema/SQLite work limits fail closed with safe validation-failure outcomes and no support promotion |

| DEV-0210 | Intake package integration tests | COMPLETE | DEV-0203 through DEV-0209 | DEV-0210-intake-package-integration-acceptance; QMS-007 | Owner approved in DEC-0027 as candidate intake architecture only; supported registry remains empty |

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
| DEV-0301 | Tenant model | COMPLETE | DEV-0103 | DEV-0301-tenant-model-acceptance | Neutral immutable UUIDv4 tenant identity and additive ORM contract validated; no migration, API, authorization, or production tenancy decision |
| DEV-0302 | User and role model | COMPLETE | DEV-0301 | DEV-0302-user-role-model-acceptance | Neutral USER/SERVICE principals and tenant-scoped opaque role memberships validated; no permissions, credentials, authorization, API, or migration |
| DEV-0303 | Case model | COMPLETE | DEV-0301 | DEV-0303-case-model-acceptance | Tenant-scoped immutable case identity and separate additive ORM contract validated; legacy cases unchanged; no migration/API/authorization |
| DEV-0305 | Evidence-source tenant and case linkage | READY | DEV-0203, DEV-0303 | To be created | Dependencies satisfied; next task in plan order |
| DEV-0306 | Audit-actor attribution | READY | DEV-0302, DEV-0206 | To be created | Dependencies satisfied; plan order remains after DEV-0303 and DEV-0305 |
| DEV-0307 | Cross-tenant isolation tests | BLOCKED | DEV-0310, DEV-0305 | To be created | Dependency corrected by DEC-0014; implementation is not authorized until dependencies complete |
| DEV-0310 | Authorization Service and Policy Enforcement | READY | DEV-0301, DEV-0302, DEV-0303 | To be created | Reserved by DEC-0014; dependencies satisfied but plan order follows DEV-0305 and DEV-0306 |

| DEV-0451 | Source Inventory Engine | BLOCKED | WP-0200, WP-0250, DEV-0402, DEV-0403 | To be created | WP-0450 allocation under DEC-0027; blocked by evidence identity/locator foundation |
| DEV-0452 | Artifact Coverage Engine | BLOCKED | DEV-0451, DEV-0304, DEV-0408, DEV-0409, DEV-1101 through DEV-1106 | To be created | Must distinguish authorization, execution, zero, rejection, failure, partial, and unsupported |
| DEV-0453 | Evidence Gap Classification | BLOCKED | DEV-0451, DEV-0452 | To be created | Closed versioned fail-closed vocabulary required |
| DEV-0454 | Backup Structure and Coverage Assessment | BLOCKED | DEV-0451, DEV-0453, WP-0200 | To be created | Must not infer completeness, deletion, concealment, destruction, or spoliation |
| DEV-0455 | Collection Opportunity Engine | FUTURE | DEV-0453, DEV-0454, WP-1900 where applicable | To be created | Post-MVP; reproducible versioned rules required |
| DEV-0456 | Question-Specific Evidence Sufficiency Engine | FUTURE | DEV-0453, WP-1200, WP-1300 | To be created | Post-MVP; no legal sufficiency conclusion |
| DEV-0457 | Acquisition Recommendation Engine | FUTURE | DEV-0455, DEV-0456 | To be created | Post-MVP; separate acquisition-method approval |
| DEV-0458 | Attorney Coverage Summary Generator | BLOCKED | DEV-0453, DEV-0454, DEV-1401, DEV-1404 | To be created | Attorney-readable limitations mandatory |
| DEV-0459 | Commercial Services Integration | FUTURE | DEV-0457; separate approval | To be created | No external or paid integration authorized |
| DEV-0460 | Coverage Report Integration | BLOCKED | DEV-0458, WP-1400 | To be created | Blocked by reporting and coverage package gates |



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
