"""Artifact parser interface and parser implementations."""

from evidence_engine.parsers.base import ArtifactParser, LegacyArtifactParserAdapter, ParserResult
from evidence_engine.parsers.registry import plugins

__all__ = ["ArtifactParser", "LegacyArtifactParserAdapter", "ParserResult", "plugins"]
