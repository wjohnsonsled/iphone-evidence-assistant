# FOR-021 — Synthetic Characterization Corpus Governance

## Control

- Profile: `synthetic-characterization-corpus-governance` version 1
- Corpus: `manifest-synthetic-characterization-corpus` version 1
- Decision: DEC-0077
- Status: candidate-only; not Supported

This profile governs project-original, non-personal, non-device,
non-evidentiary test assets. It authorizes synthetic characterization only.
Apple-produced characterization, compatibility validation, support validation,
production readiness, and Supported capability remain separate and not started.

## Sources and distribution

Committed fixtures must be `ORIGINAL_PROJECT_SYNTHETIC`,
`OPEN_SPECIFICATION_DERIVED_SYNTHETIC`, or
`APPROVED_LICENSED_SYNTHETIC`. DEV-0610 uses only
`ORIGINAL_PROJECT_SYNTHETIC`. Disallowed sources include real, sanitized,
redacted, pseudonymized, transformed, public, vendor, leaked, challenged, or
unidentified device/backup data and any source with uncertain provenance or
distribution rights.

Committed distribution classifications are limited to
`ORIGINAL_PROJECT_SYNTHETIC`, `OPEN_SPECIFICATION_DERIVED_SYNTHETIC`, and
`APPROVED_LICENSED_SYNTHETIC`. Unverified, prohibited, and internal
non-distributable assets fail closed.

## Provenance and custody

Accepted provenance states are `GENERATED_DETERMINISTICALLY`,
`GENERATED_MANUALLY_SYNTHETIC`,
`DERIVED_FROM_APPROVED_SYNTHETIC_FIXTURE`, and
`REGENERATED_FROM_APPROVED_GENERATOR`. The corpus uses deterministic generation.
Every record identifies its generator/task/decision/version/parameters,
creation and regeneration dates, manual-edit state, external-material state,
expected behavior, profiles, schema, limitations, and distribution basis.

Synthetic custody records creation, generator execution, initial digest,
repository addition, review, approval, modification, regeneration,
supersession, and retirement where applicable. This is test-asset custody, not
evidence chain of custody.

## Integrity and immutability

Each internal fixture resource has a SHA-256 digest over canonical JSON. The
corpus digest covers the canonical manifest payload excluding only its own
digest field. Unknown, missing, duplicate, unregistered, mutated,
provenance-incomplete, distribution-uncertain, disallowed-source, or
unsupported-generator records fail closed. Approved versions are immutable;
changes require a new fixture/corpus version and explicit supersession.

These are synthetic test-asset digests, not evidence hashes.

## Security boundary

The generator accepts no paths, URLs, code, commands, environment-derived
values, or fixture content. It writes only its repository-defined fixture
manifest location. Verification is data-only and does not deserialize native
objects, dynamically load code, execute content, access backup roots, or write
files.

## Apple-produced gate and limitations

Actual Apple-version/device/software claims require a separate controlled
package and owner gate covering lawful acquisition and authorization, device
and account ownership, creation procedure, encryption/software/model/OS/time
metadata, operator, controlled copies, hashing, custody, minimization,
retention/destruction, lab isolation, distribution, versioning, schema
fingerprints, profile coverage, and Git exclusion. The default is that such
fixtures never enter this repository.

`SYNTHETIC_CHARACTERIZED` means only that implementation behavior matched
explicitly constructed cases. It proves nothing about what Apple produces and
does not activate a parser, artifact, input, workflow, API, record, or support
claim.

