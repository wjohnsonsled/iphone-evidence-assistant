# FOR-016 — Manifest.db Relative-Path Lexical Profile

- Profile: `manifestdb-relative-path-lexical` version 1
- Source: proven query v1/v2 `Files.relativePath` observations
- Decisions: DEC-0067 implementation; DEC-0068 candidate completion
- Status: candidate-only, not Supported

Version 1 preserves exact raw value, SQLite storage class, complete
scope/query/locator provenance, Unicode/encoding state, lexical segments,
separator observations, resource outcome, and limitations.

TEXT is safe for lexical comparison only when it is nonempty, does not begin
with `/` or `\` or a drive-root indicator, contains no backslash, repeated `/`,
`.` segment, or `..` segment, and remains within caller-supplied positive
character, UTF-8 byte, and segment ceilings. Its canonical comparison
representation is the unchanged raw TEXT. Empty, unsafe, NULL, non-TEXT,
unavailable, failed, unevaluated, indeterminate, and resource-terminated states
remain distinct. Unicode TEXT is preserved without normalization; BLOB encoding
is unknown and never decoded.

No path is trimmed, repaired, joined, resolved, case-folded, Unicode-normalized,
or passed to a filesystem. Lexical safety does not establish a host-safe path,
file/container/physical-object existence, artifact identity, completeness,
compatibility, or support. Fixtures are synthetic, not Apple-produced.
