# ARC-001 — System Architecture Recommendation

## 1. Document control

- Task: DEV-0004
- Date: 2026-07-24
- Status: approved
- Owner approval: DEC-0002, 2026-07-24
- Decision authority: Project owner
- Inputs: AGENTS.md, DEC-0001, DOC-002, DOC-005, PRD-003, PRD-006,
  PRD-007, FOR-004, FOR-006, DEV-000, DEV-001, and repository inspection
- Runtime effect: none
- Data-migration effect: none
- Artifact support effect: none

## 2. Decision requested

Approve an incremental modular-monolith architecture for the initial MVP that:

1. retains the FastAPI, SQLAlchemy, Alembic, repository/service, and
   evidence-engine separation patterns where they are useful;
2. introduces explicit tenant, authorization, evidence-source, immutable-file,
   working-copy, parser-registry, parser-execution, provenance, timestamp,
   coverage, failure, audit, citation, and derived-work-product boundaries;
3. creates a new supported processing path that is structurally unable to call
   the legacy registry or persist quarantined output;
4. keeps legacy compatibility code and data outside supported stores and
   product claims; and
5. evolves the database through additive, reversible migrations without
   rewriting or deleting pre-existing data.

Approval would authorize detailed task design against this architecture. It
would not approve a parser, schema, artifact family, deployment, destructive
migration, or production security claim.

## 3. Architectural drivers

The architecture is ordered by the governing priorities:

1. source evidence must remain unchanged and independently verifiable;
2. every evidentiary assertion must resolve to stable source provenance;
3. unsupported and failed processing must be impossible to mistake for
   successful supported processing;
4. authorization and tenant isolation must be server-side and pervasive;
5. AI and reports must consume only authorized supported records;
6. all transformations must be deterministic, versioned, and auditable; and
7. the implementation must remain testable and incrementally replaceable.

Development speed is subordinate to these controls.

## 4. Current-state assessment

### Reusable with validation

- FastAPI routing and dependency-injection pattern;
- SQLAlchemy repositories and transaction boundaries;
- Alembic migration mechanism;
- evidence-engine/backend separation;
- UUID identifiers and case-scoped relationships;
- configured evidence-root boundary concept;
- structured API errors and generic client-facing failure messages;
- deterministic fingerprint and characterization-test patterns; and
- synchronous orchestration as a local development adapter.

### Must not enter the supported path unchanged

- `EvidenceEngineRunner` calls the legacy `plugins()` registry directly;
- broad marker checks accept extracted directories and incomplete packages;
- source SQLite files are opened directly, although with `mode=ro`;
- WAL/SHM handling is heuristic and rollback-journal handling is absent;
- current normalized records lack an enforced source-locator and timestamp
  provenance contract;
- parser versions and schema profiles are not controlled;
- coverage statuses are mapped into a lossy second vocabulary;
- unsupported parser output can reach persistence, AI, reports, and coverage;
- case IDs organize records but do not authorize access;
- tenant, membership, audit, evidence-source, and parser-run entities are
  absent; and
- current AI/citation behavior cannot prove supported-record or authorization
  boundaries.

All such code remains implemented-but-unvalidated or legacy-quarantined.

## 5. Recommended system shape

Use a modular monolith for the initial MVP, with explicit internal ports that
permit later extraction of background processing without changing forensic
contracts.

### 5.1 Control/API application

Responsibilities:

- authenticate the actor or service;
- authorize tenant and case operations;
- create and manage case and intake records;
- accept only controlled evidence-source references or uploads;
- expose processing status, coverage, search, source inspection, citations,
  AI work product, and reports;
- ensure every query is tenant- and case-scoped; and
- write immutable audit events for material actions.

The API must never invoke a parser by arbitrary name supplied by a client.

### 5.2 Intake and evidence-source module

Responsibilities:

- validate the acquisition format without mutating it;
- classify unencrypted, encrypted, incomplete, malformed/corrupted, and
  unsupported input;
- assign an evidence-source ID before processing;
- enumerate source files and relevant companions;
- compute SHA-256 with explicit failure records;
- capture size, relative path, acquisition role, and immutable source locator;
- record the evidence-root/storage boundary; and
- create a controlled working-set request.

Server-local path intake is acceptable only for controlled local development.
The eventual product intake mechanism must not expose arbitrary server paths.

### 5.3 Controlled working-copy module

Responsibilities:

- create a case- and run-scoped working directory outside the immutable source;
- copy the SQLite main database and any present `-wal`, `-shm`, and
  `-journal` companions as one controlled set;
- hash source and copied material files and record copy verification;
- reject path traversal, symlink escape, file replacement, or incomplete copy;
- open only the controlled copy for parsing;
- use read-only/query-only SQLite settings where compatible;
- retain the working-set manifest and lifecycle status; and
- record cleanup as a separate auditable derived-data action.

No implementation may claim that copying a backup database reconstructs
byte-for-byte on-device state or performs deleted-data recovery.

### 5.4 Supported parser execution module

Responsibilities:

- load only an immutable snapshot of an approved supported-parser registry;
- select parsers by approved artifact ID, acquisition type, iOS/schema profile,
  and registry version;
- fail closed for absent approval, unknown schema, corruption, or
  inaccessible encrypted content;
- run only against a controlled working set;
- create a parser-execution record before parsing;
- emit records through a typed normalized envelope;
- validate completeness before committing supported records;
- commit output atomically or retain partial diagnostic output only in a
  quarantined namespace; and
- emit controlled coverage, omission, warning, and failure records.

Candidate status never enables execution in this module.

### 5.5 Legacy compatibility module

The legacy CLI, registry, adapters, generic parsers, reports, and AI helpers
remain behind a separate composition root and explicit `legacy` namespace.
They must use separate storage or a distinct non-supported namespace and must
not share a persistence method with the supported parser executor.

Imports must flow one way: legacy code may reuse neutral utilities, but
supported code must not import `evidence_engine._legacy`, the legacy
`plugins()` registry, or a legacy adapter. An automated architectural test
should enforce this rule.

### 5.6 Supported evidence repository

Responsibilities:

- accept records only from a successful approved parser execution;
- require tenant, case, evidence source, source file, parser execution,
  artifact ID, schema fingerprint, parser version, raw values, normalized
  values, timestamp provenance, and stable source locator;
- enforce uniqueness using the complete provenance identity rather than a
  heuristic event fingerprint alone;
- preserve original records and immutable revisions of material derived work;
- expose only controlled processing statuses; and
- prohibit records from failed, partial, experimental, or quarantined runs
  from supported queries.

### 5.7 Search, AI, citation, and reporting module

All downstream retrieval must begin from an authorization-scoped supported
record query. The same query boundary must serve search, timelines, AI,
citations, and reports so that no downstream feature can broaden eligibility.

AI execution must record model/provider identifier, model version where
available, prompt-template version, retrieval query, selected record IDs,
citations, parameters, actor, timestamps, and limitations. Model output is
derived work product and cannot update normalized evidence.

A citation must resolve:

`citation -> supported record -> source locator -> parser execution ->
source file -> evidence source -> case and tenant`

The UI may show normalized context, raw values, source metadata, and locator
details subject to authorization and safe rendering. It must not execute or
trust artifact content.

## 6. Trust and storage boundaries

### Boundary A — Submitted source

- immutable after intake;
- content-addressed or otherwise protected against accidental replacement;
- SHA-256 and intake metadata retained;
- never opened writable;
- no parser scratch files stored beside it.

### Boundary B — Controlled working sets

- derived, case/run scoped, non-authoritative;
- verified against source hashes;
- only location from which supported parsers read SQLite;
- access limited to the processing service;
- lifecycle and cleanup audited.

### Boundary C — Supported derived evidence

- typed, provenance-complete, parser-run linked, tenant/case scoped;
- atomic acceptance from successful supported runs only;
- queryable by supported product features.

### Boundary D — Quarantined/diagnostic output

- physically separate store or database schema;
- explicit legacy/experimental/failed designation;
- excluded from supported repositories and retrieval;
- never merged silently with Boundary C.

### Boundary E — Presentation work product

- search sessions, AI executions, citations, and reports;
- immutable references to eligible supported record versions;
- cannot overwrite Boundaries A or C.

## 7. Recommended domain and persistence model

The following logical entities are recommended. Exact columns and constraints
must be specified in their owning tasks and migrations.

| Entity | Required purpose and relationships |
|---|---|
| `Tenant` | Root authorization and data-isolation boundary |
| `Principal` | Authenticated user or service identity |
| `TenantMembership` | Role and tenant relationship; no implicit global access |
| `Case` | Tenant-owned matter; no longer the root security boundary by itself |
| `CaseMembership` | Optional case-specific authorization within a tenant |
| `EvidenceSource` | One submitted acquisition, classification, intake status, immutable location, and aggregate metadata |
| `SourceFile` | Evidence-source-relative path, role, size, SHA-256, hash status, and stable identity |
| `WorkingSet` | Derived controlled copy, manifest, verification state, location, and lifecycle |
| `ParserDefinition` | Approved artifact/profile metadata and immutable parser version |
| `RegistrySnapshot` | Immutable set of approved parser definitions and configuration |
| `ParserExecution` | Case/source/working-set/parser run, schema fingerprint, timing, counts, status, and acceptance reference |
| `SupportedRecord` | Typed normalized envelope linked to exactly one successful parser execution and source locator |
| `SourceLocator` | Source file plus table/row/key/path semantics sufficient for stable inspection |
| `TimestampValue` | Raw value/format/field, conversion method, timezone basis, precision, normalized UTC, and limitations |
| `ArtifactCoverage` | Controlled per-artifact result status, scope examined, counts, omissions, and reason |
| `ProcessingIssue` | Structured warning, omission, error, stage, severity, and safe diagnostic detail |
| `AuditEvent` | Tenant/case/actor/action/target/correlation/time/result without secrets |
| `AiExecution` | Authorized retrieval and model execution metadata as derived work product |
| `Citation` | Stable link from work product to a supported record and resolvable provenance chain |
| `Report` | Versioned derived work product with frozen citations, scope, coverage, and limitations |

Tenant ID should be present on tenant-owned tables even when derivable through
foreign keys, allowing database constraints, indexed scoping, and optional
row-level-security defense in depth. Application authorization remains
mandatory; database row-level security must not be the sole control.

## 8. Normalized record contract

Before a record can enter the supported repository, it must contain:

- stable record ID and artifact ID;
- tenant, case, evidence-source, source-file, and parser-execution IDs;
- parser name/version, registry version, schema fingerprint, and acceptance
  reference;
- stable source locator and source SHA-256;
- original/raw values in an approved safe representation;
- normalized values in the artifact-specific schema;
- timestamp raw value, source field, raw format, conversion method, timezone
  basis, precision, normalized UTC where possible, and limitations;
- relationships whose join basis and provenance are explicit;
- controlled status and any warning/omission references; and
- deterministic record identity based on declared provenance fields.

If a required field cannot be established, the parser must not silently
persist the record as supported. The execution must follow its approved
failure/partial-output contract.

## 9. Status architecture

Use the FOR-004 processing statuses without lossy remapping:

- `SUPPORTED_COMPLETE`;
- `SUPPORTED_NO_RECORDS`;
- `UNSUPPORTED`;
- `INACCESSIBLE`;
- `CORRUPTED`;
- `FAILED`; and
- `EXCLUDED`.

Lifecycle status (`CANDIDATE`, `IN_DEVELOPMENT`, `VALIDATION_PENDING`,
`DEPRECATED`) is separate from per-run processing status. A parser definition
cannot emit a supported result until its exact profile and version have owner
or delegated forensic-review approval.

Case/job/intake/working-set states require their own controlled enums and must
not be reused as artifact coverage statuses.

## 10. Security architecture

Before shared or SaaS use:

- authenticate every non-health request;
- resolve tenant and case authorization server-side;
- scope every repository method by an authorization context, not a client
  supplied case ID alone;
- prevent object references from crossing tenant boundaries;
- use least-privilege identities for API, worker, database, and storage;
- encrypt network traffic and managed storage using approved controls;
- keep evidence paths and sensitive raw content out of ordinary logs;
- validate filenames, plists, SQLite values, archives, and display content as
  hostile input;
- apply file-size, count, path-depth, and processing-resource limits;
- record immutable audit events for intake, access, processing, export,
  retention, and deletion actions;
- define retention and deletion policy before production data is accepted; and
- add cross-tenant, cross-case, path/symlink, content-injection, and audit tests.

Authentication provider, deployment platform, retention periods, deletion
workflow, key management, and production tenancy model remain owner-controlled
decisions. This recommendation does not select a vendor.

## 11. Processing sequence

1. Authenticate and authorize the actor for the tenant and case.
2. Register an intake request and evidence source.
3. Validate path/upload boundaries and classify the Apple backup.
4. Inventory and hash submitted source files without mutation.
5. If encrypted, record `INACCESSIBLE` under the approved intake contract and
   stop content processing.
6. Create and verify a controlled working set.
7. Fingerprint candidate schemas from the working set.
8. Resolve an immutable approved registry snapshot.
9. Create parser-execution records for only matching approved profiles.
10. Parse into a staging transaction and validate completeness/provenance.
11. Atomically accept supported records and coverage, or fail closed and keep
    any diagnostic output quarantined.
12. Make supported records available through the authorization-scoped
    repository.
13. Resolve citations and generate derived work product only from that
    repository.
14. Audit completion, failures, omissions, access, and exports.

## 12. Incremental migration strategy

No destructive migration is authorized.

### Stage 1 — Contracts and security foundation

- define controlled enums and typed domain interfaces;
- add tenant/principal/membership and audit models;
- add evidence-source, source-file, and intake models;
- require authorization context in new repository interfaces;
- keep current tables untouched and unavailable to the new supported API.

### Stage 2 — Controlled processing foundation

- add working-set, registry-snapshot, parser-definition, parser-execution, and
  processing-issue models;
- implement immutable intake and controlled copy;
- create the supported executor with no dependency on legacy registry code;
- add architectural import and persistence-boundary tests.

### Stage 3 — Supported record foundation

- add the provenance-complete supported-record, source-locator, and timestamp
  contracts;
- add controlled coverage records;
- validate one backup metadata/inventory profile end to end;
- retain legacy `evidence_events` and `artifact_coverage` as quarantined
  pre-baseline data unless a separate migration and validation task proves a
  safe mapping.

### Stage 4 — Review and derived work product

- implement authorization-scoped search and source inspection;
- add citation resolution;
- add AI and reports only after eligible-record gating is tested.

Existing tables must not be relabeled as supported. Any data backfill,
transformation, deletion, or constraint that could reject/rewrite existing
rows requires its own migration plan, backup/rollback validation, and owner
approval.

## 13. Rejected alternatives

### Continue the existing runner and filter its results afterward

Rejected because unsupported parsers execute before filtering, partial
failures can contaminate shared state, and provenance/completeness cannot be
reconstructed reliably after the fact.

### Rewrite the entire repository before continuing

Rejected because reusable boundaries exist and a replacement would increase
change risk without improving forensic assurance by itself.

### Treat read-only direct SQLite access as sufficient

Rejected because it does not establish source/derived separation or controlled
main/WAL/SHM/journal handling.

### Use case ID alone as an authorization boundary

Rejected because knowledge of an identifier is not authorization and does not
provide tenant isolation.

### Store supported and experimental records together with a status flag

Rejected for the initial architecture because a missed filter could expose
unsupported evidence. Separate repositories or database schemas provide a
stronger default-deny boundary.

### Begin with independent microservices

Rejected for the MVP because service distribution adds operational and
consistency complexity. Explicit module ports preserve a later extraction path.

## 14. Unresolved owner-controlled decisions

Architecture approval does not resolve:

1. identity provider and authentication method;
2. single-tenant deployment versus shared multi-tenant SaaS sequence;
3. database/storage hosting and encryption/key-management provider;
4. retention periods, legal hold, and deletion workflow;
5. whether database row-level security is mandatory in the first deployment;
6. background job technology and deployment topology;
7. whether the legacy CLI is internal-only or distributable;
8. supported iOS versions and schema fingerprints;
9. artifact-specific normalized schemas; or
10. any parser or artifact promotion.

These decisions must be assigned explicit tasks before dependent implementation.

## 15. DEV-0004 acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Current architecture is assessed for reuse and quarantine | PASS | Section 4 |
| Immutable source and controlled working-copy boundaries are defined | PASS | Sections 5.2–5.3 and 6 |
| Supported and legacy parser paths are structurally separated | PASS | Sections 5.4–5.5 |
| Provenance, timestamps, statuses, failures, and coverage have explicit contracts | PASS | Sections 5.6, 7–9 |
| Tenant, authentication, authorization, and audit boundaries are defined | PASS | Sections 7 and 10 |
| Search, AI, citations, and reports are restricted to authorized supported records | PASS | Section 5.7 |
| Migration is incremental, additive, and non-destructive | PASS | Section 12 |
| Alternatives and remaining owner decisions are explicit | PASS | Sections 13–14 |
| No artifact, parser, schema, workflow, or conclusion is promoted | PASS | Sections 1–2 |

## 16. Recommendation

Approve the architecture in Section 2 as the basis for downstream acceptance
criteria and implementation planning. Keep DEV-0004 in `VALIDATION_PENDING`
until the owner records an approval or requested revisions in DOC-003.

The project owner approved this recommendation on 2026-07-24. DEC-0002 records
the decision. This approval establishes an architectural basis only and does
not promote any parser, artifact, input type, schema, workflow, or conclusion
to supported status.

## Candidate supported-store implementation

DEC-0047 and migration `0004_candidate_supported_store` implement candidate
relational infrastructure. Exact registry, scope, integrity, provenance,
coverage, and promotion references gate admission. The supported registry and
normalized-record store remain empty; schema existence is not support.
## DEV-1107 persistence addendum

Migration 0005 is the additive linear candidate persistence contract for
logical processing requests, atomic exact claims, immutable execution attempts,
and prior-run relationships. Request identity and run identity are distinct.
Production repository and transaction-isolation behavior remain unapproved.
