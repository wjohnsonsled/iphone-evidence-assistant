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

## DEC-0004 — Approve DEV-0201 Apple backup input adapter

- Date: 2026-07-24
- Status: APPROVED
- Owner: Project owner
- Task: DEV-0201
- Decision source: Explicit owner approval recorded in the controlled
  development task on 2026-07-24
- Governing document: DEV-0201 Apple backup input adapter acceptance criteria

### Decision

The owner approved DEV-0201 as complete. The read-only, root-confined adapter,
its six controlled outcomes, provenance, deterministic audit data, limitations,
synthetic tests, and recorded validation results satisfy the task-specific
acceptance criteria.

### Consequences

- DEV-0201 may be marked `COMPLETE`.
- DEV-0202 is next in the implementation-plan order.
- DEV-0201 ready outcomes remain adapter handoff states only.
- No input type, parser, artifact family, workflow, evidence source, or
  production capability is promoted to supported status.

## DEC-0005 — DEV-0202 requested validation scope

- Date: 2026-07-24
- Status: BLOCKED_PENDING_CLARIFICATION
- Owner: Project owner
- Task: DEV-0202
- Decision source: Owner instruction recorded in the controlled development
  task on 2026-07-24

### Requested scope

The owner requested a complete Apple backup validation subsystem with distinct
outcomes for invalid, non-Apple, unencrypted, encrypted, corrupt, incomplete,
and unsupported-version inputs. The requested minimum checks include required
backup files and layout, plist keys, encryption state, SQLite readability and
required tables, schema/version compatibility, corruption, and missing
components.

### Blocking conflicts

Implementation cannot begin defensibly until both conflicts are resolved:

1. SQLite readability, required-table, and corruption checks require SQLite
   processing. AGENTS.md and ARC-001 require controlled working copies for
   SQLite processing, while the DEV-0202 instruction prohibits creating working
   copies.
2. `APPLE_BACKUP_UNSUPPORTED_VERSION` requires an approved compatibility
   profile identifying accepted backup, Manifest plist, Manifest database,
   iOS, and schema versions/fingerprints. PRD-007 §12 reserves supported iOS
   versions and schema fingerprints for owner approval, and no such profile
   currently exists.

No implementation or implied compatibility policy is authorized while these
conflicts remain.

## DEC-0006 — Limited DEV-0202 controlled-copy and profile authorization

- Date: 2026-07-27
- Status: APPROVED_LIMITED
- Owner: Project owner
- Task: DEV-0202
- Decision source: Explicit owner instruction recorded in the controlled
  development task on 2026-07-27

### Decision

The owner authorized:

1. a generic ephemeral controlled-copy mechanism for `Manifest.db` and present
   `-wal`, `-shm`, and `-journal` companions, solely to demonstrate safe
   structural validation and SQLite integrity checking; and
2. preparation of a proposed Apple local-backup compatibility profile for
   separate owner review.

The copy mechanism must hash source and copied files, verify source stability
across copying, preserve companion names/relationships, use read-only SQLite
access, record cleanup, fail closed, and use synthetic fixtures only.

### Remaining gate

Apple identity, structure, encryption, schema, version, and classification
rules must not be implemented until FOR-007 is approved. Rules without
authoritative Apple documentation must remain provisional and identify their
fixture or implementation-observation basis.

No general working-copy subsystem, input support, parser support, or artifact
support is approved.

## DEC-0007 — DEV-0202 Stage-A approval and Stage-B compatibility decisions

- Date: 2026-07-27
- Status: APPROVED_WITH_IMPLEMENTATION_CLARIFICATION_REQUIRED
- Owner: Project owner
- Task: DEV-0202
- Decision source: Explicit owner instruction supplied in the controlled
  development task on 2026-07-27
- Governing documents: FOR-007 and DEV-0202 acceptance criteria

### Decision

The owner approved DEV-0202 Stage A and commit
`8bea1677eae4a30d5205bbe45ac8652c85acab19`. The owner also approved the
Stage-B outcome vocabulary, identity and completeness rules, plist and
encryption handling, controlled-copy failure treatment, Manifest SQLite
integrity checks, `MANIFEST_FILES_V1`, deterministic schema fingerprint,
version handling, classification precedence, and synthetic-fixture plan.

Stage B is authorized for isolated implementation without production API
exposure. Synthetic characterization is not production compatibility
validation. A separate validation package using documented Apple-produced test
backups and owner approval remains required before any compatibility or support
claim.

### Unresolved implementation conflict

The approved minimum identity threshold requires `Manifest.db` to be identified
as SQLite and says a failure to meet that threshold is
`NOT_AN_APPLE_BACKUP`. The separately approved corruption rule says an invalid
SQLite `Manifest.db` is `APPLE_BACKUP_CORRUPT`. Because
`NOT_AN_APPLE_BACKUP` precedes `APPLE_BACKUP_CORRUPT`, both cannot control the
same present-but-invalid `Manifest.db` fixture. Owner clarification is required
before implementing that user-facing classification.

### Consequences

- DEV-0201 remains `COMPLETE`.
- DEV-0202 returns to `IN_PROGRESS` for Stage B.
- No Apple backup, input type, parser, artifact, workflow, or production
  capability is promoted to supported status.
- Repository decisions and DEV-009 override stale generic backlog wording.

## DEC-0008 — Independent identity and Manifest structural-validity resolution

- Date: 2026-07-27
- Status: APPROVED
- Owner: Project owner
- Task: DEV-0202

The owner resolved DEC-0007 by separating plist-derived Apple-backup candidate
identity from `Manifest.db` structural validity. Candidate identity requires a
validated directory, regular `Manifest.db`, at least one regular recognized
plist, and at least one approved recognized identity field in a safely parsed
plist.

An invalid `Manifest.db` is `APPLE_BACKUP_CORRUPT` only after independent
identity is established. Without independent identity it is
`NOT_AN_APPLE_BACKUP`; safely readable but insufficient identity observations
may be `APPLE_BACKUP_INDETERMINATE`; operational inability to decide is
`APPLE_BACKUP_VALIDATION_FAILED`.

No support status changes.

## DEC-0012 — DEV-0102 reproducible Python dependency strategy

- Date: 2026-07-27
- Status: IMPLEMENTED_PENDING_PACKAGE_REVIEW
- Owner: Development task authority
- Task: DEV-0102

The backend retains abstract direct dependency declarations in `pyproject.toml`
and uses a committed, exact direct-and-transitive `requirements.lock` as the
reproducible development and container installation input. A standard-library
validator fails when the lock contains a range, duplicate, or omits a declared
runtime or development dependency. The container uses the same lock and
installs the application non-editably without dependency re-resolution.

This decision changes dependency resolution only. It adds no evidence behavior,
API, migration, parser, artifact support, or production approval. Automated
vulnerability and secret scanning remain later foundation controls.

## DEC-0010 — DEV-0202 completion approval

- Date: 2026-07-27
- Status: APPROVED
- Owner: Project owner
- Task: DEV-0202

The owner approved DEV-0202 as complete. DEV-0202 establishes only the
validation framework and controlled classification logic validated with
synthetic fixtures.

The candidate compatibility profile is not approved for production use. Apple
local backups, `Manifest.db`, parsers, artifacts, workflows, APIs, and real
customer evidence remain unapproved and unsupported. Any future support
promotion requires a documented validation package using Apple-produced test
backups across multiple intended versions and a separate owner approval.

## DEC-0011 — Insert and execute WP-0250 evidence-integrity infrastructure

- Date: 2026-07-27
- Status: APPROVED_FOR_IMPLEMENTATION
- Owner: Project owner
- Tasks: DEV-0251 through DEV-0265
- Architecture: ARC-001 with additive ARC-002 contract

The owner authorized an additive relational evidence-integrity layer between
intake and future parser execution. It owns stable evidence UUIDs, immutable
SHA-256 observations, lifecycle and integrity states, application-level access
locks, append-only custody and audit services, tenant-scoped provenance,
mutation and policy enforcement, and the common future supported-parser
contract and conformance harness.

DEV-0203 remains the encryption-reporting projection; existing controlled-copy
work is reused rather than duplicated. No graph database, OS write-block claim,
digital-signature/nonrepudiation claim, production API, real evidence, or
support promotion is authorized.

## DEC-0009 — Single encryption signal and secondary-indicator deferral

- Date: 2026-07-27
- Status: APPROVED
- Owner: Project owner
- Task: DEV-0202

The owner removed contradictory-encryption-indicator handling and its fixture
from DEV-0202. For the current candidate profile,
`Manifest.plist.IsEncrypted` is the only approved signal: Boolean true or false
is recorded and controls the corresponding final outcome only when no
higher-precedence outcome applies; missing or non-Boolean is indeterminate; an
operational inability to inspect it is validation failure.

Encryption must not be inferred from filenames, database behavior, versions,
directory names, keybag-like material, entropy, parser behavior, password
prompts, third-party observations, or undocumented plist keys.

Secondary signals are deferred to DEV-0211 and require sourced characterization,
precedence and conflict rules, synthetic fixtures, Apple-produced validation
fixtures, a revised profile, and owner approval before implementation.
No support status changes.

## DEC-0013 — DEV-0304 empty supported-registry and quarantine boundary

- Date: 2026-07-27
- Status: IMPLEMENTED_PENDING_FORENSIC_REVIEW
- Owner: Development task authority
- Task: DEV-0304

DEV-009 controls DEV-0304 as the artifact support-status and parser-quarantine
task where generic BACKLOG wording conflicted. The implementation separates
FOR-004 lifecycle labels from processing-result statuses, creates an explicit
versioned supported registry, and requires exact registry authorization before
supported output admission. The production registry composition is empty.

Candidate, legacy, compatibility, experimental, excluded, unknown, mismatched,
and unregistered parsers fail closed. Supported success output also fails
closed for unissued authorization, incomplete provenance, unreconciled
coverage, or invalid zero-record semantics.

This implementation neither authenticates approval metadata nor activates a
parser. A future nonempty registry requires an authorized, audited registry
snapshot and the separate per-artifact owner promotion gate. No parser,
artifact, input, workflow, API, or support status changed.

## DEC-0014 — Owner package approvals and authorization-task reconciliation

- Date: 2026-07-28
- Status: APPROVED
- Owner: Project owner
- Tasks: DEV-0102, DEV-0203, DEV-0251 through DEV-0265, DEV-0304, DEV-0310

The owner approved DEV-0102 with its documented limitations; DEV-0304 under
the controlling DEV-009 definition with an empty supported registry; WP-0250
and DEV-0251 through DEV-0265 as complete candidate infrastructure for
architectural use only; and DEV-0203 as a reporting-only projection.

DEV-0310, `Authorization Service and Policy Enforcement`, is reserved. DEV-0307
now depends on DEV-0310 and DEV-0305. DEV-0310 remains blocked until its
dependencies and task-specific acceptance record are complete.

These approvals do not authorize production deployment, parser activation,
Apple compatibility-profile approval, decryption, API or persistence exposure,
real evidence processing, artifact support, or support promotion. The DEV-0304
supported registry remains empty.

Every capability promoted to Supported must permanently reference its Owner
Decision ID, Validation Package ID, Acceptance Record IDs, Promotion Date, and
Current Support Status. Missing traceability fails closed; promotion must be
fully traceable through repository documentation.

## DEC-0015 — DEV-0103 fail-closed configuration policy

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0100_REVIEW
- Task: DEV-0103

Backend configuration uses closed environment and log-level vocabularies,
environment-appropriate database drivers, absolute unique evidence roots, and
credential-safe diagnostics. SQLite is test-only. Production rejects the
documented development database password.

This is startup-value validation, not database connectivity, filesystem access,
secret-manager integration, or production-readiness validation. It creates no
route, migration, evidence workflow, parser activation, or support effect.

## DEC-0016 — DEV-0104 structured safe API errors

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0100_REVIEW
- Task: DEV-0104

API application, validation, framework HTTP, and unexpected failures use a
single typed envelope with stable code, category, safe message, retryable flag,
and server-generated request identifier. Validation input and unexpected
exception text are not returned to clients.

Server-log content controls remain DEV-0105 scope. This task adds no route,
evidence behavior, migration, external service, or support effect.

## DEC-0017 — DEV-0105 safe structured operational logging

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0100_REVIEW
- Task: DEV-0105

Supported-path operational logs use JSON, allowlisted metadata, credential
redaction, and no traceback or raw exception serialization. API error events
retain safe request correlation. Free-form compatibility messages reduce to a
generic event unless migrated to the structured boundary.

Operational logs are not append-only audit or custody records. Redaction does
not authorize evidence-content logging. No route, migration, evidence workflow,
external service, or support effect is introduced.

## DEC-0018 — DEV-0106 least-privilege CI regression gate

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0100_REVIEW
- Task: DEV-0106

The repository CI definition uses read-only contents permission, Python
3.12.13, the exact dependency lock, nonisolated application installation,
lock/environment checks, compilation, offline migration validation, full
backend regressions, and legacy characterization tests. It has no deploy,
remote-write, evidence-processing, or production migration step.

The workflow has not run remotely; action references are major tags; and lint,
type, vulnerability, license, secret, container, and live-database gates remain
future hardening. No support status changes.

## DEC-0019 — WP-0100 Backend Foundation completion approval

- Date: 2026-07-28
- Status: APPROVED
- Owner: Project owner
- Work package: WP-0100
- Tasks: DEV-0103, DEV-0104, DEV-0105, DEV-0106

The owner approved WP-0100 and DEV-0103 through DEV-0106 as complete foundation
infrastructure. The owner accepted the limitations recorded in QMS-006,
RSK-0015, RSK-0017, and RSK-0018, including local-only CI validation, unavailable
Docker validation, mutable GitHub Action version tags, omitted lint, type,
vulnerability, license, secret, container-security, and live-PostgreSQL gates,
configuration validation that does not establish production readiness,
operational logs that are not immutable audit records, and the accepted
TestClient warning.

This approval does not authorize production deployment or production-facing
APIs, customer-evidence processing, parser execution, artifact validation,
support promotion, or a change to the trust model. The all-or-nothing support
rule remains controlling.

## DEC-0020 — DEV-0204 adopts the WP-0250 hash authority

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0200_REVIEW
- Task: DEV-0204

DEV-0204 uses the owner-approved WP-0250 `HashRegistry` as the sole SHA-256
implementation for intake. This resolves stale task wording without
renumbering history and prevents a competing evidence hash registry.

The task validates immutable, provenance-complete success and failure
observations with synthetic caller-controlled files. It does not implement
path selection, evidence storage, persistence adapters, package orchestration,
an API, parsing, real-evidence use, or support promotion.

## DEC-0021 — DEV-0205 adopts the existing controlled-copy service

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0200_REVIEW
- Task: DEV-0205

The schema-neutral controlled-copy mechanism first authorized for limited
DEV-0202 validation is adopted as the single general candidate SQLite
working-copy service. No second copy implementation is created. Its
pre/copy/post digest fields verify copying; WP-0250 remains the sole durable
evidence hash-observation authority.

This decision grants no Apple compatibility, parsing, persistence, API, real
evidence, deployment, or support authority.

## DEC-0022 — DEV-0206 adopts the WP-0250 audit authority

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0200_REVIEW
- Task: DEV-0206

DEV-0206 uses the owner-approved WP-0250 closed audit taxonomy and append-only
service for registered intake evidence. It creates no competing intake audit
model. Operational logs and stage-result serialization remain separate.

The reference service is application-level and in-memory. This decision makes
no persistence, storage immutability, legal chain-of-custody, API, production,
real-evidence, or support claim.

## DEC-0023 — DEV-0207 adopts the WP-0250 provenance authority

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0200_REVIEW
- Task: DEV-0207

DEV-0207 uses the owner-approved WP-0250 relational provenance contracts for
the intake evidence-source, source-artifact, and controlled-copy path. It
creates no competing provenance model or graph database.

The reference service is in-memory and caller-provided locators are not yet
bound by integrated intake orchestration. This decision grants no parser,
artifact, Apple compatibility, persistence, API, production, real-evidence, or
support authority.

## DEC-0024 — DEV-0208 bounded controlled-workspace recovery

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0200_REVIEW
- Task: DEV-0208

Recovery may remove only stale, immediate, controlled-prefix directories under
one validated temporary workspace root. Links, root escapes, non-directories,
recent workspaces, unrelated entries, and deletion failures are retained and
reported explicitly.

Recovery is not scheduled and has no persistent ledger or multi-process lock.
It does not authorize evidence-source deletion, arbitrary path deletion, an
API, production use, real-evidence processing, or support promotion.

## DEC-0025 — DEV-0209 caller-supplied intake resource policy

- Date: 2026-07-28
- Status: APPROVED_AND_IMPLEMENTED_PENDING_WP_0200_REVIEW
- Owner: Project owner
- Task: DEV-0209

The owner requires explicit positive deployment configuration for directory
entries/depth, pathname length, plist size, SQLite main/WAL/SHM size, aggregate
controlled-copy size, schema enumeration, SQLite processing work, and any
additional governing limit. Missing, malformed, nonpositive, or out-of-range
configuration fails startup or dependency composition. No implicit production
ceiling exists; documented synthetic values are test/development-only.

Adapter exceedance is `VALIDATION_FAILED`; Apple structural-validation
exceedance is `APPLE_BACKUP_VALIDATION_FAILED`. Both record safe
`resource_limit_exceeded` data and do not independently imply corrupt,
incomplete, unsupported, encrypted, or unencrypted.

This decision grants no production capacity value, compatibility approval,
deployment, real-evidence use, API, parser, artifact, or support authority.
