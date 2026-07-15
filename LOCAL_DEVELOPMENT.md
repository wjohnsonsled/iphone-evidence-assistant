# Local Development

## Prerequisites

- Python 3.12
- Docker and Docker Compose
- A sanitized decrypted iPhone backup or extracted case directory for manual
  processing tests

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

## Processing a Sanitized Local Backup

Place a sanitized decrypted backup under:

```text
./dev-evidence/test-backup
```

Create a case:

```bash
curl -X POST http://localhost:8000/api/v1/cases \
  -H "Content-Type: application/json" \
  -d '{"name":"Sanitized Backup","description":"Development case","source_path":"/evidence/test-backup"}'
```

Process the backup:

```bash
curl -X POST http://localhost:8000/api/v1/cases/{case_id}/process \
  -H "Content-Type: application/json" \
  -d '{"backup_path":"/evidence/test-backup"}'
```

Then inspect evidence:

```bash
curl http://localhost:8000/api/v1/cases/{case_id}/evidence
curl http://localhost:8000/api/v1/cases/{case_id}/summary
```

## Security Notes

- Processing paths are resolved and restricted to configured evidence roots.
- `..` traversal outside `EVIDENCE_ROOT` is rejected.
- Backup passwords are not accepted, logged, or stored.
- Raw evidence values are excluded from list and summary responses.
