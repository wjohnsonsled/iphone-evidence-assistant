# FOR-010 — Apple Metadata Normalization Profiles

## Status and boundary

DEC-0056 approves two version 1 candidate normalization profiles:

- `apple-backup-identifier-normalization`;
- `apple-product-version-normalization`.

They provide deterministic, lossless comparison observations only. They do not
establish device attribution, authenticity, Apple or parser compatibility,
artifact support, or support promotion. Raw observations remain immutable and
independently addressable through the DEV-0406 typed-value envelope.

## Identifier profile version 1

Every call declares one of these classes:

- `DEVICE_IDENTIFIER`;
- `BACKUP_IDENTIFIER`;
- `BACKUP_ROOT_NAME`;
- `SERIAL_NUMBER`;
- `PRODUCT_IDENTIFIER`;
- `SOURCE_DEFINED_IDENTIFIER`;
- `UNKNOWN_IDENTIFIER_CLASS`.

The recognized device/backup/root textual syntaxes are exactly 40 hexadecimal
characters or 8 hexadecimal characters, a required hyphen, and 16 hexadecimal
characters. Hexadecimal alphabetic characters are lowercase only in the
separate canonical comparison representation. The raw form and required
separator remain unchanged.

Serial and source-defined identifiers are opaque: only leading and trailing
ASCII whitespace may be removed. Product identifiers recognize only the
candidate structured form `[letter][letters-or-digits]*,[digits]+` and preserve
case. Unknown classes, non-ASCII values, unsupported punctuation, altered
separators, internal whitespace in hex syntax, and malformed values are not
repaired.

A backup-root name always remains `BACKUP_ROOT_NAME`. Even exact canonical
agreement with a device-identifier observation means only textual agreement
under this profile; it does not prove that the folder identifies a physical
device or was not renamed.

## Product-version profile version 1

The supported grammar is one or more unsigned decimal components separated by
periods, with no empty component, embedded whitespace, prefix, suffix, sign,
exponent, or hexadecimal notation. Leading/trailing ASCII whitespace may be
removed as a recorded transformation.

The observation preserves:

- the full raw text;
- exact raw text for each component;
- component count;
- arbitrary-size non-negative integer values;
- a leading-zero flag for each component;
- normalized canonical text, when available;
- transformation provenance and limitations.

No zero component is appended or removed. Thus `17`, `17.0`, and `17.0.0`
remain different component sequences. Build versions, product identifiers,
backup-format versions, and schema fingerprints remain separate observation
types.

## Comparison operations

Version 1 implements:

- `EXACT_RAW_MATCH`;
- `EXACT_CANONICAL_TEXT_MATCH`;
- `EXACT_COMPONENT_SEQUENCE_MATCH`;
- `ORDERED_COMPONENT_COMPARISON`;
- `NOT_COMPARABLE`.

Identifier comparison requires the same explicit identifier class. Component
comparison requires valid dotted-numeric observations and the same component
count. No mode performs fuzzy matching, suffix removal, separator repair,
class conversion, or trailing-zero padding.

## Provenance and limitations

Every normalized observation retains tenant, case, evidence-source,
source-artifact, source-file, source-field, reader, processing-run, normalizer,
profile, method, time, state, and limitation data. Normalized representations
are linked through a DEV-0406 `ValueTransformation`; raw representations are
never overwritten.

Unsupported values remain valid raw observations. Product-version ordering is
informative only. DEV-0601 remains the sole governing task for candidate
Manifest.db schema compatibility.
