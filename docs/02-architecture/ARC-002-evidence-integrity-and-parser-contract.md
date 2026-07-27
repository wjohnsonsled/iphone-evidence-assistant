# ARC-002 — Evidence Integrity and Supported-Parser Contract

**Status:** Authorized for WP-0250 implementation by DEC-0011; owner package review pending
**Parent architecture:** ARC-001  
**Applies to:** WP-0250 and all future supported artifact parsers  
**Owner approval:** Required before implementation choices that conflict with ARC-001

---

## 1. Decision Summary

Adopt a shared evidence-integrity layer and a mandatory supported-parser contract.

All future supported parsers must use the same services for:

- evidence registration;
- integrity verification;
- controlled-copy access;
- lifecycle enforcement;
- audit events;
- chain-of-custody records;
- provenance;
- coverage and limitation reporting.

A parser cannot become supported merely by implementing the interface. Support still requires a separate artifact-validation package and explicit owner promotion.

---

## 2. Architectural Placement

The integrity layer sits between intake and artifact parsing.

```text
Input Adapter
    ↓
Structure Validator
    ↓
Evidence Integrity Infrastructure
    ↓
Supported Parser Registry
    ↓
Candidate Artifact Parser
    ↓
Supported Evidence Store
    ↓
Search / Timeline / AI / Reports
```

Legacy and experimental parsers remain outside the supported path.

---

## 3. Components

### Evidence Registry

Creates stable evidence-object identities and links them to tenant and case records.

### Hash Registry

Stores immutable hash observations and their context.

### Integrity Verification Service

Evaluates current observations against approved policy.

### Lifecycle Service

Applies atomic state transitions.

### Access and Lock Service

Controls application-level evidence access intents.

### Chain-of-Custody Service

Creates append-only custody and handling events.

### Audit Service

Creates append-only operational audit events.

### Provenance Service

Creates and validates derivation relationships.

### Supported Parser Registry

Allows execution only for parsers explicitly enabled as candidates or supported under approved policy.

### Parser Conformance Harness

Tests whether a parser obeys the shared contract.

---

## 4. Supported-Parser Interface

The exact language syntax may vary, but the logical interface must provide equivalents of:

```python
class EvidenceParser:
    @property
    def parser_id(self) -> str: ...

    @property
    def parser_version(self) -> str: ...

    @property
    def artifact_family(self) -> str: ...

    def declared_schema_profiles(self) -> tuple[str, ...]: ...

    def validate(self, context: ValidationContext) -> ValidationResult: ...

    def parse(self, context: ParseContext) -> ParseResult: ...

    def report_coverage(self, context: CoverageContext) -> CoverageResult: ...

    def report_limitations(self, context: LimitationContext) -> LimitationResult: ...

    def self_test(self, context: SelfTestContext) -> SelfTestResult: ...
```

This is a logical contract, not a mandate to use this exact class shape.

---

## 5. Validation Contract

`validate()` must:

- operate only on approved controlled inputs;
- identify the parser and version;
- identify the schema profile;
- return deterministic typed outcomes;
- distinguish invalid, corrupt, unsupported, indeterminate, and operational failure when applicable;
- avoid modifying evidence;
- emit observations and limitations;
- never imply support.

---

## 6. Parse Contract

`parse()` must:

- require a successful integrity-policy decision;
- require an approved schema profile;
- use controlled inputs only;
- never write source evidence;
- emit deterministic raw and normalized values;
- create source locators;
- create provenance links;
- report record-level failures;
- report coverage and omissions;
- fail closed when completeness cannot be characterized as required by the artifact profile.

---

## 7. Coverage Contract

Coverage must report at least:

- records examined;
- records emitted;
- records intentionally excluded;
- records rejected;
- records failed;
- records indeterminate;
- unsupported variants encountered;
- schema profile;
- parser version;
- limitations affecting completeness.

A zero-result parse is not automatically a successful complete parse.

---

## 8. Provenance Contract

Every emitted supported record must identify:

- evidence UUID;
- source artifact;
- stable source locator;
- controlled-copy relationship;
- parser ID;
- parser version;
- schema profile;
- processing run;
- raw source representation or raw-value reference;
- normalized representation;
- transformation notes;
- timestamp conversion, when applicable.

---

## 9. Failure Contract

Parsers must use typed failures.

Prohibited behavior:

- swallowing exceptions that affect completeness;
- logging and continuing without a coverage impact;
- substituting default values that appear evidentiary;
- converting an unknown value to false, zero, empty, or absent without a recorded transformation;
- reporting a successful parse after an integrity-policy failure.

---

## 10. Self-Test Contract

A parser self-test must:

- use deterministic synthetic fixtures;
- verify parser identity and version;
- verify supported schema-profile declarations;
- verify provenance generation;
- verify coverage accounting;
- verify failure behavior;
- verify no source writes;
- be runnable without real evidence or external services.

Self-test success is not support approval.

---

## 11. Registry States

Suggested parser registry states:

- `QUARANTINED`
- `EXPERIMENTAL`
- `CANDIDATE`
- `SUPPORTED`
- `DEPRECATED`
- `DISABLED`

Only `SUPPORTED` parsers may provide customer-facing supported records.

A `CANDIDATE` parser may be exercised only in approved synthetic or validation workflows.

---

## 12. Enforcement Rules

The supported parser executor must reject:

- unregistered parsers;
- legacy parsers;
- disabled parsers;
- parsers without versions;
- parsers without declared schema profiles;
- parsers without provenance capability;
- parsers whose inputs fail integrity policy;
- parsers attempting prohibited source operations;
- parser output without coverage records.

---

## 13. Data Storage

A relational implementation is preferred for the MVP.

Do not introduce a graph database solely for provenance.

Use normal relational tables and constraints for:

- evidence objects;
- hash observations;
- lifecycle transitions;
- audit events;
- chain-of-custody events;
- provenance nodes;
- provenance edges;
- parser identities;
- parser executions;
- coverage summaries.

---

## 14. Security and Tenancy

Every service operation must carry tenant and case context.

Requirements:

- no cross-tenant evidence lookup;
- no cross-tenant provenance edge;
- no globally enumerable evidence source;
- authorization before sensitive operations;
- actor identity on lifecycle, custody, and audit events;
- non-sensitive failure details only.

---

## 15. Limitations

The integrity infrastructure provides application-level controls and records.

It does not, by itself, prove:

- physical write blocking;
- acquisition authenticity;
- identity of a human actor beyond the authenticated application context;
- absence of manipulation before intake;
- legal chain-of-custody sufficiency;
- cryptographic nonrepudiation;
- completeness of an Apple backup;
- correctness of an artifact parser.

Reports and UI must avoid overstating these controls.

---

## 16. Consequences

### Positive

- provenance is designed in rather than retrofitted;
- parsers become modular and testable;
- AI citations can resolve to source artifacts;
- support boundaries become enforceable;
- audit and legal-review workflows are easier to explain;
- future artifact families share one integrity foundation.

### Costs

- more models and services before artifact parsing;
- additional migrations and tests;
- more explicit failure handling;
- candidate parsers require conformance work.

These costs are accepted because retrofitting integrity after parser development would create larger forensic and commercial risk.
