# AI-Powered iPhone Evidence Assistant — Pre-Validation Repository

> **Support notice:** This repository contains legacy compatibility code and an
> implemented-but-unvalidated backend scaffold. No parser, artifact family,
> Apple backup input, AI workflow, or report is currently approved as supported
> production functionality. Plugin presence and successful execution do not
> establish forensic support. See `docs/01-product/PRD-007-mvp-scope-reconciliation.md`
> and `docs/03-forensics/FOR-006-legacy-parser-quarantine-policy.md`.

## Legacy Evidence Engine

Legacy-compatible Python package extracted from `window_investigator.py`.

The refactor keeps the original forensic logic in `evidence_engine._legacy`
and exposes package import boundaries for models, parsers, normalization,
analysis, inventory, AI grounding, reports, and CLI execution. This preserves
the current command behavior while giving a future FastAPI application importable
entry points.

## Legacy compatibility execution

The following commands preserve historical behavior for characterization and
compatibility. Their output is not a supported production evidence workflow.
From the repository root, run with Python 3.11+:

```powershell
python window_investigator.py --list-plugins --start "2026-06-25 16:25:00" --end "2026-06-25 16:58:00"
```

The package CLI can also be executed directly:

```powershell
python -m evidence_engine.cli --case birch --start "2026-06-25 16:25:00" --end "2026-06-25 16:58:00" --single-report
```

Existing script behavior is preserved through the root `window_investigator.py`
wrapper.

## Package Layout

- `evidence_engine/models/`: event, coverage, context, entity, and relationship models.
- `evidence_engine/parsers/`: parser protocol, parser result model, parser registry, and artifact parser modules.
- `evidence_engine/normalization/`: event and entity normalization functions.
- `evidence_engine/analysis/`: context windows, correlations, confidence, coverage scoring, and hypotheses.
- `evidence_engine/inventory/`: artifact and coverage inventory builders.
- `evidence_engine/ai/`: evidence package construction and AI guardrail prompt preparation.
- `evidence_engine/reports/`: report assembly, report sections, formats, and relationship outputs.
- `evidence_engine/cli.py`: backward-compatible CLI entry point.

## Tests

Run the characterization tests with:

```powershell
python -m unittest discover -s tests
```

The tests use sanitized synthetic events and coverage records, plus the
deterministic self-checks already present in the original implementation.

## Backend scaffold

The default `backend/app/main.py` application is a pre-validation scaffold that
exposes only database health. Case creation, local-path processing, evidence
queries, and summaries were moved behind the explicit
`backend/app/legacy/main.py` compatibility composition root. They remain
implemented-but-unvalidated and are not included in the default product path.

The backend still lacks authentication, authorization, tenant isolation,
evidence-source intake, controlled working copies, validated Apple backup
classification, supported-parser execution, and supported evidence storage.

DEV-0304 adds a closed support-status vocabulary, an explicit versioned
supported-registry boundary, and a supported-output quarantine gate. Its
production composition is deliberately empty. No parser or artifact is
registered, executed, or promoted by that foundation.

## Supported-boundary intake foundation

`backend/app/intake/apple_backup.py` contains the DEV-0201 read-only filesystem
adapter. It confines directory candidates to configured evidence roots and
returns typed adapter outcomes with provenance for later DEV-0202 structure
validation.

The adapter does not validate Apple backup structure, detect encryption, hash
or parse source files, create working copies, or establish input support. It is
not exposed through the default API.

The following are development commands, not a production deployment procedure.
Compose uses the committed dependency lock but still requires local environment
configuration and is not an approved production deployment:

```bash
docker compose up --build
```

Apply migrations:

```bash
cd backend
alembic upgrade head
```

Create a clean environment, install the exact locked dependencies, and install
the application without resolving a second dependency graph:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.lock
.venv/Scripts/python -m pip install --no-deps --no-build-isolation ./backend
.venv/Scripts/python backend/scripts/verify_lock.py --project backend/pyproject.toml --lock backend/requirements.lock
.venv/Scripts/python -m pytest backend
```

On POSIX systems, replace `.venv/Scripts/python` with `.venv/bin/python`.
`backend/requirements.lock` is the reproducible application and development
resolution; update it deliberately and validate it whenever dependency
declarations change.

See `API.md`, `DATABASE_DESIGN.md`, and `LOCAL_DEVELOPMENT.md` for details.
