"""C4: a backup is a hope until it is restored. The artifact records the restore and how long it took."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.audit import format_timestamp


@dataclass(frozen=True)
class RestoreResult:
    """A restore into a scratch database, with the row counts at both ends."""

    backup_taken_at: datetime
    started_at: datetime
    finished_at: datetime
    table: str
    source_rows: int
    restored_rows: int

    @property
    def seconds(self) -> int:
        """Whole seconds the restore took."""
        return int((self.finished_at - self.started_at).total_seconds())

    @property
    def verified(self) -> bool:
        """True when the restored table has as many rows as the source had at backup time."""
        return self.source_rows == self.restored_rows


def format_duration(seconds: int) -> str:
    """4 min 41 s, or 9 s under a minute."""
    minutes, rest = divmod(seconds, 60)
    return f"{minutes} min {rest} s" if minutes else f"{rest} s"


def render_restore(result: RestoreResult) -> str:
    """The artifact, in the three lines the lesson shows, plus a verdict line."""
    verdict = "verified" if result.verified else "MISMATCH"
    return (
        f"restore started {format_timestamp(result.started_at)} "
        f"from backup {format_timestamp(result.backup_taken_at)}\n"
        f"restore finished {format_timestamp(result.finished_at)} ({format_duration(result.seconds)})\n"
        f"check: {result.table} table has {result.restored_rows:,} rows; "
        f"source had {result.source_rows:,} rows at backup time\n"
        f"result: {verdict}\n"
    )
