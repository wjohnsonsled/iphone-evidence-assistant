# QMS-013 — DEV-0603 Identifier Normalization Validation

## Scope

Candidate validation of `canonical-identifier-normalization` v1 and
`manifestdb-fileid-normalization` v1 under DEC-0063, using synthetic fixtures
only.

## Permanent limitations

- Lexical 40-character hexadecimal recognition is not SHA-1 verification,
  content hashing, cryptographic integrity, or knowledge of Apple generation.
- Normalization is not physical resolution, file existence, artifact identity,
  parsing, authenticity, or completeness.
- Canonical equality is textual agreement only, not content/object identity.
- Repeated fileIDs are not duplicate, orphan, absence, tampering, or corruption
  conclusions; absence has not been evaluated.
- Strict ASCII BLOB decoding is bounded representation handling, not metadata
  decoding or interpretation.
- Corpus values are deterministic synthetic identifiers, not Apple-produced or
  customer evidence and are unsuitable for supported-record seeding.
- No migration, persistence, public API, physical search, file opening,
  evidence hash, parser activation, registry entry, supported record, real
  evidence, production use, deployment, or support promotion exists.
- DEV-0604 through DEV-0607 and DEV-0609 remain independent owner gates.
- Supported Parser Registry entries and supported normalized records remain
  zero.

Validation results:

- DEV-0603 focused: 40 passed;
- combined DEV-0601/DEV-0602/DEV-0602A/DEV-0603: 80 passed;
- backend regression: 487 passed with the accepted TestClient warning;
- legacy characterization: 5 passed;
- compilation, exact dependency lock, `pip check`, Alembic single head/history,
  offline migration SQL, repository hygiene, and diff checks: passed.

## Comparison complexity limitation

Only explicit-pair and one-subject-to-explicit-candidate-set orchestration is
implemented. Both are linear in caller-supplied work and enforce comparison,
projected-byte, deterministic-memory, monotonic-time, and cancellation
ceilings before the next comparison. No implicit Cartesian product, all-pairs
engine, global matching, persistent index, or duplicate/content conclusion
exists.
