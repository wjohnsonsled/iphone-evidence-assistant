# Controlled Apple Fixture Registry

The JSON registry is authoritative. Package IDs use `CAF-YYYY-NNN`: uppercase
Controlled Apple Fixture prefix, assignment year, and unreused zero-padded sequence.

## Current fixtures

| Package ID | Classification | Lifecycle | Fixture generated | Preflight passed | Processing authorized | Apple-produced characterization | Compatibility validation | Support validation | Supported capability | Raw fixture in Git |
|---|---|---|---|---|---|---|---|---|---|---|
| CAF-2026-001 | Controlled Apple-produced test fixture | PREPARATION_COMPLETE | No | No | No | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED | UNAUTHORIZED | Prohibited |

## Validation dimensions and lifecycle

Preparation, Apple-produced characterization, compatibility validation, support
validation, production readiness, and Supported capability are independent.
Closed lifecycle values are: PLANNED, PREPARATION_IN_PROGRESS,
PREPARATION_COMPLETE, FIXTURE_GENERATED, PREFLIGHT_PENDING, PREFLIGHT_FAILED,
READY_FOR_OWNER_VALIDATION_AUTHORIZATION, PROCESSING_AUTHORIZED,
CHARACTERIZATION_IN_PROGRESS, CHARACTERIZATION_COMPLETE, VALIDATION_REJECTED,
ARCHIVED, RETIRED, DESTROYED.

## Restrictions and next action

Raw fixture bytes, sensitive device/account identifiers, secrets, and protected
storage mappings are prohibited from Git. CAF-2026-001 has not been generated;
no backup has been opened or processed. Owner follows OWNER-001 and SOP-001 to
create the fixture, then separately authorizes processing by exact package ID.

Logical digest: `b0533520fc033c9dca607bbc43e1e65632dfe10af0757d3a916d4a53397eda1d` (`SHA-256`, canonical profile v1).
