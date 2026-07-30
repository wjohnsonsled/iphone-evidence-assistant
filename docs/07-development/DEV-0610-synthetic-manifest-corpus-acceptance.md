# DEV-0610 — Synthetic Manifest Characterization Corpus Acceptance

- Status: COMPLETE — candidate synthetic characterization only
- Decision: DEC-0077
- Profile: FOR-021
- Validation: QMS-020
- Support effect: none

| ID | Acceptance criterion | Result |
|---|---|---|
| AC-01 | Versioned corpus governance defines source, provenance, custody, distribution, integrity, supersession, acceptance, and Apple-produced boundaries. | PASS |
| AC-02 | Every committed fixture is project-original synthetic, non-personal, non-device, non-evidentiary, lawfully distributable, and completely provenance-bound. | PASS |
| AC-03 | Deterministic manifest records every required identity, generation, profile, outcome, classification, digest, limitation, date, and status field. | PASS |
| AC-04 | Matrix covers all approved Manifest candidate profiles and records positive, negative, malformed, unsupported, boundary, resource, compatibility, rerun, outcome, and missing coverage. | PASS |
| AC-05 | At least 60 required synthetic scenarios are registered without Apple-version or support claims. | PASS — 60 |
| AC-06 | SHA-256 fixture/corpus integrity, deterministic regeneration, missing/unregistered/mutated/prohibited/incomplete denial, and supersession are verified. | PASS |
| AC-07 | Tooling is fixed-root/data-only and cannot ingest arbitrary paths/backups, fetch, execute, dynamically load, unsafe-deserialize, escape, or read secrets. | PASS |
| AC-08 | Synthetic characterization remains separate from Apple-produced, compatibility, support, production, and Supported states. | PASS |
| AC-09 | Focused, integrated Manifest, backend, legacy, dependency, migration, compilation, and hygiene gates pass. | PASS |
| AC-10 | No real/Apple/customer data, migration, parser activation, API, supported entry/record, compatibility claim, or support promotion exists. | PASS |
