# Master Engineering Specification (MES-v1)

# Part 3 — Evidence Model, Integrity, Provenance & Data Contracts

**Status:** Draft v1.0

---

# 24. Purpose

This section defines the canonical evidence model. Every component in the system SHALL
treat these definitions as authoritative.

---

# 25. Core Engineering Rule

The system SHALL distinguish:

- Original Evidence
- Controlled Copy
- Normalized Record
- Derived Analysis
- AI Conclusion

These are separate object types and SHALL never be conflated.

---

# 26. Evidence Object

Every evidence object SHALL include:

- Evidence UUID
- Tenant ID
- Case ID
- Source Type
- Intake Timestamp
- Current Lifecycle State
- Original Location
- Current Storage Location
- Integrity Status

Evidence UUIDs SHALL be immutable.

---

# 27. Controlled Copies

Processing SHALL occur only from approved controlled copies.

The original evidence SHALL remain read-only.

Every controlled copy SHALL record:

- parent evidence UUID
- creation timestamp
- tool version
- operator
- purpose

---

# 28. Hash Policy

Required:

- SHA-256

Future algorithms MAY be added.

Hash observations SHALL be append-only.

Hash mismatches SHALL prevent parser execution unless explicitly authorized by future policy.

---

# 29. Lifecycle

Minimum lifecycle:

REGISTERED

VALIDATED

HASH_VERIFIED

PROCESSING

NORMALIZED

REPORTED

ARCHIVED

Terminal states:

- REJECTED
- QUARANTINED
- ARCHIVED

Invalid transitions SHALL fail atomically.

---

# 30. Provenance

Every normalized record SHALL maintain provenance back to its originating evidence object.

Required provenance fields:

- source evidence UUID
- parser
- parser version
- artifact family
- extraction timestamp
- normalized record ID

No AI output may cite a normalized record lacking valid provenance.

---

# 31. Normalized Records

Normalized records SHALL:

- remain immutable
- reference originating evidence
- reference parser version
- preserve source timestamps
- distinguish missing values from unknown values

---

# 32. Parser Contracts

Every parser SHALL declare:

- supported input
- supported schema versions
- limitations
- omitted artifacts
- coverage
- known assumptions
- self-test

Unsupported artifacts SHALL NOT be inferred.

---

# 33. Data Quality

Every parser SHALL report:

- records parsed
- records rejected
- warnings
- unsupported structures
- fatal errors

Silent data loss is prohibited.

---

# 34. AI Citation Contract

Every AI-generated statement SHALL reference one or more normalized records.

If evidence is insufficient the AI SHALL:

- explain why
- identify limitations
- decline unsupported conclusions

---

# 35. Acceptance Criteria

AC-0301

Evidence UUID never changes.

AC-0302

Hash observations remain immutable.

AC-0303

Every normalized record validates provenance.

AC-0304

Parsers reject unsupported schema versions.

AC-0305

AI refuses unsupported conclusions.

---

# 36. Codex Execution Contract

Dependencies:

- WP-0250
- MES Parts 1–3

Implement next READY work package.

Update:

- Master Engineering Specification
- Decision Log
- Risk Register
- Backlog

Run:

- unit tests
- integration tests
- regression tests

Commit locally.

Stop only for:

- owner review
- architecture conflict
- support promotion
- security decision

End of MES-v1 Part 3.
