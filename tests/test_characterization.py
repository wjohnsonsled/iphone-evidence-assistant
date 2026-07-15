"""Characterization tests for the refactored evidence engine package."""

from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from evidence_engine.ai import build_case_knowledge
from evidence_engine.analysis import (
    assess_finding_confidence,
    build_conversation_context,
    build_correlation_clusters,
    build_entity_correlations,
    relationship_edges,
)
from evidence_engine.analysis.confidence import apply_confidence
from evidence_engine.inventory import build_artifact_inventory
from evidence_engine.models import CaseContext, CoverageRecord, Event
from evidence_engine.parsers import LegacyArtifactParserAdapter, ParserResult
from evidence_engine.reports.assembly import write_markdown


def make_context(tmp_path: Path) -> CaseContext:
    """Create a reusable case context for deterministic fixture tests."""

    return CaseContext(
        tmp_path,
        datetime(2026, 6, 25, 16, 25),
        datetime(2026, 6, 25, 16, 58),
        context_minutes=5,
        conversation_context_count=1,
        correlation_window_minutes=3,
        min_correlation_score=1,
    )


def make_events() -> list[Event]:
    """Create a small normalized cross-artifact event fixture."""

    return [
        Event(
            datetime(2026, 6, 25, 16, 32),
            "sms",
            "message",
            "Message from +15551234567",
            "Incoming message: Are you there?",
            {
                "direction": "incoming",
                "contact": "+1 (555) 123-4567",
                "conversation_id": "chat-1",
                "message_id": "m1",
                "body": "Are you there?",
                "source_db": "sms.db",
            },
        ),
        Event(
            datetime(2026, 6, 25, 16, 33),
            "photos",
            "attachment",
            "Message attachment",
            "IMG_0001.JPG",
            {
                "filename": "IMG_0001.JPG",
                "attachment_guid": "a1",
                "message_id": "m1",
                "source_db": "sms.db",
            },
        ),
        Event(
            datetime(2026, 6, 25, 16, 51),
            "safari",
            "browser_history",
            "Visited example.com",
            "https://example.com/path",
            {"url": "https://example.com/path", "domain": "example.com", "source_db": "History.db"},
        ),
        Event(
            datetime(2026, 6, 25, 16, 52),
            "network_configuration",
            "network_domain",
            "Domain metadata",
            "example.com",
            {"domain": "example.com", "source_db": "network.plist"},
        ),
    ]


class CharacterizationTests(unittest.TestCase):
    def test_events_preserve_counts_timestamps_and_source_labels(self) -> None:
        events = make_events()
        apply_confidence(events)

        self.assertEqual(len(events), 4)
        self.assertEqual(events[0].timestamp, datetime(2026, 6, 25, 16, 32))
        self.assertEqual([event.source for event in events], ["sms", "photos", "safari", "network_configuration"])
        self.assertEqual(events[0].confidence_basis, "No confidence rule matched")
        self.assertGreater(events[1].confidence_score, 0)

    def test_correlation_coverage_confidence_and_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_context(Path(tmp))
            events = make_events()
            apply_confidence(events)
            ctx.coverage_records.append(
                CoverageRecord(
                    artifact_id="sms_messages",
                    artifact_name="SMS Messages",
                    category="communications",
                    relative_path="Library/SMS/sms.db",
                    parser_name="sms",
                    parser_enabled=True,
                    parser_status="parsed",
                    coverage_status="PRESENT_PARSED_WITH_RECORDS",
                    file_present=True,
                    database_opened=True,
                    schema_recognized=True,
                    records_normalized_total=1,
                    records_normalized_in_window=1,
                )
            )

            conversations = build_conversation_context(ctx, events)
            clusters = build_correlation_clusters(ctx, events)
            entity_correlations = build_entity_correlations(ctx, events)
            relationships = relationship_edges(events)
            confidence = assess_finding_confidence(ctx, ctx.coverage_records, [], events)

            self.assertIsInstance(conversations, list)
            self.assertGreaterEqual(len(clusters), 1)
            self.assertGreaterEqual(len(entity_correlations), 1)
            self.assertEqual(len(relationships), 0)
            self.assertIn(ctx.coverage_records[0].coverage_status, {"PRESENT_PARSED_WITH_RECORDS"})
            self.assertGreaterEqual(len(confidence), 1)
            self.assertIn(confidence[0].confidence_ceiling, {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT"})

    def test_report_headings_and_ai_package_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_context(Path(tmp))
            events = make_events()
            apply_confidence(events)
            inventory = build_artifact_inventory(ctx, events)
            clusters = build_correlation_clusters(ctx, events)
            entity_correlations = build_entity_correlations(ctx, events)
            edges = relationship_edges(events)
            knowledge = build_case_knowledge(ctx, events, clusters, ctx.coverage_records, [], [])
            report_path = Path(tmp) / "report.md"
            error_path = Path(tmp) / "errors.log"
            error_path.write_text("", encoding="utf-8")

            write_markdown(
                report_path,
                ctx,
                events,
                error_path,
                inventory,
                clusters,
                [],
                entity_correlations,
                [],
                [],
                {},
                ctx.coverage_records,
                [],
                [],
                None,
                edges,
                knowledge,
            )
            text = report_path.read_text(encoding="utf-8")

            for heading in [
                "## Time Window",
                "## Findings Summary",
                "## Artifact Inventory",
                "## Chronological Reconstruction",
            ]:
                self.assertIn(heading, text)
            self.assertIsInstance(inventory, list)
            for key in ["events", "entities", "relationships", "coverage_summary", "correlation_clusters"]:
                self.assertIn(key, knowledge)

    def test_parser_result_and_legacy_adapter_shape(self) -> None:
        class FakePlugin:
            name = "fake"

            def safe_collect(self, case_context: CaseContext) -> list[Event]:
                return make_events()[:1]

        with tempfile.TemporaryDirectory() as tmp:
            ctx = make_context(Path(tmp))
            result = LegacyArtifactParserAdapter(FakePlugin()).parse(ctx)  # type: ignore[arg-type]

        self.assertIsInstance(result, ParserResult)
        self.assertEqual(result.parser_name, "fake")
        self.assertEqual(len(result.events), 1)


if __name__ == "__main__":
    unittest.main()
