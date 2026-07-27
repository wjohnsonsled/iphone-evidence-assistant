# FOR-007 — Proposed Apple Local-Backup Compatibility Profile

## 1. Document control

- Task: DEV-0202
- Date prepared: 2026-07-27
- Status: APPROVED FOR DEV-0202 STAGE-B SYNTHETIC VALIDATION
- Runtime effect: isolated non-API validator implementation authorized
- Input/artifact support effect: none
- Profile identifier: `APPLE_LOCAL_BACKUP_PROFILE_PROPOSED_001`

The owner approved the profile decisions on 2026-07-27 for synthetic Stage-B
implementation. This approval is not a compatibility or support promotion.
DEC-0008 resolves the invalid-SQLite classification by separating independent
plist identity from database structural validity.

## 2. Evidence-basis labels

Every rule uses one of these labels:

- `APPLE_AUTHORITATIVE`: published by Apple;
- `SQLITE_AUTHORITATIVE`: published by the SQLite project;
- `EXTERNAL_IMPLEMENTATION_OBSERVATION`: behavior in an independent
  open-source implementation, not Apple authorization;
- `REPOSITORY_OBSERVATION`: pre-existing project code, not validation evidence;
- `SYNTHETIC_FIXTURE_PROPOSAL`: a fixture design that has not validated an
  Apple-produced backup; or
- `PROVISIONAL_OWNER_APPROVAL_REQUIRED`: an assumption requiring explicit
  approval.

## 3. Sources reviewed

### Apple authoritative

1. [Apple Support — Locate and manage backups](https://support.apple.com/en-euro/108809)
   documents the host locations and management of local iPhone/iPad backups.
   It does not document the internal backup directory, plist, or database
   schema.
2. [Apple Support — About encrypted backups](https://support.apple.com/en-euro/108353)
   confirms that local backups can be encrypted, are not encrypted by default,
   require a password for use, and may contain categories absent from
   unencrypted backups. It does not document an internal encryption flag.

No authoritative Apple source was found that specifies the `Manifest.plist`,
`Status.plist`, `Info.plist`, or `Manifest.db` internal contract. Internal rules
below are therefore not labeled Apple authoritative.

### SQLite authoritative

1. [SQLite URI filenames](https://www.sqlite.org/uri.html) defines `mode=ro`
   and `immutable=1` behavior and cautions that immutable files must not change.
2. [SQLite WAL](https://www.sqlite.org/wal.html) explains WAL/SHM relationships
   and read-only WAL database conditions.
3. [SQLite database file format](https://www.sqlite.org/fileformat.html)
   defines the `SQLite format 3\0` header, read/write format bytes, schema
   format, encoding, user version, and application ID fields.
4. [SQLite PRAGMA integrity_check](https://www.sqlite.org/pragma.html#pragma_integrity_check)
   defines the low-level consistency checks and the single `ok` result.
5. [SQLite — How to corrupt a database](https://www.sqlite.org/howtocorrupt.html)
   states that a rollback journal or WAL must be copied with the database when
   present and warns against mismatching companions.

### External implementation observation

[libimobiledevice `idevicebackup2.c`](https://raw.githubusercontent.com/libimobiledevice/libimobiledevice/master/tools/idevicebackup2.c),
reviewed 2026-07-27:

- checks `Info.plist` and `Manifest.plist` for restore/unback behavior;
- reads boolean `Manifest.plist` key `IsEncrypted`;
- reads `Status.plist` string key `SnapshotState` and requires `finished`
  before restore;
- writes/uses Info plist keys including `Product Version`,
  `Target Identifier`, and `Unique Identifier`.

libimobiledevice explicitly identifies itself as independent and not approved
by Apple. These observations are corroboration only.

### Repository observation

The quarantined legacy implementation:

- searches for `Manifest.db`, `Manifest.plist`, `Info.plist`, and
  `Status.plist`;
- queries a `Files` table for `fileID`, `domain`, `relativePath`, and `flags`;
  and
- accepts overly broad marker combinations in its legacy path validator.

These observations are inventory evidence only. They cannot establish support.

### Fixture basis

No Apple-produced, lawfully distributable, or independently validated
known-format fixture is currently approved. The proposed classification
fixtures would be synthetic and would test only declared rules, not prove that
the rules cover real Apple backups.

## 4. Proposed outcome vocabulary

Owner-requested outcomes:

- `INVALID_INPUT`
- `NOT_AN_APPLE_BACKUP`
- `APPLE_BACKUP_UNENCRYPTED`
- `APPLE_BACKUP_ENCRYPTED`
- `APPLE_BACKUP_CORRUPT`
- `APPLE_BACKUP_INCOMPLETE`
- `APPLE_BACKUP_UNSUPPORTED_VERSION`

Two additional outcomes are proposed because operational uncertainty and
conflicting evidence must not be collapsed into invalid input or corruption:

- `APPLE_BACKUP_INDETERMINATE`
- `APPLE_BACKUP_VALIDATION_FAILED`

Approval of these two additional outcomes is required.

## 5. A — Minimum identity checks

### Proposed identity observations

| Observation | Use | Basis | Approval state |
|---|---|---|---|
| Candidate is a DEV-0201 ready directory | Required boundary precondition | Approved architecture and DEV-0201 | Approved precondition |
| `Info.plist` exists and is a parseable plist dictionary | Strong identity observation | External implementation and repository observation | Provisional |
| `Info.plist` has nonempty string `Target Identifier` or `Unique Identifier` | Strong identity observation | External implementation observation | Provisional |
| `Manifest.plist` exists and is a parseable plist dictionary | Strong identity observation | External implementation and repository observation | Provisional |
| `Manifest.plist.IsEncrypted` exists and is Boolean | Strong identity observation and encryption signal | External implementation observation | Provisional |
| `Status.plist` is a parseable dictionary with string `SnapshotState` | Corroborating identity/completion observation | External implementation observation | Provisional |
| Unencrypted `Manifest.db` begins with the SQLite format-3 magic header | Corroborating identity observation | SQLite authoritative format; Apple use is provisional | Provisional for Apple identity |

### Proposed identity rule

Classify a candidate as having Apple-backup identity only when:

1. `Info.plist` satisfies its two strong observations; and
2. at least one of:
   - `Manifest.plist` satisfies both strong observations;
   - `Status.plist` satisfies its corroborating observation; or
   - an unencrypted candidate has a SQLite format-3 `Manifest.db`.

Apple-like filenames alone are insufficient. If this threshold is not met,
return `NOT_AN_APPLE_BACKUP`, unless an operational failure prevents a reliable
decision, in which case return `APPLE_BACKUP_VALIDATION_FAILED`.

This threshold is entirely provisional.

## 6. B — Structural-completeness checks

### Proposed required files

- `Info.plist`
- `Manifest.plist`
- `Status.plist`
- `Manifest.db`

Basis: owner-requested checks plus external/repository observations. Apple does
not publicly document this as a complete requirement.

### Proposed optional companions

- `Manifest.db-wal`
- `Manifest.db-shm`
- `Manifest.db-journal`

Their absence is acceptable. Their presence requires them to be copied and
validated as a relationship with `Manifest.db`.

### Proposed acceptable missing material

- SQLite companions when absent;
- backup payload shard directories during identity determination only.

Payload layout validation and manifest-to-file reconciliation remain DEV-0206
through DEV-0208 and are not part of this profile gate.

### Proposed incomplete conditions

After minimum identity is established:

- any required file is missing;
- a required plist lacks a required identity/completion key;
- `Status.plist.SnapshotState` is present and not exactly `finished`;
- a required file is zero bytes; or
- a companion-file set changes while the controlled copy is created.

The last condition may instead be classified as validation failure; owner
selection is required.

### Proposed corrupt conditions

After minimum identity is established:

- a present required plist cannot be decoded as a plist dictionary;
- a required key has an impossible type;
- an unencrypted `Manifest.db` has an invalid SQLite header;
- read-only SQLite open fails with a format/corruption error;
- `PRAGMA integrity_check` does not return exactly one `ok` row; or
- copied bytes fail source/copy/source hash verification.

Hash/copy instability is also a candidate for validation failure rather than
corruption; owner selection is required.

## 7. C — Encryption-state checks

### Proposed primary source

`Manifest.plist.IsEncrypted` Boolean:

- `true` -> encrypted;
- `false` -> unencrypted;
- absent/wrong type -> indeterminate or incomplete according to precedence.

Basis: external implementation observation only. Apple confirms local-backup
encryption exists but does not publicly identify this field.

### Proposed corroborating observations

- encrypted `Manifest.db` may not present a SQLite format-3 header;
- presence of keybag-related plist data may corroborate encryption but must not
  be required or interpreted until separately profiled.

No password is accepted, logged, stored, or attempted.

### Proposed conflict handling

- `IsEncrypted=true` with a plaintext SQLite `Manifest.db` ->
  `APPLE_BACKUP_INDETERMINATE`;
- `IsEncrypted=false` with a non-SQLite `Manifest.db` ->
  `APPLE_BACKUP_CORRUPT` unless an approved encrypted-manifest signature later
  proves the flag conflict, then `APPLE_BACKUP_INDETERMINATE`;
- missing/wrong-type `IsEncrypted` after identity is otherwise established ->
  `APPLE_BACKUP_INCOMPLETE` or `APPLE_BACKUP_INDETERMINATE` (owner choice
  required).

For an encrypted outcome, no SQLite table or integrity check is attempted
because the initial MVP does not decrypt.

## 8. D — SQLite validation checks

These checks apply only after the candidate is provisionally classified
unencrypted.

1. Create a verified controlled copy of main/WAL/SHM/journal files.
2. Preserve exact companion basenames in one working directory.
3. Open only the copied main database with SQLite URI read-only mode and private
   cache; use immutable mode only after verified copy stability.
4. enable connection-level query-only behavior;
5. run full `PRAGMA integrity_check`;
6. read `sqlite_schema` for table names;
7. read `PRAGMA table_info` only for proposed required tables;
8. close the connection;
9. verify copied-file hashes remain unchanged; and
10. record and perform cleanup.

Prohibited operations include schema changes, writes, `VACUUM`, journal-mode
changes, checkpointing, repair, recovery against source files, and attaching
unapproved databases.

### Proposed schema family

`MANIFEST_FILES_V1_PROPOSED`:

- required table: `Files`;
- required columns: `fileID`, `domain`, `relativePath`, `flags`;
- optional column for this validation stage: `file`;
- other tables/columns permitted but recorded.

Basis: repository observation and independent implementation/community
observation, not authoritative Apple documentation. Owner approval and
known-format fixture validation are required.

### Proposed schema fingerprint

Compute SHA-256 over canonical UTF-8 JSON containing:

- sorted non-internal table names;
- for each table, sorted `PRAGMA table_info` records containing column name,
  declared type, not-null flag, default-presence marker, and primary-key
  position;
- SQLite header read/write version bytes;
- SQLite schema format number;
- `PRAGMA user_version`; and
- `PRAGMA application_id`.

This is a derived schema fingerprint, not an evidence-file hash.

## 9. E — Compatibility rules

### Proposed accepted database format

- SQLite magic header `SQLite format 3\0`;
- SQLite read-format version 1 or 2;
- SQLite schema format 1 through 4.

These are SQLite-format compatibility rules, not Apple backup support rules.

### Proposed accepted Apple schema family

No Apple schema fingerprint is currently accepted.

Owner may approve `MANIFEST_FILES_V1_PROPOSED` for synthetic implementation,
but synthetic success alone must remain `IMPLEMENTED_TASK_VALIDATED`, not input
support. At least one approved known-format fixture and separate input-support
review would still be required.

### Unsupported and unknown versions

- structurally readable SQLite with an unapproved schema family ->
  `APPLE_BACKUP_UNSUPPORTED_VERSION`;
- SQLite read-format version greater than 2 ->
  `APPLE_BACKUP_UNSUPPORTED_VERSION`;
- unknown `Manifest.plist.Version` alone does not cause unsupported status;
- newer iOS `Product Version` alone does not cause unsupported status; and
- a newer iOS version with an approved structure/schema remains compatible.

### iOS version

`Info.plist.Product Version` is recorded as informative provenance only. It is
never dispositive by itself.

## 10. F — Proposed classification precedence

Apply the first matching outcome:

1. `INVALID_INPUT`
   - DEV-0201 did not yield a ready result or the supplied result is malformed.
2. `APPLE_BACKUP_VALIDATION_FAILED`
   - operational failure, unsafe copy, cleanup failure affecting assurance,
     source instability, or inability to complete mandatory checks.
3. `NOT_AN_APPLE_BACKUP`
   - minimum identity threshold is not met and no operational uncertainty
     prevents that decision.
4. `APPLE_BACKUP_INCOMPLETE`
   - identity is established but a required component/key is missing,
     zero-length, or snapshot state is not `finished`.
5. `APPLE_BACKUP_INDETERMINATE`
   - required observations conflict and no approved rule resolves them.
6. `APPLE_BACKUP_ENCRYPTED`
   - complete identity/structure checks pass and `IsEncrypted=true`; no
     encrypted database parsing occurs.
7. `APPLE_BACKUP_CORRUPT`
   - required present plist is malformed, unencrypted SQLite is malformed, or
     integrity check fails.
8. `APPLE_BACKUP_UNSUPPORTED_VERSION`
   - structure/integrity pass but format/schema is unapproved or incompatible.
9. `APPLE_BACKUP_UNENCRYPTED`
   - all approved unencrypted checks pass.

This precedence is proposed. It deliberately places encrypted before SQLite
integrity because encrypted `Manifest.db` is not expected to be plaintext
SQLite.

## 11. G — Limitations

The validator would prove only that:

- the inspected directory met the approved identity and structural profile;
- the declared encryption signal was interpreted under the approved rule;
- an unencrypted controlled copy passed declared SQLite checks;
- the observed schema matched an approved compatibility profile; and
- observations were captured deterministically.

It would not prove:

- that the backup is a complete representation of the device;
- that every backup file is present or authentic;
- that the acquisition was performed correctly;
- that content artifacts are readable, complete, or supported;
- that deleted data can be recovered;
- that an encrypted backup can be decrypted;
- that any parser or artifact family is supported; or
- that absence of a record proves an event did not occur.

Structural validity is not evidentiary completeness. Detection is not artifact
support.

## 12. Required owner decisions

Approve, revise, or reject:

1. the two additional outcomes;
2. the minimum identity threshold;
3. required files and plist keys;
4. `SnapshotState=finished` as a completeness rule;
5. the encryption source and conflict handling;
6. whether copy/source instability is corrupt, incomplete, or validation
   failure;
7. `MANIFEST_FILES_V1_PROPOSED` and its required columns;
8. the schema-fingerprint algorithm;
9. the classification precedence; and
10. the fixture evidence required before any compatibility or support claim.

## 13. Approved controlling addendum — DEC-0008

This addendum replaces conflicting provisional text above.

Independent identity requires a validated directory, regular `Manifest.db`, at
least one regular identity plist, and at least one safely parsed recognized
field. Initial recognized fields are:

- `Info.plist`: `Product Version`, `Target Identifier`, `Unique Identifier`;
- `Manifest.plist`: `IsEncrypted`;
- `Status.plist`: `SnapshotState`.

SQLite validity is observed separately. Invalid SQLite with independent
identity is `APPLE_BACKUP_CORRUPT`; invalid or valid SQLite without independent
identity is `NOT_AN_APPLE_BACKUP`, except that safely readable but insufficient
identity observations may be `APPLE_BACKUP_INDETERMINATE`. Operational
inspection failure is `APPLE_BACKUP_VALIDATION_FAILED`.

`MANIFEST_FILES_V1` requires case-insensitive SQLite identifiers for table
`Files` and columns `fileID`, `domain`, `relativePath`, `flags`, and `file`.
Additional tables and columns are allowed. Canonical deterministic UTF-8 JSON
records normalized tables, columns, declared types, nullability, primary-key
position, and indexes; its SHA-256 is the schema fingerprint.

Synthetic validation does not establish production compatibility. The
Apple-produced multi-version validation package and a separate owner decision
remain mandatory before any compatibility or support claim.

## 14. Approved encryption addendum — DEC-0009

For DEV-0202, `Manifest.plist.IsEncrypted` is the only encryption signal.
Boolean true records encrypted; Boolean false records unencrypted. Either
controls the final encrypted/unencrypted outcome only after all
higher-precedence rules. Missing or non-Boolean is indeterminate. Operational
inability to inspect the value is validation failure.

Contradictory-signal handling is removed from this profile. Do not infer
encryption from filenames, `Manifest.db` behavior, iOS or backup versions,
directory names, keybag-like files, entropy, parser behavior, password prompts,
third-party observations, or undocumented plist keys. Earlier provisional
conflict text is superseded by this addendum.

Secondary signals are deferred to DEV-0211 pending sourced characterization,
precedence and conflict rules, synthetic and Apple-produced fixtures, a revised
profile, and owner approval.
