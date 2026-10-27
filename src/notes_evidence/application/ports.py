"""What the use cases need from the outside world: ports, implemented by adapters in infrastructure."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from notes_evidence.domain.access import AccessEntry
from notes_evidence.domain.audit import AuditEvent
from notes_evidence.domain.changes import MergedChange
from notes_evidence.domain.controls import Control, Gap, RecordedException
from notes_evidence.domain.evidence import ManifestEntry
from notes_evidence.domain.notes import Note, User
from notes_evidence.domain.review import Person, ReviewRequest
from notes_evidence.domain.roles import Role
from notes_evidence.domain.scan import ScanReport


class Clock(Protocol):
    """The current time, injected so tests are deterministic."""

    def now(self) -> datetime:
        """The current moment, timezone aware."""
        ...


class UserRepository(Protocol):
    """Accounts and their password hashes."""

    def find_by_username(self, username: str) -> tuple[User, str] | None:
        """The user and the stored password hash, or None."""
        ...

    def find_by_id(self, user_id: int) -> User | None:
        """The user, or None."""
        ...

    def set_role(self, user_id: int, role: Role) -> None:
        """Change a user's role."""
        ...


class UserProvisioner(Protocol):
    """Creates accounts with a given password hash. Only an administrative connection holds this power."""

    def provision(self, username: str, role: Role, password_hash: str) -> User:
        """Create the user, or reset its role and password hash when it exists."""
        ...


class NoteRepository(Protocol):
    """Notes."""

    def add(self, owner_id: int, title: str, body: str, at: datetime) -> Note:
        """Store a new note."""
        ...

    def get(self, note_id: int) -> Note | None:
        """One note or None."""
        ...

    def list_for(self, owner_id: int | None) -> list[Note]:
        """One owner's notes, or every note when the owner is None."""
        ...

    def update(self, note_id: int, title: str, body: str, at: datetime) -> Note | None:
        """Replace a note's text; None when it does not exist."""
        ...

    def delete(self, note_id: int) -> bool:
        """Delete a note; False when it did not exist."""
        ...


class AuditLog(Protocol):
    """An append-only trail. There is deliberately no update and no delete."""

    def append(self, event: AuditEvent) -> None:
        """Record one event."""
        ...

    def since(self, moment: datetime) -> list[AuditEvent]:
        """Events at or after the moment, oldest first."""
        ...

    def latest(self, limit: int) -> list[AuditEvent]:
        """The most recent events, oldest first."""
        ...


class PasswordHasher(Protocol):
    """Slow, salted password hashing."""

    def hash(self, password: str) -> str:
        """A self-describing hash."""
        ...

    def verify(self, password: str, stored: str) -> bool:
        """Constant-time comparison."""
        ...


class TokenService(Protocol):
    """Signed, expiring session tokens."""

    def issue(self, user: User, now: datetime) -> str:
        """A token for the user."""
        ...

    def verify(self, token: str, now: datetime) -> int | None:
        """The user id the token names, or None when it is forged or expired."""
        ...


class RepositoryAccess(Protocol):
    """Who can reach the repository, as the hosting platform reports it."""

    def collaborators(self) -> list[AccessEntry]:
        """Collaborators and their permission."""
        ...


class DatabaseAccess(Protocol):
    """Who can reach the database, from its own catalog."""

    def roles(self) -> list[AccessEntry]:
        """Roles and their level."""
        ...


class CloudDirectory(Protocol):
    """The cloud account's users."""

    def users(self) -> list[AccessEntry]:
        """Users in the account."""
        ...

    def remove_user(self, name: str) -> None:
        """Delete one user."""
        ...


class ChangeSource(Protocol):
    """Merged pull requests with their reviews and deployments."""

    def merged_changes(self) -> list[MergedChange]:
        """Merged changes, any order."""
        ...


class BackupRunner(Protocol):
    """Take a backup and restore it into a scratch database."""

    def backup(self) -> datetime:
        """Take a backup and return the moment it was taken."""
        ...

    def restore_and_count(self, table: str) -> tuple[int, int]:
        """Restore into a scratch database; the rows of the table at backup time and after the restore."""
        ...


class ScanRunner(Protocol):
    """Run the dependency scan."""

    def scan(self) -> ScanReport:
        """Scan the locked dependencies."""
        ...


class EvidenceStore(Protocol):
    """The evidence folder and its manifest."""

    def write(self, name: str, text: str, control: str, produced_at: datetime, run_by: str, source: str) -> None:
        """Write a file and record it in the manifest."""
        ...

    def read(self, name: str) -> str | None:
        """A file's text, or None when it does not exist."""
        ...

    def read_all(self) -> dict[str, str]:
        """Every file in the folder."""
        ...

    def manifest(self) -> dict[str, ManifestEntry]:
        """The manifest entries by file name."""
        ...


class AlertSink(Protocol):
    """Where an alert message goes: a chat channel, a pager, a file."""

    def send(self, message: str) -> None:
        """Deliver one alert message."""
        ...


class ControlCatalog(Protocol):
    """The control matrix, the recorded exceptions, the tracked gaps, the people and the review's decisions."""

    def controls(self) -> list[Control]:
        """The controls and their evidence."""
        ...

    def exceptions(self) -> list[RecordedException]:
        """Known deviations."""
        ...

    def gaps(self) -> list[Gap]:
        """Tracked gaps."""
        ...

    def people(self) -> dict[str, Person]:
        """People who may hold access, by principal name."""
        ...

    def review_request(self) -> ReviewRequest:
        """The reviewer's decisions."""
        ...


class Notes(Protocol):
    """The slice of the notes service the alert test drives."""

    def login(self, username: str, password: str) -> str:
        """Return a token or raise InvalidCredentialsError."""
        ...
