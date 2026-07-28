## Candidate idempotency isolation control — DEV-1107

Exact claims are scoped by tenant, case, evidence source, source artifact,
parser/version, profiles, operation, controlled-input digest, authorization
reference, and idempotency profile/version. Cross-tenant and cross-case
requests cannot suppress each other or disclose another claim. Relational
transaction isolation remains unvalidated on live PostgreSQL and is prohibited
from production use pending that validation.
