# Master Engineering Specification (MES-v1)

# Part 5 — Timeline, Correlation & Search Engine

## 49. Purpose

The Timeline Engine SHALL transform normalized records into a unified chronological
representation suitable for investigation, reporting, and AI retrieval.

## 50. Canonical Event Model

Every event SHALL include:

- Event UUID
- Evidence UUID
- Normalized Record UUID
- Artifact Family
- Event Type
- Primary Timestamp
- Timestamp Precision
- Time Zone
- Source Parser
- Provenance Reference
- Confidence Score

Events are immutable.

## 51. Time Normalization

All timestamps SHALL be normalized to UTC internally while preserving:

- original timestamp
- original timezone
- source precision

No timestamp shall be overwritten.

## 52. Event Types

Minimum supported categories:

- Communication
- Location
- Application
- Media
- System
- Network
- Account
- File
- Security

Unknown events remain categorized as UNKNOWN rather than inferred.

## 53. Correlation Engine

Correlations SHALL be evidence-based only.

Permitted signals:

- Shared identifiers
- Shared attachment references
- Shared conversation identifiers
- Temporal proximity
- Explicit foreign-key relationships

The engine SHALL NOT invent relationships.

## 54. Confidence

Confidence is assigned to correlations, not evidence.

Suggested bands:

- High
- Medium
- Low

Confidence SHALL never imply truth or authenticity.

## 55. Entity Resolution

Entities MAY include:

- Contact
- Phone Number
- Email
- Apple Account
- Device
- Application
- Attachment
- Conversation

Resolution SHALL preserve ambiguity rather than merging uncertain identities.

## 56. Search

Search SHALL operate only on normalized data.

Support:

- keyword
- UUID
- artifact family
- date range
- entity
- timeline window

Search SHALL never query raw evidence directly.

## 57. AI Retrieval Contract

AI retrieves:

Evidence → Normalized Records → Timeline Events → Provenance

If provenance validation fails, retrieval SHALL fail.

## 58. Acceptance Criteria

AC-0501 Unified timeline generated.

AC-0502 Original timestamps preserved.

AC-0503 Provenance retained.

AC-0504 Search returns deterministic results.

AC-0505 Correlations never created without supporting evidence.

## 59. Codex Execution Contract

Dependencies:

- MES Parts 1–5
- WP-0250

Implement:

- Timeline Engine
- Correlation Engine
- Search foundation

Run:

- unit
- integration
- regression
- synthetic timeline tests

Update:

- MES
- Backlog
- Decision Log

Commit locally.

Stop only for:

- owner review
- architecture conflict
- support promotion
- security decision

End of MES-v1 Part 5.
