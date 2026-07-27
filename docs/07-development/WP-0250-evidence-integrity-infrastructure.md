# WP-0250 — Evidence Integrity Infrastructure

**Status:** `READY` after DEV-0202 is approved `COMPLETE`  
**Execution branch:** `mvp-development`  
**Execution model:** Autonomous within this work package  
**Owner-review gate:** Required after DEV-0265  
**Support effect:** None. This package does not promote any input, parser, artifact, workflow, report, or API to supported status.

---

## 1. Objective

Create the common evidence-integrity foundation used by every future supported evidence source, parser, normalized record, timeline event, AI answer, citation, export, and report.

This package must be completed before supported artifact parsers are permitted to persist normalized evidence records.

The design must:

- preserve source-evidence immutability;
- assign stable internal evidence identifiers;
- record cryptographic integrity observations;
- provide deterministic lifecycle controls;
- provide immutable audit and chain-of-custody events;
- establish provenance relationships;
- detect mutation and broken provenance;
- prevent unsupported or legacy records from entering supported workflows;
- remain modular, testable, and suitable for a multi-tenant SaaS.

---

## 2. Scope

### Included

- immutable evidence-object domain model;
- stable identifier strategy;
- evidence lifecycle state machine;
- cryptographic hash registry;
- evidence integrity verification service;
- controlled lock and access policy;
- chain-of-custody event model;
- evidence audit-event taxonomy;
- provenance graph foundation;
- mutation detection;
- evidence integrity regression tests;
- common supported-parser contract;
- parser-contract conformance tests;
- architecture and forensic-method documentation.

### Excluded

- production upload endpoints;
- real Apple backup processing;
- message, contact, call, or attachment parsing;
- user-facing reports;
- AI retrieval or answering;
- production deployment;
- digital signatures or public-key infrastructure;
- legal conclusions;
- support promotion.

---

## 3. Dependencies

| Dependency | Requirement |
|---|---|
| DEV-0201 | Apple backup input adapter approved complete |
| DEV-0202 | Apple backup validation framework approved complete |
| ARC-001 | Approved modular-monolith architecture |
| Existing governance | `AGENTS.md`, `BACKLOG.md`, `CODEX_AUTONOMY_CHARTER.md`, task ledger, decision log, risk register, traceability matrix |

Codex must not begin WP-0250 until DEV-0202 is recorded as `COMPLETE`.

---

## 4. Included Tasks

| Task | Title | Initial Status | Dependencies | Owner Gate |
|---|---|---:|---|---|
| DEV-0251 | Evidence-object domain contract | NOT_STARTED | DEV-0202 | Package gate |
| DEV-0252 | Stable evidence identifier strategy | NOT_STARTED | DEV-0251 | Package gate |
| DEV-0253 | Evidence lifecycle state machine | NOT_STARTED | DEV-0251 | Package gate |
| DEV-0254 | Cryptographic hash registry | NOT_STARTED | DEV-0251, DEV-0252 | Package gate |
| DEV-0255 | Evidence integrity verification service | NOT_STARTED | DEV-0254 | Package gate |
| DEV-0256 | Evidence access and lock policy | NOT_STARTED | DEV-0253, DEV-0255 | Package gate |
| DEV-0257 | Chain-of-custody event model | NOT_STARTED | DEV-0251, DEV-0253 | Package gate |
| DEV-0258 | Evidence audit-event taxonomy | NOT_STARTED | DEV-0257 | Package gate |
| DEV-0259 | Provenance graph foundation | NOT_STARTED | DEV-0251, DEV-0258 | Package gate |
| DEV-0260 | Provenance relationship validation | NOT_STARTED | DEV-0259 | Package gate |
| DEV-0261 | Evidence mutation detector | NOT_STARTED | DEV-0254, DEV-0255 | Package gate |
| DEV-0262 | Integrity policy enforcement service | NOT_STARTED | DEV-0256, DEV-0260, DEV-0261 | Package gate |
| DEV-0263 | Common supported-parser contract | NOT_STARTED | DEV-0259, DEV-0262 | Package gate |
| DEV-0264 | Parser-contract conformance harness | NOT_STARTED | DEV-0263 | Package gate |
| DEV-0265 | End-to-end integrity validation package | NOT_STARTED | DEV-0251 through DEV-0264 | Package gate |

---

## 5. Evidence-Object Contract

The evidence object represents a registered evidentiary source or derived controlled object. It must not contain mutable user commentary or unsupported conclusions.

Required fields or equivalent typed relationships:

- `tenant_id`
- `case_id`
- `evidence_source_id`
- `evidence_uuid`
- `parent_evidence_uuid`, when derived
- `evidence_kind`
- `source_type`
- `source_locator`
- `logical_identifier`
- `acquisition_or_intake_method`
- `registered_at`
- `registered_by_actor_id`
- `processing_run_id`, when applicable
- `integrity_state`
- `lifecycle_state`
- `lock_state`
- `current_hash_set_id`
- `provenance_node_id`
- `created_at`
- `last_verified_at`
- `version`

### Prohibited content

The evidence object must not directly store:

- mutable examiner notes;
- AI conclusions;
- report prose;
- unsupported parser output;
- passwords or decryption secrets;
- raw credentials;
- evidence file contents;
- customer-controlled labels that could alter evidence identity.

---

## 6. Stable Identifier Strategy

### Evidence UUID

Use UUIDv7 when the repository's language and dependency policy provide a stable, well-tested implementation. Otherwise use UUIDv4.

The selected strategy must:

- generate identifiers application-side;
- be independent of filenames and paths;
- never be derived solely from evidence content;
- remain stable after registration;
- be unique across tenants;
- be suitable for audit and provenance references.

### Content identity

Content identity must remain separate from object identity.

Content identity is represented by one or more cryptographic hashes. Two evidence objects may have identical content hashes while retaining distinct evidence UUIDs and chain-of-custody histories.

---

## 7. Hash Registry

The initial required algorithm is:

- SHA-256

The design must permit future algorithm additions without rewriting historical records.

Each hash observation must include:

- evidence UUID;
- algorithm;
- digest;
- byte length;
- observation purpose;
- observed at;
- actor or service identity;
- tool or component version;
- source or controlled-copy role;
- success or failure;
- failure code;
- related audit event;
- superseded-by relationship, if any.

Hash values are immutable observations. They must not be overwritten.

---

## 8. Evidence Lifecycle State Machine

Initial lifecycle states:

- `REGISTERED`
- `VALIDATING`
- `VALIDATED`
- `HASH_VERIFIED`
- `PROCESSING`
- `DERIVED_RECORDS_CREATED`
- `REPORTABLE`
- `ARCHIVED`
- `FAILED`
- `QUARANTINED`
- `REJECTED`

### Rules

- Transitions must be explicitly enumerated.
- Invalid transitions fail closed.
- Every transition produces an audit event.
- A failed transition must not partially change state.
- `REJECTED` and `ARCHIVED` are terminal unless a separately approved policy allows reopening.
- `QUARANTINED` cannot enter supported processing until a documented release event occurs.
- Lifecycle state does not itself establish forensic support.

Codex must prepare a transition table before implementation.

---

## 9. Integrity States

Initial integrity states:

- `UNKNOWN`
- `PENDING_VERIFICATION`
- `VERIFIED`
- `MISMATCH`
- `SOURCE_UNSTABLE`
- `VERIFICATION_FAILED`
- `NOT_APPLICABLE`

A record may enter supported processing only when the applicable integrity policy resolves to `VERIFIED`.

---

## 10. Evidence Access and Lock Policy

Supported access intents:

- inspect metadata;
- compute a hash;
- create an approved controlled copy;
- inspect an approved controlled copy;
- verify integrity;
- parse an approved controlled copy;
- archive through an approved lifecycle operation.

Prohibited source operations:

- modify;
- overwrite;
- rename;
- truncate;
- repair;
- recover in place;
- checkpoint source SQLite;
- run `VACUUM`;
- alter schema;
- write temporary files inside the evidence root;
- delete through the application;
- follow an unapproved symlink or reparse point.

Locks are application coordination controls, not claims that the operating system or storage medium is forensically write-blocked.

---

## 11. Chain-of-Custody Event Model

Each chain-of-custody event must include:

- event UUID;
- tenant ID;
- case ID;
- evidence UUID;
- actor identity;
- actor type;
- action type;
- event timestamp;
- event time-zone representation;
- component and version;
- host or execution-environment identifier;
- purpose;
- result;
- failure code and non-sensitive failure detail;
- before-hash reference, when applicable;
- after-hash reference, when applicable;
- prior-event reference;
- related audit-event reference;
- created-at timestamp;
- immutable sequence or ordering information.

A digital-signature field may be reserved for future use, but no cryptographic signature claim may be made in the MVP.

---

## 12. Audit Event Taxonomy

Minimum event families:

- `EVIDENCE_REGISTERED`
- `EVIDENCE_VALIDATION_STARTED`
- `EVIDENCE_VALIDATION_COMPLETED`
- `EVIDENCE_VALIDATION_FAILED`
- `HASH_COMPUTED`
- `HASH_VERIFIED`
- `HASH_MISMATCH`
- `CONTROLLED_COPY_CREATED`
- `CONTROLLED_COPY_VERIFIED`
- `CONTROLLED_COPY_RELEASED`
- `CONTROLLED_COPY_CLEANUP_FAILED`
- `EVIDENCE_LOCK_ACQUIRED`
- `EVIDENCE_LOCK_RELEASED`
- `EVIDENCE_LOCK_DENIED`
- `LIFECYCLE_TRANSITION`
- `LIFECYCLE_TRANSITION_DENIED`
- `PARSER_EXECUTION_STARTED`
- `PARSER_EXECUTION_COMPLETED`
- `PARSER_EXECUTION_FAILED`
- `NORMALIZED_RECORD_CREATED`
- `PROVENANCE_LINK_CREATED`
- `PROVENANCE_VALIDATION_FAILED`
- `INTEGRITY_POLICY_BLOCKED`
- `EXPORT_CREATED`
- `REPORT_CREATED`
- `AI_RETRIEVAL_PERFORMED`
- `ARCHIVE_COMPLETED`
- `SYSTEM_FAILURE`

Audit records must be append-only through application services.

---

## 13. Provenance Graph Foundation

Every future supported normalized record must have a complete path to its source.

Minimum provenance node types:

- tenant;
- case;
- evidence source;
- source artifact;
- controlled copy;
- processing run;
- parser execution;
- normalized record;
- timeline event;
- report citation;
- AI citation;
- export.

Minimum relationship types:

- `BELONGS_TO`
- `DERIVED_FROM`
- `COPIED_FROM`
- `HASHED_AS`
- `PROCESSED_BY`
- `CREATED_BY`
- `NORMALIZED_FROM`
- `CITED_BY`
- `INCLUDED_IN`
- `SUPERSEDES`

Requirements:

- no cycles where the relationship semantics require acyclic derivation;
- no cross-tenant edges;
- no dangling required nodes;
- stable source locators;
- parser identity and version on parser-derived edges;
- validation service capable of producing a deterministic pass/fail report.

A relational implementation is acceptable. A graph database is not required for the MVP.

---

## 14. Evidence Mutation Detection

The mutation detector must compare approved hash observations at defined checkpoints.

At minimum:

- registration hash;
- pre-processing verification hash;
- controlled-copy source hash;
- controlled-copy destination hash;
- post-processing source verification hash, when the source remains available.

A mismatch must:

- produce an immutable audit event;
- set an appropriate integrity state;
- block supported processing;
- preserve prior observations;
- avoid declaring the cause of the mismatch unless supported by evidence.

---

## 15. Common Supported-Parser Contract

Every parser eligible for future support must conform to the approved interface defined in `ARC-002-evidence-integrity-and-parser-contract.md`.

Required logical operations:

- declare parser identity and version;
- declare candidate artifact family;
- declare approved schema profiles;
- validate inputs;
- estimate or report coverage;
- parse from approved controlled inputs only;
- emit raw-to-normalized provenance;
- emit deterministic failures;
- emit limitations;
- perform self-test or fixture validation;
- never write to source evidence;
- never silently skip a failure that affects completeness.

Implementation may use a protocol, abstract base class, or equivalent typed interface appropriate to the repository.

---

## 16. Required Tests

Deterministic synthetic tests must cover at least:

### Identifier and model tests

- evidence UUID uniqueness;
- UUID stability after persistence;
- identical-content objects retaining distinct UUIDs;
- required field validation;
- cross-tenant identity isolation.

### Hash tests

- known SHA-256 fixture;
- empty file;
- large synthetic file streaming;
- hash mismatch;
- source mutation during hashing;
- repeated matching observations;
- historical hash observations not overwritten.

### Lifecycle tests

- every permitted transition;
- every prohibited transition;
- atomic transition failure;
- terminal-state enforcement;
- quarantine enforcement;
- audit event created for each transition.

### Lock and access tests

- permitted read intent;
- prohibited write intent;
- duplicate lock request;
- concurrent lock conflict;
- release behavior;
- stale-lock policy;
- failure does not grant access.

### Chain-of-custody tests

- deterministic event ordering;
- prior-event linkage;
- hash-reference linkage;
- actor attribution;
- failure-event recording;
- immutable history behavior.

### Provenance tests

- complete derivation path;
- missing source node;
- dangling edge;
- prohibited cross-tenant edge;
- invalid cycle;
- parser-version linkage;
- citation path validation.

### Mutation and policy tests

- modified source blocked;
- unstable source blocked;
- missing required hash blocked;
- verified source permitted;
- broken provenance blocked;
- unsupported parser blocked;
- legacy output blocked.

### Parser-contract tests

- conforming synthetic parser passes;
- parser that writes source is rejected;
- parser lacking provenance is rejected;
- parser silently omitting records is rejected;
- parser without version is rejected;
- parser using unsupported schema profile is rejected;
- parser with deterministic failure reporting passes.

---

## 17. Acceptance Criteria

Codex must create detailed AC identifiers, but the package-level acceptance criteria are:

1. Every registered evidence object receives a stable global identifier.
2. Content hashes are immutable observations and are not used as object IDs.
3. Source-evidence write operations are unavailable through approved services.
4. Lifecycle transitions are explicit, deterministic, atomic, and audited.
5. Hash mismatch or source instability blocks supported processing.
6. Chain-of-custody records are append-only through application services.
7. Provenance can be validated from a normalized record to the source artifact.
8. Cross-tenant provenance and evidence access fail closed.
9. Legacy and unsupported outputs cannot satisfy the supported-parser contract.
10. A conforming synthetic parser can complete the contract without bypassing integrity services.
11. All focused, backend, characterization, compilation, migration, and diff checks pass.
12. No production endpoint, real evidence access, or support promotion occurs.

---

## 18. Required Documentation

Update or create:

- architecture decision or addendum;
- requirements traceability entries;
- decision-log entries;
- risk-register entries;
- task-ledger entries;
- lifecycle transition table;
- audit-event taxonomy;
- provenance relationship specification;
- parser-contract specification;
- integrity validation report;
- test summary;
- known limitations.

---

## 19. Mandatory Stop Conditions

In addition to the global autonomy charter, stop if:

- evidence UUID strategy requires an unapproved external dependency;
- a destructive migration is proposed;
- event immutability cannot be enforced through the approved data model;
- tenant isolation conflicts with the existing architecture;
- a graph database is proposed;
- digital signatures or evidentiary sealing are proposed;
- a parser could be considered supported;
- an API endpoint is required;
- real evidence is required;
- chain-of-custody terminology would overstate what the application can prove.

---

## 20. Owner-Review Deliverables

At the end of DEV-0265, provide:

- completed task and AC matrix;
- model and migration summary;
- lifecycle transition table;
- hash and integrity policy;
- chain-of-custody event specification;
- audit taxonomy;
- provenance model;
- parser contract;
- conformance-test results;
- full test results;
- risks and limitations;
- local commit hashes;
- clean working-tree confirmation;
- explicit statement that no capability was promoted to supported status.
