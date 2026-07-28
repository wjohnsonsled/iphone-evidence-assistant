# Local Development

## Prerequisites

- Python 3.12
- Docker and Docker Compose
- No evidence input is required for the default backend scaffold

## Environment Setup

Copy the example environment file if you want to run locally outside Docker:

```bash
cp backend/.env.example backend/.env
```

Do not put production credentials or real client paths in committed files.

Configuration validation is fail-closed:

- `ENVIRONMENT` is one of `development`, `test`, `staging`, or `production`;
- `LOG_LEVEL` is one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`;
- non-test environments require `postgresql+psycopg`;
- SQLite is permitted only for deterministic tests;
- every semicolon-separated `EVIDENCE_ROOT` entry must be absolute and unique;
- the documented development database password is rejected in production.

On Windows local runs, replace the container path `/evidence` with an absolute
Windows path. Configuration diagnostics use `Settings.safe_summary()` and
must never include a password or complete database URL. These checks do not
connect to the database or establish production readiness.

## Docker Startup

Create a local evidence directory:

```bash
mkdir -p dev-evidence
```

Start PostgreSQL and the FastAPI backend:

```bash
docker compose up --build
```

The backend listens on `http://localhost:8000`.

The container starts the default `app.main:app` composition root. DEV-0101
limits that application to the database health endpoint. It does not expose an
evidence-processing workflow.

## Database Migrations

From inside the backend container or a local environment with dependencies
installed:

```bash
cd backend
alembic upgrade head
```

## Running Tests

Create an isolated environment and install the committed resolution:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.lock
.venv/Scripts/python -m pip install --no-deps --no-build-isolation ./backend
.venv/Scripts/python backend/scripts/verify_lock.py --project backend/pyproject.toml --lock backend/requirements.lock
.venv/Scripts/python -m pip check
.venv/Scripts/python -m pytest backend
```

On POSIX systems, use `.venv/bin/python`. The lock contains exact direct and
transitive versions for the backend and its development tests. `pyproject.toml`
remains the abstract package declaration; it is not the reproducible install
input. Do not use an editable install for clean-environment validation.

The automated tests use mocked/sanitized evidence-engine outputs and do not
require a real iPhone backup.

## Legacy compatibility testing

The pre-existing case, processing, evidence, and summary routes are retained
only through `app.legacy.main:legacy_app`. They are unsupported
characterization behavior and are not included in the default application.

When a task specifically requires legacy API characterization with synthetic
fixtures, it may be started explicitly from `backend/`:

```bash
uvicorn app.legacy.main:legacy_app
```

Do not use real evidence. Do not distribute or deploy this compatibility
application as a supported product surface.

## Security Notes

- The default application exposes no case or evidence routes.
- The legacy path boundary remains characterization behavior only.
- Backup passwords are not accepted, logged, or stored.
- Authentication, authorization, tenant isolation, intake, and audit controls
  remain required before evidence APIs can enter the default application.
