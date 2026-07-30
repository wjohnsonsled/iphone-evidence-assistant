# FOR-017 — Manifest.db Flags Observation Profile

- Profile: `manifestdb-flags-observation` version 1
- Source: proven query v1/v2 `Files.flags` observations
- Decisions: DEC-0069 implementation; DEC-0070 candidate completion
- Status: candidate-only, not Supported

The governing repository establishes that `Files.flags` has candidate INTEGER
affinity but establishes no bit meaning. Version 1 therefore preserves the
exact raw SQLite value, storage/value state, complete scope/query/locator
provenance, numeric representation, bit width, set-bit positions, resource
outcome, and limitations. `known_meanings` is always empty and every set bit is
explicitly unknown.

Zero, positive, negative, NULL, non-INTEGER, unavailable, read-failed,
unevaluated, indeterminate, and resource-exceeded values remain distinct.
Positive bit enumeration requires a caller-supplied maximum bit width from 1
through 4096 and stops before enumeration when exceeded.

No numeric or bit value establishes file type, file/directory existence,
deletion, user action, tampering, corruption, physical backup-object state,
artifact identity, completeness, compatibility, or support. Metadata BLOBs are
not decoded. Fixtures are synthetic and not Apple-produced.
