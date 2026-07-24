# Database Design

## Tables

- `cases`: one forensic case, public UUID ID, processing status, optional source
  path, metadata JSONB, and timestamps.
- `devices`: one or more device or backup-source records per case. Identifiers
  such as serial number, UDID, and backup identifier are nullable because not
  every decrypted backup exposes them.
- `evidence_events`: normalized evidence rows generated from the evidence
  engine. List endpoints do not return `raw_values_json` by default.
- `artifact_coverage`: parser and artifact coverage rows. The API status is a
  compact vocabulary, while the original evidence-engine coverage status is
  preserved in `details_json`.
- `processing_jobs`: synchronous MVP processing job state. The schema is ready
  for a later background worker without adding a fake queue now.

## Relationships

- `cases.id` is referenced by all child tables with cascade delete.
- `devices.case_id` links device metadata to a case.
- `evidence_events.device_id` and `artifact_coverage.device_id` are nullable and
  use `SET NULL` so evidence remains available even if a device row is removed.
- `processing_jobs.case_id` tracks processing attempts for a case.

## Indexes

Evidence query indexes:

- `case_id`
- `device_id`
- `timestamp`
- `event_type`
- `category`
- `source_artifact`
- `conversation_key`
- `contact_key`

Composite indexes:

- `(case_id, timestamp)`
- `(case_id, event_type)`
- `(case_id, conversation_key)`

Coverage and status indexes:

- `cases.status`
- `artifact_coverage.case_id`
- `artifact_coverage.device_id`
- `artifact_coverage.coverage_status`
- `processing_jobs.case_id`

## Deduplication Strategy

The backend computes a deterministic fingerprint for each normalized event and
stores it in `evidence_events.artifact_hash`.

Order of preference:

1. Use an existing engine `external_event_id` or normalized `event_id` when
   present.
2. Otherwise hash selected stable fields: case ID, source database, source
   table, source record ID, event type, and timestamp.

No unique constraint is added in this MVP. The persistence service checks
existing fingerprints and in-batch duplicates before insertion, but avoids a
database-level uniqueness rule that could incorrectly merge distinct forensic
records if upstream provenance is incomplete.

## JSONB Usage

JSONB is used for:

- flexible normalized event details
- raw evidence values returned only from detail endpoints
- confidence basis and evidence strength
- coverage details preserving original engine distinctions
- processing statistics and warnings
- case/device metadata

Core query fields such as timestamps, event type, source artifact, contact key,
and conversation key are typed columns.

## Future pgvector Integration Points

Future embeddings should live in a separate table keyed to `evidence_events.id`,
for example `evidence_event_embeddings`. That keeps vector lifecycle, model
versioning, and access controls separate from deterministic forensic records.

## Data Retention Considerations

This MVP does not implement retention policies. Production deployments should
define retention by case, preserve audit logs for processing actions, and avoid
storing backup passwords or unnecessary raw artifact values.
