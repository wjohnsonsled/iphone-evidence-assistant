"""Structured logging setup."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any

ALLOWED_FIELDS = frozenset(
    {
        "request_id",
        "correlation_id",
        "case_id",
        "job_id",
        "path",
        "status",
        "code",
        "error_count",
        "result",
    }
)
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(://[^:/@\s]+:)([^@\s]+)(@)"),
    re.compile(r"(?i)\b(password|token|api[_-]?key|secret)\s*[=:]\s*([^\s,;]+)"),
)


def redact(value: str) -> str:
    sanitized = value
    sanitized = SENSITIVE_PATTERNS[0].sub(r"\1[REDACTED]\3", sanitized)
    sanitized = SENSITIVE_PATTERNS[1].sub(r"\1=[REDACTED]", sanitized)
    return sanitized[:512]


class SafeJsonFormatter(logging.Formatter):
    """Format operational logs without serializing exception tracebacks."""

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "event", None) or "application_log"
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "event": redact(str(event)),
        }
        fields = getattr(record, "safe_fields", {})
        for key in sorted(fields):
            payload[key] = _safe_value(fields[key])
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact(str(value))


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **fields: Any,
) -> None:
    unknown = set(fields) - ALLOWED_FIELDS
    if unknown:
        raise ValueError("Unsupported structured log fields: " + ", ".join(sorted(unknown)))
    logger.log(level, event, extra={"event": event, "safe_fields": fields})


def configure_logging(level: str = "INFO") -> None:
    """Configure safe operational logs, not append-only audit records."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(SafeJsonFormatter())
    level_value = getattr(level, "value", level)
    logging.basicConfig(
        level=getattr(logging, str(level_value).upper(), logging.INFO),
        handlers=[handler],
        force=True,
    )
