import io
import json
import logging

import pytest

from app.core.config import LogLevel
from app.core.logging import SafeJsonFormatter, configure_logging, log_event, redact


def logger_and_stream():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(SafeJsonFormatter())
    logger = logging.getLogger("synthetic.structured")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    return logger, stream


def test_json_event_has_required_fields_and_sorted_metadata():
    logger, stream = logger_and_stream()
    log_event(
        logger,
        logging.WARNING,
        "synthetic_event",
        request_id="00000000-0000-0000-0000-000000000105",
        status=409,
        code="synthetic_conflict",
    )
    payload = json.loads(stream.getvalue())
    assert payload["event"] == "synthetic_event"
    assert payload["level"] == "WARNING"
    assert payload["logger"] == "synthetic.structured"
    assert payload["timestamp"].endswith("Z")
    assert payload["status"] == 409


def test_unknown_structured_field_fails_closed():
    logger, _ = logger_and_stream()
    with pytest.raises(ValueError, match="Unsupported"):
        log_event(logger, logging.INFO, "event", evidence_body="do not log")


@pytest.mark.parametrize(
    "value",
    [
        "postgresql://user:private-password@db/evidence",
        "password=private-password",
        "token:private-token",
        "api_key=private-key",
        "secret=private-secret",
    ],
)
def test_sensitive_values_are_redacted(value):
    rendered = redact(value)
    assert "private-" not in rendered
    assert "[REDACTED]" in rendered


def test_formatter_omits_exception_and_traceback_content():
    logger, stream = logger_and_stream()
    try:
        raise RuntimeError("private exception evidence content")
    except RuntimeError:
        logger.exception("safe_failure_event")
    rendered = stream.getvalue()
    assert "private exception evidence content" not in rendered
    assert "Traceback" not in rendered
    assert json.loads(rendered)["event"] == "application_log"


def test_configuration_accepts_typed_log_level():
    configure_logging(LogLevel.ERROR)
    assert logging.getLogger().level == logging.ERROR
