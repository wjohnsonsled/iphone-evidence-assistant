# Master Engineering Specification (MES-v1)

# Part 6 — AI Retrieval, Reasoning & Attorney Reporting

**Status:** Draft v1.0

---

# 60. Purpose

This section defines how artificial intelligence SHALL interact with digital evidence.

The AI is an evidence analysis assistant, not an evidence source.

---

# 61. AI Operating Principles

The AI SHALL:

- reason only from normalized evidence
- cite supporting records
- disclose limitations
- distinguish facts from inferences
- refuse unsupported conclusions

The AI SHALL NOT:

- fabricate evidence
- invent timeline events
- speculate beyond available artifacts
- conceal uncertainty

---

# 62. Retrieval Pipeline

Every response SHALL follow this sequence:

1. Receive user question
2. Identify relevant evidence scope
3. Retrieve normalized records
4. Validate provenance
5. Rank supporting records
6. Generate answer
7. Attach citations
8. State limitations

If provenance validation fails, the response SHALL fail safely.

---

# 63. Evidence Hierarchy

The AI SHALL prioritize:

1. Original evidence provenance
2. Normalized records
3. Timeline events
4. Correlation results
5. Derived summaries

AI-generated summaries SHALL never become evidence.

---

# 64. Citation Contract

Every substantive conclusion SHALL reference one or more normalized records.

Responses SHOULD identify:

- Evidence UUID
- Artifact family
- Event timestamp (when applicable)
- Parser version (when relevant)

Narrative text without supporting evidence SHALL be identified as analysis or inference.

---

# 65. User Questions

The AI SHALL support questions such as:

- What communications occurred?
- What happened before or after an event?
- Which artifacts support this conclusion?
- Which evidence contradicts this theory?
- What evidence is missing?

When evidence cannot answer a question, the AI SHALL say so.

---

# 66. Reporting

Reports SHALL separate:

## Evidence

Observed facts supported by artifacts.

## Analysis

Reasoned interpretation of evidence.

## Limitations

Known gaps, unsupported areas, parser limitations, and assumptions.

The sections SHALL remain distinct.

---

# 67. Hallucination Prevention

The AI SHALL refuse to:

- identify nonexistent artifacts
- invent dates
- invent participants
- infer intent without evidentiary support
- attribute actions to a person without supporting evidence

---

# 68. Explainability

For every conclusion, the AI SHOULD be able to explain:

- why it reached the conclusion
- which artifacts support it
- what evidence would change the conclusion
- what limitations remain

---

# 69. Attorney-Focused Output

Unless otherwise requested, responses SHOULD:

- use plain English
- avoid unnecessary technical jargon
- define specialized forensic terms
- distinguish observed facts from opinion
- avoid legal conclusions

The system SHALL assist legal professionals but SHALL NOT provide legal advice.

---

# 70. Acceptance Criteria

AC-0601 Every AI answer cites supporting evidence.

AC-0602 Unsupported questions receive an explicit limitation.

AC-0603 AI never fabricates artifacts.

AC-0604 Facts and analysis remain separate.

AC-0605 Provenance validation succeeds before retrieval.

---

# 71. Codex Execution Contract

Dependencies:

- MES Parts 1–6
- Evidence integrity infrastructure
- Timeline engine

Implement:

- Retrieval layer
- Citation framework
- AI response formatter
- Report generation foundation

Update:

- MES
- BACKLOG.md
- Decision Log
- Risk Register

Run:

- Unit tests
- Integration tests
- AI regression tests
- Synthetic evidence validation

Commit locally.

Stop only for:

- Owner review
- Architecture conflict
- Support promotion
- Security decision

End of MES-v1 Part 6.
