## Candidate idempotency isolation control — DEV-1107

Exact claims are scoped by tenant, case, evidence source, source artifact,
parser/version, profiles, operation, controlled-input digest, authorization
reference, and idempotency profile/version. Cross-tenant and cross-case
requests cannot suppress each other or disclose another claim. Relational
transaction isolation remains unvalidated on live PostgreSQL and is prohibited
from production use pending that validation.

## Candidate Manifest.db query controls — DEV-0602A

Version 2 query continuations bind tenant, case, evidence source, artifact,
database identity, processing run, query ID, and version. Application-level
concurrency controls acquire PROCESS → TENANT → CASE → EVIDENCE_SOURCE →
PROCESSING_RUN. Denial exposes only the scope and no workload or evidence
content. Default BLOB observations return no bytes; explicit internal access
requires authorization and remains nonpersistent, unlogged, uninterpreted, and
unexposed. Production ceilings and distributed concurrency are unvalidated.

DEC-0062 accepts these controls at the candidate infrastructure level with all
QMS-012 limitations; it does not establish production authorization,
distributed isolation, deployment readiness, or API exposure.

## Candidate identifier-normalization controls — DEV-0603

Production adapters accept only scope-matched query v1/v2 row observations.
Canonical comparisons deny cross-tenant and cross-case scope and incompatible
profiles without fallback or existence disclosure. Batch normalization and
comparison require caller-supplied observation, comparison, byte, deterministic
memory-estimate, monotonic time, and cancellation ceilings. No cross-case
index, filesystem search, raw-BLOB logging, public API, or persistence exists.
## Candidate metadata scope

DEC-0058 does not expose WP-0500 through an API or production composition.
Discovery remains authorized-root-confined, read-only, top-level only, and
tenant/case/source/run scoped. Filenames and plist values remain untrusted.
No real evidence or user-content artifact was processed during validation.
