# Master Engineering Specification (MES-v1)

# Part 7 — Database Architecture, Repository Layer & REST API

**Status:** Draft v1.0

---

# 72. Purpose

This section defines the persistence, repository, and API architecture for the MVP.

All external access SHALL occur through defined service and API boundaries.

---

# 73. Architectural Layers

Client
↓
REST API
↓
Service Layer
↓
Repository Layer
↓
PostgreSQL
↓
Evidence Storage

Each layer SHALL have a single responsibility.

---

# 74. Database Principles

The database SHALL:

- Preserve evidence relationships
- Support immutable evidence records
- Support transactions
- Preserve provenance
- Prevent cross-tenant access

Raw evidence SHALL NOT be stored inside normalized tables.

---

# 75. Core Tables

Minimum logical tables:

- tenants
- cases
- evidence
- controlled_copies
- hash_observations
- normalized_records
- timeline_events
- provenance_nodes
- provenance_edges
- parser_registry
- audit_events
- custody_events

Future tables SHALL be additive whenever practical.

---

# 76. Repository Contracts

Repositories SHALL expose typed operations only.

Examples:

- EvidenceRepository
- TimelineRepository
- ParserRepository
- ReportRepository

Business logic SHALL NOT reside in repositories.

---

# 77. Transaction Rules

A transaction SHALL be atomic.

If any required persistence operation fails:

- rollback
- emit audit event
- return deterministic error

Partial persistence is prohibited.

---

# 78. REST API

Initial endpoints MAY include:

POST /cases

POST /evidence

GET /cases/{id}

GET /timeline/{caseId}

GET /reports/{caseId}

POST /ai/query

API contracts SHALL remain versioned.

---

# 79. Authentication

The MVP SHALL support authenticated access.

Authorization SHALL occur before:

- evidence access
- AI queries
- report generation
- exports

Multi-tenant isolation SHALL be enforced at every repository query.

---

# 80. API Response Rules

Responses SHALL:

- return structured errors
- include correlation identifiers
- distinguish validation from system failures

HTTP status codes SHALL accurately reflect outcome.

---

# 81. Acceptance Criteria

AC-0701 Repository layer isolates SQL.

AC-0702 Transactions rollback correctly.

AC-0703 Cross-tenant access prevented.

AC-0704 API returns deterministic responses.

AC-0705 Audit events generated for failures.

---

# 82. Codex Execution Contract

Dependencies:

- MES Parts 1–7

Implement:

- Repository interfaces
- Transaction management
- REST API foundation
- Authentication scaffolding

Update:

- MES
- BACKLOG.md
- Decision Log
- Risk Register

Run:

- Unit tests
- API integration tests
- Repository tests
- Migration tests

Commit locally.

Stop only for:

- Owner review
- Architecture conflict
- Support promotion
- Security decision

End of MES-v1 Part 7.
