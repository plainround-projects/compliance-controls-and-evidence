"""A scripted day of use, so the audit trail holds real events from real calls into the service."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass

from notes_evidence.application.notes_service import NotesService
from notes_evidence.application.ports import PasswordHasher, UserProvisioner
from notes_evidence.domain.errors import NotAllowedError, NotFoundError
from notes_evidence.domain.notes import User
from notes_evidence.domain.roles import Role

ROSTER = (("ada", Role.ADMIN), ("bruno", Role.MEMBER), ("chen", Role.MEMBER), ("dana", Role.READONLY))


@dataclass(frozen=True)
class ExerciseSummary:
    """What the scripted day did: how many notes were written, and how many requests the service refused."""

    users: dict[str, User]
    notes_created: int
    refusals: int


def exercise_service(
    provisioner: UserProvisioner,
    hasher: PasswordHasher,
    service: NotesService,
    new_password: Callable[[], str] = lambda: secrets.token_urlsafe(18),
) -> ExerciseSummary:
    """Create the four accounts with throwaway passwords that exist only in this process, then use the service as each.

    The passwords are generated here, hashed, and dropped when the function returns; none is stored or printed.
    """
    passwords = {name: new_password() for name, _ in ROSTER}
    for name, role in ROSTER:
        provisioner.provision(name, role, hasher.hash(passwords[name]))
    actors = {name: service.authenticate(service.login(name, passwords[name])) for name, _ in ROSTER}
    created = 0
    first = service.create_note(actors["bruno"], "Call back on Tuesday", "Customer asked for a quote.")
    second = service.create_note(actors["chen"], "Delivery address check", "Confirmed by phone.")
    service.create_note(actors["bruno"], "Renewal reminder", "Renewal is due next month.")
    created += 3
    service.get_note(actors["bruno"], first.id)
    service.update_note(actors["bruno"], first.id, "Call back on Wednesday", "Customer moved the call.")
    service.get_note(actors["dana"], second.id)
    refusals = _refused(lambda: service.get_note(actors["bruno"], second.id))  # a member cannot read another's note
    refusals += _refused(lambda: service.create_note(actors["dana"], "Not allowed", "No writing."))  # read-only role
    service.delete_note(actors["chen"], second.id)
    return ExerciseSummary(actors, created, refusals)


def _refused(call: Callable[[], object]) -> int:
    """1 when the service refuses the call, 0 when it goes through."""
    try:
        call()
    except (NotFoundError, NotAllowedError):
        return 1
    return 0
