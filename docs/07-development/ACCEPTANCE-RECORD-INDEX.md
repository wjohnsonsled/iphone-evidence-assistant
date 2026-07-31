# Acceptance Record Index

## WP-0200 permanent traceability

- Owner decision: DEC-0027
- Validation package: QMS-007
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`
- Supported registry: empty

| Task | Acceptance record | Completion commit |
|---|---|---|
| DEV-0201 | DEV-0201-apple-backup-input-adapter-acceptance | `d831181`, approval `dce91b8` |
| DEV-0202 | DEV-0202-apple-backup-validation-acceptance | `78b0763`, approval `96101c5` |
| DEV-0203 | DEV-0203-backup-encryption-state-acceptance | `fbee309`, approval DEC-0014 |
| DEV-0204 | DEV-0204-sha256-hashing-acceptance | `818275b` |
| DEV-0205 | DEV-0205-controlled-sqlite-working-copy-acceptance | `2ed759e` |
| DEV-0206 | DEV-0206-intake-audit-event-acceptance | `44c7b20` |
| DEV-0207 | DEV-0207-intake-provenance-acceptance | `4b066b2` |
| DEV-0208 | DEV-0208-intake-cleanup-recovery-acceptance | `497cccd` |
| DEV-0209 | DEV-0209-intake-resource-limits-acceptance | `13bf589` |
| DEV-0210 | DEV-0210-intake-package-integration-acceptance | `23c74ab` |

Validation commands and results remain in the individual records and QMS-007.
DEC-0027 limitations remain permanent unless explicitly superseded. None of
these records promotes a capability to Supported.

## WP-0300 permanent traceability

- Owner decision: DEC-0037
- Validation package: QMS-008
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`
- Supported registry: empty

| Task | Acceptance record | Completion commit |
|---|---|---|
| DEV-0301 | DEV-0301-tenant-model-acceptance | `de0c648` |
| DEV-0302 | DEV-0302-user-role-model-acceptance | `5af6353` |
| DEV-0303 | DEV-0303-case-model-acceptance | `8182fe7` |
| DEV-0304 | DEV-0304-support-status-quarantine-acceptance | `252f767` |
| DEV-0305 | DEV-0305-evidence-source-linkage-acceptance | `d96ad70` |
| DEV-0306 | DEV-0306-audit-actor-attribution-acceptance | `13073a1` |
| DEV-0307 | DEV-0307-cross-tenant-isolation-acceptance | `a02fb3f` |
| DEV-0308 | DEV-0308-additive-security-migration-acceptance | `b167af8` |
| DEV-0309 | DEV-0309-security-package-integration-acceptance | `2cdd8ed` |
| DEV-0310 | DEV-0310-authorization-service-acceptance | `f7a494b` |

Validation commands and results remain in the individual records and QMS-008.
DEC-0037 limitations remain permanent unless explicitly superseded.

## WP-0400 permanent traceability

- Owner decision: DEC-0049
- Validation package: QMS-009
- Migration: `0004_candidate_supported_store`
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`
- Supported registry entries: 0
- Supported normalized records: 0

DEV-0401 through DEV-0412 acceptance records and commits form the permanent
package record. QMS-009 limitations remain active. No record promotes support.

## WP-1100 permanent traceability

- Owner decision: DEC-0055
- Validation package: QMS-010
- Migration: `0005_processing_idempotency`
- Current support status: `CANDIDATE_INFRASTRUCTURE_NOT_SUPPORTED`
- Supported registry entries: 0
- Supported normalized records: 0

DEV-1101 through DEV-1110 acceptance records and their focused local commits
form the permanent package record. QMS-010 preserves the reported focused,
backend-regression, legacy-characterization, compilation, lock, package,
migration, and hygiene results. Its live PostgreSQL, production repository,
production concurrency, API, deployment, real-evidence, parser-activation, and
support limitations remain active.

## WP-0500 permanent traceability

- Owner decision: DEC-0058
- Validation package: QMS-011
- Current support status: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries: 0
- Supported normalized records: 0

DEV-0501 through DEV-0509 acceptance records form the complete candidate
package. QMS-011 limitations remain active. Its synthetic corpus is not an
Apple-produced compatibility fixture and no record promotes support.

## DEV-0602A permanent validation traceability

- Implementation decision: DEC-0061
- Completion decision: DEC-0062
- Validation package: QMS-012
- Acceptance record: DEV-0602A-files-query-hardening-acceptance
- Current status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Current support status: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries: 0
- Supported normalized records: 0

DEV-0602 remains COMPLETE under DEC-0060 and its version 1 profiles remain
immutable. DEV-0602A is separately versioned owner-approved candidate
infrastructure; it promotes no support.

## DEV-0603 validation traceability

- Implementation decision: DEC-0063
- Completion decision: DEC-0064
- Validation package: QMS-013
- Acceptance record: DEV-0603-manifest-fileid-normalization-acceptance
- Current status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Current support status: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries: 0
- Supported normalized records: 0

The generic framework and single fileID profile remain synthetic candidate
infrastructure. Lexical/canonical equality is not hash, content, physical,
duplicate, absence, artifact, parser, or support validation.

## DEV-0604 validation traceability

- Implementation decision: DEC-0065
- Completion decision: DEC-0066
- Validation package: QMS-014
- Acceptance record: DEV-0604-manifest-domain-normalization-acceptance
- Current status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Current support status: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries: 0
- Supported normalized records: 0

The exact domain grammar is repository-characterized and synthetic. Structural
recognition is not Apple authority, application activity, physical existence,
completeness, artifact meaning, parser support, or capability support.

## DEV-0605 validation traceability

- Implementation decision: DEC-0067
- Completion decision: DEC-0068
- Validation package: QMS-015
- Acceptance record: DEV-0605-manifest-relative-path-acceptance
- Status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Support: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries / normalized records: 0 / 0

Lexical relative-path safety is not host-path safety, filesystem resolution,
physical existence, artifact identity, completeness, or support.

## DEV-0606 validation traceability

- Implementation decision: DEC-0069
- Completion decision: DEC-0070
- Validation package: QMS-016
- Acceptance record: DEV-0606-manifest-flags-observation-acceptance
- Status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Support: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries / normalized records: 0 / 0

All observed set bits remain unknown. The profile creates no file-state,
deletion, tampering, corruption, artifact, parser, or support conclusion.

## DEV-0607 validation traceability

- Implementation decision: DEC-0071
- Completion decision: DEC-0072
- Validation package: QMS-017
- Acceptance record: DEV-0607-manifest-metadata-blob-acceptance
- Status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Support: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries / normalized records: 0 / 0

The bounded scanner establishes binary-plist syntax only. It instantiates no
class and assigns no metadata-field, artifact, compatibility, or support
meaning.

## DEV-0609 validation traceability

- Implementation decision: DEC-0073
- Completion decision: DEC-0074
- Validation package: QMS-018
- Acceptance record: DEV-0609-manifest-reconciliation-semantics-acceptance
- Status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Support: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries / normalized records: 0 / 0

Repetition patterns create no duplicate, orphan, missing-object, absence,
artifact, parser, or support conclusion.

## DEV-0608 validation traceability

- Implementation decision: DEC-0075
- Completion decision: DEC-0076
- Validation package: QMS-019
- Acceptance record: DEV-0608-manifest-inventory-coverage-acceptance
- Status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Support: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries / normalized records: 0 / 0

Logical Files-row coverage never establishes backup, physical-object, artifact,
parser, metadata, normalized-record, user-activity, or absence conclusions.

## DEV-0610 validation traceability

- Implementation decision: DEC-0077
- Completion decision: DEC-0078
- Validation package: QMS-020
- Acceptance record: DEV-0610-synthetic-manifest-corpus-acceptance
- Profile/corpus: FOR-021; `manifest-synthetic-characterization-corpus` v1
- Status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Support: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries / normalized records: 0 / 0

Only synthetic characterization is in scope. Apple-produced, compatibility,
support, production, parser, artifact, input, and workflow validation remain
not started/not evaluated.

## DEV-0611 validation traceability

- Implementation decision: DEC-0079
- Completion decision: DEC-0080
- Validation package: QMS-021
- Acceptance record: DEV-0611-acceptance-record
- Profile: `manifest-synthetic-validation-report` version 1
- Authoritative report: `DEV-0611-manifest-synthetic-validation-report.md`
- Machine-readable report: `DEV-0611-manifest-synthetic-validation-report.json`
- Logical-content SHA-256:
  `5953d2d3a462dd3b15d42f287c65b660540c8d8b52cdf9081b00ef8798a42cc7`
- Disposition: `SYNTHETIC_CHARACTERIZATION_ACCEPTED_WITH_LIMITATIONS`
- Status: `COMPLETE_CANDIDATE_INFRASTRUCTURE`
- Support: `CANDIDATE_NOT_SUPPORTED`
- Supported registry entries / normalized records: 0 / 0

The report accepts only implementation and synthetic characterization with
limitations. Apple-produced characterization is not started; compatibility,
support, and production readiness are not evaluated; Supported capability is
unauthorized.
