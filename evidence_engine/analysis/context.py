"""Time-window and conversation-context analysis."""

from evidence_engine._legacy import (
    build_conversation_context,
    events_near_times,
    map_conversations_by_message,
    parse_time_from_question,
    window_event_subset,
)

__all__ = [
    "build_conversation_context",
    "events_near_times",
    "map_conversations_by_message",
    "parse_time_from_question",
    "window_event_subset",
]
