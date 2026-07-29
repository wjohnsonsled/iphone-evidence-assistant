# FOR-014 — Canonical Identifier Framework and Manifest fileID Profile

## Profiles

- Framework: `canonical-identifier-normalization` version 1
- Concrete profile: `manifestdb-fileid-normalization` version 1
- Identifier class: `MANIFEST_FILE_ID`
- Decisions: DEC-0063 implementation; DEC-0064 candidate completion
- Status: owner-authorized COMPLETE candidate infrastructure, not Supported

The generic framework preserves immutable raw identifier observations, dynamic
SQLite storage class, complete source/query/locator provenance, versioned
syntax and normalization profiles, ordered transformations, explicit
comparison eligibility, stable serialization, prior-observation lineage, and
limitations. The only other controlled generic classes are
`SOURCE_DEFINED_IDENTIFIER` and `UNKNOWN_IDENTIFIER_CLASS`; DEV-0603 infers
neither from value shape.

## Input and provenance

Only `Files.fileID` values from explicitly approved
`manifestdb-files-query` v1 or v2 observations may enter the evidence path.
Adapters bind tenant, case, evidence source, artifact, controlled-copy identity,
Manifest.db identity, processing run, source table/column, ROWID locator,
locator/query profiles, observed storage class, upstream value state, and
timestamp. Detached caller strings are rejected; a separate function exists
only for explicitly marked deterministic synthetic fixtures.

## Syntax and transformations

Version 1 recognizes exactly 40 ASCII characters from `0-9`, `A-F`, or `a-f`.
It does not trim whitespace, remove prefixes/separators/braces, normalize
Unicode, repair characters, pad, truncate, fuzz, or derive values. A recognized
value has canonical form exactly 40 lowercase ASCII hexadecimal characters.

The closed transformation set is:

1. `NONE`;
2. `STRICT_ASCII_BLOB_DECODE`;
3. `ASCII_HEX_CASE_CANONICALIZATION`.

Strict BLOB decoding occurs only for authorized, bounded, source/run-scoped
bytes when every byte is ASCII. Arbitrary 20-byte BLOBs are never hex-expanded,
hashed, deserialized, or interpreted. Raw values remain separate from decoded
and canonical representations.

## Outcomes and comparison

The closed result vocabulary distinguishes canonical/normalized recognized
TEXT, NULL, empty TEXT/BLOB, length, character, non-ASCII, whitespace,
unsupported syntax, recognized/unrecognized/non-ASCII BLOB, unsupported
storage class, unavailable, read failure, not evaluated, and indeterminate.

`EXACT_RAW` requires compatible recognized raw storage classes.
`EXACT_CANONICAL` requires canonical values under the same v1 profile.
Malformed, empty, NULL, unsupported, unavailable, indeterminate, incompatible,
or insufficiently proven observations are `NOT_COMPARABLE`. Cross-tenant and
cross-case comparison is denied. There is no fallback between modes.

Canonical equality means only that two observations normalized to the same
canonical representation under the same compatible profile. It does not prove
file content, physical object, existence, readability, correctness,
uniqueness, artifact identity, duplication, completeness, tampering, or
corruption.

## Resources, serialization, and limits

Batch operations require positive caller ceilings for observations,
comparisons, projected bytes, deterministic memory estimate, and monotonic
wall-clock duration plus cancellation. Completed observations remain valid on
termination. There is no independent Files scan, physical-directory search, or
unbounded comparison matrix.

Comparison orchestration is caller-directed. Authorized forms are one explicit
pair, one subject against an explicitly supplied bounded candidate set, and an
explicit bounded sequence of pairs. Normalization is linear in supplied
observations; both comparison forms are linear in supplied candidates/pairs.
Implicit Cartesian products, all-pairs collection comparison, global matching,
and silently derived ceilings are outside DEV-0603.

Canonical JSON uses stable sorted fields, explicit profile versions,
deterministic NULL/length/transformation/limitation representation, and no host
paths or memory addresses. Raw BLOB bytes are represented only by bounded type
and length metadata, never serialized as bytes.

## Permanent limitations

Lexical recognition is not a verified SHA-1 or any hash conclusion.
Normalization is not physical backup-object resolution. Canonical equality is
not content identity. Repeated fileIDs are not duplicate-file conclusions.
Absence has not been evaluated. No physical path is constructed, no object is
opened, no evidence hash is calculated, and no content is parsed. The corpus is
synthetic and not Apple-produced. No parser, artifact, input, workflow, API, or
capability is Supported.
