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

## Candidate Manifest domain controls — DEV-0604

Production adapters accept only tenant/case/source/run-matched query v1/v2
observations. Exact case-sensitive grammar prevents broad coercion; malformed
and unknown values fail closed while raw values remain immutable. Serialization
omits raw BLOB bytes and host paths. No filesystem lookup, global index,
parser, API, persistence, supported store, or cross-scope discovery exists.

## Candidate relative-path controls — DEV-0605

Untrusted `relativePath` values remain data. Exact absolute, alternate
separator, repeated separator, dot, parent-traversal, encoding, and resource
states fail closed. The module imports no filesystem API and never joins or
resolves a path. Caller-supplied positive lexical ceilings are mandatory.

## Candidate flags controls — DEV-0606

Only proven scope-matched query observations enter. Bit enumeration is bounded
by a positive caller policy and stops before excess work. Every bit remains
unknown, raw BLOB bytes are not serialized, and no metadata decoder,
filesystem, parser, API, persistence, or supported-store path exists.

## Candidate metadata-BLOB controls — DEV-0607

Only explicitly authorized raw BLOB projections enter the iterative scanner.
Exact byte/object/depth/scalar/collection/memory/time/cancellation limits,
payload/offset/reference bounds, and cycle checks fail closed. No native
deserialization, class loading/instantiation, DATA emission, filesystem,
parser, API, persistence, or supported-store path exists.

## Candidate reconciliation controls — DEV-0609

Inputs must share exact tenant/case/source/artifact/run scope and compatible
profile versions. Caller row/group/member/byte/memory/time/cancellation bounds
fail closed. No raw BLOB identifier is textualized, no filesystem or physical
inventory is reachable, and all evidentiary conclusions remain unavailable.
