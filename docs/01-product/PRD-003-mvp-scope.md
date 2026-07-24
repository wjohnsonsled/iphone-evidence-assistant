# PRD-003 — MVP Scope

## 1. Status and reconciliation

This scope was reconciled against the repository baseline by DEV-0002 on
2026-07-24. PRD-007 records the detailed decisions. Existing implementation is
not evidence of support, and no current parser or artifact family is approved
as supported.

## 2. Product objective

Build a secure, evidence-aware application that accepts a validated Apple local
iPhone backup and helps authorized investigators and attorneys understand
approved forensic artifacts through search, timelines, source inspection,
evidence-grounded AI, citations, and reporting.

The product is an evidence-understanding and review platform. It is not a
forensic acquisition tool or a complete representation of the device.

## 3. Input scope

The initial supported-input candidate is a structurally valid Apple local
iPhone backup.

The intake workflow must distinguish:

- unencrypted;
- encrypted;
- incomplete;
- malformed or corrupted; and
- unsupported input.

Unencrypted Apple local backups are the initial implementation and validation
priority. The MVP must not require an encrypted backup.

Encrypted backups must be detected and reported. Decryption is excluded from
the initial release unless separately approved. The initial release must not
accept or log backup passwords and must not make encrypted-only artifact claims.

Extracted case directories, physical/full-filesystem acquisitions, device
exploitation output, Cellebrite extraction ingestion, and GrayKey extraction
ingestion are not initial supported-input candidates. Pre-existing compatibility
behavior for extracted directories remains quarantined legacy behavior.

## 4. Initial artifact candidates

Only these artifact families are candidates for complete MVP support:

1. Backup metadata:
   - `Info.plist`;
   - `Status.plist`;
   - `Manifest.plist`.
2. `Manifest.db` and backup file inventory:
   - file identifier;
   - domain;
   - relative path;
   - file size;
   - source location;
   - SHA-256;
   - availability status.
3. Messages:
   - SMS;
   - iMessage;
   - chats;
   - handles;
   - approved fields;
   - direction where determinable.
4. Message attachments:
   - approved metadata;
   - message relationship;
   - source path;
   - hash;
   - MIME type where determinable.
5. Call history.
6. Contacts.

Candidate does not mean supported. Each family must satisfy the all-or-nothing
support rule before promotion.

## 5. Required MVP capabilities

### 5.1 Case and evidence-source management

- Create a case and stable internal identifier.
- Associate one or more controlled evidence sources with the case.
- Enforce server-side authorization and tenant isolation.
- Record material case actions.

### 5.2 Backup intake

- Validate Apple local backup structure.
- Detect and report encryption state.
- Preserve source evidence unchanged.
- generate and retain source SHA-256 hashes;
- create a deterministic intake inventory;
- separate controlled working copies from source evidence;
- record errors, omissions, corruption, and unsupported conditions; and
- produce an intake coverage report.

### 5.3 Artifact processing

- Execute only parsers in the approved supported registry.
- Preserve original and normalized values.
- Preserve timestamp source, raw value, format, conversion method, precision,
  timezone basis, and limitations.
- Maintain stable source provenance.
- Record parser name, version, schema fingerprint, and execution.
- Record controlled status per artifact family.
- Fail visibly when complete processing cannot be established.

### 5.4 Search, timeline, AI, and reporting

- Search and filter authorized supported records.
- Inspect original, normalized, provenance, and limitation data.
- Normalize comparable timestamps to UTC without silently assuming a timezone.
- Avoid representing uncertain ordering as exact.
- Ground AI only in authorized supported records.
- Require inspectable, resolvable citations for material claims.
- Distinguish facts, interpretations, uncertainty, and limitations.
- Produce attorney-readable reports with scope, sources, methods, findings,
  citations, coverage, unsupported-source disclosures, and limitations.

## 6. Deferred and excluded scope

The initial supported path excludes:

- Notes;
- Safari;
- Calendar;
- Health;
- keychain-derived records;
- saved credentials and credential recovery;
- arbitrary third-party applications;
- Mail, Reminders, Photos, Maps/location, KnowledgeC, notifications, and broad
  network/system parsing unless separately approved;
- deleted-data and unallocated-space recovery;
- malware and spyware analysis;
- physical and full-filesystem acquisition;
- jailbreaking and exploitation;
- Cellebrite and GrayKey ingestion;
- complete device or application coverage;
- attribution to a physical person;
- intent or motive determination;
- legal conclusions; and
- automatic testimony opinions.

Legacy code for an excluded family remains compatibility or experimental code
and must be quarantined under FOR-006.

## 7. MVP success boundary

The MVP is successful only when it:

1. accepts a validated supported unencrypted Apple local backup;
2. explicitly classifies encrypted, incomplete, malformed, corrupted, and
   unsupported input;
3. produces a complete source-file inventory and retained hashes;
4. processes every approved artifact family without silent omissions;
5. links every normalized record to a stable source locator;
6. preserves original and normalized values and timestamp provenance;
7. searches and reviews supported records within authorized case/tenant
   boundaries;
8. answers supported questions with inspectable citations;
9. produces a professional report containing sources, coverage, and
   limitations;
10. passes approved fixtures, regression, provenance, timestamp, authorization,
    security, and failure tests; and
11. explicitly reports unsupported, inaccessible, corrupted, failed, or
    excluded data.

Partial implementation does not satisfy this boundary.

## 8. Related controls

- PRD-007: detailed baseline reconciliation and claim boundary.
- FOR-004: artifact support matrix.
- FOR-006: legacy-parser quarantine policy.
- DOC-005 and PRD-006: repository baseline and capability inventory.
