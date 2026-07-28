# DEV-1102 — Legacy Parser Registry Isolation

- Status: COMPLETE
- Dependency: DEV-1101 — COMPLETE
- Support effect: none

## Scope and acceptance

This task validates the already-approved physical composition boundary rather
than creating a duplicate legacy registry. The supported registry package must
have no import of legacy applications, legacy processing services, or
`evidence_engine`; access to the quarantined legacy plugin collection must
remain confined to the explicit legacy processing service; and the production
supported registry must remain empty.

All three focused static/runtime checks pass. Existing legacy behavior is
unchanged. There is no transfer, adapter, promotion, parser execution, evidence
read, migration, API exposure, or support effect.

Validation: focused boundary suite 28 passed; full backend regression 319
passed with the accepted TestClient warning; legacy characterization 5 passed;
compilation and diff checks passed.

## Limitation

Static import controls do not replace deployment controls. The explicit legacy
application remains deployable as code and must continue to be excluded from
the supported SaaS deployment surface under RSK-0001.
