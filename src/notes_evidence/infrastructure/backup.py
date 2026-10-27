"""C4: a pg_dump backup and a pg_restore into a scratch database, both run inside the database container."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from datetime import UTC, datetime

SCRATCH = "notes_restore_test"
Execute = Callable[[list[str], bytes | None], bytes]


class BackupError(RuntimeError):
    """pg_dump, pg_restore or psql failed."""


def run_in_container(argv: list[str], stdin: bytes | None) -> bytes:
    """Run a command, optionally feeding stdin, with a timeout; a non-zero exit is a BackupError."""
    try:
        done = subprocess.run(argv, input=stdin, capture_output=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as problem:
        raise BackupError(f"{argv[0]}: {problem}") from None
    if done.returncode != 0:
        raise BackupError(
            f"{' '.join(argv[:6])} exited {done.returncode}: {done.stderr.decode(errors='replace').strip()[:300]}"
        )
    return done.stdout


class DockerBackupRunner:
    """Backs up the database and restores it into `notes_restore_test`, then drops the scratch database."""

    def __init__(self, prefix: tuple[str, ...], user: str, database: str, execute: Execute = run_in_container) -> None:
        self._prefix = list(prefix)
        self._user = user
        self._database = database
        self._execute = execute
        self._dump: bytes = b""
        self._count_at_backup = 0

    def backup(self) -> datetime:
        """pg_dump in custom format; remember the row count at the same moment."""
        taken = datetime.now(UTC)
        self._count_at_backup = self._count(self._database, "notes")
        self._dump = self._execute(
            [*self._prefix, "pg_dump", "-U", self._user, "-d", self._database, "--format=custom"], None
        )
        return taken

    def restore_and_count(self, table: str) -> tuple[int, int]:
        """Restore the dump into a fresh scratch database and count the rows there."""
        self._psql("postgres", f"DROP DATABASE IF EXISTS {SCRATCH}")
        self._psql("postgres", f"CREATE DATABASE {SCRATCH}")
        try:
            self._execute(
                [*self._prefix, "pg_restore", "-U", self._user, "-d", SCRATCH, "--no-owner", "--no-privileges"],
                self._dump,
            )
            return self._count_at_backup, self._count(SCRATCH, table)
        finally:
            self._psql("postgres", f"DROP DATABASE IF EXISTS {SCRATCH}")

    def _psql(self, database: str, sql: str) -> str:
        out = self._execute(
            [*self._prefix, "psql", "-U", self._user, "-d", database, "-At", "-v", "ON_ERROR_STOP=1", "-c", sql], None
        )
        return out.decode().strip()

    def _count(self, database: str, table: str) -> int:
        if table != "notes":
            raise BackupError(f"unsupported table {table!r}")
        return int(self._psql(database, "SELECT count(*) FROM notes"))
