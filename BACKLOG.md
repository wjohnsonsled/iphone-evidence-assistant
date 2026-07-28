# AI-Powered iPhone Evidence Assistant
## Master MVP Implementation Backlog

**Document status:** Active  
**Primary branch:** `mvp-development`  
**Execution model:** Codex may complete the next unblocked task automatically within the active work package.  
**Owner-review model:** Codex must stop only at the gates defined in this document and in `CODEX_AUTONOMY_CHARTER.md`.

---

## 1. Governing Principles

All implementation work must preserve:

1. Evidence integrity.
2. Explainable and traceable AI.
3. Supported-record-only retrieval, citations, and reports.
4. Clear separation of supported, legacy, experimental, and unsupported functionality.
5. Fail-closed behavior.
6. Tenant isolation and least privilege.
7. Deterministic tests using synthetic fixtures.
8. Attorney-readable limitations.
9. Additive and reversible migrations unless separately approved.
10. No production support claim without an explicit owner-review gate.

A feature is not supported merely because code exists.

Partial support is unsupported.

---

## 2. Global Task Status Vocabulary

Use only the following statuses:

- `NOT_STARTED`
- `READY`
- `IN_PROGRESS`
- `BLOCKED`
- `VALIDATION_PENDING`
- `COMPLETE`
- `REJECTED`
- `DEFERRED`

A task may become `READY` only when all dependencies are `COMPLETE`.

---

## 3. Global Completion Requirements

A task may be marked `VALIDATION_PENDING` only when:

- task-specific acceptance criteria exist;
- requirements are mapped in the traceability matrix;
- implementation is complete;
- deterministic tests pass;
- regression tests pass;
- documentation is updated;
- risk-register changes are recorded when applicable;
- no unsupported capability is promoted;
- a local Git commit exists;
- the working tree is clean.

A task may be marked `COMPLETE` only after the required owner approval is recorded.

---

# PHASE 0 — GOVERNANCE

## WP-0000 Governance Baseline

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0001 | Repository baseline and gap analysis | COMPLETE | None | Complete |
| DEV-0002 | MVP scope reconciliation | COMPLETE | DEV-0001 | Complete |
| DEV-0003 | Requirements traceability baseline | COMPLETE | DEV-0002 | Complete |
| DEV-0004 | Architecture recommendation | COMPLETE | DEV-0003 | Complete |

**Work package status:** `COMPLETE`

---

# PHASE 1 — APPLICATION FOUNDATION

## WP-0100 Backend Foundation

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0101 | Backend scaffold and legacy isolation | COMPLETE | DEV-0004 | Complete |
| DEV-0102 | Dependency locking and reproducible environment | COMPLETE | DEV-0101 | Complete; DEC-0014 |
| DEV-0103 | Configuration model and environment validation | COMPLETE | DEV-0102 | Complete; DEC-0019 |
| DEV-0104 | Structured error model | COMPLETE | DEV-0103 | Complete; DEC-0019 |
| DEV-0105 | Structured application logging baseline | COMPLETE | DEV-0103 | Complete; DEC-0019 |
| DEV-0106 | CI architecture and regression gate | COMPLETE | DEV-0102 | Complete; DEC-0019 |

### WP-0100 completion criteria

- reproducible local installation;
- pinned dependency strategy;
- validated configuration;
- typed error model;
- structured logs without evidence-content leakage;
- automated tests and architecture-boundary checks.

**Owner-review gate:** Satisfied by DEC-0019 for foundation infrastructure
only. Production-facing API work remains separately governed.

---

# PHASE 2 — APPLE BACKUP INTAKE

## WP-0200 Apple Backup Intake and Validation

**Package status:** `COMPLETE` — owner approved candidate infrastructure in
DEC-0027; support effect remains none.
**Support effect:** None.

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0201 | Apple backup input adapter | COMPLETE | DEV-0101 | Complete |
| DEV-0202 | Apple backup structure validator | COMPLETE | DEV-0201 | Complete; synthetic framework only |
| DEV-0203 | Backup encryption-state detection | COMPLETE | DEV-0202 | Complete; DEC-0014 |
| DEV-0204 | SHA-256 hashing service | COMPLETE | DEV-0203 | WP-0200 package review |
| DEV-0205 | Controlled SQLite working-copy service | COMPLETE | DEV-0204 | WP-0200 package review |
| DEV-0206 | Intake audit-event model | COMPLETE | DEV-0203 | WP-0200 package review |
| DEV-0207 | Intake provenance model | COMPLETE | DEV-0203 | WP-0200 package review |
| DEV-0208 | Intake cleanup and failure recovery | COMPLETE | DEV-0205 | WP-0200 package review |
| DEV-0209 | Intake resource limits and denial-of-service controls | COMPLETE | DEV-0202 | WP-0200 package review |
| DEV-0210 | Intake package integration tests | COMPLETE | DEV-0203 through DEV-0209 | Complete; DEC-0027 |
| DEV-0211 | Profile and validate secondary Apple backup encryption indicators | DEFERRED | Separately approved signal sources and revised compatibility profile | Owner profile gate |

### DEV-0202 required classifications

The approved validator vocabulary must explicitly distinguish at least:

- `INVALID_INPUT`
- `NOT_AN_APPLE_BACKUP`
- `APPLE_BACKUP_INCOMPLETE`
- `APPLE_BACKUP_CORRUPT`
- `APPLE_BACKUP_ENCRYPTED`
- `APPLE_BACKUP_UNENCRYPTED`
- `APPLE_BACKUP_UNSUPPORTED_VERSION`
- `APPLE_BACKUP_VALIDATION_FAILED`
- `APPLE_BACKUP_INDETERMINATE`

The vocabulary and precedence were approved by the owner for DEV-0202 Stage B
on 2026-07-27. Existing approved decisions and DEV-009 control if generic
backlog wording differs.

### WP-0200 completion criteria

- immutable source boundary;
- source registration and stable evidence identifier;
- SHA-256 hashing with deterministic records;
- controlled-copy validation of SQLite files and companions;
- explicit encryption-state detection;
- intake audit and provenance;
- cleanup verification;
- fail-closed resource limits;
- synthetic end-to-end intake fixtures;
- no artifact parser support claim.

**Owner-review gate:** Satisfied by DEC-0027 for candidate intake architecture
only. Apple compatibility and every support-promotion decision remain separate.

---

# PHASE 2.5 — EVIDENCE INTEGRITY INFRASTRUCTURE

## WP-0250 Evidence Integrity Infrastructure

**Package status:** `COMPLETE` — owner approved candidate infrastructure in
DEC-0014; support effect remains none.
**Support effect:** None.

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0251 | Evidence-object domain contract | COMPLETE | DEV-0202 | Complete; DEC-0014 |
| DEV-0252 | Stable evidence identifier strategy | COMPLETE | DEV-0251 | Complete; DEC-0014 |
| DEV-0253 | Evidence lifecycle state machine | COMPLETE | DEV-0251 | Complete; DEC-0014 |
| DEV-0254 | Cryptographic hash registry | COMPLETE | DEV-0251, DEV-0252 | Complete; DEC-0014 |
| DEV-0255 | Evidence integrity verification service | COMPLETE | DEV-0254 | Complete; DEC-0014 |
| DEV-0256 | Evidence access and lock policy | COMPLETE | DEV-0253, DEV-0255 | Complete; DEC-0014 |
| DEV-0257 | Chain-of-custody event model | COMPLETE | DEV-0251, DEV-0253 | Complete; DEC-0014 |
| DEV-0258 | Evidence audit-event taxonomy | COMPLETE | DEV-0257 | Complete; DEC-0014 |
| DEV-0259 | Provenance graph foundation | COMPLETE | DEV-0251, DEV-0258 | Complete; DEC-0014 |
| DEV-0260 | Provenance relationship validation | COMPLETE | DEV-0259 | Complete; DEC-0014 |
| DEV-0261 | Evidence mutation detector | COMPLETE | DEV-0254, DEV-0255 | Complete; DEC-0014 |
| DEV-0262 | Integrity policy enforcement service | COMPLETE | DEV-0256, DEV-0260, DEV-0261 | Complete; DEC-0014 |
| DEV-0263 | Common supported-parser contract | COMPLETE | DEV-0259, DEV-0262 | Complete; DEC-0014 |
| DEV-0264 | Parser-contract conformance harness | COMPLETE | DEV-0263 | Complete; DEC-0014 |
| DEV-0265 | End-to-end integrity validation package | COMPLETE | DEV-0251 through DEV-0264 | Complete; DEC-0014 |

DEV-0203 remains the intake encryption-report projection. WP-0250 is the sole
authority for evidence registration, stable evidence UUIDs, hash observations,
lifecycle, locks, custody, audit, provenance, mutation policy, and parser
conformance. Later WP-0200 tasks must adapt to these contracts and must not
create competing implementations.

**Owner-review gate:** Satisfied by DEC-0014 for candidate architectural use
only; all limitations and support prohibitions remain controlling.

---

# PHASE 3 — TENANCY, AUTHORIZATION, AND CASE MODEL

## WP-0300 SaaS Security Foundation

**Package status:** `COMPLETE` — owner approved candidate infrastructure in
DEC-0037. No production policy, authentication, API, live PostgreSQL
validation, evidence processing, or support status is authorized.

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0301 | Tenant model | COMPLETE | DEV-0103 | WP-0300 package review |
| DEV-0302 | User and role model | COMPLETE | DEV-0301 | WP-0300 package review |
| DEV-0303 | Case model | COMPLETE | DEV-0301 | WP-0300 package review |
| DEV-0304 | Artifact support-status model and parser quarantine enforcement | COMPLETE | DEV-0003, DEV-0004 | Complete; DEC-0014 |
| DEV-0305 | Evidence-source tenant and case linkage | COMPLETE | DEV-0203, DEV-0303 | WP-0300 package review |
| DEV-0306 | Audit-actor attribution | COMPLETE | DEV-0302, DEV-0206 | WP-0300 package review |
| DEV-0307 | Cross-tenant isolation tests | COMPLETE | DEV-0310, DEV-0305 | WP-0300 review |
| DEV-0308 | Additive Alembic migration baseline | COMPLETE | DEV-0301 through DEV-0306 | WP-0300 review; offline validated only |
| DEV-0309 | Security package integration tests | COMPLETE | DEV-0301 through DEV-0308; DEV-0310 | Owner approved in DEC-0037; QMS-008 limitations retained |
| DEV-0310 | Authorization Service and Policy Enforcement | COMPLETE | DEV-0301, DEV-0302, DEV-0303 | WP-0300 review; no default grants |

### WP-0300 completion criteria

- every case and evidence source belongs to exactly one tenant;
- explicit authorization at service and API boundaries;
- cross-tenant reads and writes fail closed;
- actor attribution exists for sensitive operations;
- additive and reversible migrations;
- deterministic isolation tests.

**Owner-review gate:** Approve the SaaS security foundation before exposing evidence workflows through the supported API.

Reconciliation: DEV-009's owner-approved DEV-0304 definition controls over the
stale generic authorization-service wording previously in this table. No task
was renumbered or overwritten. DEC-0014 reserves DEV-0310 for the displaced
authorization service and corrects DEV-0307's dependency.

---

# PHASE 4 — SUPPORTED EVIDENCE CORE

## WP-0400 Supported Evidence Data Model

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0401 | Processing-run model | READY | WP-0200, WP-0250, WP-0300 | Package gate |
| DEV-0402 | Source-artifact identity model | NOT_STARTED | DEV-0401 | Package gate |
| DEV-0403 | Stable source-locator model | NOT_STARTED | DEV-0402 | Package gate |
| DEV-0404 | Parser identity and version model | NOT_STARTED | DEV-0401 | Package gate |
| DEV-0405 | Schema-fingerprint model | NOT_STARTED | DEV-0402 | Package gate |
| DEV-0406 | Raw and normalized value model | NOT_STARTED | DEV-0402 | Package gate |
| DEV-0407 | Timestamp provenance model | NOT_STARTED | DEV-0406 | Package gate |
| DEV-0408 | Coverage and omission model | NOT_STARTED | DEV-0401 | Package gate |
| DEV-0409 | Failure and partial-processing model | NOT_STARTED | DEV-0401 | Package gate |
| DEV-0410 | Supported evidence store | NOT_STARTED | DEV-0401 through DEV-0409 | Package gate |
| DEV-0411 | Legacy and experimental store isolation | NOT_STARTED | DEV-0410 | Package gate |
| DEV-0412 | Evidence-core integration tests | NOT_STARTED | DEV-0401 through DEV-0411 | Package gate |

### WP-0400 completion criteria

Every supported record can be traced to:

- tenant;
- case;
- evidence source;
- processing run;
- source artifact;
- stable source locator;
- parser identity and version;
- schema fingerprint;
- raw value;
- normalized value;
- timestamp-conversion record;
- hashes where applicable;
- coverage and limitations.

**Owner-review gate:** Approve the normalized supported-evidence contract before any artifact family is promoted.

---

# PHASE 4.5 — EVIDENCE COVERAGE AND COLLECTION ADVISOR

## WP-0450 Evidence Coverage & Collection Advisor

Identifier reconciliation: the requested WP-0400 and DEV-0401 through DEV-0410
identifiers were already assigned to the controlling Supported Evidence Data
Model. DEC-0027 preserves those assignments and allocates this package as
WP-0450 with corresponding DEV-0451 through DEV-0460 IDs.

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0451 | Source Inventory Engine | BLOCKED | WP-0200, WP-0250, DEV-0402, DEV-0403 | WP-0450 gate |
| DEV-0452 | Artifact Coverage Engine | BLOCKED | DEV-0451, DEV-0304, DEV-0408, DEV-0409, DEV-1101 through DEV-1106 | WP-0450 gate |
| DEV-0453 | Evidence Gap Classification | BLOCKED | DEV-0451, DEV-0452 | WP-0450 gate |
| DEV-0454 | Backup Structure and Coverage Assessment | BLOCKED | DEV-0451, DEV-0453, WP-0200 | WP-0450 gate |
| DEV-0455 | Collection Opportunity Engine | FUTURE | DEV-0453, DEV-0454, WP-1900 where applicable | Post-MVP gate |
| DEV-0456 | Question-Specific Evidence Sufficiency Engine | FUTURE | DEV-0453, WP-1200, WP-1300 | Post-MVP gate |
| DEV-0457 | Acquisition Recommendation Engine | FUTURE | DEV-0455, DEV-0456 | Post-MVP gate |
| DEV-0458 | Attorney Coverage Summary Generator | BLOCKED | DEV-0453, DEV-0454, DEV-1401, DEV-1404 | WP-0450 gate |
| DEV-0459 | Commercial Services Integration | FUTURE | DEV-0457; separate commercial/security approval | Post-MVP gate |
| DEV-0460 | Coverage Report Integration | BLOCKED | DEV-0458, WP-1400 | WP-0450 gate |

The closed candidate coverage vocabulary and permanent forensic rules are
defined in `WP-0450-evidence-coverage-collection-advisor.md`. No coverage
implementation is authorized ahead of its dependencies.

**Owner-review gate:** Approve the coverage package before attorney-facing use.

---

# PHASE 5 — BACKUP METADATA CANDIDATE

## WP-0500 Apple Backup Metadata

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0501 | Metadata artifact discovery via Manifest.db | NOT_STARTED | WP-0200, WP-0400, DEV-0263, DEV-0264 | Artifact gate |
| DEV-0502 | Info.plist controlled reader | NOT_STARTED | DEV-0501 | Artifact gate |
| DEV-0503 | Manifest.plist controlled reader | NOT_STARTED | DEV-0501 | Artifact gate |
| DEV-0504 | Status.plist controlled reader | NOT_STARTED | DEV-0501 | Artifact gate |
| DEV-0505 | Backup metadata normalization | NOT_STARTED | DEV-0502 through DEV-0504 | Artifact gate |
| DEV-0506 | Encryption and version field reconciliation | NOT_STARTED | DEV-0502 through DEV-0504 | Artifact gate |
| DEV-0507 | Metadata coverage and limitation reporting | NOT_STARTED | DEV-0505 | Artifact gate |
| DEV-0508 | Metadata fixture corpus | NOT_STARTED | DEV-0502 through DEV-0506 | Artifact gate |
| DEV-0509 | Metadata validation report | NOT_STARTED | DEV-0501 through DEV-0508 | Artifact gate |

**Owner-review gate:** Decide whether backup metadata is promoted to `SUPPORTED`, remains `CANDIDATE`, or is `REJECTED`.

---

# PHASE 6 — MANIFEST INVENTORY CANDIDATE

## WP-0600 Manifest.db Inventory

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0601 | Manifest.db schema-profile validator | NOT_STARTED | WP-0200, WP-0400, DEV-0263, DEV-0264 | Artifact gate |
| DEV-0602 | Files-table controlled query layer | NOT_STARTED | DEV-0601 | Artifact gate |
| DEV-0603 | FileID normalization | NOT_STARTED | DEV-0602 | Artifact gate |
| DEV-0604 | Domain normalization | NOT_STARTED | DEV-0602 | Artifact gate |
| DEV-0605 | Relative-path normalization | NOT_STARTED | DEV-0602 | Artifact gate |
| DEV-0606 | Flags and file metadata normalization | NOT_STARTED | DEV-0602 | Artifact gate |
| DEV-0607 | Manifest metadata-blob characterization | NOT_STARTED | DEV-0602 | Artifact gate |
| DEV-0608 | Inventory provenance and coverage | NOT_STARTED | DEV-0603 through DEV-0607 | Artifact gate |
| DEV-0609 | Duplicate and orphan detection | NOT_STARTED | DEV-0602 | Artifact gate |
| DEV-0610 | Manifest fixture corpus | NOT_STARTED | DEV-0601 through DEV-0609 | Artifact gate |
| DEV-0611 | Manifest validation report | NOT_STARTED | DEV-0601 through DEV-0610 | Artifact gate |

**Owner-review gate:** Decide whether Manifest.db inventory is promoted to `SUPPORTED`, remains `CANDIDATE`, or is `REJECTED`.

---

# PHASE 7 — CONTACTS CANDIDATE

## WP-0700 Contacts

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0701 | Contacts artifact discovery | NOT_STARTED | WP-0600, DEV-0263, DEV-0264 | Artifact gate |
| DEV-0702 | Contacts schema-profile validator | NOT_STARTED | DEV-0701 | Artifact gate |
| DEV-0703 | Person and organization extraction | NOT_STARTED | DEV-0702 | Artifact gate |
| DEV-0704 | Phone-number extraction and normalization | NOT_STARTED | DEV-0702 | Artifact gate |
| DEV-0705 | Email extraction and normalization | NOT_STARTED | DEV-0702 | Artifact gate |
| DEV-0706 | Address extraction and normalization | NOT_STARTED | DEV-0702 | Artifact gate |
| DEV-0707 | Contact-group relationships | NOT_STARTED | DEV-0702 | Artifact gate |
| DEV-0708 | Contact-image references | NOT_STARTED | DEV-0702 | Artifact gate |
| DEV-0709 | Contacts provenance and coverage | NOT_STARTED | DEV-0703 through DEV-0708 | Artifact gate |
| DEV-0710 | Contacts fixture corpus | NOT_STARTED | DEV-0702 through DEV-0709 | Artifact gate |
| DEV-0711 | Contacts validation report | NOT_STARTED | DEV-0701 through DEV-0710 | Artifact gate |

**Owner-review gate:** Decide whether contacts are promoted to `SUPPORTED`, remain `CANDIDATE`, or are `REJECTED`.

---

# PHASE 8 — CALL HISTORY CANDIDATE

## WP-0800 Call History

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0801 | Call-history artifact discovery | NOT_STARTED | WP-0600, DEV-0263, DEV-0264 | Artifact gate |
| DEV-0802 | Call-history schema-profile validator | NOT_STARTED | DEV-0801 | Artifact gate |
| DEV-0803 | Call record extraction | NOT_STARTED | DEV-0802 | Artifact gate |
| DEV-0804 | Direction and disposition normalization | NOT_STARTED | DEV-0803 | Artifact gate |
| DEV-0805 | Duration normalization | NOT_STARTED | DEV-0803 | Artifact gate |
| DEV-0806 | Service/provider normalization | NOT_STARTED | DEV-0803 | Artifact gate |
| DEV-0807 | FaceTime and call-type characterization | NOT_STARTED | DEV-0803 | Artifact gate |
| DEV-0808 | Call timestamp provenance | NOT_STARTED | DEV-0803 | Artifact gate |
| DEV-0809 | Call coverage and omissions | NOT_STARTED | DEV-0803 through DEV-0808 | Artifact gate |
| DEV-0810 | Call fixture corpus | NOT_STARTED | DEV-0802 through DEV-0809 | Artifact gate |
| DEV-0811 | Call-history validation report | NOT_STARTED | DEV-0801 through DEV-0810 | Artifact gate |

**Owner-review gate:** Decide whether call history is promoted to `SUPPORTED`, remains `CANDIDATE`, or is `REJECTED`.

---

# PHASE 9 — MESSAGES CANDIDATE

## WP-0900 SMS and iMessage

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0901 | sms.db artifact discovery | NOT_STARTED | WP-0600, DEV-0263, DEV-0264 | Artifact gate |
| DEV-0902 | sms.db schema-profile validator | NOT_STARTED | DEV-0901 | Artifact gate |
| DEV-0903 | Message extraction | NOT_STARTED | DEV-0902 | Artifact gate |
| DEV-0904 | Handle extraction | NOT_STARTED | DEV-0902 | Artifact gate |
| DEV-0905 | Chat extraction | NOT_STARTED | DEV-0902 | Artifact gate |
| DEV-0906 | Message-chat-handle relationships | NOT_STARTED | DEV-0903 through DEV-0905 | Artifact gate |
| DEV-0907 | Service and direction normalization | NOT_STARTED | DEV-0903 | Artifact gate |
| DEV-0908 | Delivery and read-state normalization | NOT_STARTED | DEV-0903 | Artifact gate |
| DEV-0909 | Group-chat normalization | NOT_STARTED | DEV-0905, DEV-0906 | Artifact gate |
| DEV-0910 | Reaction and tapback characterization | NOT_STARTED | DEV-0903 | Artifact gate |
| DEV-0911 | Edited-message characterization | NOT_STARTED | DEV-0903 | Artifact gate |
| DEV-0912 | Deleted/recoverable indicator characterization | NOT_STARTED | DEV-0903 | Artifact gate |
| DEV-0913 | Message timestamp provenance | NOT_STARTED | DEV-0903 | Artifact gate |
| DEV-0914 | Message coverage and omissions | NOT_STARTED | DEV-0903 through DEV-0913 | Artifact gate |
| DEV-0915 | Message fixture corpus | NOT_STARTED | DEV-0902 through DEV-0914 | Artifact gate |
| DEV-0916 | Message validation report | NOT_STARTED | DEV-0901 through DEV-0915 | Artifact gate |

**Owner-review gate:** Decide whether SMS/iMessage is promoted to `SUPPORTED`, remains `CANDIDATE`, or is `REJECTED`.

---

# PHASE 10 — MESSAGE ATTACHMENTS CANDIDATE

## WP-1000 Message Attachments

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1001 | Attachment-row extraction | NOT_STARTED | WP-0900, DEV-0263, DEV-0264 | Artifact gate |
| DEV-1002 | Message-attachment relationship extraction | NOT_STARTED | DEV-1001 | Artifact gate |
| DEV-1003 | Backup-file resolution through Manifest.db | NOT_STARTED | DEV-1001, WP-0600 | Artifact gate |
| DEV-1004 | Attachment controlled-copy service | NOT_STARTED | DEV-1003, DEV-0205 | Artifact gate |
| DEV-1005 | Attachment SHA-256 hashing | NOT_STARTED | DEV-1004 | Artifact gate |
| DEV-1006 | Filename and MIME normalization | NOT_STARTED | DEV-1001, DEV-1004 | Artifact gate |
| DEV-1007 | Missing and orphan attachment classification | NOT_STARTED | DEV-1002 through DEV-1004 | Artifact gate |
| DEV-1008 | Attachment provenance and coverage | NOT_STARTED | DEV-1001 through DEV-1007 | Artifact gate |
| DEV-1009 | Safe preview metadata | NOT_STARTED | DEV-1004 | Artifact gate |
| DEV-1010 | Attachment fixture corpus | NOT_STARTED | DEV-1001 through DEV-1009 | Artifact gate |
| DEV-1011 | Attachment validation report | NOT_STARTED | DEV-1001 through DEV-1010 | Artifact gate |

**Owner-review gate:** Decide whether message attachments are promoted to `SUPPORTED`, remain `CANDIDATE`, or are `REJECTED`.

---

# PHASE 11 — PROCESSING ORCHESTRATION

## WP-1100 Supported Processing Pipeline

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1101 | Supported parser registry | NOT_STARTED | WP-0400, DEV-0262, DEV-0263, DEV-0264 | Package gate |
| DEV-1102 | Legacy parser registry isolation | NOT_STARTED | DEV-1101 | Package gate |
| DEV-1103 | Fail-closed parser executor | NOT_STARTED | DEV-1101 | Package gate |
| DEV-1104 | Processing-run state machine | NOT_STARTED | DEV-0401 | Package gate |
| DEV-1105 | Coverage aggregation | NOT_STARTED | DEV-0408 | Package gate |
| DEV-1106 | Failure aggregation | NOT_STARTED | DEV-0409 | Package gate |
| DEV-1107 | Idempotency and rerun controls | NOT_STARTED | DEV-1104 | Package gate |
| DEV-1108 | Cancellation and cleanup | NOT_STARTED | DEV-1104 | Package gate |
| DEV-1109 | Pipeline audit events | NOT_STARTED | DEV-1104, DEV-0206 | Package gate |
| DEV-1110 | Pipeline integration tests | NOT_STARTED | DEV-1101 through DEV-1109 | Package gate |

**Owner-review gate:** Approve the supported processing pipeline before API exposure.

---

# PHASE 12 — SEARCH AND TIMELINE

## WP-1200 Evidence Exploration

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1201 | Supported-record search service | NOT_STARTED | WP-0400, DEV-0260, supported artifact gates | Package gate |
| DEV-1202 | Exact text search | NOT_STARTED | DEV-1201 | Package gate |
| DEV-1203 | Phone-number search | NOT_STARTED | DEV-1201 | Package gate |
| DEV-1204 | Email-address search | NOT_STARTED | DEV-1201 | Package gate |
| DEV-1205 | Attachment-name search | NOT_STARTED | DEV-1201 | Package gate |
| DEV-1206 | Safe regex search | NOT_STARTED | DEV-1201 | Package gate |
| DEV-1207 | Search filters | NOT_STARTED | DEV-1201 | Package gate |
| DEV-1208 | Unified timeline model | NOT_STARTED | supported artifact gates | Package gate |
| DEV-1209 | Time-zone rendering and provenance | NOT_STARTED | DEV-1208 | Package gate |
| DEV-1210 | Timeline filtering and sorting | NOT_STARTED | DEV-1208 | Package gate |
| DEV-1211 | Source-citation resolver | NOT_STARTED | DEV-0403 | Package gate |
| DEV-1212 | Search and timeline tests | NOT_STARTED | DEV-1201 through DEV-1211 | Package gate |

**Owner-review gate:** Approve supported search and timeline semantics.

---

# PHASE 13 — EVIDENCE-GROUNDED AI

## WP-1300 AI Retrieval and Answering

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1301 | Supported-record retrieval interface | NOT_STARTED | WP-1200, DEV-0260 | Package gate |
| DEV-1302 | Evidence chunking and context assembly | NOT_STARTED | DEV-1301 | Package gate |
| DEV-1303 | Citation-required answer contract | NOT_STARTED | DEV-1301 | Package gate |
| DEV-1304 | Unsupported-evidence rejection | NOT_STARTED | DEV-1301 | Package gate |
| DEV-1305 | Insufficient-evidence response contract | NOT_STARTED | DEV-1303 | Package gate |
| DEV-1306 | Prompt-injection resistance for evidence text | NOT_STARTED | DEV-1302 | Package gate |
| DEV-1307 | Tenant-aware retrieval isolation | NOT_STARTED | DEV-1301, WP-0300 | Package gate |
| DEV-1308 | Answer audit record | NOT_STARTED | DEV-1303, DEV-0206 | Package gate |
| DEV-1309 | Citation verification | NOT_STARTED | DEV-1303, DEV-1211 | Package gate |
| DEV-1310 | Deterministic mock-LLM test harness | NOT_STARTED | DEV-1301 | Package gate |
| DEV-1311 | AI evaluation corpus | NOT_STARTED | DEV-1310 | Package gate |
| DEV-1312 | Hallucination and unsupported-claim tests | NOT_STARTED | DEV-1303 through DEV-1311 | Package gate |

### WP-1300 completion criteria

- AI consumes supported records only;
- every factual answer has verifiable citations;
- unsupported evidence is rejected;
- insufficient evidence is stated clearly;
- evidence text cannot alter system instructions;
- tenant isolation is tested;
- answer generation is auditable.

**Owner-review gate:** Approve AI behavior before any customer-facing AI endpoint.

---

# PHASE 14 — ATTORNEY-FACING REPORTS

## WP-1400 Reporting

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1401 | Report data contract | NOT_STARTED | WP-0400, WP-1200, DEV-0260 | Package gate |
| DEV-1402 | Device and backup summary section | NOT_STARTED | supported metadata gate | Package gate |
| DEV-1403 | Evidence-source and chain-of-custody section | NOT_STARTED | WP-0200 | Package gate |
| DEV-1404 | Coverage and limitation section | NOT_STARTED | DEV-0408, DEV-1105 | Package gate |
| DEV-1405 | Contacts section | NOT_STARTED | supported contacts gate | Package gate |
| DEV-1406 | Calls section | NOT_STARTED | supported calls gate | Package gate |
| DEV-1407 | Messages section | NOT_STARTED | supported messages gate | Package gate |
| DEV-1408 | Attachments section | NOT_STARTED | supported attachments gate | Package gate |
| DEV-1409 | Timeline section | NOT_STARTED | WP-1200 | Package gate |
| DEV-1410 | AI findings section with citations | NOT_STARTED | WP-1300 | Package gate |
| DEV-1411 | Methodology section | NOT_STARTED | architecture and processing docs | Package gate |
| DEV-1412 | PDF renderer | NOT_STARTED | DEV-1401 through DEV-1411 | Package gate |
| DEV-1413 | Deterministic report snapshot tests | NOT_STARTED | DEV-1412 | Package gate |
| DEV-1414 | Report validation checklist | NOT_STARTED | DEV-1412 | Package gate |

**Owner-review gate:** Approve report format and legal-review limitations.

---

# PHASE 15 — SUPPORTED API

## WP-1500 API Surface

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1501 | Authentication integration | NOT_STARTED | WP-0300 | Package gate |
| DEV-1502 | Case endpoints | NOT_STARTED | DEV-1501, DEV-0303 | Package gate |
| DEV-1503 | Evidence-source registration endpoints | NOT_STARTED | DEV-1501, WP-0200 | Package gate |
| DEV-1504 | Processing endpoints | NOT_STARTED | DEV-1501, WP-1100 | Package gate |
| DEV-1505 | Processing-status endpoints | NOT_STARTED | DEV-1504 | Package gate |
| DEV-1506 | Search endpoints | NOT_STARTED | DEV-1501, WP-1200 | Package gate |
| DEV-1507 | Timeline endpoints | NOT_STARTED | DEV-1501, WP-1200 | Package gate |
| DEV-1508 | AI query endpoint | NOT_STARTED | DEV-1501, WP-1300 | Package gate |
| DEV-1509 | Report endpoints | NOT_STARTED | DEV-1501, WP-1400 | Package gate |
| DEV-1510 | Rate limiting | NOT_STARTED | DEV-1501 | Package gate |
| DEV-1511 | API audit logging | NOT_STARTED | DEV-1501, DEV-0206 | Package gate |
| DEV-1512 | OpenAPI contract tests | NOT_STARTED | DEV-1502 through DEV-1511 | Package gate |
| DEV-1513 | API security tests | NOT_STARTED | DEV-1501 through DEV-1512 | Package gate |

**Owner-review gate:** Approve the supported API surface before deployment.

---

# PHASE 16 — FRONTEND MVP

## WP-1600 Investigator and Attorney UI

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1601 | Frontend scaffold | NOT_STARTED | WP-1500 | Package gate |
| DEV-1602 | Authentication UI | NOT_STARTED | DEV-1601 | Package gate |
| DEV-1603 | Case dashboard | NOT_STARTED | DEV-1602 | Package gate |
| DEV-1604 | Evidence upload and intake wizard | NOT_STARTED | DEV-1603 | Package gate |
| DEV-1605 | Processing status UI | NOT_STARTED | DEV-1604 | Package gate |
| DEV-1606 | Evidence search UI | NOT_STARTED | DEV-1603 | Package gate |
| DEV-1607 | Timeline UI | NOT_STARTED | DEV-1603 | Package gate |
| DEV-1608 | Evidence-aware chat UI | NOT_STARTED | DEV-1603 | Package gate |
| DEV-1609 | Citation and source-detail UI | NOT_STARTED | DEV-1606 through DEV-1608 | Package gate |
| DEV-1610 | Report-generation UI | NOT_STARTED | DEV-1603 | Package gate |
| DEV-1611 | Coverage and limitations UI | NOT_STARTED | DEV-1603 | Package gate |
| DEV-1612 | Error and recovery UX | NOT_STARTED | DEV-1604 through DEV-1611 | Package gate |
| DEV-1613 | Accessibility and keyboard review | NOT_STARTED | DEV-1601 through DEV-1612 | Package gate |
| DEV-1614 | Frontend test suite | NOT_STARTED | DEV-1601 through DEV-1613 | Package gate |

**Owner-review gate:** Approve the MVP user workflow.

---

# PHASE 17 — PRODUCTION HARDENING

## WP-1700 Production Readiness

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1701 | Production Docker build | NOT_STARTED | WP-1500, WP-1600 | Package gate |
| DEV-1702 | Secrets-management integration | NOT_STARTED | DEV-1701 | Package gate |
| DEV-1703 | Security headers and transport controls | NOT_STARTED | DEV-1701 | Package gate |
| DEV-1704 | Malware-safe upload handling | NOT_STARTED | DEV-1701 | Package gate |
| DEV-1705 | Storage lifecycle and retention controls | NOT_STARTED | DEV-1701 | Package gate |
| DEV-1706 | Backup and restore procedures | NOT_STARTED | DEV-1701 | Package gate |
| DEV-1707 | Monitoring and alerting | NOT_STARTED | DEV-1701 | Package gate |
| DEV-1708 | Metrics without evidence leakage | NOT_STARTED | DEV-1707 | Package gate |
| DEV-1709 | Performance and resource tests | NOT_STARTED | DEV-1701 | Package gate |
| DEV-1710 | Dependency and container scanning | NOT_STARTED | DEV-1701 | Package gate |
| DEV-1711 | Incident-response runbook | NOT_STARTED | DEV-1702 through DEV-1710 | Package gate |
| DEV-1712 | Disaster-recovery exercise | NOT_STARTED | DEV-1706 | Package gate |
| DEV-1713 | Production-readiness review | NOT_STARTED | DEV-1701 through DEV-1712 | Release gate |

**Owner-review gate:** Production release authorization.

---

# PHASE 18 — MVP RELEASE

## WP-1800 Release Candidate

| Task | Title | Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-1801 | End-to-end synthetic acceptance case | NOT_STARTED | WP-1700 | Release gate |
| DEV-1802 | Security regression suite | NOT_STARTED | WP-1700 | Release gate |
| DEV-1803 | Evidence-integrity regression suite | NOT_STARTED | WP-1700 | Release gate |
| DEV-1804 | Attorney workflow usability review | NOT_STARTED | WP-1600 | Release gate |
| DEV-1805 | Known-limitations register | NOT_STARTED | All packages | Release gate |
| DEV-1806 | Support matrix finalization | NOT_STARTED | All artifact gates | Release gate |
| DEV-1807 | Release documentation | NOT_STARTED | DEV-1801 through DEV-1806 | Release gate |
| DEV-1808 | MVP release candidate | NOT_STARTED | DEV-1801 through DEV-1807 | Release gate |

**Owner-review gate:** Explicit MVP production-release decision.

---

# FUTURE — CLOUD EVIDENCE ACQUISITION

## WP-1900 Cloud Evidence Acquisition

**Status:** FUTURE — separate owner, legal, security, compatibility, capacity,
and support approvals required.

Cloud acquisition remains separate from Apple local computer backups and must
distinguish iCloud device backup, iCloud Photos, Messages in iCloud, iCloud
Drive, synchronized Notes, Contacts, Calendar, and other separately
synchronized services. An iCloud device backup must never be represented as a
complete acquisition of an iCloud account.

---

## 4. Codex Automatic Execution Rule

Codex shall:

1. Read this file, `AGENTS.md`, `CODEX_AUTONOMY_CHARTER.md`, the decision log, task ledger, risk register, architecture, and traceability matrix.
2. Select the first `READY` task in plan order.
3. Create task-specific requirements and measurable acceptance criteria.
4. Update traceability before implementation.
5. Implement the smallest complete solution.
6. Use synthetic fixtures only.
7. Run focused and full regression tests.
8. Fix failures before continuing.
9. Update documentation and risks.
10. Create a local commit.
11. Mark the task `VALIDATION_PENDING` when complete.
12. Continue automatically to the next task in the same work package when no owner gate is required.
13. Stop at the work-package gate or any mandatory stop condition.

Codex must never infer that owner silence equals approval.

---

## 5. Mandatory Stop Conditions

Codex must stop when:

- an owner-review gate is reached;
- requirements conflict;
- a new architecture decision is necessary;
- an artifact, parser, input type, report, API, or workflow may be promoted to supported status;
- a destructive or data-rewriting migration is proposed;
- real evidence, credentials, paid services, or external infrastructure are required;
- a security control would be weakened;
- tenant isolation cannot be proven;
- tests cannot be made deterministic;
- authoritative compatibility rules are unavailable and a provisional assumption would affect classification;
- a Git push, merge, force operation, branch deletion, deployment, or production change is required.

---

## 6. Priority Rule

Plan order controls unless a task is blocked.

When the next task is blocked, Codex may select the earliest later task that:

- is explicitly `READY`;
- does not depend on the blocked decision;
- does not create likely rework;
- does not bypass a required architectural or support gate.

Codex must record why it selected an out-of-order task.

---

## 7. MVP Definition of Done

The MVP is not complete until:

- at least one Apple local-backup format has an approved compatibility profile;
- all supported artifact families passed separate validation and owner-promotion gates;
- source evidence remains immutable;
- every supported record has complete provenance;
- cross-tenant isolation is demonstrated;
- AI uses supported records only and requires citations;
- reports disclose coverage and limitations;
- synthetic end-to-end acceptance tests pass;
- security and evidence-integrity regression suites pass;
- the owner explicitly authorizes release.
