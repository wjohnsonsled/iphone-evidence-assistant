"""Coverage report section renderers."""

from evidence_engine._legacy import (
    write_acquisition_limitations_section,
    write_additional_evidence_recommendations_section,
    write_evidence_confidence_section,
    write_evidence_coverage_heat_map,
    write_evidence_coverage_score_section,
    write_evidence_coverage_section,
    write_evidence_not_collected_section,
    write_examination_gaps_section,
    write_forensic_blind_spots_section,
    write_supported_parser_coverage_section,
    write_unparsed_sources_section,
)

__all__ = [
    "write_acquisition_limitations_section",
    "write_additional_evidence_recommendations_section",
    "write_evidence_confidence_section",
    "write_evidence_coverage_heat_map",
    "write_evidence_coverage_score_section",
    "write_evidence_coverage_section",
    "write_evidence_not_collected_section",
    "write_examination_gaps_section",
    "write_forensic_blind_spots_section",
    "write_supported_parser_coverage_section",
    "write_unparsed_sources_section",
]
