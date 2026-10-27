"""The audit event: who did what, to which note, when, with what outcome. Never the note's content."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class AuditAction(Enum):
    """Every action the service records."""

    LOGIN_OK = "login_ok"
    LOGIN_FAILED = "login_failed"
    NOTE_CREATED = "note_created"
    NOTE_READ = "note_read"
    NOTE_UPDATED = "note_updated"
    NOTE_DELETED = "note_deleted"
    ROLE_GRANTED = "role_granted"
    ACCESS_DENIED = "access_denied"


@dataclass(frozen=True)
class AuditEvent:
    """One line of the audit trail. `detail` holds short facts such as the role granted, never a caller's free text."""

    at: datetime
    user_id: int | None
    username: str
    action: AuditAction
    note_id: int | None
    outcome: str
    detail: dict[str, str] = field(default_factory=dict)


def format_timestamp(moment: datetime) -> str:
    """UTC, to the second, with a trailing Z: 2026-10-22T09:12:03Z."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def render_line(event: AuditEvent) -> str:
    """The log line: timestamp, user, action, note, outcome. Fixed fields, so no caller text can inject a line."""
    user = f"{event.user_id}" if event.user_id is not None else "-"
    note = f"{event.note_id}" if event.note_id is not None else "-"
    extra = "".join(f" {key}={value}" for key, value in sorted(event.detail.items()))
    return (
        f"{format_timestamp(event.at)} user={event.username} id={user} action={event.action.value} "
        f"note={note} outcome={event.outcome}{extra}"
    )
