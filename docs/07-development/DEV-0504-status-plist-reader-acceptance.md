# DEV-0504 — Status.plist Controlled Reader

- Status: COMPLETE
- Dependency: DEV-0501 — COMPLETE
- Profile: `status-plist-candidate-reader` version `1`
- Support effect: none

The versioned projection adopts DEV-0501's root-confined plist reader and
preserves only the source-specific `SnapshotState` claim. A value such as
`finished` remains a plist claim and never becomes forensic completeness,
artifact availability, compatibility, or support.

Validation: focused 1 passed; full backend 371 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation and diff
checks passed.
