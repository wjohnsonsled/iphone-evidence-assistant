## Candidate metadata normalization

DEC-0056 and FOR-010 require every candidate Apple metadata normalization to
retain the immutable raw typed representation and create a separately
addressable normalized representation with versioned transformation
provenance. Exact normalized agreement is an observation about values, not
proof of physical-device identity, attribution, authenticity, or
compatibility. Unsupported values remain valid raw observations.

## Candidate Manifest.db query hardening

DEC-0061/FOR-013 preserve finalized row observations when a v2 query stops.
The exact profile, controlled-copy/source identities, processing run, ROWID
locator, schema, reader, audit times, resource measurement, last completed
locator, continuation availability, reason, and limitations remain explicit.
Memory is a deterministic query-layer estimate, not process memory. Operational
limits and BLOB availability create no corruption, absence, completeness,
interpretation, or support conclusion.
