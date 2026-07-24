# PRD-006 — Existing Capability Inventory

## Status and use

This inventory was created by DEV-0001 on 2026-07-24. It describes code found in
the repository; it does not declare product support.

Allowed capability classifications:

- `VERIFIED_IMPLEMENTED`
- `IMPLEMENTED_NOT_VALIDATED`
- `PARTIALLY_IMPLEMENTED`
- `PLACEHOLDER`
- `NOT_IMPLEMENTED`
- `UNABLE_TO_DETERMINE`

`VERIFIED_IMPLEMENTED` is used only for narrow behavior exercised by a passing
test during this inspection. No forensic artifact family receives that
classification as a supported whole.

Test references below use:

- **EE tests:** `tests/test_characterization.py` and
  `tests/test_legacy_self_checks.py`; executed, 5 passed.
- **Backend tests:** files under `backend/tests`; not executed because pytest
  was unavailable.

## Capability inventory

| # | Capability and intended purpose | Classification | Relevant implementation and interfaces | Existing tests / execution result | Integrity, provenance, security, limitations, contradiction | Disposition |
|---|---|---|---|---|---|---|
| 1 | Case management: create and retrieve a case and processing state | IMPLEMENTED_NOT_VALIDATED | `backend/app/api/cases.py`: `create_case`, `get_case`; `CaseRepository`; `Case`; `cases` migration; `POST /api/v1/cases`, `GET /api/v1/cases/{case_id}` | `backend/tests/test_api.py`; not executed | UUID and case FK structure exists. No actor, tenant, authorization, or material-action record. Conflicts with PRD-003 isolation and audit requirements. | validate |
| 2 | Evidence-source management: associate one or more sources with a case | PARTIALLY_IMPLEMENTED | `Case.source_path`; `Device`; `CaseProcessingService`; `devices` migration | No dedicated tests | Source is a string on a case plus an inferred first device; no evidence-source entity, intake hash set, source status, or multiple-source lifecycle. | refactor |
| 3 | Apple backup detection: recognize supported Apple local backup input | PARTIALLY_IMPLEMENTED | `appears_supported_backup()` checks any of several markers | Path test uses an empty `Manifest.db`; not executed | Marker presence is not format identification and accepts extracted case directories. It cannot establish Apple backup type. | replace |
| 4 | Backup validation: validate required structure and completeness | PARTIALLY_IMPLEMENTED | `LocalBackupPathValidator.validate()` and broad marker check; `/cases/{id}/process` | Traversal and marker tests; not executed | Path existence and root boundary are checked; required plist/manifest relationships, file layout, corruption, and completeness are not. API.md overstates “supported” structure. | replace |
| 5 | Encryption-state detection | NOT_IMPLEMENTED | `Device.backup_encrypted` column exists but no detector populates it | None | Runner hard-codes encrypted acquisition labels. Cannot distinguish encrypted, unencrypted, incomplete, malformed, or unsupported as required. | implement in later approved task |
| 6 | `Manifest.plist` parsing | PARTIALLY_IMPLEMENTED | Generic plist discovery/summarization; `extract_device_metadata()` may read metadata plists | No schema fixture/test | No approved field list, schema profile, raw-field preservation, encryption-state validation, or failure contract. | validate |
| 7 | `Manifest.db` parsing | PARTIALLY_IMPLEMENTED | `parse_backup_manifests()` and coverage manifest lookup in `_legacy.py` | No Manifest fixture/test | Uses assumed `Files` columns; no schema fingerprints or version matrix. Backend runner does not invoke coverage audit. | validate |
| 8 | File inventory and hashing | PARTIALLY_IMPLEMENTED | `CaseContext` file index; `build_coverage_audit`, `audit_file_coverage`, `coverage_sha256`, `sha256` | Characterization test checks artifact inventory shape; executed/passed | Hashing is optional/size-limited by default; hash errors silently become empty strings; no complete intake inventory acceptance fixture. | refactor |
| 9 | Source-evidence immutability | PARTIALLY_IMPLEMENTED | SQLite uses URI `mode=ro`; Docker evidence mount is `:ro` | No immutability test | Other source files are directly read; non-Docker OS controls are absent; no intake seal or before/after hash validation. | replace |
| 10 | Working-copy separation | NOT_IMPLEMENTED | No controlled-copy service or work-product source mapping found | None | Direct source SQLite access conflicts with AGENTS.md even though mode is read-only. | implement before parser validation |
| 11 | Message parsing | IMPLEMENTED_NOT_VALIDATED | `_legacy.SmsPlugin.collect`; SQL over `message`, `handle`, chat joins; exported by `parsers/messages.py` | Synthetic events only; no parser/schema fixture | Code appears functional but assumes one schema and query alias behavior; incomplete raw values and no declared field coverage. Candidate remains unsupported. | validate |
| 12 | Attachment parsing | IMPLEMENTED_NOT_VALIDATED | `SmsPlugin.attachments_for_message`, `find_attachment_path`, hashing, EXIF, link functions | Legacy deterministic attachment-link checks executed/passed; no database/file fixture | First basename match may be ambiguous; attachment event uses parent timestamp even when attachment timestamps exist; no complete provenance fixture. | validate |
| 13 | Call-history parsing | IMPLEMENTED_NOT_VALIDATED | `_legacy.CallHistoryPlugin`; exported by `parsers/calls.py` | No parser fixture/test | Schema/path assumptions are unvalidated; no declared direction/timestamp matrix. | validate |
| 14 | Contact parsing | PARTIALLY_IMPLEMENTED | `ContactResolver` reads `AddressBook.sqlitedb` and resolves aliases | No contact fixture/test | Contacts enrich other events but are not emitted as a complete supported artifact family; merges may obscure original identifiers. | refactor |
| 15 | Timestamp handling | PARTIALLY_IMPLEMENTED | `parse_dt`, Apple/Unix/WebKit helpers, `timestamp_from_any`; event and DB timestamp fields | Synthetic timestamp preservation assertion executed/passed | Host-local `fromtimestamp`, timezone stripping, heuristic epochs, and absent conversion provenance violate the documented time rules. | replace |
| 16 | SQLite WAL and journal handling | PARTIALLY_IMPLEMENTED | Coverage records WAL/SHM presence; `SQLiteArtifact` opens main DB `mode=ro` | No WAL/journal fixture | No controlled copy; rollback journal omitted; whether WAL was applied is not reliably established. | replace |
| 17 | Raw-value preservation | PARTIALLY_IMPLEMENTED | Some plugins store `metadata["raw"]`; backend `raw_values_json` | Persistence synthetic raw-value test exists; not executed | SMS and other dedicated plugins select subsets and do not preserve every original field/value or format. | refactor |
| 18 | Normalized-value preservation | IMPLEMENTED_NOT_VALIDATED | `NormalizedEvent`, `normalize_event`, backend `EvidenceEvent` | EE characterization checks shapes; executed/passed | Normalization exists, but incomplete raw pairing and timestamp provenance prevent validation. | retain and validate |
| 19 | Provenance and source locators | PARTIALLY_IMPLEMENTED | normalized `source_*` fields, event IDs, relationship provenance, backend source columns | EE knowledge-field test executed/passed; no resolver test | Fields may be inferred or blank; no enforced stable locator format or UI/source-record resolver. | refactor |
| 20 | Parser-version tracking | PLACEHOLDER | `NormalizedEvent.parser_version="1"`; adapter `"legacy"`; DB columns | No version test | Values do not identify code revision, schema profile, configuration, or parser execution. | replace |
| 21 | Processing coverage | PARTIALLY_IMPLEMENTED | extensive `_legacy` coverage model and reports; `ArtifactCoverage` persistence | Legacy coverage/completeness checks executed/passed | Vocabulary conflicts with AGENTS.md controlled statuses; backend runner never invokes coverage audit, so API processing may persist none. | refactor |
| 22 | Processing failures and omissions | PARTIALLY_IMPLEMENTED | `ErrorLog`, `safe_collect`, job failure state, coverage failure fields | Persistence rollback test exists; not executed | Broad exceptions are often logged, but helpers also silently return empty values; backend runner converts error-log strings incorrectly as if mappings. | refactor |
| 23 | Search | IMPLEMENTED_NOT_VALIDATED | `EvidenceRepository.list`; evidence list/detail routes; filters and pagination | API test exists; not executed | Queries are case-scoped but unauthenticated; participant filter is a single derived key, not full-text search. | retain and validate |
| 24 | Timeline generation | IMPLEMENTED_NOT_VALIDATED | CLI chronological reports and timestamp-sorted API evidence query | Report-heading test executed/passed | Sorting exists, but timezone and precision uncertainty are not represented adequately. | retain and refactor |
| 25 | AI retrieval and grounding | PARTIALLY_IMPLEMENTED | deterministic `answer_question`; `build_case_knowledge`; Ollama prompt/output | AI package shape tested and passed; no evaluation dataset | CLI prompt has guardrails, but no authorized-case retrieval service, model-output validation, or production OpenAI integration. It can include unsupported plugin records. | defer then refactor |
| 26 | Citation generation and resolution | PARTIALLY_IMPLEMENTED | normalized event/relationship IDs included in knowledge and prompt | No citation-resolution test | Prompt demands IDs, but generated text is not checked and no API/UI citation resolver exists. IDs are derived from mutable presentation fields. | replace |
| 27 | Report generation | IMPLEMENTED_NOT_VALIDATED | multiple Markdown/CSV/HTML/simple-PDF report functions in `_legacy.py` | Report headings and deterministic pipeline checks executed/passed | Output generation works for synthetic inputs; no approved report acceptance fixture, export validation, source resolver, or attorney review. | retain and validate |
| 28 | Authentication | NOT_IMPLEMENTED | No authentication dependency, identity model, or token/session validation | None | All endpoints are public to any network caller that can reach them. | implement before shared deployment |
| 29 | Authorization | NOT_IMPLEMENTED | Case-ID filters only | No authorization tests | Possession/guessing of UUID grants access; server-side authorization requirement is unmet. | implement before shared deployment |
| 30 | Tenant isolation | NOT_IMPLEMENTED | No tenant table or `tenant_id` columns | No tenant tests | Database and queries have no tenant boundary. | implement before shared deployment |
| 31 | Audit logging | PLACEHOLDER | Application logs processing start/complete/failure; timestamps on rows | No audit tests | Operational logs are not immutable, actor-aware material case-action records. | replace |
| 32 | Upload and path-security controls | PARTIALLY_IMPLEMENTED | `LocalBackupPathValidator`, configured roots, Docker read-only mount | Traversal test exists; not executed | No upload/archive handling. Symlink/race and untrusted-content controls are incomplete. Root configuration is empty/broken by default. | retain and validate |
| 33 | Database persistence | IMPLEMENTED_NOT_VALIDATED | SQLAlchemy models, repositories, persistence service, Alembic `0001` | Persistence, API, and summary tests exist; not executed | PostgreSQL migration not run. No tenant keys, evidence-source/run tables, immutable provenance constraints, or uniqueness enforcement. | retain and refactor |
| 34 | Docker and local development | PARTIALLY_IMPLEMENTED | Compose, Dockerfile, local guide | Not executed | Compose refers to missing `backend/.env.example`; root example is empty. Development password is explicit. No healthcheck for backend. | refactor |
| 35 | Automated tests | PARTIALLY_IMPLEMENTED | 5 EE unittest tests and 8 collected-style backend tests in four files | EE: 5 passed. Backend: unable to run (`pytest` missing) | Tests are narrow characterization/unit checks and do not establish forensic correctness. | expand |
| 36 | Validation fixtures | PLACEHOLDER | Synthetic in-test objects and temporary empty `Manifest.db`; no controlled fixture directory | EE synthetic tests passed | No Apple-backup, schema-version, malformed, WAL, provenance, timestamp, or expected-result fixtures. | create in approved validation task |
| 37 | CI configuration | NOT_IMPLEMENTED | `.github` has no workflow file | None | No automated quality, migration, security, or fixture checks. | defer until conventions approved |
| 38 | Frontend implementation | NOT_IMPLEMENTED | Empty `frontend/` | None | No search UI, timeline, record/source inspection, citation inspection, coverage display, or authorization experience. | defer |

## Additional pre-existing capability findings

The registry includes code for Safari, Photos, Notes, Mail, Calendar, Reminders,
Maps/location, KnowledgeC, notifications, and multiple network/system sources.
Several are expressly outside the current MVP or absent from `FOR-004`. They
look callable and are enabled by default, which could be mistaken for production
support. They are all `IMPLEMENTED_NOT_VALIDATED` or `PARTIALLY_IMPLEMENTED` at
most and must be excluded from any supported workflow until separately approved.

## Verification boundary

The passing evidence-engine tests establish only deterministic behavior for
their synthetic objects and legacy self-checks. They do not validate artifact
source paths, Apple schema versions, complete record extraction, source
immutability, WAL behavior, timestamp correctness, provenance resolution, or
legal/forensic interpretation.
