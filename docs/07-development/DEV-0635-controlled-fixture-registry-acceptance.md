# DEV-0635 — Controlled Apple Fixture Registry Acceptance

CAF-2026-001 is registered as `PREPARATION_COMPLETE`. Fixture generated,
preflight passed, and processing authorized are all false. Apple-produced
characterization is `NOT_STARTED`; compatibility, support, and production are
`NOT_EVALUATED`; Supported capability is `UNAUTHORIZED`.

Acceptance requires the authoritative JSON registry, consistent Markdown
projection, versioned schema, current pointer, deterministic SHA-256 logical
digest, closed IDs/lifecycle/status dimensions, fail-closed validation, safe
document references, and zero backup processing or support effects.

Focused registry and preparation tests: 47 passed. Backend: 851 passed, 2
skipped, 1 accepted warning. Legacy: 5 passed. Compilation, lock, `pip check`,
Alembic, consistency, hygiene, and diff checks passed. No migration was added.
