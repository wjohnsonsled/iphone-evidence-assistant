# FOR-011 — Candidate Manifest.db Schema Profile

## Profile

- Identifier: `apple-manifestdb-schema`
- Version: `1`
- Status: candidate schema-recognition infrastructure
- Owner decision: DEC-0059
- Support effect: none

Recognition under this profile means only: the observed schema matches a
documented schema profile recognized by this software. It is not Apple backup,
parser, artifact, input, workflow, or device support and does not interpret
evidence.

## Basis

DEC-0008 controls the required case-insensitive identifiers:

- table `Files`;
- columns `fileID`, `domain`, `relativePath`, `flags`, and `file`.

Additional tables and columns are permitted but preserved as unknown
observations. The candidate affinity expectations—TEXT, TEXT, TEXT, INTEGER,
and BLOB respectively—come from the repository's approved synthetic fixtures
and implementation characterization. They are not represented as
authoritative Apple documentation.

Version 1 requires no primary key, uniqueness constraint, foreign key, index,
trigger, view, statistic, AUTOINCREMENT, or WITHOUT ROWID behavior. Indexes are
fingerprinted as informational schema observations only.

## SQLite preconditions

The validator operates only on a DEV-0205 verified controlled copy using an
immutable private read-only URI and `query_only`. It verifies:

- SQLite format-3 header;
- valid power-of-two page size from 512 through 65536;
- read format 1 or 2;
- schema format 1 through 4;
- schema readability and `sqlite_schema` availability;
- approved integrity preconditions;
- configured schema-enumeration and SQLite-work limits.

There is no repair, recovery, checkpoint, journal/WAL replay, vacuum, write,
row read, or evidence-value inspection.

## Observations and outcomes

Tables and columns have separate closed state vocabularies. Unknown additions
remain in raw and canonical schema observations. Missing required components
use `REQUIRED_SCHEMA_COMPONENT_MISSING`; affinity mismatch or duplicate modeled
components fail closed as invalid.

The only compatibility outcomes are:

- `SCHEMA_COMPATIBLE`;
- `SCHEMA_COMPATIBLE_WITH_UNKNOWN_OPTIONAL_ELEMENTS`;
- `SCHEMA_UNKNOWN`;
- `SCHEMA_NOT_RECOGNIZED`;
- `SCHEMA_REQUIRED_COMPONENT_MISSING`;
- `SCHEMA_INVALID`;
- `SCHEMA_CORRUPT`;
- `SCHEMA_NOT_EVALUATED`;
- `SCHEMA_INDETERMINATE`.

No nearest-match, best-match, iOS allowlist, or assumed future compatibility is
permitted.

## Fingerprint

Fingerprint profile:

- identifier: `manifestdb-schema-canonical-json-sha256`;
- version: `1`;
- algorithm: SHA-256;
- canonical input: deterministic UTF-8 JSON.

The canonical input includes normalized table and column names, declared
types, nullability, default-presence markers, primary-key positions, and
informational indexes. It excludes row counts, evidence values, timestamps,
page order, and record order. The fingerprint is a DEV-0405 observation, not
proof of schema equivalence, parser compatibility, or support.

## Limitations

The synthetic validation package is not an Apple-produced multi-version
fixture set. Future Apple schema changes require a new immutable profile,
validation package, and owner decision. DEV-0601 does not read `Files` rows,
Properties, property-list blobs, fileIDs, domains, relative paths, metadata, or
user evidence.
