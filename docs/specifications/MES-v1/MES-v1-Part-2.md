# Master Engineering Specification (MES-v1)

# Part 2 — System Architecture & Repository Design

**Status:** Draft v1.0

---

# 12. Architectural Objectives

The architecture shall:

- Preserve evidence integrity.
- Separate evidence ingestion from analysis.
- Isolate parsers from business logic.
- Keep AI independent of raw evidence.
- Support deterministic testing.
- Scale from single-user MVP to multi-tenant SaaS.

---

# 13. High-Level Architecture

```
Apple Backup
      │
      ▼
Input Validation
      │
      ▼
Evidence Registration
      │
      ▼
Integrity Verification
      │
      ▼
Supported Parser Layer
      │
      ▼
Normalized Evidence Store
      │
      ▼
Timeline & Correlation
      │
      ▼
AI Retrieval Layer
      │
      ▼
Attorney Reports / REST API / UI
```

Each layer has a single responsibility and communicates only through defined interfaces.

---

# 14. Repository Layout

```
app/
    api/
    core/
    evidence/
    parsers/
    provenance/
    reporting/
    search/
    services/
    timeline/

tests/
    unit/
    integration/
    regression/
    characterization/
    synthetic/

docs/
engineering-spec/

alembic/
```

No parser may directly access UI or API code.

---

# 15. Dependency Rules

Allowed:

Input → Evidence → Parser → Store → Timeline → AI → Reports

Forbidden:

- AI reading raw evidence.
- UI calling parsers directly.
- Parsers modifying evidence.
- Reports bypassing normalized records.

---

# 16. Repository Layer

All database access shall occur through repository interfaces.

Repositories shall:

- hide SQL implementation
- provide transactions
- return typed models
- support testing with synthetic fixtures

---

# 17. Service Layer

Business rules belong only in services.

Examples:

- EvidenceService
- IntegrityService
- TimelineService
- ReportService
- AIRetrievalService

---

# 18. Parser Isolation

Every parser:

- read-only
- deterministic
- independently testable
- versioned
- registered
- reports coverage and limitations

No parser may infer unsupported artifacts.

---

# 19. Configuration

Environment-specific values shall be externalized.

Never hard-code:

- database credentials
- API keys
- tenant identifiers
- filesystem roots

---

# 20. Logging

Every significant operation shall emit structured logs.

Logs shall include:

- timestamp
- component
- correlation id
- evidence UUID (when applicable)
- severity
- outcome

---

# 21. Error Handling

Errors shall be classified:

- Validation
- Integrity
- Parser
- Repository
- Service
- AI
- System

Errors shall never be silently ignored.

---

# 22. Documentation Requirements

Every work package shall update:

- Master Engineering Specification
- Backlog
- Decision Log (if architecture changes)
- Risk Register (if new risks identified)

---

# 23. Codex Execution Contract

Before implementation:

1. Read MES Parts 1–2.
2. Verify clean working tree.
3. Read BACKLOG.md.
4. Select next READY task.

After implementation:

- run all required tests
- update documentation
- commit locally

Stop only for:

- owner review
- architecture conflict
- support promotion
- security decision

End of MES-v1 Part 2.
