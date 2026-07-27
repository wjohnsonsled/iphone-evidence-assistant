# Master Engineering Specification (MES-v1)

# Part 4 — Parser Framework & Apple Backup Support

**Status:** Draft v1.0

---

# 37. Purpose

This section defines the parser framework. Every parser SHALL conform to the same lifecycle,
interfaces, validation rules, provenance requirements, and reporting behavior.

---

# 38. Parser Philosophy

Parsers SHALL:

- Read evidence only.
- Never modify evidence.
- Produce deterministic output.
- Declare limitations.
- Produce normalized records.
- Emit provenance.
- Report coverage.

Parsers SHALL NOT infer unsupported artifacts.

---

# 39. Parser Registry

Every parser SHALL register:

- Parser ID
- Name
- Version
- Artifact Family
- Supported Input
- Supported Schema Profiles
- Status (Candidate/Supported)
- Owner Approval Reference

Only "Supported" parsers may be enabled for production workflows.

---

# 40. Parser Lifecycle

1. Validate Input
2. Validate Integrity
3. Detect Schema
4. Parse Records
5. Normalize Records
6. Emit Provenance
7. Produce Coverage Report
8. Complete Self-Test

Failure at any stage SHALL prevent downstream processing.

---

# 41. Apple Backup Input

MVP supports only Apple local iPhone backups approved by the input validation layer.

The parser SHALL reject:

- Unknown layouts
- Unsupported schema profiles
- Corrupt inputs
- Integrity failures

The parser SHALL never repair evidence.

---

# 42. Candidate Artifact Families

Initial candidate families:

- Backup metadata
- Manifest inventory
- SMS / iMessage
- Call history
- Contacts
- Attachments

Support status remains candidate until owner approval.

---

# 43. Normalization Contract

Each parser SHALL output normalized records using canonical field names.

Every record SHALL include:

- Record UUID
- Evidence UUID
- Parser Version
- Source Location
- Source Timestamp(s)
- Artifact Family
- Provenance Reference

Missing values SHALL be explicit, not implied.

---

# 44. Coverage Reporting

Every parser SHALL produce a coverage report containing:

- Records discovered
- Records normalized
- Records rejected
- Unsupported structures
- Parser warnings
- Known limitations

Coverage reports SHALL be preserved with the case.

---

# 45. Parser Self-Test

Every parser SHALL include synthetic fixtures demonstrating:

- Successful parsing
- Empty dataset handling
- Unsupported schema handling
- Integrity failure handling
- Malformed record handling

No parser is complete without self-tests.

---

# 46. Compatibility Profiles

Compatibility SHALL be versioned.

Unknown profile:

- reject parsing
- report unsupported profile
- preserve evidence

Future profiles SHALL be added through owner-approved work packages.

---

# 47. Acceptance Criteria

AC-0401 Parser registry entry required.

AC-0402 Provenance emitted for every normalized record.

AC-0403 Coverage report generated.

AC-0404 Synthetic fixtures pass.

AC-0405 Unsupported profiles rejected deterministically.

---

# 48. Codex Execution Contract

Read:

- MES Parts 1–4
- ARC-001
- ARC-002
- BACKLOG.md

Implement only the next READY parser-related work package.

Update:

- MES
- Backlog
- Decision Log
- Risk Register

Run:

- Unit tests
- Integration tests
- Regression tests
- Parser self-tests

Commit locally.

Stop only for:

- Owner review
- Architecture conflict
- Support promotion
- Security decision

End of MES-v1 Part 4.
