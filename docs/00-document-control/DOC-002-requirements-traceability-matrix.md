# DOC-002 — Requirements Traceability Matrix

## 1. Document control

- Task: DEV-0003
- Baseline date: 2026-07-24
- Scope authority: AGENTS.md, PRD-003, PRD-007, FOR-004, FOR-006,
  DEV-001, and DEC-0001
- Baseline type: requirements-to-implementation inventory
- Artifact support effect: none

## 2. Purpose

This matrix establishes the controlled traceability baseline for the MVP. It
maps approved requirements to current implementation evidence, verification
evidence, documentation, and an owning task or explicit unassigned gap.

An implementation reference records only that relevant code exists. It is not
evidence that the requirement is complete, validated, accepted, or supported.
The pre-baseline evidence engine, backend, parsers, AI, and reports remain
implemented-but-unvalidated or quarantined as recorded in DOC-005 and PRD-006.

## 3. Traceability statuses

| Status | Meaning |
|---|---|
| `DOCUMENTED_CONTROL` | The requirement is an approved control; runtime implementation may belong to a later task |
| `IMPLEMENTED_TASK_VALIDATED` | The requirement passed its task-specific acceptance tests; this does not establish artifact or workflow support |
| `PARTIAL_UNVALIDATED` | Some relevant code exists, but declared behavior, validation, or acceptance is incomplete |
| `APPROVED_UNIMPLEMENTED` | The requirement is approved and no conforming implementation has been identified |
| `LEGACY_QUARANTINED` | Relevant pre-baseline behavior exists only in the unsupported legacy/compatibility path |
| `NOT_ASSESSED` | Assessment requires a later approved task or architecture decision |

These are traceability statuses, not artifact lifecycle or processing-result
statuses. They must not be displayed as support claims.

## 4. Product and input requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| PRD-IN-001 | Accept only a structurally valid Apple local iPhone backup in the initial supported path | PRD-003 §3; PRD-007 §4 | `PARTIAL_UNVALIDATED` | DEV-0201 adds a supported-boundary directory adapter; Apple structure validation is not implemented | DEV-0201 adapter tests do not establish Apple structure support | DEV-0202 |
| PRD-IN-002 | Distinguish unencrypted, encrypted, incomplete, malformed/corrupted, and unsupported inputs | AGENTS.md Input scope; PRD-007 §4 | `IMPLEMENTED_TASK_VALIDATED` | DEV-0202 classifier and DEV-0203 reporting projection | Synthetic classification and encryption-report suites | DEV-0201 through DEV-0203; production compatibility remains unvalidated |
| PRD-IN-003 | Prioritize unencrypted backups as the first input target | PRD-003 §3; PRD-007 §4; DEC-0001 | `DOCUMENTED_CONTROL` | No conforming supported intake path exists | Owner approval DEC-0001 | DEV-0201 through DEV-0202 |
| PRD-IN-004 | Detect and report encrypted backups without decrypting or processing inaccessible content | PRD-007 §5; DEC-0001 | `IMPLEMENTED_TASK_VALIDATED` | `app.intake.encryption_state` | DEV-0203 focused tests | DEV-0203 owner review |
| PRD-IN-005 | Do not accept, retain, or log backup passwords in the initial MVP | PRD-007 §5; SEC-001 placeholder | `DOCUMENTED_CONTROL` | No password intake interface identified | No secret-handling tests | DEV-0203; security task unassigned |
| PRD-IN-006 | Exclude physical/full-filesystem acquisitions, third-party tool ingestion, and nonvalidated extracted directories | PRD-007 §4; DEC-0001 | `LEGACY_QUARANTINED` | Legacy CLI accepts broader extracted-directory layouts | Documentation approval only; runtime gate absent | DEV-0201; DEV-0304 |
| PRD-SCP-001 | Limit initial artifact candidates to backup metadata/inventory, messages, attachments, calls, and contacts | PRD-007 §6; FOR-004 §2; DEC-0001 | `DOCUMENTED_CONTROL` | Legacy registry contains both candidate and excluded families | FOR-004 matrix and DEC-0001 | DEV-0304 and per-artifact Phase 4 tasks |
| PRD-SCP-002 | Keep all other listed artifact families excluded or quarantined | PRD-007 §7; FOR-004 §3; FOR-006 §5 | `LEGACY_QUARANTINED` | `evidence_engine/_legacy.py::plugins()` exposes excluded families | No production registry enforcement test | DEV-0304 |
| PRD-SCP-003 | Do not represent a local backup as a complete device image | AGENTS.md Mandatory forensic rules; PRD-007 §2 | `DOCUMENTED_CONTROL` | Legacy reports contain limitations but are not an accepted product surface | No product-content acceptance suite | Reporting task unassigned |

## 5. Evidence integrity and provenance requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| FOR-INT-001 | Treat submitted source evidence as immutable and never modify it | AGENTS.md Mandatory forensic rules | `PARTIAL_UNVALIDATED` | DEV-0201 adapter performs metadata-only inspection; immutable evidence-source registration is not implemented | Synthetic DEV-0201 before/after fixture hash and directory-state test | DEV-0103; DEV-0207 |
| FOR-INT-002 | Separate submitted source evidence from derived data and working copies | AGENTS.md; PRD-007 §10 | `IMPLEMENTED_TASK_VALIDATED` | DEV-0205 `ControlledCopyManager` creates isolated verified workspaces; legacy direct-source behavior remains quarantined | Synthetic boundary, source mutation, workspace isolation, and cleanup tests | DEV-0205; DEV-0210 integration |
| FOR-INT-003 | Generate and retain SHA-256 for source and material derived files; surface hash failures | AGENTS.md; PRD-007 §10 | `IMPLEMENTED_TASK_VALIDATED` | WP-0250 `HashRegistry` is the sole authority; DEV-0204 adopts it for intake without duplicating the implementation | DEV-0204 focused metadata/failure tests; WP-0250 known/empty/streaming/history/mismatch/instability tests | DEV-0204; DEV-0210 integration |
| FOR-INT-004 | Clean controlled material explicitly and recover abandoned owned workspaces without touching source evidence | ARC-001 §5.3; CODEX autonomy charter §5 | `IMPLEMENTED_TASK_VALIDATED` | DEV-0208 context cleanup and root/prefix/age-bounded recovery service | Synthetic removal, retention, unsafe-candidate, failure, and policy tests | DEV-0208; DEV-0210 integration |
| SEC-RES-001 | Require explicit fail-closed intake resource ceilings and avoid false evidentiary classifications on denial | ARC-001 §10; DEC-0025 | `IMPLEMENTED_TASK_VALIDATED` | Required `Settings` fields and `IntakeResourcePolicy` guard adapter, plist, copy, schema, and SQLite work | DEV-0209 configuration and synthetic resource-exceedance matrix | DEV-0209; DEV-0210 integration |
| FOR-INT-005 | Integrate candidate intake identity, hashing, controlled copies, audit, provenance, cleanup, and failure distinctions without support leakage | ARC-001; DEC-0011; BACKLOG WP-0200 | `IMPLEMENTED_OWNER_APPROVED_CANDIDATE` | Test-only composition of DEV-0201 through DEV-0209 and WP-0250 reference services | DEV-0210 suite; QMS-007; DEC-0027 | DEV-0210 complete; no support effect |
| COV-GOV-001 | Coverage conclusions use closed, versioned, non-overlapping states with complete observation and provenance basis | DEC-0027 | `APPROVED_UNIMPLEMENTED` | WP-0450 governance definition | Future DEV-0451 through DEV-0460 acceptance packages | WP-0450 |
| COV-INV-001 | Source inventory preserves scoped source/artifact/locator identities without inferring coverage, absence, completeness, or support | DEC-0027; DEC-0049 | `IMPLEMENTED_TASK_VALIDATED` | `app.evidence_core.source_inventory` | DEV-0451 deterministic synthetic scope, ordering, zero, and failure tests | DEV-0451 |
| COV-ART-001 | Artifact coverage projects exact registered measurable-set observations while preserving zero, unsupported, failure, and nonexecution distinctions | DEC-0027; DEC-0045 | `IMPLEMENTED_TASK_VALIDATED` | `app.coverage.build_artifact_coverage` | DEV-0452 synthetic exact-set and denial tests | DEV-0452 |
| FOR-DISC-001 | Candidate Apple backup discovery is root-confined, source-specific, versioned, conflict-preserving, and separate from parsing/compatibility/support | DEC-0054; FOR-007 | `IMPLEMENTED_TASK_VALIDATED` | `app.discovery.apple_backup` | DEV-0501 synthetic presence, plist, manifest, conflict, scope, and determinism tests | DEV-0501 |
| FOR-META-001 | Governed Info, Manifest, and Status plist projections preserve source-specific typed claims without compatibility or completeness inference | DEC-0009; DEC-0054 | `IMPLEMENTED_TASK_VALIDATED` | `app.discovery.metadata_readers` | DEV-0502 through DEV-0504 focused and regression tests | DEV-0502 through DEV-0504 |
| FOR-META-002 | Encryption/version reconciliation uses the sole approved signal, preserves unresolved conflicts, and treats version as informative only | DEC-0009; DEC-0054 | `IMPLEMENTED_TASK_VALIDATED` | `encryption_version_reconciliation` | DEV-0506 focused tests | DEV-0506 |
| FOR-META-003 | Candidate identifier and product-version normalization is lossless, class-specific, versioned, deterministic, provenance-complete, and makes no identity or compatibility inference | DEC-0056; DEV-0406; FOR-010 | `IMPLEMENTED_TASK_VALIDATED` | `app.discovery.metadata_normalization` | DEV-0505 focused, dependent, regression, scope, and boundary tests | DEV-0505 |
| FOR-META-004 | Candidate metadata coverage projects exactly the approved six-item measurable set with factual states, exact counts, provenance, and permanent non-completeness limitations | DEV-0408; DEC-0056; FOR-010 | `IMPLEMENTED_TASK_VALIDATED` | `app.discovery.metadata_coverage` | DEV-0507 focused and regression tests | DEV-0507 |
| FOR-META-005 | Candidate metadata behavior is exercised by a deterministic repository-local corpus explicitly identified as synthetic and non-Apple-produced | QMS-TST-001; DEC-0056 | `IMPLEMENTED_TASK_VALIDATED` | `backend/tests/fixtures/apple_metadata` | DEV-0508 corpus schema, materialization, behavior, and support-boundary tests | DEV-0508 |
| FOR-META-006 | Candidate Apple backup metadata package integrates discovery, projections, normalization, reconciliation, coverage, provenance, limitations, and synthetic fixtures without support leakage | DEC-0054; DEC-0056; DEC-0058; FOR-010 | `IMPLEMENTED_TASK_VALIDATED` | `app.discovery`; synthetic corpus | DEV-0509 integrated suite; QMS-011; owner approval DEC-0058 | WP-0500 COMPLETE candidate infrastructure |
| FOR-MAN-001 | Candidate Manifest.db schema recognition is controlled-copy-only, read-only, profile-versioned, schema-only, deterministic, provenance-complete, and fail-closed without support inference | DEC-0008; DEC-0059; FOR-011 | `IMPLEMENTED_TASK_VALIDATED` | `app.manifest.schema_profile` | DEV-0601 synthetic schema, controlled-copy, scope, fingerprint, and boundary tests | DEV-0601 |
| FOR-MAN-002 | Candidate Files-table access is controlled-copy-only, read-only, ROWID-located, keyset-paginated, raw-value-preserving, resource-governed, cancellable, and provenance-complete without interpretation | DEC-0060; FOR-011; FOR-012 | `IMPLEMENTED_TASK_VALIDATED` | `app.manifest.files_query` | DEV-0602 synthetic raw-row, locator, pagination, scope, failure, and boundary tests | DEV-0602 |
| FOR-MAN-003 | Candidate Files query v2 separates completion/termination/resource/value states; bounds default BLOB access; enforces deterministic byte/memory estimates, monotonic time, and hierarchical concurrency without changing v1 | DEC-0061; DEC-0062; FOR-013 | `OWNER_APPROVED_CANDIDATE` | `app.manifest.files_query_v2` | DEV-0602A focused, integration, isolation, resource, and regression validation; QMS-012 | DEV-0602A COMPLETE; no support effect |
| FOR-MAN-004 | Generic candidate identifier framework and Manifest fileID v1 preserve raw dynamic types/provenance, recognize exact 40-ASCII-hex syntax, permit only declared transformations, and allow only caller-directed linear bounded comparison without physical/hash/duplicate conclusions | DEC-0063; DEC-0064; FOR-014 | `OWNER_APPROVED_CANDIDATE` | `app.manifest.identifier_normalization` | DEV-0603 40-scenario synthetic corpus, v1/v2 integration, comparison/resource/isolation, 487-test regression; QMS-013 | DEV-0603 COMPLETE; no support effect |
| FOR-MAN-005 | Candidate Manifest domain v1 preserves exact raw/dynamic-type/provenance observations, applies only exact case-sensitive grammar, and keeps unknown/malformed forms and semantic limitations explicit | DEC-0065; DEC-0066; FOR-015 | `OWNER_APPROVED_CANDIDATE` | `app.manifest.domain_normalization` | DEV-0604 33 focused, 113 combined Manifest, 520 backend regression; QMS-014 | DEV-0604 COMPLETE; no support effect |
| FOR-MAN-006 | Candidate relativePath v1 preserves exact raw/provenance, distinguishes unsafe lexical states, requires explicit resource ceilings, and performs no repair or filesystem resolution | DEC-0067; DEC-0068; FOR-016 | `OWNER_APPROVED_CANDIDATE` | `app.manifest.relative_path_normalization` | DEV-0605 23 focused, 136 combined Manifest, 543 backend; QMS-015 | DEV-0605 COMPLETE; no support effect |
| FOR-MAN-007 | Candidate Files.flags v1 preserves raw INTEGER/provenance and bounded set-bit positions while assigning no unapproved meaning | DEC-0069; DEC-0070; FOR-017 | `OWNER_APPROVED_CANDIDATE` | `app.manifest.flags_observation` | DEV-0606 17 focused, 153 combined Manifest, 560 backend; QMS-016 | DEV-0606 COMPLETE; no support effect |
| FOR-MAN-008 | Candidate Files.file BLOB v1 recognizes and syntactically decodes only bounded bplist00 without native deserialization, class instantiation, field meaning, or support | DEC-0071; DEC-0072; FOR-018 | `OWNER_APPROVED_CANDIDATE` | `app.manifest.metadata_blob` | DEV-0607 19 focused, 172 combined Manifest, 579 backend; QMS-017 | DEV-0607 COMPLETE; no support effect |
| FOR-MAN-009 | Candidate reconciliation v1 separates repetition patterns while permanently withholding duplicate/orphan/missing/absence conclusions without a complete physical universe | DEC-0073; DEC-0074; FOR-019 | `OWNER_APPROVED_CANDIDATE` | `app.manifest.reconciliation_semantics` | DEV-0609 13 focused, 185 combined Manifest, 592 backend; QMS-018 | DEV-0609 COMPLETE; no support effect |
| FOR-MAN-010 | Candidate inventory coverage v1 preserves immutable complete provenance and independent factual scope/completion/termination/resource/mutation/compatibility/comparison/absence dimensions; continuation composition and absence eligibility fail closed | DEC-0075; FOR-020 | `IMPLEMENTED_TASK_VALIDATED` | `app.manifest.inventory_coverage` | DEV-0608 41-scenario synthetic corpus and full matrix; QMS-019 | DEV-0608; no support effect |
| FOR-MAN-011 | Manifest candidate profiles are covered by a deterministic project-original synthetic corpus with complete test-asset provenance/custody/distribution, SHA-256 integrity, regeneration, matrix, and fail-closed source controls | DEC-0077; FOR-021 | `IMPLEMENTED_TASK_VALIDATED` | `app.manifest.corpus_governance`; fixed-root generator; corpus manifest | DEV-0610 80 focused tests and full regression; QMS-020 | DEV-0610; synthetic characterization only |
| FOR-MAN-012 | The Manifest workstream has a deterministic internal Markdown/JSON report with separate readiness levels, bounded claims, complete task/profile/validation/corpus traceability, and no support disposition | DEC-0079; DEC-0080 | `OWNER_APPROVED_CANDIDATE` | `app.manifest.validation_report`; fixed-input report generator; DEV-0611 report package | 63 focused, 385 Manifest, 776 backend; QMS-021 | DEV-0611 COMPLETE; no support effect |
| FOR-PHY-001 | Candidate physical inventory is authorized-root-confined, read-only, depth/profile-bounded, type-explicit, deterministic, resource-governed, and locator/provenance complete | DEC-0081; DEC-0082; FOR-022 | `OWNER_APPROVED_CANDIDATE` | `app.physical_inventory.inventory` | DEV-0621 focused and regression tests | DEV-0621 COMPLETE; no support effect |
| FOR-PHY-002 | Eligible physical-object hashing uses the existing SHA-256 integrity registry with root/scope checks, byte ceilings, pre/post stat, immutable provenance, and explicit instability/failure outcomes | DEC-0081; DEV-0622 acceptance | `CANDIDATE_IMPLEMENTED` | `app.physical_inventory.hashing` | DEV-0622 focused, integration, and regression tests | No authenticity, compatibility, artifact, or support inference |
| FOR-PHY-003 | Canonical Manifest fileIDs resolve only against same-scope candidate physical filename observations with exact provisional rules and explicit complete/partial/failure outcomes | DEC-0081; FOR-023 | `CANDIDATE_IMPLEMENTED` | `app.physical_inventory.resolution` | DEV-0623 focused, integration, regression | Synthetic characterization only; no content or support inference |
| FOR-PHY-004 | Physical coverage is a separate scoped observation universe with explicit complete/partial no-match counts and prohibited absence/deletion/duplicate/orphan conclusions | DEC-0081; DEV-0624 acceptance | `CANDIDATE_IMPLEMENTED` | `app.physical_inventory.coverage` | DEV-0624 focused and regression | Counts are factual observations only |
| COV-GOV-002 | Coverage never equates backup absence with device absence, deletion, concealment, destruction, or spoliation | DEC-0027; AGENTS.md | `DOCUMENTED_CONTROL` | WP-0450 forensic rules | Future adversarial coverage tests | DEV-0453, DEV-0454, DEV-0458 |
| COV-GOV-003 | Percentages describe only a defined measurable set and never all device evidence | DEC-0027 | `DOCUMENTED_CONTROL` | WP-0450 governance definition | Future denominator tests | DEV-0452, DEV-0458 |
| CLD-GOV-001 | Cloud evidence remains a separate future source family and iCloud device backup is not complete iCloud-account acquisition | DEC-0027 | `DOCUMENTED_CONTROL` | WP-1900 placeholder; FOR-009 | Separate future approval package | WP-1900 |
| SEC-TEN-001 | Define a stable neutral tenant identity before membership, case, or evidence authorization | ARC-001 §§7, 10, 12; DEV-0301 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Immutable `Tenant`; additive `TenantModel` | DEV-0301 contract/metadata/boundary tests | DEV-0301; migration DEV-0308 |
| SEC-IDN-001 | Represent authenticated user/service identities and tenant-scoped role relationships without implicit global access | ARC-001 §§7, 10, 12; DEV-0302 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Immutable Principal/TenantMembership and additive ORM contracts | DEV-0302 domain/scope/foreign-key tests | DEV-0302; policy DEV-0310; migration DEV-0308 |
| SEC-CASE-001 | Bind every supported-boundary case identity to exactly one tenant while preserving legacy isolation | ARC-001 §§7, 10, 12; DEV-0303 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Immutable SecurityCase; separate SecurityCaseModel | DEV-0303 domain/FK/legacy-separation tests | DEV-0303; migration DEV-0308 |
| SEC-SRC-001 | Bind every supported evidence-source identity to one tenant and a case in that same tenant | ARC-001 §§7, 10, 12; DEV-0305 acceptance | `IMPLEMENTED_TASK_VALIDATED` | EvidenceSource factory; composite tenant/case ORM foreign key | DEV-0305 cross-tenant relational denial tests | DEV-0305; migration DEV-0308 |
| SEC-AUD-002 | Attribute evidence-relevant audit events to a tenant membership principal and prohibit cross-tenant attribution | ARC-001 §§7, 10; DEV-0306 acceptance | `IMPLEMENTED_TASK_VALIDATED` | AuditActorContext/TenantAuditService over WP-0250 audit | DEV-0306 matching/mismatch/cross-tenant tests | DEV-0306; denial policy DEV-0310 |
| FOR-PROV-001 | Retain provenance from every normalized record to its source artifact and stable source record | AGENTS.md; FOR-004 §5 | `PARTIAL_UNVALIDATED` | `NormalizedEvent` and `EvidenceEvent` contain provenance-like fields without an enforced locator contract | Persistence tests verify storage, not locator resolvability | DEV-0301; DEV-0302 |
| FOR-PROV-005 | Retain tenant/case-scoped intake lineage from controlled copy through source artifact to evidence source | ARC-001 §5; ARC-002; DEC-0011 | `IMPLEMENTED_TASK_VALIDATED` | DEV-0207 adopts WP-0250 relational provenance nodes, edges, and validation | Synthetic resolution, dangling, cycle, cross-tenant, and cross-case tests | DEV-0207; DEV-0210 integration |
| FOR-PROV-002 | Preserve original values separately from normalized values | AGENTS.md; FOR-004 §5 | `PARTIAL_UNVALIDATED` | Backend stores `raw_values_json` when supplied; legacy normalization does not guarantee a complete raw envelope | `backend/tests/test_persistence.py` covers supplied synthetic raw values only | DEV-0305 |
| FOR-PROV-003 | Tie every parser result to parser version, schema fingerprint, execution record, and source hashes | AGENTS.md; FOR-006 §8 | `APPROVED_UNIMPLEMENTED` | Legacy parser versions are placeholders; no parser-run entity exists | No execution-record tests | DEV-0303; DEV-0304 |
| FOR-PROV-004 | Make every displayed evidentiary assertion resolvable to inspectable source records | AGENTS.md AI rules; PRD-007 §10 | `APPROVED_UNIMPLEMENTED` | Normalized IDs exist, but there is no citation resolver/source inspection contract | No citation resolution tests | Phase 5/6 tasks unassigned |
| FOR-FAIL-001 | Record unreadable, malformed, unknown, unsupported, omitted, and failed data explicitly | AGENTS.md; FOR-006 §9 | `PARTIAL_UNVALIDATED` | Legacy error logging exists but helpers can silently return empty values | Characterization tests do not cover complete failure taxonomy | DEV-0105; DEV-0210 |
| FOR-FAIL-002 | Distinguish successful zero records from parser failure | AGENTS.md; FOR-004 §4; FOR-006 §9 | `APPROVED_UNIMPLEMENTED` | Current empty-result behavior can represent multiple outcomes | No zero-record-versus-failure suite | DEV-0105; DEV-0303; DEV-0304 |
| FOR-STS-001 | Use the controlled processing result statuses only | AGENTS.md Artifact support statuses; FOR-004 §4 | `PARTIAL_UNVALIDATED` | Legacy and backend coverage vocabularies do not preserve every controlled distinction | No status-contract tests | DEV-0105; DEV-0304 |

## 6. SQLite and timestamp requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| FOR-SQL-001 | Analyze SQLite only from controlled working copies, never source evidence directly | AGENTS.md SQLite handling; PRD-007 §10 | `IMPLEMENTED_TASK_VALIDATED` | DEV-0205 exposes read-only/query-only SQLite inspection only on verified controlled copies; legacy direct-source behavior remains quarantined | Synthetic read/write-denial, root isolation, and post-use verification tests | DEV-0205; DEV-0210 integration |
| FOR-SQL-002 | Preserve and account for main DB, WAL, SHM, and rollback journal companions | AGENTS.md SQLite handling; FOR-004 §5 | `IMPLEMENTED_TASK_VALIDATED` | Exact-name main, WAL, SHM, and rollback-journal relationships are copied and audited | All-companion and companion-set mutation tests | DEV-0205 |
| FOR-SQL-003 | Distinguish logical backup records from physical/deleted-data recovery | AGENTS.md SQLite handling; PRD-007 §7 | `DOCUMENTED_CONTROL` | Deleted-data recovery is excluded; legacy generic parsing remains quarantined | DEC-0001 and FOR-006 | DEV-0304 |
| FOR-TIME-001 | Preserve original timestamp value, format, source field, conversion method, precision, and limitations | AGENTS.md Time handling; FOR-004 §5 | `PARTIAL_UNVALIDATED` | Legacy models contain timestamps but not a uniform complete provenance envelope | Existing self-checks do not validate full timestamp provenance | DEV-0306 |
| FOR-TIME-002 | Normalize comparable timestamps to UTC without silently assuming a timezone | AGENTS.md Time handling | `PARTIAL_UNVALIDATED` | `safe_fromtimestamp()` uses host-local behavior and several paths create naive datetimes | No timezone-selection/unknown-timezone suite | DEV-0306 |
| FOR-TIME-003 | Display local time only when timezone is known or explicitly selected | AGENTS.md Time handling | `APPROVED_UNIMPLEMENTED` | No accepted UI/display timezone contract exists | No display tests | DEV-0306; frontend task unassigned |

## 7. Parser quarantine and support requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| FOR-QTN-001 | Use a separate explicit, versioned supported-parser registry | FOR-006 §3 | `IMPLEMENTED_TASK_VALIDATED` | `app.support.SupportedParserRegistry`; empty supported composition | DEV-0304 AC-02 through AC-04 | DEV-0304 |
| FOR-QTN-002 | Disable every parser by default unless approved for its declared profile | FOR-006 §4 | `IMPLEMENTED_TASK_VALIDATED` | Empty composition and exact disposition/identity/profile authorization | DEV-0304 AC-03; disposition matrix | DEV-0304 |
| FOR-QTN-003 | Prevent quarantined output from supported storage, search, AI, reports, citations, and coverage | FOR-006 §6; DEC-0001 | `PARTIAL_UNVALIDATED` | DEV-0101 excludes legacy routes; DEV-0304 output gate rejects unissued authorization, non-success, incomplete provenance, and unreconciled coverage | Gate tests pass; downstream stores/search/AI/reports do not yet exist | Phase 5–7 tasks |
| FOR-QTN-004 | Promote a parser only after complete profile validation, traceability, tests, documentation, and owner approval | AGENTS.md All-or-nothing support rule; FOR-006 §7 | `DOCUMENTED_CONTROL` | No parser is promoted | FOR-004 and explicit owner gate | Per-artifact Phase 4 tasks |
| FOR-QTN-005 | Fail closed on unknown schemas and prohibit generic-parser fallback as supported evidence | FOR-006 §9 | `IMPLEMENTED_TASK_VALIDATED` | Exact schema authorization; supported registry has no generic fallback or legacy import | DEV-0304 unknown-profile and static-boundary tests | DEV-0304; per-artifact tasks |
| FOR-QTN-006 | Retain legacy CLI only as a compatibility/characterization surface unless separately approved | FOR-006 §10; PRD-007 §8 | `DOCUMENTED_CONTROL` | Legacy CLI remains present | Distribution decision remains owner-controlled | DEV-0304; owner decision if distribution proposed |

## 8. Security requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| SEC-AUT-001 | Authenticate users and services before case access | AGENTS.md Security rules; PRD-007 §10 | `APPROVED_UNIMPLEMENTED` | No authentication principal or middleware identified | No authentication tests | Phase 8 task unassigned |
| SEC-AUT-002 | Enforce authorization and case/tenant isolation server-side | AGENTS.md Security rules; PRD-007 §10 | `APPROVED_UNIMPLEMENTED` | Case IDs filter queries but any caller may provide any case ID | No cross-case/cross-tenant tests | DEV-0310; DEV-0307 |
| SEC-INP-001 | Validate untrusted uploaded files and paths; prevent traversal and unsafe execution | AGENTS.md Security rules | `PARTIAL_UNVALIDATED` | DEV-0201 adds lexical/resolved root confinement and link/reparse rejection; upload and structural validation do not exist | DEV-0201 root escape, invalid-root, link-boundary, and input-type tests | DEV-0202; security task unassigned |
| SEC-SEC-001 | Never commit or log credentials, passwords, tokens, production secrets, or decrypted secret values | AGENTS.md Security rules; PRD-007 §5 | `DOCUMENTED_CONTROL` | No initial password flow exists; development configuration requires later review | No secret scan or log-redaction suite | DEV-0104; security task unassigned |
| SEC-AUD-001 | Record security- and evidence-relevant actions without sensitive secret content | FOR-006 §8; AGENTS.md Security rules | `PARTIAL_UNVALIDATED` | DEV-0206 adopts the WP-0250 candidate audit taxonomy for registered intake evidence; authorization and durable audit integration remain unimplemented | Synthetic DEV-0206 intake taxonomy/scope/immutability tests and WP-0250 audit tests | DEV-0206; DEV-0310 |

## 9. AI, reporting, and review requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| AI-GRD-001 | Ground AI answers only in authorized, supported case records | AGENTS.md AI rules; PRD-007 §10 | `LEGACY_QUARANTINED` | Legacy `build_case_knowledge()` has no approved-record or authorization gate | Characterization tests are not support validation | Phase 6 task unassigned |
| AI-CIT-001 | Require material factual claims to cite stable internal record identifiers | AGENTS.md AI rules | `PARTIAL_UNVALIDATED` | Legacy prompts request identifiers but output is not enforced or resolved | No citation conformance/evaluation suite | Phase 6 task unassigned |
| AI-UNC-001 | Separate artifact facts from interpretation and state material uncertainty and limitations | AGENTS.md AI rules | `LEGACY_QUARANTINED` | Legacy reports/prompts contain some cautionary text | No approved evaluation dataset | Phase 6/7 tasks unassigned |
| AI-ABS-001 | Never claim that missing evidence proves an event did not occur | AGENTS.md AI rules | `DOCUMENTED_CONTROL` | Some legacy text states limitations, but no product-wide validator exists | No negative-claim evaluation suite | Phase 6/7 tasks unassigned |
| AI-DER-001 | Keep model output as derived work product and never overwrite evidence data | AGENTS.md AI rules | `PARTIAL_UNVALIDATED` | Legacy output is generated separately; no accepted storage/audit contract | No overwrite-boundary tests | Phase 6 task unassigned |
| RPT-LIM-001 | Make acquisition, coverage, unsupported-source, and evidentiary limitations attorney-readable | PRD-003; PRD-007 §10 | `LEGACY_QUARANTINED` | Legacy reporting contains limitations but consumes unapproved inputs | No accepted report fixture/golden test | Phase 7 task unassigned |

## 10. Quality and acceptance requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| QMS-TST-001 | Test success and explicit failure behavior with synthetic or lawfully distributable data only | AGENTS.md Testing requirements; FOR-006 §7 | `PARTIAL_UNVALIDATED` | Synthetic unit/characterization tests exist; required failure suites and Apple backup fixtures do not | `tests/`; `backend/tests/` | DEV-0106 and each implementation task |
| QMS-TST-002 | Verify deterministic output, malformed input, provenance, timestamps, parser fixtures, authorization, and regressions where applicable | AGENTS.md Testing requirements | `PARTIAL_UNVALIDATED` | Narrow deterministic and path tests exist | Required complete suite absent | DEV-0106 and owning feature tasks |
| QMS-ACC-001 | Define explicit acceptance criteria and satisfy implementation, validation, tests, documentation, provenance, and failure handling before support | AGENTS.md All-or-nothing support rule; FOR-004 §1 | `DOCUMENTED_CONTROL` | Downstream task-specific acceptance documents are absent | No artifact acceptance review has occurred | Every downstream task |
| QMS-TRC-001 | Update traceability, documentation, task ledger, and completion evidence for every task | AGENTS.md Development method | `DOCUMENTED_CONTROL` | DOC-002 and DEV-009 establish the control surfaces | Document validation for DEV-0003 | Every task |
| QMS-RDY-001 | Automatically reevaluate dependencies and promote eligible tasks through dependency-satisfied to ready while preserving mandatory gates | DEC-0051; autonomous charter §21 | `GOVERNANCE_IMPLEMENTED` | AGENTS, BACKLOG, DEV-009, DEV-011, charter | Governance reconciliation and clean local commit | Every active task |
| QMS-SUP-001 | Every Supported capability permanently records Owner Decision ID, Validation Package ID, Acceptance Record IDs, Promotion Date, and Current Support Status | DEC-0014; AGENTS.md; FOR-004 §6 | `DOCUMENTED_CONTROL` | Permanent governance rule; no capability is currently promoted | Future promotion package must fail closed if any field is absent | Every support-promotion gate |
| QMS-SUP-002 | The supported processing registry enforces complete permanent promotion metadata and remains empty until a separate promotion decision | QMS-SUP-001; ARC-002 | `IMPLEMENTED_TASK_VALIDATED` | `app.support.registry.ApprovedParserEntry`; empty production composition | DEV-1101 synthetic traceability and quarantine tests | DEV-1101 |
| QMS-SUP-003 | Supported registry composition cannot import or enumerate quarantined legacy plugins | ARC-001; FOR-006 | `IMPLEMENTED_TASK_VALIDATED` | Separate `app.support` package; legacy access confined to `app.services.case_processing` | DEV-1102 static/runtime isolation tests | DEV-1102 |
| QMS-SUP-004 | Future supported parser execution fails closed before calls unless exact registry, controlled-input, integrity, provenance, identity, schema, coverage, and limitation controls pass | ARC-001; ARC-002 | `IMPLEMENTED_TASK_VALIDATED` | `app.processing.SupportedParserExecutor` | DEV-1103 synthetic denial, execution-order, zero, and safe-failure tests | DEV-1103 |
| PROC-RUN-001 | Processing lifecycle distinguishes requested, authorized, running, complete, complete-zero, partial, failed, and cancelled outcomes | ARC-001; DEC-0002 | `IMPLEMENTED_TASK_VALIDATED` | `app.processing.ProcessingRunLifecycle` | DEV-1104 transition matrix | DEV-1104 |
| PROC-COV-001 | Processing coverage aggregation preserves factual states and unknown counts without inferring evidentiary completeness | DEC-0045; ARC-001 | `IMPLEMENTED_TASK_VALIDATED` | `app.processing.aggregate_coverage` | DEV-1105 synthetic aggregation tests | DEV-1105 |
| PROC-FAIL-001 | Failure aggregation preserves safe issue/partial identities and closed factual counts without evidentiary conclusions | DEC-0046; ARC-001 | `IMPLEMENTED_TASK_VALIDATED` | `app.processing.aggregate_failures` | DEV-1106 synthetic aggregation tests | DEV-1106 |
| PROC-IDEM-001 | Exact versioned request idempotency prevents duplicate execution without reusing run identity or erasing retry/rerun provenance | DEC-0052; ARC-001; ARC-002 | `IMPLEMENTED_TASK_VALIDATED` | `app.processing.idempotency`; migration 0005 | DEV-1107 focused concurrency, retry/rerun, isolation, recovery, and migration tests | DEV-1107 |
| PROC-PIPE-001 | Candidate processing pipeline integrates registry denial, execution, lifecycle, coverage, failures, idempotency, cancellation, and audit without support leakage | ARC-001; ARC-002; DEC-0055 | `IMPLEMENTED_TASK_VALIDATED` | `app.processing` | DEV-1110 integration tests; QMS-010; owner approval DEC-0055 | WP-1100 COMPLETE candidate infrastructure |

## 11. DEV-0101 backend-scaffold requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| DEV-0101-R01 | Default factory is the supported-path composition root | DEV-0101 acceptance §5 | `IMPLEMENTED_TASK_VALIDATED` | `backend/app/main.py` | `backend/tests/test_scaffold_boundaries.py` | DEV-0101 |
| DEV-0101-R02 | Default API exposes health only | DEV-0101 acceptance §5 | `IMPLEMENTED_TASK_VALIDATED` | `backend/app/api/router.py` | Default OpenAPI and route-negative tests | DEV-0101 |
| DEV-0101-R03 | Default composition has no legacy-processing import dependency | DEV-0101 acceptance §5 | `IMPLEMENTED_TASK_VALIDATED` | Supported main/router import graph | Static AST boundary test | DEV-0101 |
| DEV-0101-R04 | Legacy API is reachable only through an explicit compatibility factory | DEV-0101 acceptance §5 | `LEGACY_QUARANTINED` | `backend/app/legacy/main.py`; `backend/app/legacy/router.py` | Legacy route characterization test | DEV-0101 acceptance review |
| DEV-0101-R05 | Legacy API warns that it is unsupported and characterization-only | DEV-0101 acceptance §5 | `LEGACY_QUARANTINED` | Legacy FastAPI title and description | Metadata assertion | DEV-0101 acceptance review |
| DEV-0101-R06 | Structured errors, settings, sessions, and Alembic scaffold remain intact | DEV-0101 acceptance §5 | `IMPLEMENTED_TASK_VALIDATED` | Existing backend core and migration modules unchanged | Backend regression suite | DEV-0101 |
| DEV-0101-R07 | Repository ignores evidence, secrets, databases, companions, and generated data without conflict debris | DEV-0101 acceptance §5 | `IMPLEMENTED_TASK_VALIDATED` | `.gitignore` | Repository-safety test | DEV-0101 |
| DEV-0101-R08 | Scaffold tests are deterministic and synthetic | DEV-0101 acceptance §5 | `IMPLEMENTED_TASK_VALIDATED` | In-memory SQLite and temporary-path tests | Backend and characterization suites | DEV-0101 |
| DEV-0101-R09 | Scaffold introduces no migration or support promotion | DEV-0101 acceptance §5 | `DOCUMENTED_CONTROL` | No migration added; default evidence routes absent | Git diff and acceptance review | DEV-0101 |

## 12. Baseline gaps and controls

The following governing documents remain empty placeholders and cannot yet
supply detailed requirements or acceptance criteria:

- DOC-000 document register;
- PRD-001 product requirements;
- PRD-004 limitations;
- FOR-001, FOR-002, and FOR-005;
- AI-001, AI-003, and AI-005;
- SEC-001 threat model;
- QMS-003 definition of done; and
- QMS-004 test strategy.

The matrix marks affected work as unimplemented, unassessed, or assigned to a
later task. It does not fill remaining policy gaps by inference.

## 13. DEV-0201 Apple backup input-adapter requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| DEV-0201-R01 | Supported adapter has no legacy dependency | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | `backend/app/intake/apple_backup.py` | AC-11 | DEV-0201 owner review |
| DEV-0201-R02 | Configured evidence roots fail closed unless valid directories without link/reparse boundaries | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | `AppleBackupInputAdapter._validate_roots()` | AC-12 | DEV-0201 owner review |
| DEV-0201-R03 | Adapter uses the exact six controlled outcomes | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | `InputAdapterStatus` | AC-01 | DEV-0201 owner review |
| DEV-0201-R04 | Result preserves adapter-level source provenance and audit fields | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | `InputInspectionResult` | AC-02; AC-08 | DEV-0201 owner review |
| DEV-0201-R05 | Root escape and link/reparse components fail validation | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | Adapter boundary checks | AC-06 | DEV-0201 owner review |
| DEV-0201-R06 | Adapter performs no writes, parsing, hashing, copying, or recursive traversal | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | Metadata-only implementation | AC-10; AC-14 | DEV-0201 owner review |
| DEV-0201-R07 | Missing input and existing unsupported input are distinct | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | `MISSING` and `UNSUPPORTED_INPUT` branches | AC-04; AC-05 | DEV-0201 owner review |
| DEV-0201-R08 | Successful empty-directory inspection is distinct and makes no support claim | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | `READY_ZERO_RESULTS` branch and limitations | AC-03 | DEV-0201 owner review |
| DEV-0201-R09 | Filesystem operational errors become structured processing failures | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | Structured `PROCESSING_FAILED` branches | AC-07 | DEV-0201 owner review |
| DEV-0201-R10 | Fixed inputs, clock, and correlation ID produce deterministic results | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | Injected clock/correlation and frozen result | AC-09 | DEV-0201 owner review |
| DEV-0201-R11 | Ready results explicitly leave structure, encryption, hashing, and support unassessed | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | `UNASSESSED_LIMITATIONS` | AC-08; AC-14 | DEV-0201 owner review |
| DEV-0201-R12 | Tests use synthetic temporary fixtures and prove source immutability | DEV-0201 acceptance §4 | `IMPLEMENTED_TASK_VALIDATED` | `backend/tests/test_apple_backup_input_adapter.py` | AC-10; AC-13 | DEV-0201 owner review |

## 14. Maintenance rules

1. Assign a stable requirement ID before implementing requirement-driven
   behavior.
2. Record the governing source, implementation location, verification
   evidence, owner task, and current traceability status.
3. Never change a requirement merely to match existing code.
4. Never use `PARTIAL_UNVALIDATED` or `LEGACY_QUARANTINED` as support evidence.
5. Add separate rows when a requirement has materially different acceptance,
   security, provenance, or failure behavior.
6. Update this matrix in the same task that changes behavior or validation.
7. Record owner-controlled decisions in DOC-003.
8. A parser or artifact promotion requires its complete FOR-004 profile and a
   separate owner approval; updating this matrix cannot perform promotion.

## 15. DEV-0202 controlled-copy and profile requirements

DEV-0202 Stage A is limited by DEC-0006. FOR-007 is proposed and is not an
approved runtime requirement source.

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| DEV-0202-R01 | Copy only main and exact supported companion names | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | `ControlledCopyManager` companion discovery | AC-01; AC-02 passed | DEV-0202 Stage A |
| DEV-0202-R02 | Require regular link-free files inside evidence source | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Controlled-copy path validation | AC-03 passed | DEV-0202 Stage A |
| DEV-0202-R03 | Record paths, sizes, and pre/copy/post SHA-256 | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | `ControlledFileRecord` | AC-01; AC-04; AC-12 passed | DEV-0202 Stage A |
| DEV-0202-R04 | Fail unless all hashes match | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Copy verification failure path | AC-01; AC-04 passed | DEV-0202 Stage A |
| DEV-0202-R05 | Detect companion-set mutation | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Companion rediscovery check | AC-02; AC-05 passed | DEV-0202 Stage A |
| DEV-0202-R06 | Create temporary workspace outside evidence source | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Workspace boundary check | AC-06 passed | DEV-0202 Stage A |
| DEV-0202-R07 | Preserve companion basenames together | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Single controlled workspace | AC-02 passed | DEV-0202 Stage A |
| DEV-0202-R08 | Open copied SQLite read-only/query-only | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | `ControlledSQLiteCopy.read_only_uri`; `inspect_sqlite_structure()` | AC-07 passed | DEV-0202 Stage A |
| DEV-0202-R09 | Prohibit mutation and source SQLite access | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Controlled-copy-only SQLite boundary | AC-07; AC-13 passed | DEV-0202 Stage A |
| DEV-0202-R10 | Verify working hashes after SQLite use | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Post-inspection hash verification | AC-08 passed | DEV-0202 Stage A |
| DEV-0202-R11 | Delete workspace unless retained explicitly for a test | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Context cleanup and test-retention flag | AC-09; AC-11 passed | DEV-0202 Stage A |
| DEV-0202-R12 | Record cleanup outcome deterministically | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | `ControlledCopyAudit`; `CleanupStatus` | AC-09 through AC-12 passed | DEV-0202 Stage A |
| DEV-0202-R13 | Fail closed with structured safe audit data | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | `ControlledCopyError` | AC-03 through AC-05; AC-10 passed | DEV-0202 Stage A |
| DEV-0202-R14 | No legacy, Apple compatibility, or API integration | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Isolated `app.intake.controlled_copy` module | AC-13; AC-15 passed | DEV-0202 Stage A |
| DEV-0202-R15 | Synthetic fixtures only | DEV-0202 acceptance §3 | `IMPLEMENTED_TASK_VALIDATED` | Temporary generated SQLite/byte fixtures | AC-14 passed | DEV-0202 Stage A |
| DEV-0202-R16 | Preserve nine distinct validation outcomes and precedence | DEC-0007; FOR-007 | `IMPLEMENTED_TASK_VALIDATED` | `BackupValidationOutcome`; `AppleBackupValidator.validate()` | Stage-B outcome tests | DEV-0202 Stage B |
| DEV-0202-R17 | Establish candidate identity independently from SQLite validity | DEC-0008 | `IMPLEMENTED_TASK_VALIDATED` | Recognized-field identity observations | Invalid/valid SQLite identity matrix tests | DEV-0202 Stage B |
| DEV-0202-R18 | Distinguish missing, malformed, insufficient, and operational plist outcomes | DEC-0007; DEC-0008 | `IMPLEMENTED_TASK_VALIDATED` | Plist classification branches | Missing/malformed/read-failure tests | DEV-0202 Stage B |
| DEV-0202-R19 | Apply case-sensitive `SnapshotState=finished` rule | DEC-0007 | `IMPLEMENTED_TASK_VALIDATED` | Snapshot-state branch | Finished/non-finished/missing tests | DEV-0202 Stage B |
| DEV-0202-R20 | Use only Boolean `Manifest.plist.IsEncrypted`; missing/wrong-type is indeterminate and operational failure is validation failure | DEC-0007; DEC-0009 | `IMPLEMENTED_TASK_VALIDATED` | Encryption-state and plist-read failure branches | True/false/missing/wrong-type/read-failure tests | DEV-0202 Stage B |
| DEV-0202-R21 | Inspect Manifest SQLite only through verified controlled copy | DEC-0007; ARC-001 | `IMPLEMENTED_TASK_VALIDATED` | `ControlledCopyManager` integration | Corruption/integrity/cleanup tests | DEV-0202 Stage B |
| DEV-0202-R22 | Validate `MANIFEST_FILES_V1` without table/column-order sensitivity | DEC-0007 | `IMPLEMENTED_TASK_VALIDATED` | Case-folded schema inspection | Missing table/each column/additional schema tests | DEV-0202 Stage B |
| DEV-0202-R23 | Record canonical schema JSON and SHA-256 fingerprint | DEC-0007 | `IMPLEMENTED_TASK_VALIDATED` | `_inspect_manifest()` | Deterministic fingerprint test | DEV-0202 Stage B |
| DEV-0202-R24 | Record explanation, observations, provenance, limitations, and deterministic audit | DEV-0202 owner scope | `IMPLEMENTED_TASK_VALIDATED` | `BackupValidationResult` | Canonical audit test | DEV-0202 Stage B |
| DEV-0202-R25 | Keep validator isolated from API, legacy, and artifact parsing | DEC-0007; AGENTS.md | `IMPLEMENTED_TASK_VALIDATED` | `app.intake.backup_validator` | Static boundary and regression tests | DEV-0202 Stage B |
| DEV-0211-R01 | Do not implement secondary encryption indicators until each is sourced, characterized, ordered, conflict-profiled, fixture-tested, and owner approved | DEC-0009 | `DOCUMENTED_CONTROL` | No secondary signal exists in the validator | Static boundary and DEV-0202 encryption tests | DEV-0211 deferred |
| DEV-0203-R01 | Consume only DEV-0202 validation results | DEV-0203 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `report_encryption_state()` typed input | AC-01 through AC-03 | DEV-0203 |
| DEV-0203-R02 | Report five closed encryption states distinctly | DEV-0203 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `BackupEncryptionState` | AC-01 through AC-03 | DEV-0203 |
| DEV-0203-R03 | Preserve raw Boolean and locator when present | DEV-0203 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `EncryptionStateReport` | AC-05 | DEV-0203 |
| DEV-0203-R04 | Only unencrypted is handoff-eligible, without support implication | DEV-0203 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `processing_eligible` | AC-04 | DEV-0203 |
| DEV-0203-R05 | Encrypted is reporting-only; no decryption or parsing | DEV-0203 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Closed projection module | AC-04; AC-07 | DEV-0203 |
| DEV-0203-R06 | Accept no password and infer no secondary signal | DEC-0009; DEV-0203 acceptance | `IMPLEMENTED_TASK_VALIDATED` | No source inspection or credential interface | AC-07 | DEV-0203 |
| DEV-0203-R07 | Preserve provenance, correlation, limitations, and deterministic audit | DEV-0203 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Report audit serialization | AC-05; AC-06 | DEV-0203 |
| DEV-0203-R08 | Add no API, migration, legacy dependency, persistence, or support | DEV-0203 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Isolated intake module | AC-07; regression suite | DEV-0203 |

## 16. DEV-0004 architecture-recommendation trace

## 15A. WP-0250 evidence-integrity requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| WP0250-ID | Stable application UUID distinct from content hashes | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | EvidenceObject/register service and relational model | UUID/domain tests | DEV-0251/0252 |
| WP0250-LIFE | Explicit atomic audited lifecycle | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | LifecycleService/TRANSITIONS | Transition/denial tests | DEV-0253 |
| WP0250-HASH | Immutable SHA-256 observation registry and verification | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | HashRegistry/MutationDetector | Known/mutation/history tests | DEV-0254/0255/0261 |
| WP0250-LOCK | Approved intent and application lock policy | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | EvidenceLockService | Conflict/stale/release tests | DEV-0256 |
| WP0250-CUST | Append-only tenant-scoped handling history without signature claim | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | CustodyService/model | Ordering/linkage/immutability tests | DEV-0257 |
| WP0250-AUD | Closed append-only audit taxonomy | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | AuditEventType/AppendOnlyAuditService | Event and immutability tests | DEV-0258 |
| WP0250-PROV | Relational complete tenant-scoped provenance and validation | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | ProvenanceService/models | Path/cycle/cross-tenant tests | DEV-0259/0260 |
| WP0250-POL | Mutation and policy enforcement block unsafe, legacy, unsupported, or broken-provenance processing | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | MutationDetector/IntegrityPolicy | Policy matrix tests | DEV-0261/0262 |
| WP0250-PARSER | Common typed parser contract and conformance harness; candidate is not supported | ARC-002; WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | EvidenceParser/ParserConformanceHarness | Synthetic conformance suite | DEV-0263/0264 |
| WP0250-E2E | Additive relational migration and deterministic end-to-end integrity package | WP-0250 | `IMPLEMENTED_TASK_VALIDATED` | Migration 0002 and E2E flow | Migration/regression checks | DEV-0265 |

ARC-001 was approved by DEC-0002 on 2026-07-24 and is an architecture
requirement source for downstream tasks. It addresses existing requirement IDs
as follows:

| Existing requirement group | ARC-001 recommendation |
|---|---|
| PRD-IN and PRD-SCP | Intake module, classification sequence, and legacy input separation in §§5.2 and 11 |
| FOR-INT and FOR-PROV | Trust boundaries and domain model in §§5–8 |
| FOR-FAIL and FOR-STS | Atomic parser execution and controlled statuses in §§5.4 and 9 |
| FOR-SQL and FOR-TIME | Controlled working-copy and normalized record contracts in §§5.3 and 8 |
| FOR-QTN | Separate composition roots, stores, registry snapshots, and architectural import tests in §§5.4–5.6 |
| SEC | Authorization context, tenant-owned entities, least privilege, and audit controls in §§7 and 10 |
| AI and RPT | One authorization-scoped supported-record query boundary and citation chain in §5.7 |
| QMS | Additive migration stages and boundary tests in §12 |

These references are architecture traceability evidence. They do not establish
runtime implementation, validation, or artifact support.

## 16E. DEV-0106 CI-gate requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0106-R01 | Least-privilege locked CI environment | DEV-0106 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `.github/workflows/ci.yml` | AC-01 through AC-03 | DEV-0106 |
| DEV-0106-R02 | Mandatory regression, architecture, compilation, and migration gates | MES-v1 Part 9; DEV-0106 acceptance | `IMPLEMENTED_TASK_VALIDATED` | CI job commands | AC-04 through AC-06 | DEV-0106 |
| DEV-0106-R03 | No deployment, mutation, evidence, or support effect | DEV-0106 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Read-only workflow definition | AC-07 | DEV-0106 |
| DEV-0106-R04 | Deterministic local validation of workflow structure | DEV-0106 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `test_ci_gate.py` | AC-08 | DEV-0106 |

## 16D. DEV-0105 structured-logging requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0105-R01 | Structured JSON operational logs with allowlisted metadata | DEV-0105 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `SafeJsonFormatter`; `log_event()` | AC-01; AC-02 | DEV-0105 |
| DEV-0105-R02 | Redact credentials and omit raw exception content | AGENTS.md; DEV-0105 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `redact()`; formatter omission policy | AC-03; AC-04 | DEV-0105 |
| DEV-0105-R03 | Preserve safe request correlation | MES-v1 Part 7; DEV-0105 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Structured DEV-0104 handler events | AC-05 | DEV-0105 |
| DEV-0105-R04 | Distinguish operational logs from immutable audit/custody records | ARC-002; DEV-0105 acceptance | `DOCUMENTED_CONTROL` | Module and acceptance documentation | AC-06 | DEV-0105 |
| DEV-0105-R05 | Add no evidence/API/migration/support behavior | DEV-0105 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Logging-boundary-only implementation | AC-07; AC-08 | DEV-0105 |

## 16C. DEV-0104 structured-error requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0104-R01 | Typed categories, stable codes, and one safe envelope | DEV-0104 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `ErrorCategory`; `ApiError`; `_response()` | AC-01; AC-02 | DEV-0104 |
| DEV-0104-R02 | Safe validation and framework error translation | MES-v1 Part 7; DEV-0104 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Registered validation and HTTP handlers | AC-03; AC-04 | DEV-0104 |
| DEV-0104-R03 | Hide unexpected exception content and retain correlation | AGENTS.md; DEV-0104 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Generic 500 response and UUID request ID | AC-05; AC-06 | DEV-0104 |
| DEV-0104-R04 | Preserve composition and add no product/support behavior | DEV-0104 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Error-boundary-only change | AC-07; AC-08 | DEV-0104 |

## 16B. DEV-0103 configuration requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0103-R01 | Closed environment and log-level vocabularies | DEV-0103 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `Environment`; `LogLevel`; `Settings` validators | AC-01 | DEV-0103 |
| DEV-0103-R02 | Parseable environment-appropriate database driver | DEV-0103 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Database URL and environment policy validators | AC-02; AC-04 | DEV-0103 |
| DEV-0103-R03 | Absolute, normalized, unique evidence roots | DEV-0103 acceptance; SEC-INP-001 | `IMPLEMENTED_TASK_VALIDATED` | Evidence-root validator | AC-03 | DEV-0103 |
| DEV-0103-R04 | Credential-safe deterministic diagnostics | AGENTS.md; DEV-0103 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Hidden database field; `safe_summary()` | AC-05; AC-06 | DEV-0103 |
| DEV-0103-R05 | No evidence inspection, API, migration, external service, or support effect | DEV-0103 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Configuration-only module change | AC-07; AC-08 | DEV-0103 |

## 16A. DEV-0102 reproducible-environment requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0102-R01 | Commit one exact runtime, development, build, and transitive Python resolution | BACKLOG WP-0100; DEV-0102 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `backend/requirements.lock` | AC-01; clean-environment install | DEV-0102 |
| DEV-0102-R02 | Fail deterministically on ranges, duplicates, or missing declared dependencies | DEV-0102 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `backend/scripts/verify_lock.py` | AC-02; AC-03; negative unit tests | DEV-0102 |
| DEV-0102-R03 | Use the same lock for container installation without editable or second-graph resolution | DEV-0102 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `backend/Dockerfile` | AC-04 static test | DEV-0102 |
| DEV-0102-R04 | Validate a non-editable application install in an isolated environment | DEV-0102 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Documented clean-install workflow | AC-05; `pip check`; import smoke test | DEV-0102 |
| DEV-0102-R05 | Preserve runtime, evidence boundaries, migrations, and support status | AGENTS.md; DEV-0102 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Dependency-only implementation | AC-06 through AC-08; regression suite | DEV-0102 |

## 16B. DEV-0308 additive migration requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0308-R01 | Add one linear migration for the validated security schema | DEV-0308 acceptance; ARC-001 | `IMPLEMENTED_TASK_VALIDATED` | `0003_security_foundation.py` | AC-01; AC-02; Alembic head/history | DEV-0308 |
| DEV-0308-R02 | Enforce tenant/case source linkage at the relational boundary | DEV-0305; DEV-0308 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Composite foreign key and unique case scope | AC-03 | DEV-0308 |
| DEV-0308-R03 | Keep migration additive and downgrade limited to new tables | ARC-001; DEV-0308 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Dependency-ordered upgrade/downgrade | AC-04; offline SQL | DEV-0308 |
| DEV-0308-R04 | Preserve evidence, API, parser, deployment, and support boundaries | AGENTS.md; DEV-0308 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Schema-only change | AC-07; diff review | DEV-0308 |

## 16C. DEV-0310 authorization requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0310-R01 | Deny closed without an exact explicit policy grant | DEC-0014; DEV-0310 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `AuthorizationService`; `PolicySnapshot` | AC-01; AC-02 | DEV-0310 |
| DEV-0310-R02 | Enforce tenant, case, and source scope before granting | AGENTS.md | `IMPLEMENTED_TASK_VALIDATED` | Authorization scope checks | AC-03; AC-04 | DEV-0310 |
| DEV-0310-R03 | Return safe traceable decisions | DEV-0310 acceptance | `IMPLEMENTED_TASK_VALIDATED` | `AuthorizationDecision` | AC-01; AC-05 | DEV-0310 |
| DEV-0310-R04 | Establish no implicit production policy or support effect | DEC-0014 | `IMPLEMENTED_TASK_VALIDATED` | Caller-supplied policy only | AC-07 | DEV-0310 |

## 16D. DEV-0307 isolation requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0307-R01 | Explicit grants never override tenant/resource scope | DEV-0307 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Authorization scope boundary | AC-01; AC-02 | DEV-0307 |
| DEV-0307-R02 | Cross-tenant audit attempts append nothing | AGENTS.md; DEV-0307 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Tenant audit boundary | AC-03 | DEV-0307 |
| DEV-0307-R03 | Use synthetic tests without runtime/support effect | DEV-0307 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Adversarial test module | AC-04; AC-05 | DEV-0307 |

## 16E. WP-0300 owner disposition

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| SEC-WP-001 | Candidate security foundation is permanently traceable to owner approval, validation, acceptance records, commits, limitations, and support state | DEC-0037 | `OWNER_APPROVED_CANDIDATE` | Acceptance Record Index WP-0300 section | QMS-008; DEV-0301 through DEV-0310 records | WP-0300 |
| SEC-AUTH-001 | Future protected boundaries authorize before content retrieval, transformation, export, or AI use | DEC-0037 | `APPROVED_UNIMPLEMENTED` | Governing decision and WP dependencies | Future boundary-specific tests | Owning future task |
| SEC-AUD-001 | Future security-sensitive boundaries emit safe structured audit events where applicable | DEC-0037 | `APPROVED_UNIMPLEMENTED` | Governing decision; WP-0250 taxonomy | Future boundary-specific tests | Owning future task |

## 16F. DEV-0401 processing-run requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0401-R01 | Immutable tenant/case/source-scoped run identity | ARC-001; WP-0400 | `IMPLEMENTED_TASK_VALIDATED` | `ProcessingRun` | AC-01; AC-02 | DEV-0401 |
| DEV-0401-R02 | Authorize before run creation and retain policy provenance | DEC-0037 | `IMPLEMENTED_TASK_VALIDATED` | `ProcessingRunService` | AC-03; AC-04 | DEV-0401 |
| DEV-0401-R03 | Separate candidate store metadata from legacy jobs | ARC-001 | `IMPLEMENTED_TASK_VALIDATED` | `SupportedProcessingRunModel` | AC-06 | DEV-0401 |
| DEV-0401-R04 | No lifecycle, parser, API, evidence, or support expansion | DEV-0401 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Bounded module | AC-07 | DEV-0401 |

## 16G. DEV-0402 source-artifact requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0402-R01 | Distinct immutable artifact identity with complete run/source scope | ARC-002; WP-0400 | `IMPLEMENTED_TASK_VALIDATED` | `SourceArtifact` | AC-01; AC-02 | DEV-0402 |
| DEV-0402-R02 | Authorize registration and reject mismatched run scope | DEC-0037 | `IMPLEMENTED_TASK_VALIDATED` | `SourceArtifactService` | AC-03; AC-04 | DEV-0402 |
| DEV-0402-R03 | Defer locators and prohibit presence-to-support inference | AGENTS.md; DEV-0402 acceptance | `IMPLEMENTED_TASK_VALIDATED` | Bounded identity contract | AC-05; AC-06 | DEV-0402 |
| DEV-0402-R04 | Separate candidate ORM metadata without migration/support effect | ARC-001 | `IMPLEMENTED_TASK_VALIDATED` | `SupportedSourceArtifactModel` | AC-07; AC-08 | DEV-0402 |

## 16H. DEV-0403 locator requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0403-R01 | Stable scoped locator identity | ARC-002; WP-0400 | `IMPLEMENTED_TASK_VALIDATED` | `SourceLocator` | AC-01 | DEV-0403 |
| DEV-0403-R02 | Preserve raw/normalized values and method separately | AGENTS.md | `IMPLEMENTED_TASK_VALIDATED` | Locator value fields | AC-02; AC-03 | DEV-0403 |
| DEV-0403-R03 | Fail closed on invalid values without filesystem/support inference | AGENTS.md | `IMPLEMENTED_TASK_VALIDATED` | Contract validation | AC-04; AC-05 | DEV-0403 |
| DEV-0403-R04 | Separate ORM metadata without migration/support effect | ARC-001 | `IMPLEMENTED_TASK_VALIDATED` | `SupportedSourceLocatorModel` | AC-06; AC-07 | DEV-0403 |

## 16I. Autonomous execution governance

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| GOV-AUT-001 | Continue through READY tasks and stop only for enumerated mandatory decisions | Autonomous Execution Charter; DEC-0041 | `APPROVED_IMPLEMENTED_GOVERNANCE` | AGENTS.md; BACKLOG automatic execution rules | GOV-001 conflict matrix | Governance |
| GOV-AUT-002 | Routine task completion does not require owner approval | Autonomous Execution Charter; DEC-0041 | `APPROVED_IMPLEMENTED_GOVERNANCE` | BACKLOG completion vocabulary | GOV-001 | Governance |
| GOV-AUT-003 | Preserve existing WP IDs and keep Evidence Coverage as WP-0450 | DEC-0027; DEC-0037; DEC-0041 | `DOCUMENTED_CONTROL` | BACKLOG; WP-0450 specification | GOV-001 | Governance |

## 16J. DEV-0404 parser identity requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0404-R01 | Preserve exact parser, version, artifact family, and contract identity | ARC-002; DEV-0263 | `IMPLEMENTED_TASK_VALIDATED` | `ParserIdentity` | AC-01; AC-02 | DEV-0404 |
| DEV-0404-R02 | Fail closed on malformed identity metadata | AGENTS.md | `IMPLEMENTED_TASK_VALIDATED` | Identity validation | AC-03 | DEV-0404 |
| DEV-0404-R03 | Candidate metadata cannot establish Supported status | DEV-0304; DEC-0037 | `IMPLEMENTED_TASK_VALIDATED` | Candidate factory and SUPPORTED rejection | AC-04; AC-05 | DEV-0404 |
| DEV-0404-R04 | Separate ORM identity metadata without execution/support effect | WP-0400 | `IMPLEMENTED_TASK_VALIDATED` | `ParserIdentityModel` | AC-06; AC-07 | DEV-0404 |

## 16K. DEV-0405 fingerprint requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0405-R01 | Record qualified profile/version, canonical reference, SHA-256, provenance, time, and limitations | DEC-0042 | `IMPLEMENTED_TASK_VALIDATED` | `SchemaFingerprintObservation` | AC-01 through AC-03 | DEV-0405 |
| DEV-0405-R02 | Fingerprint implies no compatibility, equivalence, parsing, or support | DEC-0042 | `IMPLEMENTED_TASK_VALIDATED` | Observation-only contract | AC-04 | DEV-0405 |
| DEV-0405-R03 | Implement no universal canonicalization algorithm | DEC-0042 | `IMPLEMENTED_TASK_VALIDATED` | Supplied-observation factory only | AC-05 | DEV-0405 |
| DEV-0405-R04 | Preserve observation relationally without support effect | WP-0400 | `IMPLEMENTED_TASK_VALIDATED` | ORM metadata | AC-06 through AC-08 | DEV-0405 |

## 16L. DEV-0406 typed-value requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0406-R01 | Preserve independently addressable raw and normalized typed serializations | DEC-0043 | `IMPLEMENTED_TASK_VALIDATED` | `TypedRepresentation`; `TypedValueObservation` | AC-01; AC-02 | DEV-0406 |
| DEV-0406-R02 | Keep required semantic states distinct and fail explicitly | DEC-0043 | `IMPLEMENTED_TASK_VALIDATED` | `ValueState`; validation | AC-03; AC-04 | DEV-0406 |
| DEV-0406-R03 | Require complete derivation provenance for normalized values | DEC-0043 | `IMPLEMENTED_TASK_VALIDATED` | `ValueTransformation` | AC-05; AC-06 | DEV-0406 |
| DEV-0406-R04 | Define envelopes only without transformation/support behavior | DEC-0043 | `IMPLEMENTED_TASK_VALIDATED` | Candidate domain/ORM metadata | AC-07; AC-08 | DEV-0406 |

## 16M. DEV-0407 timestamp requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0407-R01 | Preserve raw timestamp and complete source/run/parser/locator provenance | DEC-0044 | `IMPLEMENTED_TASK_VALIDATED` | `TimestampObservation` | AC-01; AC-02 | DEV-0407 |
| DEV-0407-R02 | Separate timezone source, values, rulesets, and derivation basis | DEC-0044 | `IMPLEMENTED_TASK_VALIDATED` | `TimezoneContext` | AC-03; AC-04 | DEV-0407 |
| DEV-0407-R03 | Keep ambiguity, nonexistent time, interpretation, and conversion distinct | DEC-0044 | `IMPLEMENTED_TASK_VALIDATED` | Closed enums and validation | AC-05; AC-07 | DEV-0407 |
| DEV-0407-R04 | Require explicit numeric epoch metadata without guessing | DEC-0044 | `IMPLEMENTED_TASK_VALIDATED` | `NumericEpochMetadata` | AC-06 | DEV-0407 |
| DEV-0407-R05 | Define provenance envelopes only without algorithms/support | DEC-0044 | `IMPLEMENTED_TASK_VALIDATED` | Candidate domain module | AC-08 | DEV-0407 |

## 16N. DEV-0408 processing coverage requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0408-R01 | Closed factual status, authorization, execution, count, reconciliation, and omission vocabularies | DEC-0045 | `IMPLEMENTED_TASK_VALIDATED` | `processing_coverage` enums | AC-01; AC-02 | DEV-0408 |
| DEV-0408-R02 | Complete and zero outcomes require authorized completed reconciled execution | DEC-0045 | `IMPLEMENTED_TASK_VALIDATED` | Coverage validation | AC-03; AC-04 | DEV-0408 |
| DEV-0408-R03 | Partial/resource/omission states retain explicit metadata and cannot appear complete | DEC-0045 | `IMPLEMENTED_TASK_VALIDATED` | Coverage and omission envelopes | AC-05 through AC-07 | DEV-0408 |
| DEV-0408-R04 | Processing facts produce no WP-0450, device-level, support, or legal conclusion | DEC-0045 | `IMPLEMENTED_TASK_VALIDATED` | Bounded observation contract | AC-08 | DEV-0408 |

## 16O. DEV-0409 issue requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0409-R01 | Closed category, severity, recoverability, and stable-code diagnostics | DEC-0046 | `IMPLEMENTED_TASK_VALIDATED` | `ProcessingIssue` enums/contract | AC-01; AC-02 | DEV-0409 |
| DEV-0409-R02 | Reject unsafe diagnostics and store no sensitive diagnostic fields | DEC-0046; security rules | `IMPLEMENTED_TASK_VALIDATED` | Safe validation and bounded fields | AC-03; AC-04 | DEV-0409 |
| DEV-0409-R03 | Preserve reference-only provenance and complete partial scope | DEC-0046 | `IMPLEMENTED_TASK_VALIDATED` | Issue/partial envelopes | AC-05; AC-06 | DEV-0409 |
| DEV-0409-R04 | Keep immutable diagnostics free of evidentiary/support conclusions | DEC-0046 | `IMPLEMENTED_TASK_VALIDATED` | Frozen candidate records | AC-07; AC-08 | DEV-0409 |

## 16P. DEV-0410 store requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0410-R01 | Additive reversible relational candidate store with no seeded support | DEC-0047 | `IMPLEMENTED_TASK_VALIDATED` | migration 0004 | offline/static tests | DEV-0410 |
| DEV-0410-R02 | Exact admission with complete integrity/provenance/coverage/promotion references | DEC-0047 | `IMPLEMENTED_TASK_VALIDATED` | `SupportedEvidenceStore` | focused tests | DEV-0410 |
| DEV-0410-R03 | Empty registry admits no records | DEC-0047 | `IMPLEMENTED_TASK_VALIDATED` | `REGISTRY_EMPTY` | denial test | DEV-0410 |
| DEV-0410-R04 | Scope queries before materialization without enumeration | DEC-0047 | `IMPLEMENTED_TASK_VALIDATED` | scoped `get` | isolation test | DEV-0410 |
| DEV-0410-R05 | Append-only records and acyclic supersession | DEC-0047 | `IMPLEMENTED_TASK_VALIDATED` | no update/delete; supersession | static/unit tests | DEV-0410 |

## 16Q. DEV-0411 isolation requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0411-R01 | Candidate, experimental, and legacy output remains in a distinct store | ARC-001; FOR-006 | `IMPLEMENTED_TASK_VALIDATED` | `QuarantinedOutputStore` | AC-01 | DEV-0411 |
| DEV-0411-R02 | No transfer/promotion path or broad enumeration exists | DEC-0047 | `IMPLEMENTED_TASK_VALIDATED` | bounded API | AC-02 through AC-04 | DEV-0411 |
| DEV-0411-R03 | Quarantine queries remain tenant/case scoped | DEC-0037 | `IMPLEMENTED_TASK_VALIDATED` | `list_scoped` | AC-05 | DEV-0411 |
| DEV-0411-R04 | Isolation adds no parser/support behavior | AGENTS.md | `IMPLEMENTED_TASK_VALIDATED` | diagnostic-only module | AC-06 | DEV-0411 |

## 16R. DEV-0412 integration requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| DEV-0412-R01 | Candidate evidence-core contracts compose without support-state leakage | WP-0400 | `VALIDATION_PENDING` | DEV-0401–0411 modules | 94 focused tests; QMS-009 | WP-0400 |
| DEV-0412-R02 | Default supported store and registry remain empty and quarantine remains separate | AGENTS.md; DEC-0047 | `VALIDATION_PENDING` | integration composition test | QMS-009 | WP-0400 |
| DEV-0412-R03 | Migration and regressions pass without production/evidence use | ARC-001 | `VALIDATION_PENDING` | migration 0004 | offline Alembic; 308 backend; 5 legacy | WP-0400 |

## 16S. WP-0400 owner disposition

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owner |
|---|---|---|---|---|---|---|
| CORE-WP-001 | Candidate evidence-core infrastructure is owner-approved with permanent traceability | DEC-0049 | `OWNER_APPROVED_CANDIDATE` | DEV-0401–0412; migration 0004 | QMS-009 | WP-0400 |
| CORE-WP-002 | Registry and supported normalized store remain empty | DEC-0049 | `DOCUMENTED_CONTROL` | empty default composition | QMS-009 integration tests | Future promotion gate |
| CORE-WP-003 | QMS-009 and JSON/live-PostgreSQL/production limitations remain active | DEC-0049 | `DOCUMENTED_LIMITATION` | QMS-009; RSK-0024 | Future governed validation | WP-0400 |

## 17. DEV-0003 acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Stable requirement identifiers are defined | PASS | Sections 4–10 |
| Approved scope and exclusions are traced | PASS | PRD and FOR-QTN rows |
| Pre-existing implementation is distinguished from validation | PASS | Section 3 statuses and implementation columns |
| Evidence integrity, provenance, failures, timestamps, and SQLite controls are traced | PASS | Sections 5–6 |
| Parser quarantine and output isolation are explicit | PASS | Section 7 |
| Security, AI, reporting, and quality gaps are visible | PASS | Sections 8–10 |
| Each row identifies verification and an owning task or gap | PASS | Matrix columns in Sections 4–10 |
| No artifact or parser is promoted | PASS | Document control and maintenance rule 8 |
