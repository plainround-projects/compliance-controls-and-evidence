"""Structured JSON logs on standard output: level, time, logger, message and a few safe fields. No secrets."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

_SAFE_FIELDS = ("method", "path", "status", "user_id", "duration_ms")


class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a record; only the whitelisted extra fields are included."""
        document = {
            "time": datetime.fromtimestamp(record.created, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})
        return json.dumps(document)


def configure_logging(level: str) -> None:
    """Send JSON logs to stdout at the given level."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
