# FOR-018 — Manifest.db Metadata-BLOB Syntax Profile

- Profile: `manifestdb-file-bplist-syntax` version 1
- Source: explicitly authorized raw `Files.file` BLOB observations from proven
  query v1/v2 rows
- Decisions: DEC-0071 implementation; DEC-0072 candidate completion
- Status: candidate-only, not Supported

Version 1 recognizes only exact binary-plist `bplist00` structure. A
repository-local iterative scanner validates the trailer, offset table, object
offsets, token payload boundaries, reference bounds, graph cycles, and nesting.
It decodes only plist scalar syntax and array/dictionary references. DATA bytes
are never emitted. UID values remain syntactic scalars. No NSKeyedArchiver
class, Objective-C class, dynamic type, or arbitrary object is instantiated.
No key or scalar is assigned metadata meaning.

The caller must provide positive ceilings for BLOB bytes, declared objects,
nesting depth, scalar bytes, collection items, deterministic decoded-memory
estimate, and monotonic wall time. Cancellation and limits are checked between
objects and graph steps. Only completed immutable nodes are retained on
termination. Unknown formats, malformed structures, unsupported tokens,
cycles, invalid references, unavailable bytes, and resource outcomes remain
explicit and fail closed.

This is bounded syntactic characterization, not a universal plist decoder,
NSKeyedArchiver semantic decoder, metadata-field profile, Apple compatibility
claim, parser, artifact validation, physical-object proof, or support. XML
plists and binary-plist versions other than `00` are not decoded. Fixtures are
synthetic and not Apple-produced.
