# Master Engineering Specification (MES-v1)

## Part 1 — Vision, Scope, Engineering Principles, and Autonomous Development

**Project:** AI-Powered iPhone Evidence Assistant
**Version:** 1.0 (Draft)

# 1. Purpose

This document is the authoritative engineering specification for the MVP.

Goals:
- Evidence integrity
- Deterministic behavior
- Explainable AI
- Repeatable testing
- Traceable conclusions
- Litigation-aware reporting

# 2. Vision

Build an application that accepts Apple iPhone backups, processes them read-only, normalizes evidence, and enables trustworthy natural-language interaction.

The application is not an acquisition tool.

# 3. MVP Scope

Included:
- Apple local backups
- Evidence registration
- Integrity verification
- Timeline generation
- AI evidence retrieval
- Attorney-focused reporting

Excluded:
- Android
- Live acquisition
- Cellebrite imports
- Cloud acquisition

# 4. Engineering Principles

1. Read-only processing.
2. No silent failures.
3. Every AI conclusion must be traceable.
4. Every parser declares limitations.
5. Unsupported means unavailable.
6. Deterministic outputs.
7. Synthetic tests first.
8. Tests are required for completion.

# 5. Trust Model

The system provides:
- Processing provenance
- Integrity verification
- Reproducible analysis

The system does not itself prove:
- Legal admissibility
- Device authenticity
- User identity

# 6. Support Policy

Nothing becomes supported until:
- Implemented
- Validated
- Documented
- Regression tested
- Owner approved

# 7. Evidence Integrity

Every evidence object shall have:
- Immutable UUID
- SHA-256 observations
- Lifecycle state
- Provenance
- Audit history

# 8. AI Rules

AI shall:
- Answer only from normalized evidence.
- Cite supporting artifacts.
- State limitations.
- Refuse unsupported conclusions.
- Never fabricate evidence.

# 9. Autonomous Codex Workflow

Codex shall:
- Read MES
- Read AGENTS.md
- Read BACKLOG.md
- Select next READY task
- Implement dependencies
- Run tests
- Update documentation
- Commit locally

Stop only for:
- Owner review
- Architecture conflict
- Support promotion
- Security decisions

Never:
- Push
- Merge
- Deploy
- Process customer evidence

# 10. Initial Work Packages

WP-0300 Evidence Repository

WP-0350 Supported Evidence Store

WP-0400 Apple Backup Parsers

WP-0500 Timeline Engine

WP-0600 Search

WP-0700 AI Retrieval

WP-0800 Reporting

WP-0900 REST API

WP-1000 React Frontend

WP-1100 Production Hardening

# 11. Living Specification

Each approved work package updates this specification when architecture, interfaces, or engineering constraints change.
