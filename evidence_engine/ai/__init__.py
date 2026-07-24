"""AI grounding and deterministic question-answer preparation."""

from evidence_engine.ai.grounding import (
    answer_question,
    build_ai_prompt,
    build_case_knowledge,
    build_single_report_ai_prompt,
    write_ai_summary,
    write_case_knowledge,
)

__all__ = [
    "answer_question",
    "build_ai_prompt",
    "build_case_knowledge",
    "build_single_report_ai_prompt",
    "write_ai_summary",
    "write_case_knowledge",
]
