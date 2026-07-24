# FOR-004 — Artifact Support Matrix

## 1. Support rule

No artifact family is supported because a source file or implementation exists.
Support requires complete declared behavior, approved source discovery and
schema profiles, field and relationship coverage, timestamp handling,
provenance, raw-value preservation, explicit errors, validation fixtures,
regression tests, documented limitations, traceability, and acceptance review.

FOR-006 quarantines every legacy parser until those requirements are met.

## 2. Initial MVP matrix

| Artifact ID | Artifact family | Expected source | Input candidate | MVP | Current support status | Runtime classification |
|---|---|---|---|---|---|---|
| BAK-001 | Backup metadata | `Info.plist` | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| BAK-002 | Backup status | `Status.plist` | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| BAK-003 | Backup manifest metadata | `Manifest.plist` | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| BAK-004 | Backup file manifest | `Manifest.db` | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| BAK-005 | Backup file inventory | Derived from `Manifest.db` and stored files | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| MSG-001 | SMS/iMessage messages | `HomeDomain/Library/SMS/sms.db` | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| MSG-002 | Chats | `sms.db` | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| MSG-003 | Handles | `sms.db` | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| MSG-004 | Message attachments | `sms.db` and attachment files | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| CALL-001 | Call history | Approved CallHistory source to be profiled | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |
| CON-001 | Contacts | Approved AddressBook sources to be profiled | Apple local backup | Yes | CANDIDATE | Legacy/implemented-not-validated |

No row above is currently supported.

## 3. Deferred or excluded matrix

| Artifact ID | Artifact family | Initial MVP | Current support status | Supported-path treatment |
|---|---|---|---|---|
| NOTE-001 | Notes | No | UNSUPPORTED | Quarantined |
| SAF-001 | Safari history | No | UNSUPPORTED | Quarantined |
| CAL-001 | Calendar | No | UNSUPPORTED | Quarantined |
| HLT-001 | Health | No | UNSUPPORTED | Excluded; no encrypted-only claims |
| KEY-001 | Keychain-derived records | No | UNSUPPORTED | Excluded; no credential processing |
| CRED-001 | Saved credentials | No | UNSUPPORTED | Excluded |
| DEL-001 | Deleted/unallocated records | No | UNSUPPORTED | Excluded |
| APP-001 | Arbitrary third-party apps | No | UNSUPPORTED | Quarantined/excluded |
| MAL-001 | Malware/spyware analysis | No | UNSUPPORTED | Excluded |
| MAIL-001 | Mail | No | UNSUPPORTED | Quarantined |
| REM-001 | Reminders | No | UNSUPPORTED | Quarantined |
| PHOTO-001 | Photos | No | UNSUPPORTED | Quarantined |
| LOC-001 | Maps/location | No | UNSUPPORTED | Quarantined |
| KNOW-001 | KnowledgeC/CoreDuet | No | UNSUPPORTED | Quarantined |
| NOTIF-001 | Notifications | No | UNSUPPORTED | Quarantined |
| NET-001 | Broad network/system artifacts | No | UNSUPPORTED | Quarantined |

Physical/full-filesystem acquisition and Cellebrite/GrayKey ingestion are input
types, not artifact families, and are excluded by PRD-003 and PRD-007.

## 4. Controlled lifecycle and result statuses

Planning/lifecycle labels:

- `CANDIDATE`
- `IN_DEVELOPMENT`
- `VALIDATION_PENDING`
- `DEPRECATED`

Supported processing result statuses:

- `SUPPORTED_COMPLETE`
- `SUPPORTED_NO_RECORDS`
- `UNSUPPORTED`
- `INACCESSIBLE`
- `CORRUPTED`
- `FAILED`
- `EXCLUDED`

A lifecycle label is not a successful processing result. No parser may produce a
supported result until its declared profile is approved.

## 5. Required per-artifact profile

Before promotion, document:

- supported input and acquisition type;
- supported iOS versions;
- supported schema fingerprints;
- source paths and discovery method;
- required main, WAL, SHM, journal, and other companion files;
- parsed tables and fields;
- excluded tables and fields;
- join and directionality behavior;
- timestamp source fields, raw formats, conversions, precision, timezone basis,
  and limitations;
- raw and normalized value mapping;
- stable source-record locator format;
- error and omission behavior;
- known limitations;
- validation dataset and expected results;
- parser and registry versions;
- parser execution/audit record;
- test names and results;
- traceability entries; and
- owner or delegated forensic-review approval.

Validation of one schema profile does not authorize another.
