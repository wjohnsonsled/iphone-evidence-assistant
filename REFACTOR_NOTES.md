# Refactor Notes

## Refactoring Map

- Models and context:
  - `Event`, `NormalizedEvent` -> `evidence_engine.models.events`
  - `CoverageRecord`, `AppCoverageRecord`, `CoverageCategoryResult`, `FindingConfidenceResult`, `FindingCompletenessResult` -> `evidence_engine.models.coverage`
  - `CaseContext`, `ErrorLog`, `ReportConfig`, `SQLiteArtifact` -> `evidence_engine.models.context`
  - `Entity`, `Relationship`, `EntityRegistry` -> `evidence_engine.models.relationships`
- Shared utilities:
  - datetime, timestamp, formatting, JSON, path, hash, and phone helpers -> `evidence_engine.utils`
- Parsers:
  - parser protocol and `ParserResult` -> `evidence_engine.parsers.base`
  - plugin registry -> `evidence_engine.parsers.registry`
  - SMS, calls, Safari, photos, SQLite-backed apps, system/plist, and network parser classes -> `evidence_engine.parsers.*`
- Analysis:
  - conversation context and time-window helpers -> `evidence_engine.analysis.context`
  - correlation clusters, scored buckets, entity correlation, and relationship derivation -> `evidence_engine.analysis.correlation`
  - coverage scoring, confidence ceilings, blind spots, and evidence recommendations -> `evidence_engine.analysis.coverage`
  - event confidence -> `evidence_engine.analysis.confidence`
  - hypothesis assessment -> `evidence_engine.analysis.hypotheses`
- Inventory:
  - artifact inventory -> `evidence_engine.inventory.artifacts`
  - backup/file/SQLite/plist coverage audit and coverage outputs -> `evidence_engine.inventory.coverage`
- AI grounding:
  - evidence package construction, question answering, AI prompts, and guardrails -> `evidence_engine.ai.grounding`
- Reports:
  - report assembly and output writing -> `evidence_engine.reports.assembly`
  - section renderers -> `evidence_engine.reports.sections`
  - coverage sections -> `evidence_engine.reports.coverage`
  - HTML/PDF helpers -> `evidence_engine.reports.formats`
  - relationship graph outputs -> `evidence_engine.reports.relationships`
- CLI:
  - `build_arg_parser` and `main` -> `evidence_engine.cli`
  - root `window_investigator.py` is now a thin compatibility wrapper.

## Behavioral Changes

No intentional forensic behavior, wording, confidence, limitation, parser, AI
grounding, or report-output changes were made. The original implementation was
copied verbatim to `evidence_engine._legacy`, and the package modules currently
re-export or adapt that implementation.

The only interface addition is the reusable parser protocol:

- `ArtifactParser`
- `ParserResult`
- `LegacyArtifactParserAdapter`

## Known Technical Debt

- Most implementation code still lives in `evidence_engine._legacy`; the new
  modules provide stable import boundaries but do not yet physically move every
  function body.
- Parser modules expose the original plugin classes. A later pass should move
  each parser implementation into its module and leave compatibility imports in
  `_legacy` or a dedicated compatibility layer.
- Characterization tests use sanitized synthetic records. Real-case golden-file
  output comparisons should be added in a private test suite where evidence data
  can be stored safely.
- The original code uses broad dictionaries for several report and AI structures.
  Typed dictionaries or dataclasses would make the future FastAPI API contract
  clearer.

## Recommended Next Step for PostgreSQL Persistence

Add a persistence package such as `evidence_engine/storage/` with repository
interfaces for normalized events, entities, relationships, coverage records,
parser runs, and report runs. Keep the analysis functions pure: accept model
objects and return model objects or dictionaries, then persist at orchestration
boundaries. For PostgreSQL, start with tables keyed by case ID and acquisition
ID, store raw parser provenance separately from normalized event rows, and use
JSONB only for flexible metadata fields rather than core query fields such as
timestamp, source, event type, entity IDs, and relationship endpoints.
