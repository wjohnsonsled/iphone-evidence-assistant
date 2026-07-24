# FOR-006 — Legacy Parser Quarantine Policy

## 1. Purpose

This policy prevents pre-baseline and unvalidated parser output from being
mistaken for supported evidence. It defines the future supported-path boundary
without changing current runtime behavior.

## 2. Definitions

### Legacy parser

A parser that existed before the controlled requirements and validation
baseline, including parsers implemented in or re-exported from
`evidence_engine._legacy`. A legacy parser is unsupported unless promoted under
this policy.

### Supported parser

A parser approved for a specifically declared artifact family, source
discovery method, iOS/schema profile, field set, relationship behavior,
timestamp method, source-locator format, failure contract, and parser version.
All required tests, fixtures, documentation, provenance, and acceptance review
must be complete.

### Experimental parser

An explicitly labeled parser available only in an isolated evaluation
environment. Its records are derived experimental output and cannot be treated
as validated evidence.

### Compatibility parser

A legacy parser retained to reproduce historical CLI behavior or support
characterization testing. Compatibility status describes retention purpose, not
forensic support.

### Parser quarantine

Technical and procedural isolation that prevents a parser and its output from
entering the supported production registry, normalized evidence store, AI
retrieval corpus, supported reports, or supported coverage calculations.

## 3. Approved parser registry

The future supported product path must use a separate, explicit, versioned
registry containing only parsers approved as `SUPPORTED_COMPLETE` for the
declared schema or capable of returning `SUPPORTED_NO_RECORDS` after complete
successful examination.

The current legacy `plugins()` registry is not the approved parser registry.
Its presence and default behavior are retained compatibility behavior only.

An approved registry entry must identify:

- artifact ID and family;
- parser name and immutable version;
- supported input and acquisition type;
- supported iOS versions and schema fingerprints;
- source discovery method and companion files;
- field and relationship coverage;
- timestamp conversion profile;
- source-locator format;
- controlled success and failure statuses;
- validation fixture and expected result;
- test names and results;
- approval record; and
- effective and retirement dates where applicable.

## 4. Default-disabled policy

In the future supported product path:

- every parser is disabled unless present in the approved registry;
- candidate status does not enable a parser;
- legacy, compatibility, experimental, deferred, excluded, unknown-schema, and
  unsupported parsers are disabled by default;
- only the minimum parser set needed for the approved artifact family executes;
  and
- registry configuration must be enforced server-side and recorded per run.

Implementation of this behavior requires a separately approved task. DEV-0002
does not alter the current legacy registry or CLI.

## 5. Initial MVP quarantine assignments

### Eligible for validation and future promotion

The following legacy logic may be evaluated for reuse, but remains quarantined
until promoted:

- backup metadata discovery/parsing;
- `Manifest.db` parsing and file inventory;
- SMS/iMessage messages, chats, and handles;
- message attachments;
- call history; and
- contacts.

### Mandatory quarantine from the initial supported path

The following existing parser families must not enter the initial supported
path:

- Notes;
- Safari;
- Calendar;
- Health;
- keychain-derived or saved-credential processing;
- arbitrary third-party applications;
- deleted-data recovery;
- malware or spyware analysis;
- Mail;
- Reminders;
- Photos;
- Maps/location;
- KnowledgeC/CoreDuet;
- notifications;
- Wi-Fi, Bluetooth, AirDrop/Nearby, network configuration,
  cellular/telephony, and data-usage parsers;
- generic SQLite parsing;
- generic plist/system-file parsing except a separately approved backup-metadata
  parser profile.

## 6. Output isolation rules

Output from a quarantined parser is prohibited from entering:

1. the supported normalized evidence store;
2. indexes, embeddings, or retrieval sets used by supported AI;
3. supported evidence-grounded answers;
4. supported timelines or search results;
5. supported client or attorney reports;
6. supported coverage percentages or completeness calculations;
7. supported no-record determinations; and
8. supported citations or evidentiary assertions.

If experimental output is retained, it must use a separate store or explicit
namespace, include its parser and experiment identifiers, and display an
unambiguous unsupported/experimental warning. It must never be merged silently
with supported records.

## 7. Promotion requirements

A quarantined parser may be promoted only when all declared behavior is:

- approved in scope;
- implemented;
- validated against approved synthetic or lawfully distributable fixtures;
- tested for success, zero records, malformed input, corruption, unknown schema,
  deterministic output, provenance, timestamps, and regression behavior;
- documented with complete FOR-004 per-artifact details;
- provenance-aware and raw-value preserving;
- based on controlled SQLite working copies where applicable;
- failure-aware with controlled statuses;
- versioned and tied to a parser execution record;
- secured and case/tenant scoped;
- traceable in DOC-002;
- reviewed against explicit acceptance criteria; and
- approved by the owner or delegated forensic reviewer.

Promotion is specific to the declared schema profile. Validation of one schema
does not authorize another.

## 8. Required audit records

Every future supported parser decision and execution must record:

- case, tenant, evidence source, and intake identifiers;
- source hashes and working-copy hashes;
- artifact ID;
- parser name and version;
- registry version;
- configuration;
- start/end times;
- source paths and companion-file presence;
- detected schema fingerprint;
- status and status reason;
- rows examined and records normalized;
- omissions, warnings, and errors;
- validation/acceptance reference;
- actor or service identity; and
- immutable correlation/request identifier.

Passwords, decrypted secrets, tokens, or unnecessary artifact content must not
be placed in audit records.

## 9. Required failure behavior

A parser must fail closed for unsupported or unknown conditions:

- unknown schema: `UNSUPPORTED` or another approved explicit non-success status;
- inaccessible encrypted content: `INACCESSIBLE`;
- corrupted source or working copy: `CORRUPTED`;
- parser or processing error: `FAILED`;
- deliberately excluded source: `EXCLUDED`;
- successful complete processing with records: `SUPPORTED_COMPLETE`;
- successful complete processing with no records: `SUPPORTED_NO_RECORDS`.

The parser must not:

- return an empty list as the only indication of failure;
- convert an exception into a no-record conclusion;
- claim support based on file presence;
- silently omit unreadable rows or fields;
- fall back to a generic parser and call the result supported; or
- allow partial output into the supported store after completeness can no
  longer be established.

Partial results may be retained only as clearly separated derived diagnostic
work product with a `FAILED`, `CORRUPTED`, `UNSUPPORTED`, or experimental
designation, according to the approved status model.

## 10. Legacy CLI compatibility

The historical CLI may remain available without deletion to preserve
characterization and compatibility. Until an approved implementation task adds
the necessary separation:

- it is a legacy compatibility surface;
- its registry and output are not the supported production registry or store;
- documentation must call its parsers implemented-but-unvalidated;
- CLI output must not be described as a supported forensic report;
- users must not infer support from a listed plugin or successful run; and
- no supported backend, AI, coverage, or reporting path may consume its output.

Whether the CLI remains internal-only or is distributed requires owner approval.

## 11. Scope-decision matrix

| Decision | Rationale | Customer value | Forensic risk | Implementation impact | Owner approval |
|---|---|---|---|---|---|
| Separate supported and legacy registries | Prevents accidental parser activation | Clear, defensible scope | Registry mixing contaminates evidence | Future registry/configuration work | Approved policy; implementation task still required |
| Default-disable every unapproved parser | Enforces all-or-nothing support | Predictable results | Silent execution creates unsupported claims | Future server-side gating | Approved policy |
| Quarantine all non-MVP legacy plugins | Keeps initial scope narrow | Faster validation of high-value artifacts | Broad heuristic parsers increase error risk | Retain code but exclude output | Approved policy |
| Block quarantined output from AI/reports/coverage | Maintains evidence grounding | Trustworthy citations and limitations | Unsupported facts can propagate into conclusions | Separate stores and retrieval filters later | Approved policy |
| Permit parser-by-parser reuse after validation | Avoids unnecessary rewrite | Potential delivery efficiency | Legacy assumptions may survive unnoticed | Characterize, validate, refactor, or replace | Owner approval at promotion |
| Retain legacy CLI without support claim | Preserves historical behavior | Compatibility for controlled users | CLI may be mistaken for production | Warnings/separation require later task | Distribution decision requires owner approval |

## 12. Current status

No parser is promoted by this policy. All current legacy parsers remain
implemented-but-unvalidated, experimental, compatibility, unsupported, or
candidate code according to PRD-006 and FOR-004.
