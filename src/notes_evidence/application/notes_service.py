"""The notes service: every use case checks the role, then records what happened."""

from __future__ import annotations

from notes_evidence.application.ports import (
    AuditLog,
    Clock,
    NoteRepository,
    PasswordHasher,
    TokenService,
    UserRepository,
)
from notes_evidence.domain.audit import AuditAction, AuditEvent
from notes_evidence.domain.errors import InvalidCredentialsError, NotAllowedError, NotAuthenticatedError, NotFoundError
from notes_evidence.domain.notes import USERNAME, Note, User, validate_note, validate_username
from notes_evidence.domain.roles import Permission, Role, allowed

_UNKNOWN = "unknown"


class NotesService:
    """Logins, notes and role grants for the notes API. The audit trail holds who and what, never the note's text."""

    def __init__(
        self,
        users: UserRepository,
        notes: NoteRepository,
        audit: AuditLog,
        hasher: PasswordHasher,
        tokens: TokenService,
        clock: Clock,
    ) -> None:
        self._users = users
        self._notes = notes
        self._audit = audit
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock

    def login(self, username: str, password: str) -> str:
        """A token for a valid username and password. A failure is recorded and never says which half was wrong."""
        name = username if isinstance(username, str) and USERNAME.match(username) else _UNKNOWN
        found = self._users.find_by_username(name) if name != _UNKNOWN else None
        if found is None or not found[0].active or not self._hasher.verify(password, found[1]):
            self._record(found[0] if found else None, name, AuditAction.LOGIN_FAILED, None, "failed")
            raise InvalidCredentialsError("invalid username or password")
        user = found[0]
        self._record(user, user.username, AuditAction.LOGIN_OK, None, "ok")
        return self._tokens.issue(user, self._clock.now())

    def authenticate(self, token: str) -> User:
        """The active user a token names; NotAuthenticatedError for a forged or expired token or a disabled account."""
        user_id = self._tokens.verify(token, self._clock.now())
        user = self._users.find_by_id(user_id) if user_id is not None else None
        if user is None or not user.active:
            raise NotAuthenticatedError("invalid or expired token")
        return user

    def create_note(self, actor: User, title: object, body: object) -> Note:
        """Store a note owned by the actor."""
        self._require(actor, Permission.WRITE_OWN, None)
        data = validate_note(title, body)
        note = self._notes.add(actor.id, data.title, data.body, self._clock.now())
        self._record(actor, actor.username, AuditAction.NOTE_CREATED, note.id, "ok")
        return note

    def get_note(self, actor: User, note_id: int) -> Note:
        """A note the actor may read. A note that belongs to someone else reads as not found to a member."""
        note = self._visible(actor, note_id, Permission.READ_ANY)
        self._record(actor, actor.username, AuditAction.NOTE_READ, note.id, "ok")
        return note

    def list_notes(self, actor: User) -> list[Note]:
        """Every note for a role that may read any, otherwise the actor's own."""
        owner = None if allowed(actor.role, Permission.READ_ANY) else actor.id
        return self._notes.list_for(owner)

    def update_note(self, actor: User, note_id: int, title: object, body: object) -> Note:
        """Replace a note the actor may write."""
        self._require(actor, Permission.WRITE_OWN, note_id)
        data = validate_note(title, body)
        self._visible(actor, note_id, Permission.WRITE_ANY)
        note = self._notes.update(note_id, data.title, data.body, self._clock.now())
        if note is None:
            raise NotFoundError("note not found")
        self._record(actor, actor.username, AuditAction.NOTE_UPDATED, note.id, "ok")
        return note

    def delete_note(self, actor: User, note_id: int) -> None:
        """Delete a note the actor may write."""
        self._require(actor, Permission.WRITE_OWN, note_id)
        self._visible(actor, note_id, Permission.WRITE_ANY)
        self._notes.delete(note_id)
        self._record(actor, actor.username, AuditAction.NOTE_DELETED, note_id, "ok")

    def grant_role(self, actor: User, target_username: str, role: Role) -> User:
        """Change another user's role; an admin grant is what the alert watches for."""
        self._require(actor, Permission.GRANT_ROLE, None)
        found = self._users.find_by_username(validate_username(target_username))
        if found is None:
            raise NotFoundError("user not found")
        self._users.set_role(found[0].id, role)
        self._audit.append(
            AuditEvent(
                self._clock.now(),
                actor.id,
                actor.username,
                AuditAction.ROLE_GRANTED,
                None,
                "ok",
                {"role": role.value, "target": found[0].username},
            )
        )
        return User(found[0].id, found[0].username, role, found[0].active)

    def _visible(self, actor: User, note_id: int, override: Permission) -> Note:
        note = self._notes.get(note_id)
        if note is None or (note.owner_id != actor.id and not allowed(actor.role, override)):
            self._record(actor, actor.username, AuditAction.ACCESS_DENIED, note_id, "denied")
            raise NotFoundError("note not found")
        return note

    def _require(self, actor: User, permission: Permission, note_id: int | None) -> None:
        if not allowed(actor.role, permission):
            self._record(actor, actor.username, AuditAction.ACCESS_DENIED, note_id, "denied")
            raise NotAllowedError(f"role {actor.role.value} may not do this")

    def _record(self, user: User | None, username: str, action: AuditAction, note_id: int | None, outcome: str) -> None:
        self._audit.append(AuditEvent(self._clock.now(), user.id if user else None, username, action, note_id, outcome))
