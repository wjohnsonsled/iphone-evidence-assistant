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

## DEC-0026 — DEV-0210 test-only intake integration composition

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0200_REVIEW
- Task: DEV-0210

DEV-0210 composes the approved candidate intake and WP-0250 reference contracts
only inside deterministic synthetic tests. No production workflow or API
composition root is created. The supported registry remains empty.

Integration success is not Apple compatibility approval, evidentiary
completeness, parser/artifact support, real-evidence authority, deployment
approval, or support promotion.

## DEC-0027 — WP-0200 approval and evidence-coverage governance

- Date: 2026-07-28
- Status: APPROVED
- Owner: Project owner
- Work package: WP-0200
- Validation package: QMS-007
- Tasks: DEV-0201 through DEV-0210
- Current support status: CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED

The owner approved WP-0200 and DEV-0210 as complete candidate intake
architecture with the acceptance records, reported test results, and QMS-007
limitations. DEV-0209 remains complete. Resource-denial classifications and
the empty supported registry remain mandatory.

This approval does not establish production ceilings/capacity/readiness,
deployment, real-evidence use, Apple version/schema compatibility, an approved
compatibility profile, API/upload exposure, decryption, parsing, artifact
interpretation/support, cloud support, device completeness, or support
promotion. The TestClient warning remains development debt only.

The requested coverage IDs conflicted with controlling WP-0400 and DEV-0401
through DEV-0410. Preserving history, the Evidence Coverage & Collection
Advisor is allocated as WP-0450 with DEV-0451 through DEV-0460. Its MVP tasks
are blocked by evidence-core, processing, and reporting prerequisites;
DEV-0455, DEV-0456, DEV-0457, and DEV-0459 are future. Cloud acquisition is
separately reserved as future WP-1900.

## DEC-0028 — DEV-0301 neutral tenant identity foundation

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0300_REVIEW
- Task: DEV-0301

DEV-0301 defines an immutable UUIDv4 tenant isolation key, canonical slug,
separate display name, creation provenance, positive version, and additive
`security_tenants` ORM contract. DEV-0308 retains migration ownership.

The tenant is a neutral internal isolation boundary. This decision does not
select a billing/legal organization model, authentication provider, production
tenancy model, membership/role policy, authorization behavior, API, evidence
workflow, deployment, or support status.

## DEC-0029 — DEV-0302 neutral principal and membership foundation

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0300_REVIEW
- Task: DEV-0302

Principals use stable UUIDv4 identities and closed USER/SERVICE kinds.
Tenant memberships always bind a tenant, principal, and canonical opaque role
key. No role key has implicit permissions or global access. DEV-0308 retains
migration ownership and DEV-0310 retains authorization-policy ownership.

No provider selection, credential storage, authentication, permission
vocabulary, API, evidence access, deployment, or support status is introduced.

## DEC-0030 — DEV-0303 tenant-scoped supported case identity

- Date: 2026-07-29
- Status: IMPLEMENTED_PENDING_WP_0300_REVIEW
- Task: DEV-0303

DEV-0303 defines an immutable UUIDv4 case identity bound to exactly one tenant,
with separate name and creation provenance. The additive `security_cases` ORM
contract remains separate from the quarantined legacy `cases` table. DEV-0308
retains migration ownership.

No lifecycle, membership, repository, authorization, route, evidence workflow,
deployment, or support status is introduced.

## DEC-0031 — DEV-0305 tenant/case evidence-source linkage

- Date: 2026-07-29
- Status: IMPLEMENTED_PENDING_WP_0300_REVIEW
- Task: DEV-0305

Evidence-source identity derives tenant and case from a supported-boundary case.
The ORM contract uses a composite case/tenant foreign key so a source cannot
reference a case owned by another tenant. DEV-0308 retains migration ownership.

This adds no filesystem access, hashing, validation, parser, API,
authorization, evidence processing, deployment, or support status.

## DEC-0032 — DEV-0306 tenant-safe audit actor attribution

- Date: 2026-07-29
- Status: IMPLEMENTED_PENDING_WP_0300_REVIEW
- Task: DEV-0306

Audit actor context derives from a matching principal and tenant membership.
The attributed principal ID is passed to the existing WP-0250 audit service;
cross-tenant attribution fails before append. No second audit store or taxonomy
is created.

This grants no authentication, permission, authorization, API, evidence
processing, deployment, or support status. Authorization-denial audit
orchestration remains DEV-0310 scope.

## DEC-0033 — DEV-0308 additive security migration baseline

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0300_REVIEW
- Task: DEV-0308

One linear revision adds only the five validated WP-0300 security tables and
removes only those tables on downgrade. Static tests and PostgreSQL offline SQL
generation passed; no live PostgreSQL migration was performed. No API,
authorization, evidence processing, deployment, or support promotion results.
## DEC-0034 — DEV-0310 fail-closed policy enforcement

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0300_REVIEW
- Task: DEV-0310

Authorization consumes an explicit versioned policy snapshot and permits only
exact role/action matches after tenant, case, and evidence-source scope checks.
There are no implicit grants or production policy. No authentication provider,
API, evidence processing, deployment, or support promotion is authorized.

## DEC-0035 — DEV-0307 cross-tenant isolation validation

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0300_REVIEW
- Task: DEV-0307

Adversarial synthetic tests establish that explicit grants cannot override
tenant scope, cross-case sources are denied, and cross-tenant audit attempts
append nothing. This validation adds no runtime capability or support status.

## DEC-0036 — WP-0300 submitted for owner validation

- Date: 2026-07-28
- Status: VALIDATION_PENDING
- Tasks: WP-0300; DEV-0309

QMS-008 records passing synthetic/offline conformance and the unresolved lack
of live PostgreSQL and production API/policy integration. WP-0300 is submitted
for owner review as candidate foundation infrastructure only. No support,
deployment, evidence processing, API exposure, or production policy is granted.

## DEC-0037 — Approve WP-0300 candidate security foundation

- Date: 2026-07-28
- Status: APPROVED
- Tasks: WP-0300; DEV-0308; DEV-0310; DEV-0307; DEV-0309
- Validation package: QMS-008
- Implementation commits: `b167af8`, `f7a494b`, `a02fb3f`, `2cdd8ed`
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

The owner approves WP-0300 and DEV-0309 as COMPLETE candidate SaaS security
foundation infrastructure with all QMS-008 and acceptance-record limitations.
The supported registry remains empty. No production authorization policy,
authentication, identity provider, repository, API, live PostgreSQL validation,
deployment, evidence processing, parser activation, or support promotion is
authorized.

## DEC-0060 — Approve DEV-0602 controlled Files-table query layer

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0602
- Query profile: `manifestdb-files-query` version 1
- Locator profile: `manifestdb-row-locator` version 1
- Support effect: none

The owner approves deterministic raw Files-row observation from the same
verified DEV-0205 controlled copy and exact compatible DEV-0601 scope. Version
1 permits enumeration, exact single-row retrieval, ascending ROWID keyset
pagination, locator-only continuation, and projection only of `fileID`,
`domain`, `relativePath`, `flags`, and `file`.

ROWID is the only locator. WITHOUT ROWID returns
`ROW_LOCATOR_UNAVAILABLE`; duplicate or nonmonotonic locators return
`ROW_LOCATOR_DUPLICATE`; no composite or inferred locator is allowed. Raw
column states remain distinct with no coercion. The `file` BLOB remains opaque
bytes. Caller-supplied positive query ceilings and cancellation preserve prior
observations and fail closed.

No join, aggregation, offset pagination, write, modification PRAGMA, repair,
replay, decoding, reconstruction, evidence interpretation, artifact parsing,
parser execution, registry/store insertion, API, production, real evidence,
Apple/parser/artifact/workflow support, or support promotion is authorized.

## DEC-0061 — Reconcile DEV-0602 and authorize candidate query hardening

- Date: 2026-07-28
- Status: APPROVED_FOR_IMPLEMENTATION
- Tasks: DEV-0602; DEV-0602A
- Profiles: `manifestdb-files-query` v2;
  `manifestdb-query-resource-controls` v1
- Support effect: none

DEV-0602 remains COMPLETE under DEC-0060. Query profile
`manifestdb-files-query` v1 and locator profile `manifestdb-row-locator` v1
remain immutable. Version 1 may return raw `file` BLOB bytes as an immutable
in-memory observation, but may not decode, interpret, persist, log, hash, or
publicly expose them.

Expanded requirements are separately authorized as DEV-0602A. Candidate query
v2 defaults to BLOB state/length/storage-class observations and requires
explicit internal authorization for bounded raw bytes. It separates completion,
termination, resource, and row states; distinguishes logical determinism from
operational safety; uses monotonic time, deterministic projected-byte and
fixed-overhead memory estimates, and PROCESS → TENANT → CASE →
EVIDENCE_SOURCE → PROCESSING_RUN concurrency controls.

Version 2 cannot replace, reinterpret, or silently fall back to version 1.
DEV-0602A must stop at VALIDATION_PENDING. No BLOB interpretation, parser,
artifact, Apple compatibility, API, persistence, production, real evidence,
registry entry, supported record, or support promotion is authorized.

## DEC-0062 — Approve DEV-0602A candidate query-hardening infrastructure

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0602A
- Validation package: QMS-012
- Acceptance record: DEV-0602A-files-query-hardening-acceptance
- Profiles: `manifestdb-files-query` v2;
  `manifestdb-query-resource-controls` v1
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

The owner approves DEV-0602A as COMPLETE candidate Files-table query-hardening
and resource-control infrastructure with every QMS-012 limitation retained.
DEV-0602 remains COMPLETE under DEC-0060. Query profile v1 and locator profile
v1 remain immutable; v2 is explicitly selected and does not migrate,
reinterpret, replace, or invalidate v1 observations.

Candidate v2 retains bounded default BLOB observations, explicitly authorized
internal run/source-scoped raw-byte access, independent completion,
termination, value, and resource states, lossless SQLite dynamic types,
logical determinism, monotonic operational timing, deterministic byte and
memory estimates, hierarchical application concurrency controls, scoped
continuations, and fail-closed controlled-copy behavior. BLOB access is not
decoding or interpretation.

No query or resource profile is Supported. No parser, artifact, Apple input,
Manifest.db content, workflow, API, production use, deployment, physical file
resolution, normalization, AI/report conclusion, real-evidence processing, or
support promotion is authorized. Registry entries and supported normalized
records remain zero. DEV-0603 through DEV-0607 and DEV-0609 remain independent
mandatory owner gates.

## DEC-0063 — Approve DEV-0603 canonical identifier framework and fileID profile

- Date: 2026-07-28
- Status: APPROVED_FOR_IMPLEMENTATION
- Task: DEV-0603
- Framework: `canonical-identifier-normalization` v1
- Profile: `manifestdb-fileid-normalization` v1
- Support effect: none

The owner authorizes a reusable immutable identifier-observation framework and
one concrete Manifest.db `Files.fileID` lexical profile. Inputs must be proven
DEV-0602 v1 or DEV-0602A v2 row observations with complete tenant, case,
source, controlled-copy/database, run, query, locator, storage-class, value
state, and source-location provenance.

Version 1 recognizes exactly 40 ASCII hexadecimal characters and may create a
lowercase canonical comparison representation only after exact recognition.
The only transformations are NONE, strict ASCII BLOB decoding, and ASCII
hexadecimal case canonicalization. Raw TEXT, BLOB, NULL, INTEGER, and REAL
observations remain distinct and immutable. Comparisons are explicitly
EXACT_RAW, EXACT_CANONICAL, or NOT_COMPARABLE and remain case/tenant scoped.

Lexical recognition is not hash verification. Normalization is not physical
resolution. Canonical equality is not content or object identity. Repeated
fileIDs are not duplicate, orphan, absence, corruption, or tampering
conclusions. No hashing, filesystem search, physical resolution, BLOB metadata
decoding, domain/path/flags interpretation, parser, artifact, API, persistence,
real evidence, production use, or support promotion is authorized. DEV-0603
must stop at VALIDATION_PENDING.

## DEC-0064 — Approve DEV-0603 candidate identifier infrastructure

- Date: 2026-07-29
- Status: APPROVED
- Task: DEV-0603
- Validation package: QMS-013
- Acceptance record: DEV-0603-manifest-fileid-normalization-acceptance
- Framework/profile: `canonical-identifier-normalization` v1;
  `manifestdb-fileid-normalization` v1
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

Under the owner-authorized autonomous Manifest workstream, the candidate-level
review accepts DEV-0603 as COMPLETE with every QMS-013 and FOR-014 limitation.
Inputs remain proven query v1/v2 observations; exact raw SQLite values and
scope/query/locator provenance are immutable. The only transformations are
NONE, strict authorized ASCII BLOB decoding, and post-recognition ASCII hex
case canonicalization.

Comparison is caller-directed and bounded: one pair, one subject against an
explicit bounded candidate set, or an explicit bounded pair sequence. These
operations are linear in supplied work and enforce count, byte,
deterministic-memory, monotonic-time, cancellation, scope, and profile limits
before each result. No implicit Cartesian product, all-pairs engine, global
matching, persistent identifier index, or duplicate/content conclusion exists.

Lexical recognition is not hash verification; canonicalization is not physical
resolution; equality is not content identity; repeated fileIDs are not
duplicate or absence conclusions. No evidence hash, filesystem access,
physical object, parser, artifact, persistence, API, real evidence, production
use, supported record, or support promotion is authorized. Registry/store
counts remain zero.

Every future protected service, repository, job, report, export, AI, and API
boundary must authorize before returning, transforming, exporting, or
retrieving protected content. Queries must be tenant/case/resource scoped where
possible; inaccessible identifiers fail closed without existence disclosure.
Safe structured security audit coverage remains mandatory at applicable future
boundaries.

The requested Evidence Coverage package already exists as WP-0450 because
controlling WP-0400 is the Supported Evidence Data Model. WP-0450 remains
dependency-blocked and retains DEC-0027 forensic limitations; cloud acquisition
remains separately governed and FUTURE.
## DEC-0038 — DEV-0401 processing-run identity

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0400_REVIEW
- Task: DEV-0401

Candidate runs have immutable identity, tenant/case/source scope,
request/correlation provenance, and exact policy authorization provenance.
Lifecycle remains DEV-1104 scope and migration DEV-0410 scope. No parser, API,
evidence processing, repository, or support promotion is introduced.

## DEC-0039 — DEV-0402 source-artifact identity

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0400_REVIEW
- Task: DEV-0402

Candidate source artifacts have content-independent UUIDv4 identity linked to
tenant, case, evidence source, processing run, and WP-0250 evidence UUID.
Registration requires exact authorization and matching scope. Locator semantics
remain DEV-0403 and migration DEV-0410. Presence never implies support.

## DEC-0040 — DEV-0403 stable source locator

- Date: 2026-07-28
- Status: IMPLEMENTED_PENDING_WP_0400_REVIEW
- Task: DEV-0403

Candidate locators use immutable internal identity and preserve raw and
normalized values plus the declared normalization method. They perform no
filesystem access and assert no presence, readability, completeness, or
support. Migration remains DEV-0410 scope.

## DEC-0041 — Adopt autonomous execution charter

- Date: 2026-07-28
- Status: APPROVED
- Governance record: GOV-001

The owner adopts `docs/governance/AUTONOMOUS_EXECUTION_CHARTER.md`. It controls
autonomous execution where older generic stop/completion wording conflicts.
Mandatory review is limited to architecture/trust boundaries, evidence
integrity/provenance/security, support promotion, AI reasoning policy,
production exposure/deployment, and legal/licensing/compliance decisions.

Existing approved scope, architecture, support, forensic limitations, task IDs,
and audit history remain controlling. Evidence Coverage remains WP-0450 because
WP-0400 is already allocated to the Supported Evidence Data Model. No support
or production status changes.
## DEC-0042 — Approve DEV-0405 qualified fingerprint observations

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0405

Fingerprints are profile-qualified observations with canonical-input reference,
SHA-256 digest, provenance, time, and limitations. They imply no compatibility,
equivalence, parse success, or support. No universal cross-artifact algorithm
is approved. DEC-0008 applies only to its candidate Manifest.db profile; every
future profile requires independent validation and owner review before
promotion.
## DEC-0043 — Approve DEV-0406 lossless typed-value observations

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0406

Raw evidentiary representations remain immutable, explicitly typed and
serialized, independently addressable, and separate from normalized derived
representations. Semantic absence, value, failure, and indeterminate states
remain distinct. Normalization requires complete transformation provenance and
never supersedes raw data. This storage-envelope decision approves no
artifact-specific transformation, parser, support, display, redaction, report,
AI, compatibility, or production behavior.
## DEC-0044 — Approve DEV-0407 timestamp provenance

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0407

Timestamp observations preserve raw typed values separately from interpretation
and conversion. Controlled category, precision, timezone-source,
interpretation, ambiguity, and conversion vocabularies govern candidate
envelopes. No timezone, epoch, ambiguity, precision, or conversion algorithm is
approved; artifact-specific profiles require separate governance.
## DEC-0045 — Approve DEV-0408 processing coverage observations

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0408

Processing coverage records factual authorization, execution, source,
reconciled-count, omission, failure, resource, and partial-processing
observations. Complete zero records is permitted only after authorized complete
reconciled execution. These observations remain separate from WP-0450 derived
coverage and make no device-level, compatibility, support, legal, or intent
conclusion.
## DEC-0046 — Approve DEV-0409 processing issue observations

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0409

Immutable processing issues use closed category, severity, and recoverability
vocabularies with stable safe codes, sanitized diagnostics, complete
provenance, and limitations. Partial-processing observations link completed,
incomplete, and unresolved scope to coverage, omissions, and issues. These
diagnostics make no evidentiary, compatibility, support, intent, legal, AI,
report, authenticity, or production conclusion.
## DEC-0047 — Approve DEV-0410 candidate supported-store foundation

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0410

The owner approves additive relational candidate store infrastructure, exact
fail-closed admission, scoped queries, immutable records, and supersession.
The empty production registry admits no records. Schema existence is not
support. Live PostgreSQL, production repositories, parsers, APIs, real
evidence, and support promotion remain unapproved.
## DEC-0048 — Submit WP-0400 for owner validation

- Date: 2026-07-28
- Status: VALIDATION_PENDING
- Tasks: WP-0400; DEV-0412
- Validation package: QMS-009

The complete candidate evidence-core package passes synthetic and offline
validation and is submitted for mandatory evidence-integrity/provenance review.
The registry and supported normalized store remain empty. No support,
compatibility, production, parser, API, report, AI, or real-evidence
authorization follows.
## DEC-0049 — Approve WP-0400 candidate evidence-core infrastructure

- Date: 2026-07-28
- Status: APPROVED
- Tasks: WP-0400; DEV-0401 through DEV-0412
- Validation package: QMS-009
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

The owner approves WP-0400 and DEV-0412 as COMPLETE candidate evidence-core
infrastructure with all QMS-009 limitations. Migration 0004, exact admission,
scoped retrieval, immutable observations, supersession, and quarantine
isolation may support later candidate tasks. Registry entries and supported
normalized records remain zero.

No live PostgreSQL, production repository, parser activation/execution,
artifact or Apple compatibility, API, real evidence, report, AI, deployment,
or support promotion is authorized. JSON observation payloads remain an
accepted candidate limitation, not a final production representation.

## DEC-0050 — Designate DEV-1101 READY

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-1101
- Support effect: none

The owner designates DEV-1101 ready for immediate autonomous implementation.
The task must preserve zero Supported Parser Registry entries, zero supported
normalized records, legacy quarantine, and the prohibitions on parser or
artifact promotion, real-evidence processing, API exposure, and deployment.

## DEC-0051 — Approve automatic task readiness workflow

- Date: 2026-07-28
- Status: APPROVED
- Scope: task-state administration only

Codex may automatically move eligible tasks through `NOT_STARTED`,
`DEPENDENCIES_SATISFIED`, and `READY`, reevaluate stale blockers, and continue
independent READY work when another task is in `OWNER_REVIEW`. The canonical
ten-state vocabulary, readiness record, priority model, and work-in-progress
limit are governing. All architecture, evidence-integrity, provenance,
security, support, legal, AI-policy, production, deployment, and real-evidence
owner gates remain unchanged.

## DEC-0052 — Approve DEV-1107 idempotency and forensic rerun model

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-1107
- Support effect: none

Logical requests, idempotency claims, execution attempts, processing runs, and
retry/rerun relationships are distinct immutable observations. Exact versioned
SHA-256 keys may deduplicate only before a new attempt starts; every attempt
gets a new run identity. Atomic relational claims, scoped non-disclosure,
explicit retry/rerun intent, prior-outcome preservation, and no assumed
resumability govern. No parser, artifact, compatibility, API, production,
real-evidence, or support authority follows.

## DEC-0053 — Submit WP-1100 candidate processing pipeline for review

- Date: 2026-07-28
- Status: OWNER_REVIEW
- Tasks: DEV-1101 through DEV-1110
- Validation package: QMS-010
- Support effect: none

The candidate pipeline passes synthetic integration and regression validation.
The registry and supported normalized store remain empty. Owner review may
approve candidate architectural use only; it cannot activate a parser, promote
an artifact or workflow, expose an API, authorize real evidence or production
use, or change support status.

## DEC-0054 — Approve DEV-0501 Apple backup discovery semantics

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0501
- Support effect: none

Discovery is limited to the authorized backup root and governed top-level
metadata. Sources remain independently attributable; missing, malformed,
unsupported, inaccessible, and conflicting claims remain distinct. No universal
Manifest.db/plist precedence applies. Manifest.db content/schema compatibility
remains DEV-0601. Directory names are observations only. No parsing,
compatibility, real-evidence, API, production, or support authority follows.

## DEC-0055 — Approve WP-1100 candidate processing infrastructure

- Date: 2026-07-28
- Status: APPROVED
- Tasks: WP-1100; DEV-1101 through DEV-1110
- Validation package: QMS-010
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

The owner approves WP-1100 and DEV-1110 as COMPLETE candidate processing
infrastructure under the review submitted in DEC-0053 and all limitations in
QMS-010. Later candidate tasks may use the exact parser-authorization,
registry-isolation, fail-closed execution, immutable lifecycle, factual
coverage/failure aggregation, versioned idempotency, retry/rerun lineage,
cancellation/cleanup, audit, and integration controls.

The accepted idempotency profile is
`processing-request-canonical-json-sha256` version 1 using SHA-256 over sorted
canonical JSON and the exact governed scope recorded in DEV-1107. Every actual
attempt, retry, or rerun receives a new immutable processing-run UUID; prior
outcomes remain immutable and checkpoint resume remains unapproved. Migration
`0005_processing_idempotency` is accepted as additive, offline-reversible
candidate infrastructure only.

The Supported Parser Registry and supported normalized-record store remain
empty. No parser, artifact, workflow, input, report, API, AI capability, Apple
compatibility profile, or other capability becomes Supported. Live PostgreSQL,
production repositories, production concurrency/cancellation/cleanup,
deployment, real-evidence processing, API exposure, parser activation, and
support promotion remain unapproved. The QMS-010 limitations and accepted
TestClient warning remain active.

## DEC-0056 — Approve DEV-0505 identifier and product-version normalization

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0505
- Profiles: `apple-backup-identifier-normalization` version 1;
  `apple-product-version-normalization` version 1
- Support effect: none

The owner approves deterministic, lossless candidate normalization for exact
metadata comparison. Raw observations remain immutable; identifier classes,
semantic states, product-version component text/count/value/leading-zero
properties, named comparison modes, transformation provenance, scope, safe
failure states, and limitations remain explicit.

Only conservative leading/trailing ASCII whitespace removal, approved
case-insensitive hexadecimal lowercase comparison form, required-separator
preservation, and exact syntax validation are authorized. No fuzzy matching,
repair, class conversion, device attribution, authenticity conclusion,
zero-component padding, suffix removal, Apple/schema/parser compatibility,
parser activation, registry/store seeding, API, production, real evidence, or
support promotion is authorized. DEV-0601 remains the Manifest.db
compatibility gate. DEC-0055 remains controlling for WP-1100 completion.

## DEC-0057 — Submit WP-0500 candidate metadata package for review

- Date: 2026-07-28
- Status: OWNER_REVIEW
- Tasks: DEV-0501 through DEV-0509
- Validation package: QMS-011
- Support effect: none

The candidate metadata package passes synthetic integration and regression
validation. It preserves raw/source provenance, exact comparison boundaries,
factual coverage, and permanent limitations. The corpus is not Apple-produced;
the candidate compatibility profile and Manifest.db schema compatibility
remain unapproved. Registry entries and supported normalized records remain
zero.

Owner review may approve candidate architectural use only. It cannot approve
production Apple compatibility, activate a parser, promote an artifact/input
or workflow, expose an API, authorize real evidence or deployment, populate
supported storage, or change support status.

## DEC-0058 — Approve WP-0500 candidate Apple backup metadata infrastructure

- Date: 2026-07-28
- Status: APPROVED
- Tasks: WP-0500; DEV-0501 through DEV-0509
- Validation package: QMS-011
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

The owner approves WP-0500 and DEV-0509 as COMPLETE candidate metadata
infrastructure with every QMS-011 limitation retained. Candidate architectural
use is approved for the version 1 discovery, metadata reconciliation,
identifier normalization, and product-version normalization profiles and the
documented readers, factual coverage, and synthetic fixture corpus.

Discovery remains root-confined, read-only, top-level only, and nonrecursive.
Manifest.db remains limited to presence/access/type/header observations with
controlled structural and schema validation separate. `IsEncrypted` remains
the only approved encryption signal. Backup-root names remain
non-authoritative; normalized equality is not device attribution; product
version is not compatibility; absent metadata is not deletion or evidentiary
absence.

The corpus is synthetic and not Apple-produced. No user-content artifact was
parsed and no real evidence was processed. The Supported Parser Registry and
supported normalized store remain empty. No Apple compatibility, schema,
parser, artifact, workflow, input, API, AI/reporting capability, production
use, deployment, decryption, or support promotion is authorized. DEV-0601
remains a mandatory owner-review gate.

## DEC-0059 — Approve DEV-0601 Manifest.db schema compatibility framework

- Date: 2026-07-28
- Status: APPROVED
- Task: DEV-0601
- Schema profile: `apple-manifestdb-schema` version 1
- Fingerprint profile: `manifestdb-schema-canonical-json-sha256` version 1
- Support effect: none

The owner approves candidate schema recognition only. DEC-0008 controls the
case-insensitive required `Files` table and `fileID`, `domain`,
`relativePath`, `flags`, and `file` columns. Version 1 uses the
repository-characterized TEXT/TEXT/TEXT/INTEGER/BLOB affinities, with no
required primary-key, uniqueness, foreign-key, index, trigger, view,
AUTOINCREMENT, or WITHOUT ROWID behavior. That affinity basis is synthetic and
not authoritative Apple schema documentation.

Validation is limited to a verified DEV-0205 controlled copy, read-only
SQLite/header/integrity/schema observations, exact profile evaluation, and a
DEC-0008/DEV-0405 algorithm-qualified SHA-256 schema fingerprint. Unknown
tables and columns are preserved and do not fail an otherwise exact profile;
unknown schemas and missing or invalid required components fail closed.

No Files/Properties rows, blobs, fileIDs, domains, relative paths, metadata,
artifacts, or user content may be read or interpreted. No parser execution,
registry entry, supported record, Apple/input/parser/artifact/workflow
support, API, production, deployment, real evidence, or support promotion is
authorized.

## DEC-0065 — Authorize DEV-0604 candidate Manifest domain grammar

- Date: 2026-07-29
- Status: APPROVED FOR IMPLEMENTATION
- Task: DEV-0604
- Profile: `manifestdb-domain-grammar` version 1
- Support effect: none

Under the autonomous Manifest workstream authorization, DEV-0604 may implement
an immutable, exact, case-sensitive candidate grammar for proven
`Files.domain` observations from query profiles v1 and v2. Raw values, dynamic
SQLite types, full scope/query/locator provenance, unknown and malformed forms,
and limitations must remain explicit. Repository-characterized literal and
prefixed forms are provisional and synthetic, not an exhaustive or
authoritative Apple specification.

The profile may separate structural families and opaque application, group, or
plugin components. It may not infer installation, execution, activity,
ownership, container/file/physical-object existence, completeness,
compatibility, artifact meaning, parser behavior, or support. No trimming,
repair, filesystem access, hashing, API, migration, persistence, real evidence,
registry entry, supported record, or support promotion is authorized.

## DEC-0066 — Approve DEV-0604 candidate Manifest domain infrastructure

- Date: 2026-07-29
- Status: APPROVED
- Task: DEV-0604
- Validation package: QMS-014
- Acceptance record: DEV-0604-manifest-domain-normalization-acceptance
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

The authorized candidate-level review accepts DEV-0604 as COMPLETE. All
acceptance criteria pass using deterministic synthetic fixtures: 33 focused,
113 combined Manifest, 520 backend regression, and 5 legacy characterization
tests, plus compilation, dependency, migration, and hygiene checks. The
unchanged TestClient warning remains accepted. Migration head remains
`0005_processing_idempotency`; no migration was added.

FOR-015 limitations remain permanent. Its repository-characterized grammar is
not authoritative or exhaustive Apple documentation. Structural recognition
does not prove application installation, execution, activity, ownership,
container/file/physical-object existence, completeness, compatibility, parser
behavior, artifact meaning, or support. Registry entries and supported records
remain zero. No API, production use, deployment, real evidence, parser
activation, artifact/input/workflow support, or support promotion is approved.

## DEC-0067 — Authorize DEV-0605 candidate relative-path lexical profile

- Date: 2026-07-29
- Status: APPROVED FOR IMPLEMENTATION
- Task: DEV-0605
- Profile: `manifestdb-relative-path-lexical` version 1
- Support effect: none

The autonomous Manifest authorization permits an immutable, resource-bounded
lexical observation of proven query v1/v2 `Files.relativePath` values. It must
separate exact raw values, storage and encoding state, tokenization, empty
paths, separators, absolute indicators, dot/parent traversal, canonical lexical
comparison, unsafe/indeterminate outcomes, provenance, and limitations.

No trimming, repair, joining, filesystem access, symlink resolution, physical
existence, artifact interpretation, parser behavior, API, persistence,
migration, real evidence, or support promotion is authorized.

## DEC-0068 — Approve DEV-0605 candidate relative-path infrastructure

- Date: 2026-07-29
- Status: APPROVED
- Task: DEV-0605
- Validation package: QMS-015
- Acceptance record: DEV-0605-manifest-relative-path-acceptance
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

Candidate-level review accepts DEV-0605 COMPLETE: 23 focused, 136 combined
Manifest, 543 backend, and 5 legacy tests pass with all quality gates. The
unchanged TestClient warning remains accepted. Migration head remains
`0005_processing_idempotency`; no migration was added.

FOR-016 limitations remain permanent. Lexical safety is not host-path safety,
filesystem resolution, physical existence, artifact identity, compatibility,
or support. No path was repaired, joined, or resolved. Registry/store counts
remain zero; no API, parser, real evidence, deployment, or support promotion is
approved.

## DEC-0069 — Authorize DEV-0606 fail-closed flags observation

- Date: 2026-07-30
- Status: APPROVED FOR IMPLEMENTATION
- Task: DEV-0606
- Profile: `manifestdb-flags-observation` version 1
- Support effect: none

Repository review finds no governing source that approves any `Files.flags`
bit meaning. Under the autonomous Manifest authorization, DEV-0606 may preserve
proven query v1/v2 raw typed values and bounded set-bit positions, but the known
meaning set must remain empty and every set bit must remain unknown. Zero and
negative values require explicit non-semantic states.

No file type, existence, deletion, user action, tampering, corruption, physical
state, artifact, completeness, compatibility, parser, or support inference is
authorized. Metadata BLOB decoding remains DEV-0607. No API, persistence,
migration, filesystem operation, real evidence, or support promotion is
authorized.

## DEC-0070 — Approve DEV-0606 candidate flags infrastructure

- Date: 2026-07-30
- Status: APPROVED
- Task: DEV-0606
- Validation package: QMS-016
- Acceptance record: DEV-0606-manifest-flags-observation-acceptance
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

Candidate-level review accepts DEV-0606 COMPLETE: 17 focused, 153 combined
Manifest, 560 backend, and 5 legacy tests pass with all quality gates. The
unchanged TestClient warning remains accepted. Migration head remains
`0005_processing_idempotency`; no migration was added.

FOR-017 limitations remain permanent. No bit meaning is approved; every set bit
remains unknown. Numeric observations do not prove file type, existence,
deletion, user action, tampering, corruption, physical state, artifact meaning,
compatibility, or support. Registry/store counts remain zero. No BLOB decoding,
API, parser, real evidence, deployment, or support promotion is approved.

## DEC-0071 — Authorize DEV-0607 bounded metadata-BLOB syntax profile

- Date: 2026-07-30
- Status: APPROVED FOR IMPLEMENTATION
- Task: DEV-0607
- Profile: `manifestdb-file-bplist-syntax` version 1
- Support effect: none

Under the autonomous Manifest authorization, DEV-0607 may implement a custom
iterative scanner for exact `bplist00` syntax from explicitly authorized raw
query observations. It must validate trailer/offset/reference/graph structure,
enforce caller byte/object/depth/string/collection/memory/time/cancellation
controls, retain only completed syntactic nodes, emit no DATA bytes, and never
instantiate archived or dynamic classes.

Scalar/key/UID values and object graphs remain syntactic and uninterpreted.
Unknown formats, versions, tokens, classes, graphs, malformed inputs, cycles,
and resource termination fail closed. No universal plist support,
NSKeyedArchiver semantics, metadata-field meaning, Apple compatibility,
filesystem/physical conclusion, parser, artifact, API, persistence, migration,
real evidence, or support promotion is authorized.

## DEC-0072 — Approve DEV-0607 candidate metadata-BLOB syntax infrastructure

- Date: 2026-07-30
- Status: APPROVED
- Task: DEV-0607
- Validation package: QMS-017
- Acceptance record: DEV-0607-manifest-metadata-blob-acceptance
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`

Candidate-level review accepts DEV-0607 COMPLETE: 19 focused, 172 combined
Manifest, 579 backend, and 5 legacy tests pass with all quality gates. The
unchanged TestClient warning remains accepted. Migration head remains
`0005_processing_idempotency`; no migration was added.

FOR-018 limitations remain permanent. The custom scanner handles bounded
`bplist00` syntax only, validates nonoverlapping offsets/references/cycles, and
instantiates no class or dynamic object. Scalars, UIDs, keys, and graphs have no
approved metadata meaning. Registry/store counts remain zero. No Apple
compatibility, parser/artifact/input/workflow support, API, real evidence,
deployment, or support promotion is approved.
