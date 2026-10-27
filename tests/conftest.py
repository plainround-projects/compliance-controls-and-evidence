"""Shared fakes: a fixed clock and in-memory ports, so the domain and application are tested with no services."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from notes_evidence.application.notes_service import NotesService
from notes_evidence.domain.audit import AuditEvent
from notes_evidence.domain.evidence import ManifestEntry, digest
from notes_evidence.domain.notes import Note, User
from notes_evidence.domain.roles import Role

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 10, 22, 9, 0, 0, tzinfo=UTC)


class FixedClock:
    """A clock the test moves by hand."""

    def __init__(self, moment: datetime = T0) -> None:
        self.moment = moment

    def now(self) -> datetime:
        return self.moment

    def advance(self, **delta: float) -> None:
        self.moment += timedelta(**delta)


class MemoryUsers:
    """UserRepository and UserProvisioner in a dict."""

    def __init__(self) -> None:
        self.rows: dict[str, tuple[User, str]] = {}

    def provision(self, username: str, role: Role, password_hash: str) -> User:
        existing = self.rows.get(username)
        user = User(existing[0].id if existing else len(self.rows) + 1, username, role, True)
        self.rows[username] = (user, password_hash)
        return user

    def find_by_username(self, username: str) -> tuple[User, str] | None:
        return self.rows.get(username)

    def find_by_id(self, user_id: int) -> User | None:
        return next((user for user, _ in self.rows.values() if user.id == user_id), None)

    def set_role(self, user_id: int, role: Role) -> None:
        for name, (user, stored) in self.rows.items():
            if user.id == user_id:
                self.rows[name] = (replace(user, role=role), stored)

    def deactivate(self, username: str) -> None:
        user, stored = self.rows[username]
        self.rows[username] = (replace(user, active=False), stored)


class MemoryNotes:
    """NoteRepository in a dict."""

    def __init__(self) -> None:
        self.rows: dict[int, Note] = {}

    def add(self, owner_id: int, title: str, body: str, at: datetime) -> Note:
        note = Note(len(self.rows) + 1, owner_id, title, body, at, at)
        self.rows[note.id] = note
        return note

    def get(self, note_id: int) -> Note | None:
        return self.rows.get(note_id)

    def list_for(self, owner_id: int | None) -> list[Note]:
        return [n for n in self.rows.values() if owner_id is None or n.owner_id == owner_id]

    def update(self, note_id: int, title: str, body: str, at: datetime) -> Note | None:
        if note_id not in self.rows:
            return None
        self.rows[note_id] = replace(self.rows[note_id], title=title, body=body, updated_at=at)
        return self.rows[note_id]

    def delete(self, note_id: int) -> bool:
        return self.rows.pop(note_id, None) is not None


class MemoryAudit:
    """AuditLog in a list. Like the real one it has no update and no delete."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)

    def since(self, moment: datetime) -> list[AuditEvent]:
        return [e for e in self.events if e.at >= moment]

    def latest(self, limit: int) -> list[AuditEvent]:
        return self.events[-limit:]


class StubHasher:
    """Not a hash: lets tests read what was stored. The real scrypt hasher has its own tests."""

    def hash(self, password: str) -> str:
        return f"stub:{password}"

    def verify(self, password: str, stored: str) -> bool:
        return stored == f"stub:{password}"


class StubTokens:
    """Tokens that are just 'token-<id>', valid until a test expires them."""

    def __init__(self) -> None:
        self.expired = False

    def issue(self, user: User, now: datetime) -> str:
        return f"token-{user.id}"

    def verify(self, token: str, now: datetime) -> int | None:
        if self.expired or not token.startswith("token-") or not token[6:].isdigit():
            return None
        return int(token[6:])


class MemoryEvidenceStore:
    """EvidenceStore in dicts, with the same manifest behavior as the file-based one."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.entries: dict[str, ManifestEntry] = {}

    def write(self, name: str, text: str, control: str, produced_at: datetime, run_by: str, source: str) -> None:
        self.files[name] = text
        self.entries[name] = ManifestEntry(name, control, produced_at, run_by, source, digest(text))

    def read(self, name: str) -> str | None:
        return self.files.get(name)

    def read_all(self) -> dict[str, str]:
        return dict(self.files)

    def manifest(self) -> dict[str, ManifestEntry]:
        return dict(self.entries)


class Rig:
    """A service wired to in-memory ports."""

    def __init__(self) -> None:
        self.clock = FixedClock()
        self.users = MemoryUsers()
        self.notes = MemoryNotes()
        self.audit = MemoryAudit()
        self.tokens = StubTokens()
        self.hasher = StubHasher()
        self.service = NotesService(self.users, self.notes, self.audit, self.hasher, self.tokens, self.clock)

    def add_user(self, name: str, role: Role = Role.MEMBER, password: str = "correct-horse-battery") -> User:
        return self.users.provision(name, role, self.hasher.hash(password))
