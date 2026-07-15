# API

All endpoints are mounted under `/api/v1`.

## Health

`GET /api/v1/health`

Response:

```json
{"status": "ok", "database": "connected"}
```

If the database is unavailable, the API returns a structured `503` error.

## Create Case

`POST /api/v1/cases`

Request:

```json
{
  "name": "Test iPhone Backup",
  "description": "Sanitized development case",
  "source_path": "/evidence/test-backup"
}
```

Response:

```json
{
  "id": "uuid",
  "name": "Test iPhone Backup",
  "status": "created",
  "created_at": "2026-07-15T18:00:00Z"
}
```

`source_path` is accepted for internal tracking but is not returned from the
case detail response.

## Get Case

`GET /api/v1/cases/{case_id}`

Returns case metadata, processing state, device summaries, evidence counts, and
coverage counts.

## Process Local Backup

`POST /api/v1/cases/{case_id}/process`

Request:

```json
{"backup_path": "/evidence/test-backup"}
```

The path must exist, be a directory, appear to be a supported iPhone backup or
extracted case directory, and resolve under configured `EVIDENCE_ROOT`.

The endpoint runs synchronously for the MVP and returns a processing job.

## List Evidence

`GET /api/v1/cases/{case_id}/evidence`

Query parameters:

- `event_type`
- `category`
- `start_time`
- `end_time`
- `contact_key`
- `conversation_key`
- `limit`, default `100`, maximum `500`
- `offset`, default `0`
- `sort`, `asc` or `desc`

Response:

```json
{
  "case_id": "uuid",
  "total": 1423,
  "count": 100,
  "items": []
}
```

List items include ID, timestamp, event type, category, summary, source
artifact, source database, source record ID, confidence score, conversation key,
and contact key. Raw values are not returned by default.

## Get Evidence Record

`GET /api/v1/cases/{case_id}/evidence/{evidence_id}`

Returns the complete normalized evidence record, including details, raw values,
source metadata, confidence basis, and parser metadata. The record must belong
to the requested case.

## Evidence Summary

`GET /api/v1/cases/{case_id}/summary`

Returns deterministic summary data only:

- total events
- earliest and latest timestamps
- counts by event type
- counts by artifact
- top contacts
- top conversations
- attachment count
- coverage statuses
- warning count
- error count

## Error Responses

Errors use this shape:

```json
{
  "error": {
    "code": "case_not_found",
    "message": "Case was not found.",
    "request_id": "uuid"
  }
}
```

Common codes include `case_not_found`, `invalid_backup_path`,
`backup_path_not_found`, `unsupported_backup_structure`,
`processing_already_in_progress`, `evidence_record_not_found`,
`database_unavailable`, and `evidence_engine_failure`.
