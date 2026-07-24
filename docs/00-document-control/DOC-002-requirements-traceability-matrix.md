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
| PRD-IN-001 | Accept only a structurally valid Apple local iPhone backup in the initial supported path | PRD-003 §3; PRD-007 §4 | `PARTIAL_UNVALIDATED` | `backend/app/services/case_processing.py` performs broad path-marker checks | `backend/tests/test_path_validation.py` characterizes root/path behavior only | DEV-0201; DEV-0202 |
| PRD-IN-002 | Distinguish unencrypted, encrypted, incomplete, malformed/corrupted, and unsupported inputs | AGENTS.md Input scope; PRD-007 §4 | `APPROVED_UNIMPLEMENTED` | `backend/app/models/device.py` has an unpopulated `backup_encrypted` field | No classification fixture suite | DEV-0201 through DEV-0203 |
| PRD-IN-003 | Prioritize unencrypted backups as the first input target | PRD-003 §3; PRD-007 §4; DEC-0001 | `DOCUMENTED_CONTROL` | No conforming supported intake path exists | Owner approval DEC-0001 | DEV-0201 through DEV-0202 |
| PRD-IN-004 | Detect and report encrypted backups without decrypting or processing inaccessible content | PRD-007 §5; DEC-0001 | `APPROVED_UNIMPLEMENTED` | Database field only; no detection/reporting implementation | No encryption-state fixtures | DEV-0203 |
| PRD-IN-005 | Do not accept, retain, or log backup passwords in the initial MVP | PRD-007 §5; SEC-001 placeholder | `DOCUMENTED_CONTROL` | No password intake interface identified | No secret-handling tests | DEV-0203; security task unassigned |
| PRD-IN-006 | Exclude physical/full-filesystem acquisitions, third-party tool ingestion, and nonvalidated extracted directories | PRD-007 §4; DEC-0001 | `LEGACY_QUARANTINED` | Legacy CLI accepts broader extracted-directory layouts | Documentation approval only; runtime gate absent | DEV-0201; DEV-0304 |
| PRD-SCP-001 | Limit initial artifact candidates to backup metadata/inventory, messages, attachments, calls, and contacts | PRD-007 §6; FOR-004 §2; DEC-0001 | `DOCUMENTED_CONTROL` | Legacy registry contains both candidate and excluded families | FOR-004 matrix and DEC-0001 | DEV-0304 and per-artifact Phase 4 tasks |
| PRD-SCP-002 | Keep all other listed artifact families excluded or quarantined | PRD-007 §7; FOR-004 §3; FOR-006 §5 | `LEGACY_QUARANTINED` | `evidence_engine/_legacy.py::plugins()` exposes excluded families | No production registry enforcement test | DEV-0304 |
| PRD-SCP-003 | Do not represent a local backup as a complete device image | AGENTS.md Mandatory forensic rules; PRD-007 §2 | `DOCUMENTED_CONTROL` | Legacy reports contain limitations but are not an accepted product surface | No product-content acceptance suite | Reporting task unassigned |

## 5. Evidence integrity and provenance requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| FOR-INT-001 | Treat submitted source evidence as immutable and never modify it | AGENTS.md Mandatory forensic rules | `PARTIAL_UNVALIDATED` | Legacy SQLite access uses URI `mode=ro`; no immutable intake boundary exists | No source before/after hash test | DEV-0201; DEV-0207 |
| FOR-INT-002 | Separate submitted source evidence from derived data and working copies | AGENTS.md; PRD-007 §10 | `APPROVED_UNIMPLEMENTED` | Backend writes normalized output separately but opens source databases directly | No boundary or working-copy tests | DEV-0103; DEV-0201; architecture decision |
| FOR-INT-003 | Generate and retain SHA-256 for source and material derived files; surface hash failures | AGENTS.md; PRD-007 §10 | `PARTIAL_UNVALIDATED` | `evidence_engine/_legacy.py::sha256()` and size-limited coverage hashing exist; failures may become empty strings | Characterization tests do not prove complete hashing/failure behavior | DEV-0207; DEV-0210 |
| FOR-PROV-001 | Retain provenance from every normalized record to its source artifact and stable source record | AGENTS.md; FOR-004 §5 | `PARTIAL_UNVALIDATED` | `NormalizedEvent` and `EvidenceEvent` contain provenance-like fields without an enforced locator contract | Persistence tests verify storage, not locator resolvability | DEV-0301; DEV-0302 |
| FOR-PROV-002 | Preserve original values separately from normalized values | AGENTS.md; FOR-004 §5 | `PARTIAL_UNVALIDATED` | Backend stores `raw_values_json` when supplied; legacy normalization does not guarantee a complete raw envelope | `backend/tests/test_persistence.py` covers supplied synthetic raw values only | DEV-0305 |
| FOR-PROV-003 | Tie every parser result to parser version, schema fingerprint, execution record, and source hashes | AGENTS.md; FOR-006 §8 | `APPROVED_UNIMPLEMENTED` | Legacy parser versions are placeholders; no parser-run entity exists | No execution-record tests | DEV-0303; DEV-0304 |
| FOR-PROV-004 | Make every displayed evidentiary assertion resolvable to inspectable source records | AGENTS.md AI rules; PRD-007 §10 | `APPROVED_UNIMPLEMENTED` | Normalized IDs exist, but there is no citation resolver/source inspection contract | No citation resolution tests | Phase 5/6 tasks unassigned |
| FOR-FAIL-001 | Record unreadable, malformed, unknown, unsupported, omitted, and failed data explicitly | AGENTS.md; FOR-006 §9 | `PARTIAL_UNVALIDATED` | Legacy error logging exists but helpers can silently return empty values | Characterization tests do not cover complete failure taxonomy | DEV-0105; DEV-0210 |
| FOR-FAIL-002 | Distinguish successful zero records from parser failure | AGENTS.md; FOR-004 §4; FOR-006 §9 | `APPROVED_UNIMPLEMENTED` | Current empty-result behavior can represent multiple outcomes | No zero-record-versus-failure suite | DEV-0105; DEV-0303; DEV-0304 |
| FOR-STS-001 | Use the controlled processing result statuses only | AGENTS.md Artifact support statuses; FOR-004 §4 | `PARTIAL_UNVALIDATED` | Legacy and backend coverage vocabularies do not preserve every controlled distinction | No status-contract tests | DEV-0105; DEV-0304 |

## 6. SQLite and timestamp requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| FOR-SQL-001 | Analyze SQLite only from controlled working copies, never source evidence directly | AGENTS.md SQLite handling; PRD-007 §10 | `APPROVED_UNIMPLEMENTED` | Legacy code opens the submitted database directly in read-only mode | No controlled-copy fixtures/tests | Architecture decision; DEV-0205 |
| FOR-SQL-002 | Preserve and account for main DB, WAL, SHM, and rollback journal companions | AGENTS.md SQLite handling; FOR-004 §5 | `PARTIAL_UNVALIDATED` | WAL/SHM inventory is heuristic; rollback-journal workflow is absent | No companion-file fixture suite | Architecture decision; DEV-0205 |
| FOR-SQL-003 | Distinguish logical backup records from physical/deleted-data recovery | AGENTS.md SQLite handling; PRD-007 §7 | `DOCUMENTED_CONTROL` | Deleted-data recovery is excluded; legacy generic parsing remains quarantined | DEC-0001 and FOR-006 | DEV-0304 |
| FOR-TIME-001 | Preserve original timestamp value, format, source field, conversion method, precision, and limitations | AGENTS.md Time handling; FOR-004 §5 | `PARTIAL_UNVALIDATED` | Legacy models contain timestamps but not a uniform complete provenance envelope | Existing self-checks do not validate full timestamp provenance | DEV-0306 |
| FOR-TIME-002 | Normalize comparable timestamps to UTC without silently assuming a timezone | AGENTS.md Time handling | `PARTIAL_UNVALIDATED` | `safe_fromtimestamp()` uses host-local behavior and several paths create naive datetimes | No timezone-selection/unknown-timezone suite | DEV-0306 |
| FOR-TIME-003 | Display local time only when timezone is known or explicitly selected | AGENTS.md Time handling | `APPROVED_UNIMPLEMENTED` | No accepted UI/display timezone contract exists | No display tests | DEV-0306; frontend task unassigned |

## 7. Parser quarantine and support requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| FOR-QTN-001 | Use a separate explicit, versioned supported-parser registry | FOR-006 §3 | `APPROVED_UNIMPLEMENTED` | Backend calls legacy `plugins()` directly | No supported-registry tests | DEV-0304 |
| FOR-QTN-002 | Disable every parser by default unless approved for its declared profile | FOR-006 §4 | `APPROVED_UNIMPLEMENTED` | Legacy registry enables numerous unapproved parsers | No fail-closed registry tests | DEV-0304 |
| FOR-QTN-003 | Prevent quarantined output from supported storage, search, AI, reports, citations, and coverage | FOR-006 §6; DEC-0001 | `PARTIAL_UNVALIDATED` | DEV-0101 excludes all legacy evidence routes from the default composition; supported stores and downstream retrieval do not yet exist | Default composition-boundary tests only; no end-to-end supported-store isolation tests | DEV-0304 and Phase 5–7 tasks |
| FOR-QTN-004 | Promote a parser only after complete profile validation, traceability, tests, documentation, and owner approval | AGENTS.md All-or-nothing support rule; FOR-006 §7 | `DOCUMENTED_CONTROL` | No parser is promoted | FOR-004 and explicit owner gate | Per-artifact Phase 4 tasks |
| FOR-QTN-005 | Fail closed on unknown schemas and prohibit generic-parser fallback as supported evidence | FOR-006 §9 | `LEGACY_QUARANTINED` | Generic SQLite/plist parsing exists in the legacy path | No supported-path failure tests | DEV-0304; per-artifact tasks |
| FOR-QTN-006 | Retain legacy CLI only as a compatibility/characterization surface unless separately approved | FOR-006 §10; PRD-007 §8 | `DOCUMENTED_CONTROL` | Legacy CLI remains present | Distribution decision remains owner-controlled | DEV-0304; owner decision if distribution proposed |

## 8. Security requirements

| Requirement ID | Requirement | Source | Status | Implementation evidence | Verification evidence | Owning task or gap |
|---|---|---|---|---|---|---|
| SEC-AUT-001 | Authenticate users and services before case access | AGENTS.md Security rules; PRD-007 §10 | `APPROVED_UNIMPLEMENTED` | No authentication principal or middleware identified | No authentication tests | Phase 8 task unassigned |
| SEC-AUT-002 | Enforce authorization and case/tenant isolation server-side | AGENTS.md Security rules; PRD-007 §10 | `APPROVED_UNIMPLEMENTED` | Case IDs filter queries but any caller may provide any case ID | No cross-case/cross-tenant tests | DEV-0103; Phase 8 task unassigned |
| SEC-INP-001 | Validate untrusted uploaded files and paths; prevent traversal and unsafe execution | AGENTS.md Security rules | `PARTIAL_UNVALIDATED` | Root-boundary path validation exists; upload and structural validation do not | `backend/tests/test_path_validation.py` covers basic traversal | DEV-0201; security task unassigned |
| SEC-SEC-001 | Never commit or log credentials, passwords, tokens, production secrets, or decrypted secret values | AGENTS.md Security rules; PRD-007 §5 | `DOCUMENTED_CONTROL` | No initial password flow exists; development configuration requires later review | No secret scan or log-redaction suite | DEV-0104; security task unassigned |
| SEC-AUD-001 | Record security- and evidence-relevant actions without sensitive secret content | FOR-006 §8; AGENTS.md Security rules | `APPROVED_UNIMPLEMENTED` | Ordinary application logging exists; no audit-event model | No audit tests | DEV-0104; Phase 8 task unassigned |

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
- DOC-004 risk register;
- PRD-001 product requirements;
- PRD-004 limitations;
- ARC-001 architecture;
- FOR-001 through FOR-003 and FOR-005;
- AI-001, AI-003, and AI-005;
- SEC-001 threat model;
- QMS-003 definition of done; and
- QMS-004 test strategy.

The matrix therefore marks affected work as unimplemented, unassessed, or
assigned to a later task. It does not fill those policy and architecture gaps
by inference. DEV-0004 is the next approved task and must address architecture
recommendations without treating placeholder documents as approved decisions.

## 13. Maintenance rules

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

## 14. DEV-0004 architecture-recommendation trace

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

## 15. DEV-0003 acceptance criteria

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
