"""Where alerts go in this build: the log stream and a file, the stand-in for a chat channel or a pager."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("notes.alerts")


class FileAlertSink:
    """Appends each alert message to a file and logs it at WARNING."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def send(self, message: str) -> None:
        """Deliver one alert."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(message + "\n")
        logger.warning("%s", message)
