# DEV-0625 — Synthetic Physical Corpus Acceptance

- Corpus: `physical-inventory-synthetic-corpus` version 1.
- Count: 50 uniquely identified, deterministically hashed scenario specifications.
- Basis: project-original synthetic only; no real or Apple-produced evidence.
- Coverage: layout, types, links/security, hashing, mutation, limits,
  cancellation, resolution, physical coverage, scope isolation, determinism,
  provenance, and prohibited claims.
- Focused/integration result: 28 passed, 2 host-dependent link fixture skips.
- Full regression: 804 backend passed, 2 platform skips, 1 accepted warning;
  5 legacy passed; compilation and diff gates passed.
- Support effect: none.
