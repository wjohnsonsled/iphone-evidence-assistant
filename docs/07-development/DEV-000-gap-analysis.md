# DEV-000 — Repository Gap Analysis

## Scope

This gap analysis is the remediation input produced by DEV-0001. It compares the
pre-existing implementation with `AGENTS.md`, PRD-003, FOR-004, and DEV-001.
It does not approve feature implementation or change artifact support status.

## Executive assessment

The repository contains a useful prototype and backend scaffold that predate the
controlled development baseline. The system can parse and report a broad range
of artifacts on a best-effort basis, and narrow synthetic tests pass. It does
not meet the all-or-nothing support rule for any artifact family.

The highest risks are:

1. unsupported parsers are enabled by default and can feed reports and AI;
2. source SQLite files are read directly instead of through controlled working
   copies with companion-file preservation;
3. timezone-naive, heuristic timestamp conversion can change evidentiary order;
4. provenance and raw-value preservation are incomplete and not enforced;
5. authentication, authorization, and tenant isolation are absent;
6. backend processing omits the coverage-audit call and hard-codes the
   acquisition as encrypted;
7. broad best-effort error handling can convert failures into empty results;
8. no validated Apple-backup/schema fixtures or acceptance criteria exist.

## Gaps against governing requirements

### Code predating or conflicting with `AGENTS.md`

- The legacy tool describes itself as a parser for decrypted iPhone backups and
  predates the controlled input/support boundary.
- The default plugin registry includes both MVP candidates and out-of-scope or
  unapproved artifact families.
- Evidence processing opens original SQLite files rather than controlled copies.
- Timestamp conversion does not preserve timezone/conversion provenance.
- Parser code and coverage code use vocabularies different from the controlled
  statuses in `AGENTS.md`.
- The backend was implemented while DEV-0101 was still documented as blocked.
- Root implementation notes made assumptions before ARC-001, DOC-002, SEC-001,
  and QMS-004 were populated.

### Unsupported behavior that appears production-ready

- All 18 legacy plugins are returned by the default registry and executed by
  both the CLI and backend runner.
- Parser modules have production-style names and imports despite being legacy
  re-exports.
- API and README wording describes backup processing without clearly stating
  that no artifact family is validated as supported.
- Coverage status names such as `PRESENT_PARSED_WITH_RECORDS` can imply support
  even when there is no approved schema profile or fixture.
- AI and reports can consume events produced by unapproved artifact parsers.

### Silent and ambiguous failure behavior

- `sha256()` returns an empty string on every exception without recording why.
- plist loading, file-size checks, SQLite detection/counting, datetime parsing,
  and other helpers sometimes return empty/unknown values without structured
  failures.
- `ArtifactPlugin.safe_collect()` logs broad exceptions and returns no events,
  making downstream behavior dependent on whether coverage was separately
  populated.
- `SQLiteArtifact.query()` logs and returns an empty list, which can be confused
  with a valid zero-record result.
- backend persistence catches per-record exceptions and later raises an
  aggregate `ValueError`, but the public job stores only a generic error.

### Incomplete provenance

- Source table, row ID, GUID, path, parser, and version are optional and are not
  validated before persistence.
- Stable normalized IDs are hashes of a presentation-oriented event identity,
  not a controlled source-record locator.
- No citation resolver maps a citation back through a parser execution and
  immutable source hash to the source record.
- Coverage and device records are not tied to an intake/evidence-source or
  parser-run entity.
- Relationships and entity aliases have provenance strings but no enforced
  source-locator schema.

### Unvalidated schema assumptions

- SMS SQL assumes specific `message`, `handle`, chat, and attachment columns.
- Contacts and call-history code assumes selected schema/table patterns.
- Generic SQLite parsers select timestamp-like and text-like columns
  heuristically.
- Manifest parsing assumes a `Files` table and selected columns.
- No supported iOS versions, schema fingerprints, excluded-field declarations,
  expected-record fixtures, or schema-rejection tests are documented.

### Timestamp assumptions

- `safe_fromtimestamp()` uses the host timezone.
- several parsing functions remove `tzinfo`;
- numeric epoch selection is based on magnitude and field-name hints;
- source field, raw value, raw format, conversion method, precision, and
  limitations are not uniformly retained;
- the backend database declares timezone-aware columns but may receive naive
  values;
- attachment-specific timestamps are captured but the event timestamp is the
  parent-message timestamp;
- the runner creates a naive end time from UTC and then labels output without a
  timezone model.

### SQLite source, WAL, and journal gaps

- URI `mode=ro` is used, which is safer than a normal writable connection, but
  it still opens the submitted database directly.
- There is no controlled copy of main DB, WAL, SHM, and rollback journal.
- WAL/SHM presence is recorded by coverage code but the backend runner does not
  run that audit.
- rollback journal discovery/application is absent;
- `wal_applied_by_sqlite` is a heuristic rather than validated execution
  evidence;
- no WAL, journal, malformed-database, locked-database, or unknown-schema
  fixtures exist.

### Case, tenant, and authorization gaps

- Case foreign keys provide data organization, not authorization.
- There is no identity, role, tenant, membership, policy, or access-check layer.
- Every case/evidence endpoint is unauthenticated.
- There are no cross-tenant or cross-case authorization tests.
- Source paths and raw records reside in one database security boundary.

### AI and citation gaps

- The prompt instructs the model to cite normalized IDs, but output is not
  parsed or rejected when citations are missing.
- There is no citation-resolution endpoint or UI.
- No authorized case retrieval layer exists.
- Unsupported plugin records can enter the knowledge package.
- The deterministic question-answer function returns event summaries, not
  stable resolved citations.
- No AI evaluation dataset, unsupported-question suite, hallucination test, or
  fact-versus-interpretation validator exists.
- Ollama output is written as derived work product with a warning, but there is
  no model/version/prompt execution record.

### Security risks

- Authentication, authorization, tenant isolation, audit events, rate limits,
  retention, and secure deletion are absent.
- Broad filesystem discovery processes untrusted filenames and content.
- Server-local paths are accepted through an API; the root boundary is useful
  but does not provide an intake/upload isolation boundary.
- Symlink and time-of-check/time-of-use behavior is not tested.
- Development database credentials are embedded in Compose and Alembic config.
- Compose references a missing environment file, while the existing root
  example is empty.
- Logs can contain source paths and artifact-derived exception strings.
- No dependency lock, vulnerability scan, secret scan, or CI gate is present.

### Duplication, obsolete code, and technical debt

- Nearly all package modules re-export `_legacy.py`, creating the appearance of
  modularity while leaving one large coupled implementation.
- Root documentation and controlled `docs/` documentation conflict in maturity.
- Both legacy `Event` and `NormalizedEvent`, then backend `EvidenceEvent`, create
  multiple transformations without a single validated envelope.
- Coverage status vocabularies are mapped into a second API vocabulary, losing
  distinctions such as inaccessible versus parser failure.
- Generated `egg-info`, `__pycache__`, and `work/alembic_upgrade_head.sql` are
  present in the worktree/repository area and should be reviewed later; no
  deletion is authorized by DEV-0001.
- Deduplication has no database uniqueness constraint and may either duplicate
  or merge records depending on incomplete upstream provenance.

### Placeholder functionality

- Parser version strings (`"1"` and `"legacy"`).
- Audit logging represented only by ordinary application logs.
- Empty frontend, infrastructure, script, and CI areas.
- Empty documentation control, architecture, forensic-method, AI, security, and
  quality documents.
- `Device.backup_encrypted` and timezone columns exist without end-to-end
  population.
- Root and expected backend environment examples are absent/incomplete.

### Missing documentation

The following pre-existing files are zero-byte and must be authored and approved
before relevant implementation is treated as controlled:

- document register, traceability matrix, decision log, and risk register;
- product requirements and limitations;
- system architecture;
- forensic methodology, evidence integrity/provenance, backup ingestion, and
  timestamp normalization;
- AI grounding, citation, and hallucination controls;
- threat model;
- definition of done and test strategy.

The support matrix additionally lacks all required per-artifact details.

### Missing tests and fixtures

- validated miniature Apple local backup;
- encryption-state fixtures;
- incomplete, malformed, corrupted, and unsupported input fixtures;
- supported and unknown Manifest schemas;
- each artifact schema version and expected complete extraction result;
- raw/normalized value pairing;
- stable source locator and citation resolution;
- UTC conversion, timezone selection, precision, and invalid timestamps;
- main DB plus WAL/SHM/journal behavior;
- source immutability and before/after hashes;
- explicit failure versus no-record status;
- parser-version and execution records;
- authentication, authorization, tenant isolation, and audit events;
- PostgreSQL migration/integration;
- deterministic report golden files and AI evaluations;
- frontend and end-to-end workflows.

### Missing acceptance criteria

DEV-0101 refers to an acceptance document “To be created.” Phase 1–8 tasks do
not have task-specific acceptance documents. FOR-004 defines required fields but
contains none of the per-artifact approved profiles. No acceptance criteria
currently authorize a supported parser or production deployment.

## Documentation contradictions

| Document or behavior | Contradiction |
|---|---|
| DEV-009 says backend scaffold is blocked/pending | Backend, database models, migration, API, Dockerfile, and tests already exist |
| README says current script needs no third-party packages | Optional parser/report functions use optional packages; backend requires declared dependencies |
| README/API describe backup processing | Structural validation, encryption detection, coverage persistence, and supported artifact boundaries are incomplete |
| API says input must appear to be a supported backup | One marker, including an empty `Manifest.db`, passes the current check |
| IMPLEMENTATION_NOTES assumes a decrypted backup or extracted directory | PRD-003 requires Apple local backup classification and prioritizes unencrypted backup support |
| LOCAL_DEVELOPMENT says copy `backend/.env.example` | That file does not exist; root `.env.example` is empty |
| DATABASE_DESIGN describes preservation and future readiness | No evidence-source/parser-run provenance model, tenant boundary, or retention implementation exists |
| REFACTOR_NOTES describes stable package modules | Most modules are re-export façades over `_legacy.py` |
| Backend result exposes errors | `ErrorLog.records` are strings, but runner calls `.get()` on each record, which would fail when any parser error is recorded |
| Case knowledge labels acquisition | It always states encrypted backup without detection |

## Recommended remediation order

1. **DEV-0002 — Confirm MVP scope against this baseline.** Explicitly decide
   which pre-existing paths are quarantined from supported execution.
2. Populate and approve product limitations, document register, decision log,
   risk register, architecture, threat model, test strategy, and definition of
   done.
3. Create the traceability baseline before accepting application changes.
4. Define evidence-source, intake, immutable hash, working-copy, parser-run,
   source-locator, timestamp-provenance, and controlled status models.
5. Add authentication, authorization, tenant isolation, and audit architecture
   before any shared or SaaS deployment.
6. Establish synthetic/lawfully distributable Apple-backup validation fixtures.
7. Implement and validate backup type, structure, and encryption detection.
8. Implement controlled copying of SQLite main/WAL/SHM/journal and prove source
   immutability.
9. Complete backup metadata and inventory as the first all-or-nothing artifact
   family.
10. Validate one parser family at a time in the DEV-001 order.
11. Restrict AI, reporting, and search to authorized `SUPPORTED_COMPLETE` or
    `SUPPORTED_NO_RECORDS` records with resolvable citations.
12. Add CI only after approved commands, dependencies, and fixture policy exist.
13. Begin frontend work after server-side authorization, source inspection, and
    citation contracts are stable.

## Recommended next task

The next task is DEV-0002: confirm the MVP scope against the repository baseline.
It should decide whether all non-MVP legacy plugins are disabled/quarantined in
future supported workflows and reconcile “Apple local backup” with the existing
“decrypted case directory” assumption. No implementation should begin during
that scope decision.

## Architecture reuse assessment

The architecture is **conditionally reusable**:

- retain the evidence-engine/backend separation, repository/service boundaries,
  path-root validation concept, UUID case relationships, Alembic approach, and
  deterministic test patterns;
- validate and refactor the normalized envelope and coverage model;
- isolate the legacy core as unvalidated compatibility code;
- replace direct source access, timestamp handling, provenance/citation,
  controlled-status mapping, and security boundaries before production use.
