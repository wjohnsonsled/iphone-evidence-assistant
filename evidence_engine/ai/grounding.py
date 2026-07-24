"""Evidence package construction and AI guardrail prompt preparation."""

from evidence_engine._legacy import (
    answer_question,
    build_ai_prompt,
    build_case_knowledge,
    build_single_report_ai_prompt,
    dedupe_event_refs,
    event_summary,
    write_ai_summary,
    write_case_knowledge,
)

__all__ = [
    "answer_question",
    "build_ai_prompt",
    "build_case_knowledge",
    "build_single_report_ai_prompt",
    "dedupe_event_refs",
    "event_summary",
    "write_ai_summary",
    "write_case_knowledge",
]
