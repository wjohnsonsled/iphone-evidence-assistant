\# DEV-009 — Task Ledger



| Task ID | Description | Status | Dependencies | Acceptance document | Completion evidence |

|---|---|---|---|---|---|

Canonical states under DEC-0051 are `NOT_STARTED`,
`DEPENDENCIES_SATISFIED`, `READY`, `IN_PROGRESS`, `BLOCKED`, `OWNER_REVIEW`,
`VALIDATION_PENDING`, `COMPLETE`, `DEFERRED`, and `CANCELLED`. Eligible
readiness transitions are automatic and recorded in DEV-011.

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
| DEV-0305 | Evidence-source tenant and case linkage | COMPLETE | DEV-0203, DEV-0303 | DEV-0305-evidence-source-linkage-acceptance | Evidence-source identity derives tenant/case from supported case; composite relational key rejects cross-tenant linkage; no evidence access or support effect |
| DEV-0306 | Audit-actor attribution | COMPLETE | DEV-0302, DEV-0206 | DEV-0306-audit-actor-attribution-acceptance | Principal/membership-derived actor context attributes WP-0250 audit events and blocks cross-tenant attribution; no permission effect |
| DEV-0308 | Additive Alembic migration baseline | COMPLETE | DEV-0301 through DEV-0306 | DEV-0308-additive-security-migration-acceptance | One linear additive/reversible migration; offline SQL and regressions pass; no live PostgreSQL or support change |
| DEV-0307 | Cross-tenant isolation tests | COMPLETE | DEV-0310, DEV-0305 | DEV-0307-cross-tenant-isolation-acceptance | Adversarial grant, source-scope, and audit non-append tests pass |
| DEV-0310 | Authorization Service and Policy Enforcement | COMPLETE | DEV-0301, DEV-0302, DEV-0303 | DEV-0310-authorization-service-acceptance | Explicit versioned exact-match policy; no default grants |
| DEV-0309 | Security package integration tests | COMPLETE | DEV-0301 through DEV-0308; DEV-0310 | DEV-0309-security-package-integration-acceptance; QMS-008 | Owner approved WP-0300 candidate foundation in DEC-0037; live PostgreSQL, production policy/auth/API, and support remain unapproved |
| DEV-0401 | Processing-run model | COMPLETE | WP-0200, WP-0250, WP-0300 | DEV-0401-processing-run-model-acceptance | Immutable scoped identity and authorization provenance validated; lifecycle DEV-1104, migration DEV-0410 |
| DEV-0402 | Source-artifact identity model | COMPLETE | DEV-0401 | DEV-0402-source-artifact-identity-acceptance | Scoped authorized candidate identity; no locator/support claim; migration DEV-0410 |
| DEV-0403 | Stable source-locator model | COMPLETE | DEV-0402 | DEV-0403-stable-source-locator-acceptance | Stable internal identity preserves raw/normalized locator values separately; no filesystem/support semantics |
| DEV-0404 | Parser identity and version model | COMPLETE | DEV-0401 | DEV-0404-parser-identity-version-acceptance | Candidate-only persistent identity metadata; supported registry remains empty; migration DEV-0410 |
| DEV-0405 | Schema-fingerprint observation model | COMPLETE | DEV-0402; DEC-0042 | DEV-0405-schema-fingerprint-model-acceptance | Qualified observation only; no universal canonicalization or compatibility/support inference |
| DEV-0406 | Lossless typed-value observation model | COMPLETE | DEV-0402; DEC-0043 | DEV-0406-lossless-typed-value-acceptance | Raw/normalized independently addressable; explicit semantic states and transformation provenance; no algorithms/support |
| DEV-0407 | Timestamp provenance observation model | COMPLETE | DEV-0406; DEC-0044 | DEV-0407-timestamp-provenance-acceptance | Raw/derived separation, closed vocabularies, explicit ambiguity/failure; no algorithms/support |
| DEV-0408 | Processing coverage and omission observation model | COMPLETE | DEV-0401; DEC-0045 | DEV-0408-processing-coverage-acceptance | Closed factual processing states/counts/omissions; zero and partial fail closed; no WP-0450 conclusion |
| DEV-0409 | Processing issue and partial-processing observation model | COMPLETE | DEV-0401; DEC-0046 | DEV-0409-processing-issue-acceptance | Immutable safe diagnostics and partial scope linkage; no evidentiary/support conclusion |
| DEV-0410 | Candidate supported evidence store foundation | COMPLETE | DEV-0401 through DEV-0409; DEC-0047 | DEV-0410-supported-store-acceptance | Additive 0004 schema and exact admission/query boundary; registry/store remain empty |
| DEV-0411 | Legacy and experimental store isolation | COMPLETE | DEV-0410 | DEV-0411-store-isolation-acceptance | Separate scoped quarantine store has no promotion/transfer path; supported store remains empty |
| DEV-0412 | Evidence-core integration tests | COMPLETE | DEV-0401 through DEV-0411 | DEV-0412-evidence-core-integration-acceptance; QMS-009 | Owner approved WP-0400 candidate infrastructure in DEC-0049; registry/store remain empty |

| DEV-0451 | Source Inventory Engine | COMPLETE | WP-0200, WP-0250, DEV-0402, DEV-0403 | DEV-0451-source-inventory-acceptance | Deterministic registered-observation inventory only; no filesystem discovery, coverage conclusion, or support effect |
| DEV-0452 | Artifact Coverage Engine | COMPLETE | DEV-0451, DEV-0304, DEV-0408, DEV-0409, DEV-1101 through DEV-1106 | DEV-0452-artifact-coverage-engine-acceptance | Exact registered-set projection preserves closed factual states and denominator; no conclusion |
| DEV-0453 | Evidence Gap Classification | OWNER_REVIEW | DEV-0451, DEV-0452 | To be created | COV-SEMANTICS-GATE: evidence-gap conclusion vocabulary and rules require owner review |
| DEV-0454 | Backup Structure and Coverage Assessment | BLOCKED | DEV-0451, DEV-0453, WP-0200 | To be created | Must not infer completeness, deletion, concealment, destruction, or spoliation |
| DEV-0455 | Collection Opportunity Engine | DEFERRED | DEV-0453, DEV-0454, WP-1900 where applicable | To be created | Post-MVP; reproducible versioned rules required |
| DEV-0456 | Question-Specific Evidence Sufficiency Engine | DEFERRED | DEV-0453, WP-1200, WP-1300 | To be created | Post-MVP; no legal sufficiency conclusion |
| DEV-0457 | Acquisition Recommendation Engine | DEFERRED | DEV-0455, DEV-0456 | To be created | Post-MVP; separate acquisition-method approval |
| DEV-0458 | Attorney Coverage Summary Generator | BLOCKED | DEV-0453, DEV-0454, DEV-1401, DEV-1404 | To be created | Attorney-readable limitations mandatory |

| DEV-1101 | Supported parser registry | COMPLETE | WP-0400, DEV-0262, DEV-0263, DEV-0264 | DEV-1101-supported-parser-registry-acceptance | Reuses DEV-0304 registry; complete permanent promotion references; production entry count remains zero |
| DEV-1102 | Legacy parser registry isolation | COMPLETE | DEV-1101 | DEV-1102-legacy-registry-isolation-acceptance | Static/runtime boundary validation; legacy plugin access remains confined to explicit legacy service |
| DEV-1103 | Fail-closed parser executor | COMPLETE | DEV-1101 | DEV-1103-fail-closed-parser-executor-acceptance | Authorization-before-call, controlled-input, provenance, coverage, zero-result, and safe-failure enforcement |
| DEV-1104 | Processing-run state machine | COMPLETE | DEV-0401 | DEV-1104-processing-run-state-machine-acceptance | Immutable closed transitions with distinct complete-zero, partial, failed, and cancelled terminal states |
| DEV-1105 | Coverage aggregation | COMPLETE | DEV-0408 | DEV-1105-coverage-aggregation-acceptance | Same-run factual status/count reducer; unavailable counts remain unknown; no evidence-gap conclusion |
| DEV-1106 | Failure aggregation | COMPLETE | DEV-0409 | DEV-1106-failure-aggregation-acceptance | Same-run safe category/severity/fatal/partial reducer; broken references fail closed |
| DEV-1107 | Idempotency and rerun controls | COMPLETE | DEV-1104; DEC-0052 | DEV-1107-idempotency-rerun-acceptance | Exact versioned key, atomic claim, immutable attempts, explicit retry/rerun lineage, additive migration 0005 |
| DEV-1108 | Cancellation and cleanup | COMPLETE | DEV-1104 | DEV-1108-cancellation-cleanup-acceptance | Cleanup-before-terminal; cleanup failure is explicit FAILED with safe reason |
| DEV-1109 | Pipeline audit events | COMPLETE | DEV-1104, DEV-0206 | DEV-1109-pipeline-audit-events-acceptance | Closed append-only started/completed/zero/failed mapping with scoped attribution |
| DEV-1110 | Pipeline integration tests | COMPLETE | DEV-1101 through DEV-1109 | DEV-1110-pipeline-integration-acceptance; QMS-010 | Owner approved COMPLETE candidate integration validation in DEC-0055; all QMS-010 limitations remain; registry/store counts remain zero |
| DEV-0459 | Commercial Services Integration | DEFERRED | DEV-0457; separate approval | To be created | No external or paid integration authorized |

| DEV-0501 | Apple backup discovery and metadata reconciliation | COMPLETE | WP-0200, WP-0400, DEV-0263, DEV-0264; DEC-0054 | DEV-0501-apple-backup-discovery-acceptance | Versioned root-confined source-specific discovery; Manifest pending validation; conflicts unresolved; no support effect |
| DEV-0502 | Info.plist controlled reader | COMPLETE | DEV-0501 | DEV-0502-info-plist-reader-acceptance | Versioned projection adopts DEV-0501 reader; three approved fields; no compatibility/support |
| DEV-0503 | Manifest.plist controlled reader | COMPLETE | DEV-0501; DEC-0009 | DEV-0503-manifest-plist-reader-acceptance | Versioned projection of IsEncrypted only; no secondary signal or decryption |
| DEV-0504 | Status.plist controlled reader | COMPLETE | DEV-0501 | DEV-0504-status-plist-reader-acceptance | Versioned SnapshotState claim only; no completeness inference |
| DEV-0505 | Backup metadata normalization | COMPLETE | DEV-0502 through DEV-0504; DEC-0056 | DEV-0505-metadata-normalization-acceptance; FOR-010 | Lossless class-specific identifier and dotted-version profiles v1; raw preserved; exact comparison only; no identity/compatibility/support inference |
| DEV-0506 | Encryption and version field reconciliation | COMPLETE | DEV-0502 through DEV-0504; DEC-0009; DEC-0054 | DEV-0506-encryption-version-reconciliation-acceptance | Exact projection; IsEncrypted only; conflicts unresolved; version is not compatibility |
| DEV-0507 | Metadata coverage and limitation reporting | COMPLETE | DEV-0505 | DEV-0507-metadata-coverage-limitations-acceptance | Exact six-item candidate measurable set; factual distinct states and exact denominator; no completeness, absence, compatibility, or support conclusion |
| DEV-0508 | Metadata fixture corpus | COMPLETE | DEV-0502 through DEV-0506 | DEV-0508-metadata-fixture-corpus-acceptance | Six deterministic synthetic cases cover success, encryption observation, normalization, missing, unsupported, and malformed behavior; not Apple-produced |
| DEV-0509 | Metadata validation report | COMPLETE | DEV-0501 through DEV-0508 | DEV-0509-metadata-validation-report-acceptance; QMS-011 | Owner approved COMPLETE candidate validation in DEC-0058; all limitations remain; registry/store counts remain zero |
| DEV-0601 | Manifest.db schema-profile validator | COMPLETE | WP-0200, WP-0400, DEV-0263, DEV-0264; DEC-0059 | DEV-0601-manifest-schema-profile-acceptance; FOR-011 | Controlled-copy read-only schema-only profile/fingerprint framework; synthetic characterization only; no rows, parser, compatibility support, or support effect |
| DEV-0602 | Files-table controlled query layer | COMPLETE | DEV-0601; DEC-0060 | DEV-0602-files-query-layer-acceptance; FOR-012 | ROWID-v1 ascending keyset query; exact raw five-column projection; controlled-copy/schema/scope/resource/cancellation enforcement; no interpretation/support |
| DEV-0602A | Files-table query hardening and resource-control profile | COMPLETE | DEV-0602; DEC-0061; DEC-0062 | DEV-0602A-files-query-hardening-acceptance; FOR-013; QMS-012 | Owner-approved candidate query v2 and resource-controls v1; v1 immutable; no interpretation/support |
| DEV-0603 | Canonical identifier framework and Manifest fileID normalization | COMPLETE | DEV-0602; DEV-0602A; DEC-0063; DEC-0064 | DEV-0603-manifest-fileid-normalization-acceptance; FOR-014; QMS-013 | Owner-authorized autonomous candidate approval; caller-directed bounded comparison only; no hash, resolution, duplicate, absence, interpretation, or support |
| DEV-0604 | Domain normalization | COMPLETE | DEV-0602; DEV-0603; DEC-0065; DEC-0066 | DEV-0604-manifest-domain-normalization-acceptance; FOR-015; QMS-014 | Candidate-only exact grammar approved; no activity/existence/support inferences |
| DEV-0605 | Relative-path normalization | COMPLETE | DEV-0602; DEV-0604; DEC-0067; DEC-0068 | DEV-0605-manifest-relative-path-acceptance; FOR-016; QMS-015 | Candidate lexical path profile approved; no filesystem/existence/support inference |
| DEV-0606 | Flags and file metadata normalization | READY | DEV-0602; DEV-0605; autonomous Manifest authorization | To be created | Candidate meanings limited to documented subset; preserve unknown bits and prohibit physical/deletion/support inference |
| DEV-0607 | Manifest metadata-blob characterization | OWNER_REVIEW | DEV-0602 | To be created | MANIFEST-BLOB-GATE: serialization format, safe decoder, field vocabulary, malformed/unknown behavior, and interpretation boundaries require approval |
| DEV-0609 | Duplicate and orphan detection | OWNER_REVIEW | DEV-0602 | To be created | INVENTORY-RELATIONSHIP-GATE: duplicate identity, orphan definition, stored-file resolution, absence language, and conclusion limits require approval |
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
