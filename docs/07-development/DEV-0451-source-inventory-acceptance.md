# DEV-0451 — Source Inventory Engine

- Status: COMPLETE
- Dependencies: WP-0200, WP-0250, DEV-0402, DEV-0403 — COMPLETE
- Support effect: none
- Fixture policy: synthetic observations only

## Scope

Create deterministic, immutable inventory snapshots from already-registered,
tenant-scoped source-artifact and stable-locator observations. The task does not
inspect a filesystem, parse evidence, classify coverage, infer absence, or
determine support.

## Acceptance criteria

| ID | Criterion | Requirement mapping | Result |
|---|---|---|---|
| AC-01 | Snapshot retains tenant, case, evidence-source, processing-run, artifact, evidence, and locator identities | COV-GOV-001; FOR-INT-005 | PASS |
| AC-02 | Items and locator identities have deterministic ordering independent of caller order | COV-GOV-001 | PASS |
| AC-03 | Duplicate, orphaned, cross-tenant, cross-case, cross-source, and cross-run observations fail closed | COV-GOV-001; SEC-ISO-001 | PASS |
| AC-04 | Zero registered observations remains an empty inventory and is not recast as complete, absent, unsupported, or zero parsed records | COV-GOV-002; DEC-0027 | PASS |
| AC-05 | Mandatory limitations prohibit completeness, absence, and support inferences | COV-GOV-002; RSK-0020 | PASS |
| AC-06 | No evidence read, parser, migration, production API, registry entry, or support-status change is introduced | PRD-SCP-001; DEC-0049 | PASS |

## Validation

Focused deterministic tests cover ordering, immutable scope/provenance,
zero observations, duplicate and orphan denials, and cross-scope denial. Full
backend and legacy characterization regressions must pass before the task
commit.

Results: focused 7 passed; full backend 314 passed with the accepted
TestClient deprecation warning; legacy characterization 5 passed; compilation,
dependency-lock validation, installed-package consistency, and diff checks
passed. The first full-test attempt used a missing `--basetemp` parent and
produced fixture-setup errors; the documented pre-created repository-local
temporary-directory workaround passed on rerun.

## Limitations

This is an inventory of registered observations, not of all files or artifacts
that existed in a backup or on a device. It does not establish collection,
processing, compatibility, completeness, or support. Persistent repositories,
live PostgreSQL, source discovery, and coverage conclusions remain outside this
task.
