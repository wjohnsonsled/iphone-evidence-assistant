# DEV-0501 — Apple Backup Discovery and Metadata Reconciliation

- Status: COMPLETE
- Owner decision: DEC-0054
- Discovery profile: `apple-local-backup-top-level-discovery` version `1`
- Reconciliation profile: `apple-backup-metadata-field-reconciliation` version `1`
- Support effect: none

Root-confined read-only discovery evaluates exactly `Manifest.db`,
`Manifest.plist`, `Info.plist`, and `Status.plist`. Each target has an explicit
presence/access state and source-artifact identity. Manifest.db receives only
header recognition and remains pending controlled structural/schema
validation. Plist claims remain separate immutable typed observations; missing,
empty, malformed, and unsupported values are distinct.

Field reconciliation supports agreement, single-source observation, unresolved
conflict, and missing-from-all outcomes without universal source precedence.
Device, product, backup, encryption, snapshot, and generic conflicts have
controlled categories. The root directory name is a separate observation and
is never authoritative device identity.

All results retain tenant, case, evidence-source, source-artifact,
processing-run, reader, locator, profile, timestamp, and limitation context.
Cross-scope and root escape fail closed. No recursive discovery, user-content
parser, compatibility determination, API, persistence migration, real evidence,
registry entry, supported record, or support promotion is included.

Validation: focused 12 passed; full backend 367 passed with the accepted
TestClient warning; legacy characterization 5 passed; compilation, lock,
package consistency, migration single-head/offline SQL, and diff checks passed.
