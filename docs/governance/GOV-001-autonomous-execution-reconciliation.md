# GOV-001 — Autonomous Execution Charter Reconciliation

## Outcome

The owner-directed `AUTONOMOUS_EXECUTION_CHARTER.md` is adopted as the current
autonomous-execution authority. Existing owner decisions remain controlling
product, forensic, architecture, security, and support records. MES-v1 remains
a governing draft gap source subordinate to those approved records.

## Conflicts found and resolved

| Conflict | Resolution |
|---|---|
| AGENTS.md said to stop after each task | Updated to continue through READY work until a charter stop condition. |
| AGENTS.md and the historical charter treated every work-package gate as mandatory | New charter controls; only enumerated high-risk subjects require review. |
| BACKLOG required owner approval before every task could become COMPLETE | Tasks may complete autonomously when definition of done passes; `VALIDATION_PENDING` now means a real mandatory decision. |
| BACKLOG made the frontend workflow an independent owner gate | Removed; embedded authentication, API, AI, legal, support, and deployment gates remain. |
| Charter mission uses “Evidence Intelligence Platform,” while DEC-0027 prohibits broad scope expansion | Mission language is strategic framing only; approved MVP scope and no-duplicate/no-displacement rules control implementation. |
| Requested “WP-0400 Evidence Coverage” conflicts with existing WP-0400 Supported Evidence Data Model | Preserve audit history: Evidence Coverage remains WP-0450 under DEC-0027/DEC-0037. No duplicate IDs or work package. |

## Mandatory review classification

Review remains mandatory for new or changed architecture/trust boundaries;
evidence-integrity, hashing, chain-of-custody, or provenance rules; security or
authentication; parser/capability support promotion; AI reasoning policy;
production API exposure or deployment; and legal, licensing, or compliance
decisions.

Routine task completion, internal refactoring, documentation, deterministic
validation, additive implementation inside approved architecture, and
non-production UI workflow work are not independently owner-gated.

## Backlog and priority reconciliation

The first READY task in plan order remains controlling. WP-0400 Supported
Evidence Data Model is the current core-infrastructure work package. Its final
gate remains mandatory because the normalized evidence contract governs
evidence integrity and provenance. DEV-0404 is the highest-priority READY task.

WP-0450 Evidence Coverage & Collection Advisor remains after evidence core,
parser framework/validated artifact prerequisites, and before AI/reporting
where dependencies permit. Its rules remain:

- backup absence is not device absence;
- absence proves no deletion, concealment, wiping, destruction, corruption, or
  spoliation;
- unsupported processing is never “no evidence found”;
- zero records remains distinct from absence, non-execution, unsupported,
  failure, resource denial, and partial processing;
- conclusions are versioned and traceable;
- percentages never imply all device evidence;
- cloud acquisition remains separate and FUTURE.

## No change in support or trust state

The supported registry remains empty. No parser, artifact, source, workflow,
API, report, AI behavior, or coverage capability is promoted. No production
deployment, real-evidence use, or trust-model change is authorized.
