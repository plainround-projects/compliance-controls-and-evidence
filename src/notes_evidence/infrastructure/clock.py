"""The system clock, behind the Clock port."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """The current time in UTC."""

    def now(self) -> datetime:
        """Now, timezone aware."""
        return datetime.now(UTC)
