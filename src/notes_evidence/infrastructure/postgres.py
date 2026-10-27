"""PostgreSQL adapters: the notes service's repositories (as app_rw) and the catalog reader (as an administrator)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from notes_evidence.domain.access import DATABASE, AccessEntry
from notes_evidence.domain.audit import AuditAction, AuditEvent
from notes_evidence.domain.notes import Note, User
from notes_evidence.domain.roles import Role

CONNECT_ATTEMPTS = 5
DEFAULT_STATEMENT_TIMEOUT_MS = 30_000


class Database:
    """One long-lived connection per instance (one per worker process), reopened with backoff when it breaks.

    A connection per query would open thousands of short TCP connections in a collector run; a pool is the production
    answer for threaded servers, and gunicorn's synchronous workers need only this.
    """

    def __init__(
        self,
        url: str,
        sleep: Callable[[float], None] = time.sleep,
        statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
    ) -> None:
        self._url = url
        self._statement_timeout_ms = statement_timeout_ms
        self._sleep = sleep
        self._connection: psycopg.Connection[tuple[Any, ...]] | None = None
        self._lock = threading.RLock()

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection[tuple[Any, ...]]]:
        """The connection inside a transaction: committed on success, rolled back on any error."""
        with self._lock:
            connection = self._ensure()
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()

    def close(self) -> None:
        """Close the connection if it is open."""
        with self._lock:
            if self._connection is not None and not self._connection.closed:
                self._connection.close()
            self._connection = None

    def _ensure(self) -> psycopg.Connection[tuple[Any, ...]]:
        if self._connection is not None and not self._connection.closed and not self._connection.broken:
            return self._connection
        delay = 0.5
        for attempt in range(1, CONNECT_ATTEMPTS + 1):
            try:
                self._connection = psycopg.connect(
                    self._url, connect_timeout=5, options=f"-c statement_timeout={self._statement_timeout_ms}"
                )
                return self._connection
            except psycopg.OperationalError:
                if attempt == CONNECT_ATTEMPTS:
                    raise
                self._sleep(delay)
                delay *= 2
        raise AssertionError("unreachable")  # pragma: no cover

    def ping(self) -> bool:
        """True when a trivial query works."""
        try:
            with self.connection() as connection:
                connection.execute("SELECT 1")
        except psycopg.Error:
            return False
        return True


def _user(row: tuple[Any, ...]) -> User:
    return User(row[0], row[1], Role(row[2]), row[3])


def _note(row: tuple[Any, ...]) -> Note:
    return Note(row[0], row[1], row[2], row[3], row[4], row[5])


class PostgresUsers:
    """Users as the app reads them. The app role can read users and change roles; it cannot create users."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def find_by_username(self, username: str) -> tuple[User, str] | None:
        """The user and the stored hash, or None."""
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT id, username, role, active, password_hash FROM users WHERE username = %s", (username,)
            ).fetchone()
        return (_user(row), row[4]) if row else None

    def find_by_id(self, user_id: int) -> User | None:
        """The user or None."""
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT id, username, role, active FROM users WHERE id = %s", (user_id,)
            ).fetchone()
        return _user(row) if row else None

    def set_role(self, user_id: int, role: Role) -> None:
        """Change a role."""
        with self._db.connection() as connection:
            connection.execute("UPDATE users SET role = %s WHERE id = %s", (role.value, user_id))


class PostgresProvisioner:
    """Creates accounts. Used only with the administrative connection."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def provision(self, username: str, role: Role, password_hash: str) -> User:
        """Insert the user, or update its role and password hash when the name exists."""
        with self._db.connection() as connection:
            row = connection.execute(
                "INSERT INTO users (username, role, password_hash) VALUES (%s, %s, %s) "
                "ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role, "
                "password_hash = EXCLUDED.password_hash, active = TRUE "
                "RETURNING id, username, role, active",
                (username, role.value, password_hash),
            ).fetchone()
        assert row is not None
        return _user(row)


class PostgresNotes:
    """Notes."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def add(self, owner_id: int, title: str, body: str, at: datetime) -> Note:
        """Insert a note."""
        with self._db.connection() as connection:
            row = connection.execute(
                "INSERT INTO notes (owner_id, title, body, created_at, updated_at) VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, owner_id, title, body, created_at, updated_at",
                (owner_id, title, body, at, at),
            ).fetchone()
        assert row is not None
        return _note(row)

    def get(self, note_id: int) -> Note | None:
        """One note or None."""
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT id, owner_id, title, body, created_at, updated_at FROM notes WHERE id = %s", (note_id,)
            ).fetchone()
        return _note(row) if row else None

    def list_for(self, owner_id: int | None) -> list[Note]:
        """One owner's notes, or the newest 100 of everyone's."""
        with self._db.connection() as connection:
            if owner_id is None:
                rows = connection.execute(
                    "SELECT id, owner_id, title, body, created_at, updated_at FROM notes ORDER BY id DESC LIMIT 100"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT id, owner_id, title, body, created_at, updated_at FROM notes "
                    "WHERE owner_id = %s ORDER BY id DESC LIMIT 100",
                    (owner_id,),
                ).fetchall()
        return [_note(row) for row in rows]

    def update(self, note_id: int, title: str, body: str, at: datetime) -> Note | None:
        """Replace a note's text."""
        with self._db.connection() as connection:
            row = connection.execute(
                "UPDATE notes SET title = %s, body = %s, updated_at = %s WHERE id = %s "
                "RETURNING id, owner_id, title, body, created_at, updated_at",
                (title, body, at, note_id),
            ).fetchone()
        return _note(row) if row else None

    def delete(self, note_id: int) -> bool:
        """Delete a note."""
        with self._db.connection() as connection:
            return connection.execute("DELETE FROM notes WHERE id = %s", (note_id,)).rowcount > 0


class PostgresAuditLog:
    """The audit trail. The app role may only insert and select: the database refuses an update or a delete."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def append(self, event: AuditEvent) -> None:
        """Insert one event."""
        with self._db.connection() as connection:
            connection.execute(
                "INSERT INTO audit_log (ts, user_id, username, action, note_id, outcome, detail) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    event.at,
                    event.user_id,
                    event.username,
                    event.action.value,
                    event.note_id,
                    event.outcome,
                    Jsonb(event.detail),
                ),
            )

    def since(self, moment: datetime) -> list[AuditEvent]:
        """Events at or after the moment, oldest first."""
        with self._db.connection() as connection:
            rows = connection.execute(
                "SELECT ts, user_id, username, action, note_id, outcome, detail FROM audit_log "
                "WHERE ts >= %s ORDER BY ts, id",
                (moment,),
            ).fetchall()
        return [_event(row) for row in rows]

    def latest(self, limit: int) -> list[AuditEvent]:
        """The newest events, oldest first."""
        with self._db.connection() as connection:
            rows = connection.execute(
                "SELECT ts, user_id, username, action, note_id, outcome, detail FROM "
                "(SELECT * FROM audit_log ORDER BY id DESC LIMIT %s) AS newest ORDER BY id",
                (limit,),
            ).fetchall()
        return [_event(row) for row in rows]


def _event(row: tuple[Any, ...]) -> AuditEvent:
    at = row[0] if row[0].tzinfo else row[0].replace(tzinfo=UTC)
    return AuditEvent(at, row[1], row[2], AuditAction(row[3]), row[4], row[5], dict(row[6] or {}))


class PostgresRoles:
    """C1 for the database: the roles in the catalog, with their level. Names starting with pg_ are the server's own."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def roles(self) -> list[AccessEntry]:
        """Roles and their level: superuser, createdb or standard."""
        with self._db.connection() as connection:
            rows = connection.execute(
                "SELECT rolname, "
                "CASE WHEN rolsuper THEN 'superuser' WHEN rolcreatedb THEN 'createdb' ELSE 'standard' END "
                "FROM pg_roles WHERE rolname NOT LIKE 'pg\\_%' AND rolcanlogin ORDER BY 1"
            ).fetchall()
        return [AccessEntry(DATABASE, row[0], row[1]) for row in rows]
