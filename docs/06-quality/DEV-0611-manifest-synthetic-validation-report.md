# DEV-0611 — Manifest Synthetic Validation Report

## 1. Document control

- Report: `DEV-0611-MANIFEST-SYNTHETIC-VALIDATION-REPORT`
- Profile: `manifest-synthetic-validation-report` version `1`
- Logical-content SHA-256: `5953d2d3a462dd3b15d42f287c65b660540c8d8b52cdf9081b00ef8798a42cc7`
- Authority: DEC-0079
- Authoritative representation: this Markdown report

## 2. Executive summary

Disposition: `SYNTHETIC_CHARACTERIZATION_ACCEPTED_WITH_LIMITATIONS`.
Candidate implementation and project-original synthetic characterization are complete with the limitations below.
Apple-produced characterization, compatibility validation, support validation, production readiness, and Supported capability remain not started, not evaluated, or unauthorized.
No real evidence was processed; registry entries and supported normalized records remain zero.

## 3. Purpose

Internal architecture, quality, forensic-method, security, audit, and future support-gate preparation.

## 4. Scope

Repository-controlled DEV-0601 through DEV-0610 implementation and synthetic characterization records, plus this DEV-0611 package.

## 5. Explicit exclusions

- Apple-version compatibility
- artifact support
- parser support
- backup support
- physical-object existence or absence
- duplicate or orphaned physical objects
- user activity completeness
- production readiness
- Supported capability

## 6. Governing decisions

`DEC-0059`, `DEC-0060`, `DEC-0061`, `DEC-0062`, `DEC-0063`, `DEC-0064`, `DEC-0065`, `DEC-0066`, `DEC-0067`, `DEC-0068`, `DEC-0069`, `DEC-0070`, `DEC-0071`, `DEC-0072`, `DEC-0073`, `DEC-0074`, `DEC-0075`, `DEC-0076`, `DEC-0077`, `DEC-0078`, `DEC-0079`, `DEC-0080`

## 7. Workstream task history

| Task | Status | Decision | Commit | Profile | Acceptance | Validation |
|---|---|---|---|---|---|---|
| DEV-0601 | COMPLETE | DEC-0059 | 8b29f16 | apple-manifestdb-schema v1 | DEV-0601-manifest-schema-profile-acceptance | QMS record not separate |
| DEV-0602 | COMPLETE | DEC-0060 | c7f7e3e | manifestdb-files-query v1 | DEV-0602-files-query-layer-acceptance | FOR-012 |
| DEV-0602A | COMPLETE | DEC-0061/DEC-0062 | 74a0175/6eaee32 | manifestdb-files-query v2 | DEV-0602A-files-query-hardening-acceptance | QMS-012 |
| DEV-0603 | COMPLETE | DEC-0063/DEC-0064 | 7416db1 | manifestdb-fileid-normalization v1 | DEV-0603-manifest-fileid-normalization-acceptance | QMS-013 |
| DEV-0604 | COMPLETE | DEC-0065/DEC-0066 | 4654069 | manifestdb-domain-grammar v1 | DEV-0604-manifest-domain-normalization-acceptance | QMS-014 |
| DEV-0605 | COMPLETE | DEC-0067/DEC-0068 | c1423c6 | manifestdb-relative-path-lexical v1 | DEV-0605-manifest-relative-path-acceptance | QMS-015 |
| DEV-0606 | COMPLETE | DEC-0069/DEC-0070 | 2854ecd | manifestdb-flags-observation v1 | DEV-0606-manifest-flags-observation-acceptance | QMS-016 |
| DEV-0607 | COMPLETE | DEC-0071/DEC-0072 | ef3517d | manifestdb-file-bplist-syntax v1 | DEV-0607-manifest-metadata-blob-acceptance | QMS-017 |
| DEV-0608 | COMPLETE | DEC-0075/DEC-0076 | c8e9684 | manifestdb-inventory-coverage v1 | DEV-0608-manifest-inventory-coverage-acceptance | QMS-019 |
| DEV-0609 | COMPLETE | DEC-0073/DEC-0074 | d23738e/7a1f2e3 | manifestdb-reconciliation-semantics v1 | DEV-0609-manifest-reconciliation-semantics-acceptance | QMS-018 |
| DEV-0610 | COMPLETE | DEC-0077/DEC-0078 | f615f8b | synthetic-characterization-corpus-governance v1 | DEV-0610-synthetic-manifest-corpus-acceptance | QMS-020 |
| DEV-0611 | COMPLETE | DEC-0079/DEC-0080 | not recorded | manifest-synthetic-validation-report v1 | DEV-0611-acceptance-record | QMS-021 |

## 8. Candidate profile inventory

| Profile | Version | Task | Decision | Synthetic | Apple-produced | Compatibility | Support |
|---|---|---|---|---|---|---|---|
| apple-manifestdb-schema | 1 | DEV-0601 | DEC-0059 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-schema-canonical-json-sha256 | 1 | DEV-0601 | DEC-0008/DEC-0059 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-files-query | 1 | DEV-0602 | DEC-0060 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-row-locator | 1 | DEV-0602 | DEC-0060 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-files-query | 2 | DEV-0602A | DEC-0061/DEC-0062 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-query-resource-controls | 1 | DEV-0602A | DEC-0061/DEC-0062 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| canonical-identifier-normalization | 1 | DEV-0603 | DEC-0063/DEC-0064 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-fileid-normalization | 1 | DEV-0603 | DEC-0063/DEC-0064 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-domain-grammar | 1 | DEV-0604 | DEC-0065/DEC-0066 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-relative-path-lexical | 1 | DEV-0605 | DEC-0067/DEC-0068 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-flags-observation | 1 | DEV-0606 | DEC-0069/DEC-0070 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-file-bplist-syntax | 1 | DEV-0607 | DEC-0071/DEC-0072 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-reconciliation-semantics | 1 | DEV-0609 | DEC-0073/DEC-0074 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifestdb-inventory-coverage | 1 | DEV-0608 | DEC-0075/DEC-0076 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| synthetic-characterization-corpus-governance | 1 | DEV-0610 | DEC-0077/DEC-0078 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifest-synthetic-characterization-corpus | 1 | DEV-0610 | DEC-0077/DEC-0078 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |
| manifest-synthetic-validation-report | 1 | DEV-0611 | DEC-0079 | CHARACTERIZED | NOT_STARTED | NOT_EVALUATED | NOT_EVALUATED |

## 9. Architecture summary

Candidate modules remain isolated from production composition, persistence, APIs, supported storage, and parser activation. See ARC-002.

## 10. Evidence-integrity controls

Source immutability and controlled-copy boundaries remain governing; this package contains no source evidence. Report and corpus digests protect test/report assets only.

## 11. Provenance controls

Every task/profile/claim traces to decisions, acceptance/validation records, commits where recorded, limitations, and report sections.

## 12. Security controls

Fixed registered inputs only; no arbitrary paths, backup crawling, network, secrets, dynamic code, unsafe deserialization, or evidence access.

## 13. Resource-governance controls

Row, page, byte, deterministic memory-estimate, wall-clock, cancellation, concurrency, authorization, schema, mutation, and SQLite outcomes were synthetically characterized.

## 14. Synthetic corpus governance

Corpus `manifest-synthetic-characterization-corpus` v1 is governed by FOR-021.

## 15. Synthetic fixture source policy

Source: `PROJECT_ORIGINAL_SYNTHETIC_ONLY`; real/Apple-produced content: `False`.

## 16. Synthetic corpus inventory

- Fixtures: 60
- Profile matrix entries: 13
- Synthetic test-asset integrity digest: `159b01df907f56cd7c8f82c1a77cc67e479f6c87e169408b3aec5fcec38655bc`

## 17. Schema coverage matrix

QMS-020 and the v1 corpus matrix cover compatible, unknown, missing, unexpected, invalid, corrupt, locator, mutation, fingerprint, and unsupported synthetic schema conditions.

## 18. Profile coverage matrix

All 13 DEV-0610 matrix entries and the broader 17-entry workstream profile inventory are accounted for. See the JSON `profiles` and committed corpus `profile_matrix`.

## 19. Positive scenario coverage

Recognized schema/query/locator/normalization/syntax and complete-coverage synthetic paths are registered.

## 20. Negative scenario coverage

Denial, unsupported, unavailable, mismatch, isolation, mutation, missing, and prohibited-source paths are registered.

## 21. Malformed-input coverage

Malformed SQLite, identifier, domain, BLOB, manifest, provenance, custody, and distribution inputs fail closed.

## 22. Resource-limit coverage

Row, byte, deterministic memory-estimate, wall-clock, cancellation, and concurrency cases are registered.

## 23. Isolation coverage

Cross-tenant, cross-case, cross-source/copy/run, authorization, and unregistered-input denials are covered.

## 24. Determinism coverage

Fixture regeneration, canonical JSON, corpus manifest, observation/report serialization, and digest verification are deterministic.

## 25. Validation results

| Dimension | Status | Count | Source | Commit | Warning |
|---|---|---|---|---|---|
| focused validation | PASS | 63 | QMS-021 | not recorded | not recorded |
| integration validation | PASS | not recorded | QMS-021 | not recorded | not recorded |
| combined Manifest validation | PASS | 385 | QMS-021 | not recorded | not recorded |
| backend regression | PASS_WITH_ACCEPTED_WARNING | 776 | QMS-021 | not recorded | Accepted third-party TestClient deprecation warning. |
| legacy characterization | PASS | 5 | QMS-021 | not recorded | not recorded |
| compilation | PASS | not recorded | QMS-021 | not recorded | not recorded |
| dependency lock | PASS | 3 | QMS-020 | f615f8b | not recorded |
| pip consistency | PASS | not recorded | QMS-020 | f615f8b | not recorded |
| Alembic head | PASS | 1 | QMS-020 | f615f8b | not recorded |
| Alembic history | PASS | 5 | QMS-020 | f615f8b | not recorded |
| Alembic offline SQL | PASS | not recorded | QMS-020 | f615f8b | not recorded |
| repository hygiene | PASS | not recorded | QMS-020 | f615f8b | not recorded |
| fixture integrity | PASS | 60 | QMS-020 | f615f8b | not recorded |
| deterministic regeneration | PASS | 60 | QMS-020 | f615f8b | not recorded |
| security review | PASS_WITH_LIMITATIONS | not recorded | SEC-001/FOR-021 | f615f8b | not recorded |
| final diff review | PASS | not recorded | QMS-020 | f615f8b | not recorded |

## 26. Accepted warnings

- Third-party TestClient/httpx2 deprecation warning.

## 27. Migration status

Head remains `0005_processing_idempotency`; new migrations: 0.

## 28. Registry and normalized-record status

Supported Parser Registry entries: 0; supported normalized records: 0.

## 29. Limitation summary

- Synthetic fixtures do not prove Apple-generated behavior.
- Lexical recognition is not cryptographic verification.
- Canonical fileID equality is not content identity.
- Domain recognition is not proof of application installation or use.
- Relative-path normalization is not physical resolution.
- Flags observation is not proof of deletion or existence.
- Metadata-BLOB syntax recognition is not full semantic interpretation.
- Manifest row inventory coverage is not artifact coverage.
- Partial coverage cannot support absence.
- Reconciliation patterns do not prove missing or orphaned objects without complete comparison universes.
- No physical-object inventory was created.
- No real evidence or Apple-produced fixture was processed.
- No parser was activated and no support status changed.
- Supported Parser Registry entries and supported normalized records remain zero.

## 30. Unsupported conclusions

- Apple-version compatibility: not evaluated or not authorized.
- artifact support: not evaluated or not authorized.
- parser support: not evaluated or not authorized.
- backup support: not evaluated or not authorized.
- physical-object existence or absence: not evaluated or not authorized.
- duplicate or orphaned physical objects: not evaluated or not authorized.
- user activity completeness: not evaluated or not authorized.
- production readiness: not evaluated or not authorized.
- Supported capability: not evaluated or not authorized.

## 31. Apple-produced validation status

`NOT_STARTED`. No Apple-produced fixture was acquired, generated, or processed.

## 32. Compatibility-validation status

`NOT_EVALUATED`. Synthetic behavior cannot establish Apple/device/software compatibility.

## 33. Support-validation status

`NOT_EVALUATED`. No parser, artifact, input, backup, workflow, or capability is Supported.

### Claims matrix

| Claim | Repository | Synthetic | Apple | Compatibility | Support | Permitted wording | Prohibited wording |
|---|---|---|---|---|---|---|---|
| Manifest schema recognition | CANDIDATE_SYNTHETIC_ONLY | Permitted only for the candidate synthetic schema profile. | NONE | NONE | NOT_EVALUATED | Permitted only for the candidate synthetic schema profile. | Manifest schema recognition is Supported or Apple-compatible. |
| Files-table query behavior | CANDIDATE_SYNTHETIC_ONLY | Permitted only for controlled synthetic query behavior. | NONE | NONE | NOT_EVALUATED | Permitted only for controlled synthetic query behavior. | Files-table query behavior is Supported or Apple-compatible. |
| ROWID locator behavior | CANDIDATE_SYNTHETIC_ONLY | Permitted only within one controlled copy and processing run. | NONE | NONE | NOT_EVALUATED | Permitted only within one controlled copy and processing run. | ROWID locator behavior is Supported or Apple-compatible. |
| fileID lexical recognition | CANDIDATE_SYNTHETIC_ONLY | Permitted as lexical recognition, not hash verification. | NONE | NONE | NOT_EVALUATED | Permitted as lexical recognition, not hash verification. | fileID lexical recognition is Supported or Apple-compatible. |
| domain grammar | CANDIDATE_SYNTHETIC_ONLY | Permitted as candidate structural recognition only. | NONE | NONE | NOT_EVALUATED | Permitted as candidate structural recognition only. | domain grammar is Supported or Apple-compatible. |
| relative-path normalization | CANDIDATE_SYNTHETIC_ONLY | Permitted as lexical observation, not physical resolution. | NONE | NONE | NOT_EVALUATED | Permitted as lexical observation, not physical resolution. | relative-path normalization is Supported or Apple-compatible. |
| flags observation | CANDIDATE_SYNTHETIC_ONLY | Permitted with every bit meaning unknown. | NONE | NONE | NOT_EVALUATED | Permitted with every bit meaning unknown. | flags observation is Supported or Apple-compatible. |
| metadata-BLOB syntax recognition | CANDIDATE_SYNTHETIC_ONLY | Permitted as bounded syntax recognition without semantic field meaning. | NONE | NONE | NOT_EVALUATED | Permitted as bounded syntax recognition without semantic field meaning. | metadata-BLOB syntax recognition is Supported or Apple-compatible. |
| inventory coverage | CANDIDATE_SYNTHETIC_ONLY | Permitted only for the performed logical Files-row examination. | NONE | NONE | NOT_EVALUATED | Permitted only for the performed logical Files-row examination. | inventory coverage is Supported or Apple-compatible. |
| reconciliation semantics | CANDIDATE_SYNTHETIC_ONLY | Permitted only as repetition-pattern observation. | NONE | NONE | NOT_EVALUATED | Permitted only as repetition-pattern observation. | reconciliation semantics is Supported or Apple-compatible. |
| absence eligibility | CANDIDATE_SYNTHETIC_ONLY | Not eligible without every separately approved complete universe and layer. | NONE | NONE | NOT_EVALUATED | Not eligible without every separately approved complete universe and layer. | absence eligibility is Supported or Apple-compatible. |
| duplicate eligibility | CANDIDATE_SYNTHETIC_ONLY | Not established without physical inventory and validated conclusions. | NONE | NONE | NOT_EVALUATED | Not established without physical inventory and validated conclusions. | duplicate eligibility is Supported or Apple-compatible. |
| orphan eligibility | CANDIDATE_SYNTHETIC_ONLY | Not established without physical inventory and validated conclusions. | NONE | NONE | NOT_EVALUATED | Not established without physical inventory and validated conclusions. | orphan eligibility is Supported or Apple-compatible. |
| physical-object resolution | CANDIDATE_SYNTHETIC_ONLY | Not implemented or evaluated. | NONE | NONE | NOT_EVALUATED | Not implemented or evaluated. | physical-object resolution is Supported or Apple-compatible. |
| Apple-version compatibility | CANDIDATE_SYNTHETIC_ONLY | Not evaluated. | NONE | NONE | NOT_EVALUATED | Not evaluated. | Apple-version compatibility is Supported or Apple-compatible. |
| artifact support | CANDIDATE_SYNTHETIC_ONLY | Not evaluated. | NONE | NONE | NOT_EVALUATED | Not evaluated. | artifact support is Supported or Apple-compatible. |
| parser support | CANDIDATE_SYNTHETIC_ONLY | Not evaluated. | NONE | NONE | NOT_EVALUATED | Not evaluated. | parser support is Supported or Apple-compatible. |
| backup support | CANDIDATE_SYNTHETIC_ONLY | Not evaluated. | NONE | NONE | NOT_EVALUATED | Not evaluated. | backup support is Supported or Apple-compatible. |

## 34. Risk summary

`RSK-0031`, `RSK-0032`, `RSK-0034`, `RSK-0035`, `RSK-0036`, `RSK-0037`, `RSK-0038`, `RSK-0039`, `RSK-0040`, `RSK-0041`

## 35. Remaining dependencies

A separately owner-governed Apple-produced characterization package is required before compatibility or support validation.

## 36. Future validation requirements

- lawful device and account ownership
- documented backup-generation procedure
- device model and operating-system version
- Apple backup software and version
- encryption state and backup settings
- collection operator and date/time
- controlled-copy creation and digests
- custody and minimization
- personal-data handling and secure storage
- retention and destruction
- distribution limits and source-control prohibition
- schema fingerprints
- profile results and known ground truth
- compatibility matrix and failure cases
- repeatability and independent review

### Validation ladder

| Level | Name | Status | Completed | Missing | Permitted | Decision required |
|---|---|---|---|---|---|---|
| 1 | Synthetic implementation characterization | COMPLETE_WITH_LIMITATIONS | Candidate implementation and project-original synthetic corpus characterized. | Apple-produced behavior and every later gate. | Candidate synthetic behavior only. | Separate owner approval before advancement. |
| 2 | Controlled Apple-produced characterization | NOT_STARTED | None. | Owner-governed lawful fixture package and controlled execution. | No Apple-produced claim. | Separate owner approval before advancement. |
| 3 | Compatibility validation | NOT_EVALUATED | None. | Multi-version Apple-produced matrix and independent review. | No compatibility claim. | Separate owner approval before advancement. |
| 4 | Support validation | NOT_EVALUATED | None. | Complete all-or-nothing artifact/parser validation and owner gate. | No support claim. | Separate owner approval before advancement. |
| 5 | Production readiness review | NOT_EVALUATED | None. | Deployment, capacity, live database, operational and security review. | No production-readiness claim. | Separate owner approval before advancement. |
| 6 | Supported capability | NOT_AUTHORIZED | None. | Explicit traceable owner promotion after all prior gates. | No Supported claim. | Separate owner approval before advancement. |

## 37. Synthetic characterization disposition

`SYNTHETIC_CHARACTERIZATION_ACCEPTED_WITH_LIMITATIONS` applies only to implementation and synthetic characterization.
- Synthetic fixtures do not prove Apple-generated behavior.
- Lexical recognition is not cryptographic verification.
- Canonical fileID equality is not content identity.
- Domain recognition is not proof of application installation or use.
- Relative-path normalization is not physical resolution.
- Flags observation is not proof of deletion or existence.
- Metadata-BLOB syntax recognition is not full semantic interpretation.
- Manifest row inventory coverage is not artifact coverage.
- Partial coverage cannot support absence.
- Reconciliation patterns do not prove missing or orphaned objects without complete comparison universes.
- No physical-object inventory was created.
- No real evidence or Apple-produced fixture was processed.
- No parser was activated and no support status changed.
- Supported Parser Registry entries and supported normalized records remain zero.

## 38. Acceptance criteria

All DEV-0611 criteria are validated by QMS-021 and the focused report test suite; this statement becomes final only with the completion record.

## 39. Traceability appendix

| Requirement | Task | Decision | Implementation | Test | Limitation | Section |
|---|---|---|---|---|---|---|
| DEV-0611-R01 | DEV-0601 | DEC-0059 | apple-manifestdb-schema | QMS record not separate | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R02 | DEV-0602 | DEC-0060 | manifestdb-files-query | FOR-012 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R03 | DEV-0602A | DEC-0061/DEC-0062 | manifestdb-files-query | QMS-012 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R04 | DEV-0603 | DEC-0063/DEC-0064 | manifestdb-fileid-normalization | QMS-013 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R05 | DEV-0604 | DEC-0065/DEC-0066 | manifestdb-domain-grammar | QMS-014 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R06 | DEV-0605 | DEC-0067/DEC-0068 | manifestdb-relative-path-lexical | QMS-015 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R07 | DEV-0606 | DEC-0069/DEC-0070 | manifestdb-flags-observation | QMS-016 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R08 | DEV-0607 | DEC-0071/DEC-0072 | manifestdb-file-bplist-syntax | QMS-017 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R09 | DEV-0608 | DEC-0075/DEC-0076 | manifestdb-inventory-coverage | QMS-019 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R10 | DEV-0609 | DEC-0073/DEC-0074 | manifestdb-reconciliation-semantics | QMS-018 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R11 | DEV-0610 | DEC-0077/DEC-0078 | synthetic-characterization-corpus-governance | QMS-020 | DEV-0611 Limitation summary | Workstream task history |
| DEV-0611-R12 | DEV-0611 | DEC-0079/DEC-0080 | manifest-synthetic-validation-report | QMS-021 | DEV-0611 Limitation summary | Workstream task history |

## 40. Commit and decision appendix

| Task | Decision | Commit |
|---|---|---|
| DEV-0601 | DEC-0059 | 8b29f16 |
| DEV-0602 | DEC-0060 | c7f7e3e |
| DEV-0602A | DEC-0061/DEC-0062 | 74a0175/6eaee32 |
| DEV-0603 | DEC-0063/DEC-0064 | 7416db1 |
| DEV-0604 | DEC-0065/DEC-0066 | 4654069 |
| DEV-0605 | DEC-0067/DEC-0068 | c1423c6 |
| DEV-0606 | DEC-0069/DEC-0070 | 2854ecd |
| DEV-0607 | DEC-0071/DEC-0072 | ef3517d |
| DEV-0608 | DEC-0075/DEC-0076 | c8e9684 |
| DEV-0609 | DEC-0073/DEC-0074 | d23738e/7a1f2e3 |
| DEV-0610 | DEC-0077/DEC-0078 | f615f8b |
| DEV-0611 | DEC-0079/DEC-0080 | not recorded |
