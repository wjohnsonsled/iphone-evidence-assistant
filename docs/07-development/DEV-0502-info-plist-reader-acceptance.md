# DEV-0502 — Info.plist Controlled Reader

- Status: COMPLETE
- Dependency: DEV-0501 — COMPLETE
- Profile: `info-plist-candidate-reader` version `1`
- Support effect: none

The reader adopts DEV-0501's sole root-confined plist read path and projects
only `Product Version`, `Target Identifier`, and `Unique Identifier` in fixed
order. Source identity, raw/normalized typed state, missing versus empty,
reader identity, provenance scope, and limitations remain unchanged. Incomplete
or wrong-profile discovery input fails closed. No compatibility or support
meaning is assigned.

Validation: focused 2 passed; full backend 369 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation and diff
checks passed.
