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

Install development dependencies:

```bash
cd backend
python -m pip install -e ".[dev]"
pytest
```

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
