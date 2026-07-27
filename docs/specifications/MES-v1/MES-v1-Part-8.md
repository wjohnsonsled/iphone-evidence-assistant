# Master Engineering Specification (MES-v1)

# Part 8 — Frontend Architecture & Investigator Workflow

**Status:** Draft v1.0

---

# 83. Purpose

This section defines the MVP user experience and frontend architecture.

The interface SHALL prioritize evidence integrity, explainability, and investigator productivity.

---

# 84. Design Principles

The application SHALL:

- Be evidence-first
- Be read-only with respect to evidence
- Minimize clicks for common investigative tasks
- Surface provenance for every AI-supported conclusion
- Clearly distinguish supported from unsupported capabilities

---

# 85. Primary Workflow

1. Authenticate
2. Select Case
3. Review Case Summary
4. Inspect Evidence Inventory
5. Explore Timeline
6. Search & Filter
7. Ask AI Questions
8. Review Evidence Citations
9. Generate Report
10. Export Approved Results

Users SHALL be able to return to any previous step without altering evidence.

---

# 86. Primary Screens

Minimum MVP screens:

- Login
- Dashboard
- Case List
- Case Overview
- Evidence Inventory
- Timeline Explorer
- Search Results
- AI Chat
- Report Preview
- Settings

---

# 87. Case Overview

The Case Overview SHALL display:

- Case metadata
- Evidence count
- Supported artifact families
- Processing status
- Parser coverage summary
- Warnings and limitations

---

# 88. Timeline Explorer

The Timeline SHALL support:

- Chronological view
- Date/time filtering
- Artifact-family filtering
- Entity filtering
- Event detail panel
- Provenance display

Timeline interactions SHALL never modify evidence.

---

# 89. AI Chat Experience

Each AI response SHALL include:

- Answer
- Supporting evidence summary
- Citations
- Limitations
- Confidence statement (for analytical conclusions)

If insufficient evidence exists, the interface SHALL state that explicitly.

---

# 90. Reporting Workflow

Users SHALL be able to:

- Preview reports
- Review citations
- Confirm limitations
- Export finalized reports

AI-generated reports SHALL clearly separate:

- Evidence
- Analysis
- Limitations

---

# 91. Accessibility & Performance

The frontend SHOULD:

- Support keyboard navigation
- Provide responsive layouts
- Load primary case views efficiently
- Preserve session state during navigation

---

# 92. Acceptance Criteria

AC-0801 Core workflow completed without modifying evidence.

AC-0802 Every AI response exposes supporting citations.

AC-0803 Timeline filtering is deterministic.

AC-0804 Report preview matches exported content.

AC-0805 Unsupported features are clearly identified.

---

# 93. Codex Execution Contract

Dependencies:

- MES Parts 1–8

Implement:

- Frontend shell
- Case dashboard
- Timeline explorer
- AI chat interface
- Report preview

Update:

- MES
- BACKLOG.md
- Decision Log
- Risk Register

Run:

- UI unit tests
- Integration tests
- Accessibility checks
- End-to-end workflow tests

Commit locally.

Stop only for:

- Owner review
- Architecture conflict
- Support promotion
- Security decision

End of MES-v1 Part 8.
