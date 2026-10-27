"""Users, notes and the validation of what a caller may send."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.errors import ValidationError
from notes_evidence.domain.roles import Role

USERNAME = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")
MIN_PASSWORD = 12
MAX_TITLE = 120
MAX_BODY = 10_000


@dataclass(frozen=True)
class User:
    """An account. The password hash lives in the repository, never on this value."""

    id: int
    username: str
    role: Role
    active: bool


@dataclass(frozen=True)
class Note:
    """A customer note. It holds personal data, so the audit log never holds its content."""

    id: int
    owner_id: int
    title: str
    body: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class NoteInput:
    """A validated title and body."""

    title: str
    body: str


def validate_username(value: object) -> str:
    """A lower-case name of 2 to 32 characters starting with a letter."""
    if not isinstance(value, str) or not USERNAME.match(value):
        raise ValidationError("username", "2 to 32 lower-case letters, digits, '_' or '-', starting with a letter")
    return value


def validate_password(value: object) -> str:
    """At least 12 characters."""
    if not isinstance(value, str) or len(value) < MIN_PASSWORD:
        raise ValidationError("password", f"at least {MIN_PASSWORD} characters")
    return value


def validate_note(title: object, body: object) -> NoteInput:
    """A non-empty title of at most 120 characters and a body of at most 10,000."""
    if not isinstance(title, str) or not title.strip() or len(title) > MAX_TITLE:
        raise ValidationError("title", f"1 to {MAX_TITLE} characters")
    if not isinstance(body, str) or len(body) > MAX_BODY:
        raise ValidationError("body", f"at most {MAX_BODY} characters")
    return NoteInput(title.strip(), body)
