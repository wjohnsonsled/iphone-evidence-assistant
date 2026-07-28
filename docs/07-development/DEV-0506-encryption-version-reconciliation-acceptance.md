# DEV-0506 — Encryption and Version Field Reconciliation

- Status: COMPLETE
- Dependencies: DEV-0502 through DEV-0504 — COMPLETE
- Profile: `encryption-version-exact-reconciliation` version `1`
- Governing decisions: DEC-0009 and DEC-0054
- Support effect: none

The projection preserves DEV-0501's exact `product_version` and `encryption`
reconciliation results. `Manifest.plist.IsEncrypted` remains the only approved
encryption signal. Exact single-source/agreement values may be retained;
conflicts remain unresolved with no selected value. Product version is
informative only and never establishes Apple or parser compatibility.

Validation: focused 2 passed; full backend 373 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation, lock,
package consistency, and diff checks passed.
