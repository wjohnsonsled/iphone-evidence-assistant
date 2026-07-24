# API

## Default application

The default composition root is `app.main:app`. All endpoints are mounted
under `/api/v1`.

DEV-0101 intentionally exposes only:

`GET /api/v1/health`

Response:

```json
{"status": "ok", "database": "connected"}
```

If the database is unavailable, the API returns a structured `503` error.

No case, evidence, intake, processing, search, AI, citation, or reporting route
is available from the default application. Those routes require their approved
authorization, tenant, evidence-source, provenance, and supported-parser tasks.

The default application is a pre-validation backend foundation. Its presence
does not establish a supported input or evidence workflow.

## Legacy compatibility application

The explicit `app.legacy.main:legacy_app` composition root preserves the
pre-existing case, local-path processing, evidence-query, and summary endpoints
for synthetic characterization and controlled compatibility testing.

That application and all of its routes, parsers, records, coverage, summaries,
and output are unsupported legacy behavior. It must not be deployed or
presented as the supported product API. It is structurally excluded from the
default application.

## Error responses

Structured application errors use this shape:

```json
{
  "error": {
    "code": "database_unavailable",
    "message": "Database is unavailable.",
    "request_id": "uuid"
  }
}
```
