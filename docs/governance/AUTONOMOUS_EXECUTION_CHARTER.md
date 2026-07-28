# AUTONOMOUS_EXECUTION_CHARTER.md

**Document Type:** Repository Governance Charter\
**Applies To:** All autonomous Codex development for the AI-Powered
iPhone Evidence Assistant\
**Status:** Governing Specification

------------------------------------------------------------------------

# 1. Purpose

This charter defines how autonomous development is performed. Its
objectives are to:

-   Maximize productive autonomous implementation.
-   Preserve forensic defensibility.
-   Preserve evidence integrity.
-   Maintain litigation-grade engineering quality.
-   Reduce unnecessary owner interruptions.
-   Ensure all AI-generated work remains traceable and reviewable.

------------------------------------------------------------------------

# 2. Product Mission

The product is an **Evidence Intelligence Platform** focused on
understanding digital evidence rather than acquiring it.

Primary customer outcomes:

-   Understand what evidence exists.
-   Understand what evidence is missing.
-   Produce attorney-ready reports.
-   Preserve evidence provenance.
-   Generate explainable, source-cited AI answers.

------------------------------------------------------------------------

# 3. Core Engineering Principles

1.  Evidence is immutable.
2.  Every conclusion is traceable.
3.  Fail closed rather than guess.
4.  Unsupported means unsupported.
5.  Documentation is part of every deliverable.
6.  Small validated increments are preferred over large speculative
    features.
7.  Commercial value should guide prioritization after correctness.

------------------------------------------------------------------------

# 4. Autonomous Authority

Codex MAY autonomously:

-   Complete READY tasks.
-   Complete dependent READY subtasks.
-   Refactor internal code without changing approved behavior.
-   Add tests.
-   Improve documentation.
-   Update backlog, roadmap, ADRs, QMS, and traceability.
-   Create additive database migrations.
-   Create local Git commits.
-   Continue through multiple READY tasks without stopping.

------------------------------------------------------------------------

# 5. Mandatory Owner Review

Codex SHALL stop only when work would:

-   Introduce a new trust boundary.
-   Introduce a new evidence-source family.
-   Promote any capability to Supported.
-   Modify evidence integrity, provenance, hashing, authorization, or
    chain-of-custody rules.
-   Change AI reasoning policy.
-   Expose production APIs.
-   Introduce authentication providers.
-   Introduce legal, licensing, or compliance risk.
-   Encounter conflicting governing documents.

------------------------------------------------------------------------

# 6. Priority Model

Implement work in this order unless governance specifies otherwise:

1.  Blocking READY tasks
2.  Core infrastructure
3.  Security
4.  Validation
5.  Provenance
6.  Parser framework
7.  Evidence Coverage & Collection Advisor
8.  AI retrieval
9.  Attorney reporting
10. Future roadmap items

Never bypass higher-priority READY work for speculative capabilities.

------------------------------------------------------------------------

# 7. Commercial Development Principles

Commercial value should favor:

-   Attorney productivity
-   Examiner productivity
-   Explainable AI
-   Time savings
-   Evidence transparency
-   Report quality
-   SaaS scalability

Record future commercial ideas without interrupting MVP completion.

------------------------------------------------------------------------

# 8. Definition of Done

A task is complete only when:

-   Acceptance criteria pass.
-   Focused tests pass.
-   Regression tests pass.
-   Documentation updated.
-   Traceability updated.
-   Acceptance record updated.
-   Local commit created.
-   Working tree clean.

------------------------------------------------------------------------

# 9. Testing Philosophy

Every implementation should include, when applicable:

-   Unit tests
-   Integration tests
-   Regression tests
-   Characterization tests
-   Migration validation
-   Static validation
-   Compilation checks

------------------------------------------------------------------------

# 10. Documentation Requirements

Every completed task updates appropriate documentation including:

-   Backlog
-   Roadmap
-   QMS
-   Acceptance records
-   Architecture
-   Traceability
-   Risk register
-   Decision log

------------------------------------------------------------------------

# 11. Evidence Integrity Rules

Never:

-   Modify source evidence.
-   Fabricate findings.
-   Treat missing evidence as proof of absence.
-   Invent provenance.
-   Remove chain-of-custody information.

------------------------------------------------------------------------

# 12. AI Governance

AI outputs shall:

-   Cite evidence.
-   Separate observed facts from inference.
-   Identify limitations.
-   Preserve uncertainty.
-   Never overstate confidence.

------------------------------------------------------------------------

# 13. Evidence Coverage Principles

Coverage shall distinguish:

-   Present
-   Not collected
-   Unsupported
-   Unknown
-   Backup-method limitation
-   Cloud-dependent possibility
-   Validation failure
-   Resource-limit failure
-   Partial availability

Coverage shall never imply completeness of a device.

------------------------------------------------------------------------

# 14. Security Principles

Maintain:

-   Fail-closed behavior
-   Least privilege
-   Tenant isolation
-   Case isolation
-   Deterministic authorization
-   Auditability

------------------------------------------------------------------------

# 15. Repository Hygiene

Maintain:

-   Small commits
-   Clean working tree
-   No force pushes
-   No merges without owner authorization
-   No generated artifacts committed unless governed

------------------------------------------------------------------------

# 16. Risk Management

If uncertainty exists:

-   Document it.
-   Preserve limitations.
-   Prefer blocking over unsafe assumptions.

------------------------------------------------------------------------

# 17. Continuous Improvement

Codex may recommend:

-   New work packages
-   Technical debt reduction
-   Commercial opportunities
-   Architectural refinements

Recommendations should be documented without delaying MVP work.

------------------------------------------------------------------------

# 18. Stop Conditions

Stop only when:

-   Mandatory owner review is required.
-   Validation cannot be completed safely.
-   Governance conflicts cannot be resolved.
-   A required decision cannot be inferred.

------------------------------------------------------------------------

# 19. Status Report Requirements

When stopping, report:

-   Tasks completed
-   Validation summary
-   Tests executed
-   READY tasks
-   BLOCKED tasks
-   Dependencies
-   Commit hashes
-   Branch
-   Commits ahead of remote
-   Working-tree status
-   Confirmation that nothing was pushed, merged, deployed, or promoted
    to Supported.

------------------------------------------------------------------------

# 20. Success Criteria

This charter succeeds when Codex can autonomously complete long
sequences of READY work while preserving:

-   Evidence integrity
-   Forensic defensibility
-   Security
-   Traceability
-   Commercial focus
-   Documentation quality
-   Minimal owner interruption

------------------------------------------------------------------------

# 21. Automatic Task Readiness

DEC-0051 authorizes autonomous readiness administration. Canonical states are:
`NOT_STARTED`, `DEPENDENCIES_SATISFIED`, `READY`, `IN_PROGRESS`, `BLOCKED`,
`OWNER_REVIEW`, `VALIDATION_PENDING`, `COMPLETE`, `DEFERRED`, and `CANCELLED`.

```text
NOT_STARTED
    ↓
DEPENDENCIES_SATISFIED
    ↓
READY
    ↓
IN_PROGRESS
    ↓
VALIDATION_PENDING
    ↓
COMPLETE
```

Exceptional transitions are:

```text
NOT_STARTED or IN_PROGRESS → BLOCKED → DEPENDENCIES_SATISFIED → READY
READY or IN_PROGRESS → OWNER_REVIEW → READY or IN_PROGRESS after approval
Any active state → DEFERRED or CANCELLED through an applicable decision
```

Readiness must be reevaluated when dependencies, decisions, blockers, work
packages, or task completions change and whenever no READY task remains.
Eligible tasks may be promoted automatically. `BLOCKED` requires a concrete,
dated blocker record. `OWNER_REVIEW` is reserved for genuine mandatory gates.
One primary implementation task should normally be `IN_PROGRESS`. A review gate
on one task does not stop independent READY work.
