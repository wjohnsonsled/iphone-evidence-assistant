# PRD-007 — MVP Scope Reconciliation

## 1. Document control

- Task: DEV-0002
- Date: 2026-07-24
- Inputs: AGENTS.md, DOC-005, PRD-003, PRD-006, FOR-004, DEV-000,
  DEV-001, DEV-009, README.md, IMPLEMENTATION_NOTES.md, and REFACTOR_NOTES.md
- Status: approved
- Owner approval: DEC-0001, 2026-07-24
- Effect on runtime: none
- Effect on artifact support: none; all MVP artifacts remain candidates

## 2. Approved MVP objective

The MVP is an evidence-understanding and review application for authorized
investigators and attorneys. It will accept a validated Apple local iPhone
backup, preserve the submitted source unchanged, process only approved and
fully validated artifact families, and provide search, timeline, source
inspection, evidence-grounded AI, citations, and reporting.

The product is not an acquisition tool, a complete representation of an
iPhone, a physical-image analyzer, or a substitute for examiner judgment.

## 3. Scope terminology

### Supported production workflow

A product path in which every input type, parser, schema, normalized record,
status, citation, report, and failure mode used by the path satisfies the
all-or-nothing support rule and has explicit acceptance approval.

No current repository workflow has this status.

### Candidate

An approved target for future complete support. Candidate means planned scope,
not current support.

### Legacy compatibility code

Pre-baseline code retained to preserve historical CLI behavior, characterize
existing behavior, and assist controlled migration. It is not part of the
supported production path unless separately validated and promoted.

### Experimental code

Code available only in an explicitly labeled, isolated evaluation path. Its
output is not validated evidence and cannot enter supported stores, AI,
reports, or coverage calculations.

### Unsupported code or input

Code, artifact families, schemas, acquisition types, or workflows outside the
approved supported path. Presence or apparent functionality does not imply
support.

## 4. Approved input boundary

### Supported-input candidates

The sole acquisition-format candidate for the initial MVP is a structurally
valid Apple local iPhone backup.

The intake design must distinguish:

- unencrypted Apple local backup;
- encrypted Apple local backup;
- incomplete backup package;
- malformed or corrupted backup package; and
- unsupported input format.

The first input targeted for complete implementation and validation is an
**unencrypted Apple local backup**.

### Explicitly excluded inputs

The initial supported path excludes:

- physical acquisition;
- full-filesystem acquisition;
- jailbroken-device collections;
- device-exploitation output;
- Cellebrite extraction ingestion;
- GrayKey extraction ingestion;
- arbitrary extracted case directories that cannot be validated as an Apple
  local backup;
- deleted-data or unallocated-space recovery inputs; and
- arbitrary archives or third-party forensic-tool exports.

Pre-existing compatibility code may continue to recognize a decrypted or
extracted case directory only in the quarantined legacy CLI path. That behavior
is not an MVP input claim.

## 5. Encrypted-backup handling

The initial release must:

1. detect whether the Apple local backup is encrypted;
2. record and report that state;
3. retain the submitted source unchanged;
4. return an explicit status explaining that decryption is not implemented;
5. avoid processing encrypted content as though it were accessible; and
6. make no claims about encrypted-only artifact presence, absence, or content.

The initial MVP does not require an encrypted backup. It does not accept,
retain, log, or attempt a backup password. Decryption requires a separately
approved scope, threat assessment, design, implementation, validation,
documentation, and acceptance decision.

Health data, keychain-derived records, saved credentials, and other
encrypted-only artifact claims remain excluded.

## 6. Approved artifact candidates

Only these artifact families are candidates for the initial supported path:

1. backup metadata:
   - `Info.plist`;
   - `Status.plist`;
   - `Manifest.plist`;
2. `Manifest.db` and deterministic backup file inventory;
3. messages, including approved SMS/iMessage fields, chats, handles, and
   direction only where determinable;
4. message attachments and their supported message relationships;
5. call history; and
6. contacts.

The implementation order remains:

1. backup metadata and inventory;
2. messages;
3. message attachments;
4. call history; and
5. contacts.

Each family remains a candidate until the all-or-nothing support criteria are
met. No current parser is approved as a supported parser.

## 7. Deferred and excluded artifact families

The following are outside the initial supported path:

- Notes;
- Safari;
- Calendar;
- Health;
- keychain-derived records;
- saved credentials and credential recovery;
- arbitrary third-party applications;
- deleted-data and unallocated-space recovery;
- malware or spyware analysis;
- Mail, Reminders, Photos, Maps/location, KnowledgeC, notifications, and broad
  network/system parsing unless separately approved;
- attribution of actions to a physical person;
- intent or motive conclusions;
- legal conclusions; and
- automatic testimony opinions.

Existing implementations for these families are legacy compatibility or
experimental code, not evidence of support.

## 8. Reuse decisions

| Decision | Rationale | Customer value | Forensic risk | Implementation impact | Owner approval |
|---|---|---|---|---|---|
| Retain evidence-engine/backend separation as a candidate architecture | Separates parsing from API persistence | Enables maintainable validation boundaries | Existing adapter can transmit incomplete provenance | Validate interfaces before reuse | Not required for retention; required for final architecture approval |
| Retain repository/service and Alembic patterns | Existing boundaries are testable | Reduces unnecessary rework | Current schema lacks tenant, intake, parser-run, and locator controls | Extend only under approved tasks and migrations | Required through architecture and task acceptance |
| Retain UUID case relationships | Useful internal identifiers | Stable case references | UUID is not authorization | Add tenant and authorization controls | Required for security design |
| Retain path-root validation concept | Provides a useful server-side boundary | Reduces accidental out-of-root processing | Does not validate Apple backup structure or eliminate path races | Validate and harden in intake tasks | Not required for concept; required for production acceptance |
| Retain deterministic characterization tests | Preserves known behavior during migration | Reduces regression risk | Can be mistaken for forensic validation | Label separately from validation fixtures | No |
| Retain legacy CLI code in quarantine | Preserves historical behavior without deletion | Avoids abrupt compatibility loss | Users may mistake output for supported evidence | Add separation and warnings in a later approved implementation task | Owner approval required before distributing or exposing it as a product surface |
| Reuse legacy MVP-candidate parser logic only after full validation | Some extraction logic may be salvageable | May accelerate delivery | Schema, timestamp, provenance, and failure assumptions are unvalidated | Validate or replace parser by parser | Required at each parser promotion |
| Do not reuse legacy non-MVP output in the supported path | Enforces scope and all-or-nothing support | Prevents misleading evidence claims | Mixing unsupported records contaminates conclusions | Requires future registry and data-path separation | Scope decision approved by DEV-0002; implementation requires a later task |
| Reuse existing AI/report code only after supported-record gating and citation validation | Presentation logic may be useful | Preserves review/report investment | Current inputs can include unsupported records and unresolved citations | Add strict retrieval and citation contracts later | Required before production use |

## 9. Current repository claim boundary

The repository may claim:

- it contains a legacy evidence-engine prototype;
- it contains implemented-but-unvalidated parsers and processing code;
- it contains a pre-existing FastAPI/SQLAlchemy/Alembic scaffold;
- narrow synthetic characterization tests pass where recorded; and
- selected components may be reusable after validation.

The repository may not claim:

- that the application currently supports Apple local backups;
- that any artifact parser or artifact family is supported;
- that file presence means successful or complete processing;
- that the current backend is production-ready, secure, authorized, or
  tenant-isolated;
- that current AI output is fully source-cited or restricted to supported
  evidence;
- that an encrypted backup can be decrypted;
- that missing records prove an event did not occur; or
- that legacy CLI output is a supported production report.

## 10. MVP acceptance boundary

The MVP is not accepted until all of the following are true:

- the approved unencrypted Apple local backup structure is validated;
- encrypted, incomplete, malformed, corrupted, and unsupported inputs produce
  explicit controlled statuses;
- source evidence remains immutable and is hashed;
- SQLite analysis uses controlled working copies with main database, WAL, SHM,
  and rollback-journal handling documented;
- every approved artifact family meets its complete FOR-004 profile;
- every normalized record preserves original and normalized values, timestamp
  provenance, parser execution metadata, and a stable source locator;
- failures and omissions cannot be confused with zero records;
- authentication, authorization, case boundaries, and tenant isolation are
  enforced server-side;
- search, AI, citations, and reports use only authorized supported records;
- citations resolve to inspectable source-backed records;
- required validation fixtures, regression tests, security tests, and
  acceptance criteria pass; and
- limitations and unsupported sources are visible to the user.

Partial completion does not satisfy MVP acceptance.

## 11. Consolidated scope-decision register

| Scope decision | Rationale | Customer value | Forensic risk | Implementation impact | Owner approval |
|---|---|---|---|---|---|
| Limit the initial input candidate to Apple local iPhone backups | Matches the product objective and permits a controlled acquisition profile | Clear intake expectations | Broad input claims would create unbounded schema and provenance risk | Build one validated input adapter and reject other formats explicitly | Approved by DEV-0002 |
| Prioritize unencrypted Apple local backups | Delivers useful ordinary-backup artifacts without password/decryption handling | Lowest-friction initial workflow | Backup content is incomplete compared with a physical image | Implement and validate unencrypted structure first | Approved by DEV-0002 |
| Detect and report encrypted backups without decrypting them | Meets classification needs while avoiding secret handling | Users receive a clear explanation instead of ambiguous failure | Attempting partial access could create false absence claims | Add detection and controlled `INACCESSIBLE` reporting in a later task | Approved by DEV-0002 |
| Exclude encrypted-only artifact claims | Health and keychain content cannot be assumed accessible | Prevents misleading conclusions | Absence could be incorrectly interpreted as device absence | Gate encrypted-only families and disclose acquisition limits | Approved by DEV-0002 |
| Exclude physical and full-filesystem acquisition | The product is not an acquisition tool | Keeps the MVP focused on evidence understanding | Treating a backup as a full image overstates completeness | Reject or classify these inputs as unsupported | Approved by DEV-0002 |
| Exclude Cellebrite and GrayKey ingestion | Those formats require separate adapters, licensing, validation, and provenance models | Avoids unreliable third-party import claims | Tool-export semantics and deleted data can be misinterpreted | No initial adapter or support claim | Approved by DEV-0002 |
| Treat extracted case directories as legacy-only input | Current code accepts them, but they are not the approved acquisition-format candidate | Preserves controlled compatibility while clarifying scope | Origin, completeness, and file relationships may be unverifiable | Quarantine existing behavior; future support needs separate approval | Initial exclusion approved; any later support requires owner approval |
| Keep backup metadata as an MVP candidate | Required to classify and describe the backup | Establishes defensible source context | Incorrect plist interpretation can misstate device or backup properties | Validate declared fields and schemas first | Candidate scope approved; parser promotion requires owner approval |
| Keep `Manifest.db` and file inventory as an MVP candidate | Foundation for source discovery, hashing, and coverage | Shows what the submitted backup contains and what is unavailable | Schema errors or missed files undermine every parser | Implement before content artifacts | Candidate scope approved; parser promotion requires owner approval |
| Keep messages as an MVP candidate | High-value communications evidence | Directly supports common investigative and attorney workflows | Schema, direction, timestamp, and attribution errors are material | Validate approved schemas and complete field coverage | Candidate scope approved; parser promotion requires owner approval |
| Keep message attachments as an MVP candidate | Links communications with exchanged files | Enables inspectable attachment evidence | Ambiguous path matches or direction claims can misassociate evidence | Validate joins, hashing, paths, MIME, and timestamp basis | Candidate scope approved; parser promotion requires owner approval |
| Keep call history as an MVP candidate | High-value communications timeline | Adds call activity to case review | Direction and timestamp assumptions can misstate events | Approve source/schema profiles and fixtures | Candidate scope approved; parser promotion requires owner approval |
| Keep contacts as an MVP candidate | Helps resolve identifiers without inferring identity | Improves review readability | Alias merging can falsely attribute a person | Preserve raw identifiers and cautious resolution provenance | Candidate scope approved; parser promotion requires owner approval |
| Defer Notes, Safari, Calendar, and other non-MVP legacy families | Prevents broad prototype code from expanding MVP scope | Concentrates validation on the agreed evidence set | Heuristic parsers can generate incomplete or misleading records | Quarantine code and outputs | Deferral approved; later inclusion requires owner approval |
| Exclude Health, keychain records, saved credentials, and credential recovery | Encrypted/secret material is outside the initial risk and input model | Avoids password and sensitive-secret exposure | Mishandling creates severe confidentiality and evidentiary risk | No parser, secret intake, storage, or claim in initial path | Exclusion approved; any later inclusion requires owner approval |
| Exclude arbitrary third-party applications | Unbounded schemas cannot satisfy all-or-nothing support | Predictable product boundaries | Generic parsing can appear authoritative without semantic validation | Reject generic output from supported path | Approved by DEV-0002 |
| Exclude deleted-data recovery | Local backup logical records are not physical recovery | Prevents overstatement of acquisition capability | Recovery claims require different methods and validation | No carving or deleted-record support claim | Approved by DEV-0002 |
| Exclude malware and spyware analysis | Requires specialist indicators, methods, and validation | Prevents unsupported compromise conclusions | False positive or negative claims are high impact | Quarantine hypothesis/legacy wording from supported claims | Approved by DEV-0002 |
| Retain legacy CLI only as quarantined compatibility behavior | Avoids deletion while preserving characterization | Supports controlled regression comparison | Users may mistake successful output for supported evidence | Separate registry/store/warnings require later implementation | Retention approved; external distribution requires owner approval |
| Require all-or-nothing promotion | Governing forensic rule | Creates predictable, defensible support | Partial implementation can silently omit evidence | Per-profile validation, traceability, tests, documentation, and approval | Approved by AGENTS.md and DEV-0002 |

## 12. Decisions requiring owner approval

The following remain unresolved and require explicit owner approval in their
respective tasks:

1. whether the legacy CLI will be distributed to users or retained only as an
   internal compatibility/test surface;
2. whether any extracted directory that is not a structurally valid Apple local
   backup will ever become an approved input type;
3. whether encrypted-backup decryption will be added after the initial release;
4. whether any deferred artifact family will enter a later release;
5. the final authentication, tenant, deployment, retention, and deletion model;
6. the supported iOS versions and schema fingerprints for each candidate
   artifact;
7. the final architecture decision after ARC-001 is authored; and
8. acceptance of each parser promotion and the complete MVP.

## 13. DEV-0002 decision

The MVP scope is confirmed as unencrypted-first Apple local backup review with
only the six artifact candidates listed above. Existing code is reconciled as
implemented-but-unvalidated legacy, experimental, or scaffold code. Runtime
quarantine remains to be implemented under a separately approved development
task; this document alone does not change execution behavior.

The project owner explicitly approved this reconciliation on 2026-07-24.
DEC-0001 records the approval. The approval completes DEV-0002 but does not
promote any input, artifact, parser, schema, workflow, or conclusion to
supported status.
