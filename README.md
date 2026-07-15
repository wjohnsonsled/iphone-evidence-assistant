# Evidence Engine

Reusable Python package extracted from `window_investigator.py`.

The refactor keeps the original forensic logic in `evidence_engine._legacy`
and exposes stable package modules for models, parsers, normalization,
analysis, inventory, AI grounding, reports, and CLI execution. This preserves
the current command behavior while giving a future FastAPI application importable
entry points.

## Installation

No third-party package installation is required for the current script. From the
repository root, run commands with Python 3.11+:

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

## Backend MVP

The `backend/` project adds PostgreSQL persistence and a minimal FastAPI API for
case creation, local backup processing, evidence queries, and deterministic case
summaries.

Local Docker startup:

```bash
docker compose up --build
```

Apply migrations:

```bash
cd backend
alembic upgrade head
```

Run backend tests after installing dev dependencies:

```bash
cd backend
python -m pip install -e ".[dev]"
pytest
```

See `API.md`, `DATABASE_DESIGN.md`, and `LOCAL_DEVELOPMENT.md` for details.
