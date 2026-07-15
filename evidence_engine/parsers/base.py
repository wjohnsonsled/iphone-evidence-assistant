"""Shared parser protocol used by package callers and future web APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from evidence_engine._legacy import ArtifactPlugin
from evidence_engine.models import AppCoverageRecord, CaseContext, CoverageRecord, Event


@dataclass
class ParserResult:
    """Normalized result returned by an artifact parser."""

    events: list[Event] = field(default_factory=list)
    coverage_records: list[CoverageRecord] = field(default_factory=list)
    app_coverage_records: list[AppCoverageRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    parsed_source_paths: list[Path] = field(default_factory=list)
    parser_name: str = ""
    parser_version: str = "legacy"


class ArtifactParser(Protocol):
    """Protocol implemented by reusable artifact parsers."""

    name: str
    version: str

    def supports(self, case_context: CaseContext) -> bool:
        """Return whether this parser can inspect the supplied case context."""

    def parse(self, case_context: CaseContext) -> ParserResult:
        """Parse artifacts and return normalized events plus coverage metadata."""


class LegacyArtifactParserAdapter:
    """Adapter exposing an existing ``ArtifactPlugin`` through ``ArtifactParser``."""

    version = "legacy"

    def __init__(self, plugin: ArtifactPlugin) -> None:
        self.plugin = plugin
        self.name = plugin.name

    def supports(self, case_context: CaseContext) -> bool:
        """Return true for legacy plugins; safe collection handles missing artifacts."""

        return True

    def parse(self, case_context: CaseContext) -> ParserResult:
        """Run the legacy plugin and capture the normalized parser result."""

        errors_before = len(case_context.errors.records)
        coverage_before = len(case_context.coverage_records)
        app_coverage_before = len(case_context.app_coverage_records)
        events = self.plugin.safe_collect(case_context)
        new_errors = [
            record.get("message", str(record))
            for record in case_context.errors.records[errors_before:]
        ]
        return ParserResult(
            events=events,
            coverage_records=case_context.coverage_records[coverage_before:],
            app_coverage_records=case_context.app_coverage_records[app_coverage_before:],
            errors=new_errors,
            parser_name=self.name,
            parser_version=self.version,
        )


__all__ = ["ArtifactParser", "LegacyArtifactParserAdapter", "ParserResult"]
