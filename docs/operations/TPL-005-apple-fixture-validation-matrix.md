# Apple Fixture Validation Matrix Template

Current working package: `CAF-2026-001`. All execution rows remain `NOT_EVALUATED`.

For every row record governing task/decision/profile, expected and actual
outcome, `PASS`/`FAIL`/`INDETERMINATE`, limitations, source citation, and
validation evidence.

1. Input registration
2. Source hashing
3. Apple backup structure validation
4. Encryption-state determination
5. Top-level metadata discovery
6. Metadata reading
7. Metadata normalization
8. Manifest.db schema recognition
9. Files-table controlled query
10. FileID normalization
11. Domain observation
12. Relative-path observation
13. Flags observation
14. Metadata-BLOB syntax behavior
15. Manifest inventory coverage
16. Physical backup-object inventory
17. Physical-object hashing
18. Manifest row-to-object resolution
19. Coverage reconciliation
20. Ground-truth comparison

Allowed characterization outcomes: `EXPECTED_OBSERVATION_FOUND`,
`EXPECTED_OBSERVATION_NOT_FOUND`, `UNEXPECTED_OBSERVATION_FOUND`,
`SOURCE_NOT_AVAILABLE`, `PROFILE_NOT_APPLICABLE`, `PROFILE_INCOMPATIBLE`,
`PROCESSING_PARTIAL`, `VALIDATION_FAILED`, `INDETERMINATE`, `NOT_EVALUATED`.
