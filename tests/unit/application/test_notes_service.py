import pytest

from notes_evidence.domain.audit import AuditAction
from notes_evidence.domain.errors import (
    InvalidCredentialsError,
    NotAllowedError,
    NotAuthenticatedError,
    NotFoundError,
    ValidationError,
)
from notes_evidence.domain.roles import Role
from tests.conftest import Rig


@pytest.fixture
def rig() -> Rig:
    rig = Rig()
    rig.add_user("ada", Role.ADMIN)
    rig.add_user("bruno", Role.MEMBER)
    rig.add_user("chen", Role.MEMBER)
    rig.add_user("dana", Role.READONLY)
    return rig


def actor(rig: Rig, name: str):
    return rig.service.authenticate(rig.service.login(name, "correct-horse-battery"))


def actions(rig: Rig):
    return [(e.action, e.username, e.outcome) for e in rig.audit.events]


def test_a_good_login_returns_a_token_and_is_recorded(rig):
    token = rig.service.login("bruno", "correct-horse-battery")
    assert rig.service.authenticate(token).username == "bruno"
    assert actions(rig)[0] == (AuditAction.LOGIN_OK, "bruno", "ok")


@pytest.mark.parametrize(
    ("name", "password"),
    [("bruno", "wrong-password-here"), ("nobody", "whatever-password"), ("BAD NAME", "x"), (None, "x")],
)
def test_a_failed_login_is_recorded_and_never_says_which_half_was_wrong(rig, name, password):
    with pytest.raises(InvalidCredentialsError, match="invalid username or password"):
        rig.service.login(name, password)
    assert rig.audit.events[-1].action is AuditAction.LOGIN_FAILED
    assert rig.audit.events[-1].outcome == "failed"


def test_a_failed_login_for_a_known_user_carries_the_user_id(rig):
    with pytest.raises(InvalidCredentialsError):
        rig.service.login("bruno", "wrong-password-here")
    assert rig.audit.events[-1].user_id == 2


def test_a_disabled_account_cannot_log_in_or_use_an_old_token(rig):
    token = rig.service.login("bruno", "correct-horse-battery")
    rig.users.deactivate("bruno")
    with pytest.raises(InvalidCredentialsError):
        rig.service.login("bruno", "correct-horse-battery")
    with pytest.raises(NotAuthenticatedError):
        rig.service.authenticate(token)


def test_a_forged_or_expired_token_is_refused(rig):
    with pytest.raises(NotAuthenticatedError):
        rig.service.authenticate("garbage")
    token = rig.service.login("bruno", "correct-horse-battery")
    rig.tokens.expired = True
    with pytest.raises(NotAuthenticatedError):
        rig.service.authenticate(token)
    rig.tokens.expired = False
    with pytest.raises(NotAuthenticatedError):
        rig.service.authenticate("token-99")


def test_a_member_creates_reads_updates_and_deletes_their_own_note(rig):
    bruno = actor(rig, "bruno")
    note = rig.service.create_note(bruno, " First ", "text")
    assert rig.service.get_note(bruno, note.id).title == "First"
    assert rig.service.update_note(bruno, note.id, "Second", "more").title == "Second"
    rig.service.delete_note(bruno, note.id)
    with pytest.raises(NotFoundError):
        rig.service.get_note(bruno, note.id)
    assert [a for a, *_ in actions(rig)][-5:] == [
        AuditAction.NOTE_CREATED,
        AuditAction.NOTE_READ,
        AuditAction.NOTE_UPDATED,
        AuditAction.NOTE_DELETED,
        AuditAction.ACCESS_DENIED,
    ]


def test_a_member_cannot_see_or_change_another_members_note_and_cannot_tell_it_exists(rig):
    note = rig.service.create_note(actor(rig, "chen"), "Private", "text")
    bruno = actor(rig, "bruno")
    for call in (
        lambda: rig.service.get_note(bruno, note.id),
        lambda: rig.service.update_note(bruno, note.id, "x", "y"),
        lambda: rig.service.delete_note(bruno, note.id),
    ):
        with pytest.raises(NotFoundError, match="note not found"):
            call()
    assert rig.notes.get(note.id) is not None
    assert [e.outcome for e in rig.audit.events if e.action is AuditAction.ACCESS_DENIED] == ["denied"] * 3


def test_listing_shows_own_notes_to_a_member_and_every_note_to_a_reader_and_an_admin(rig):
    rig.service.create_note(actor(rig, "bruno"), "a", "x")
    rig.service.create_note(actor(rig, "chen"), "b", "x")
    assert len(rig.service.list_notes(actor(rig, "bruno"))) == 1
    assert len(rig.service.list_notes(actor(rig, "dana"))) == 2
    assert len(rig.service.list_notes(actor(rig, "ada"))) == 2


def test_a_read_only_role_reads_everything_and_writes_nothing(rig):
    note = rig.service.create_note(actor(rig, "bruno"), "a", "x")
    dana = actor(rig, "dana")
    assert rig.service.get_note(dana, note.id).id == note.id
    with pytest.raises(NotAllowedError):
        rig.service.create_note(dana, "t", "b")
    with pytest.raises(NotAllowedError):
        rig.service.update_note(dana, note.id, "t", "b")
    with pytest.raises(NotAllowedError):
        rig.service.delete_note(dana, note.id)
    assert rig.notes.get(note.id).title == "a"


def test_an_admin_may_change_any_note(rig):
    note = rig.service.create_note(actor(rig, "bruno"), "a", "x")
    ada = actor(rig, "ada")
    assert rig.service.update_note(ada, note.id, "edited", "y").title == "edited"
    rig.service.delete_note(ada, note.id)
    assert rig.notes.get(note.id) is None


def test_invalid_input_is_refused_before_anything_is_stored(rig):
    bruno = actor(rig, "bruno")
    with pytest.raises(ValidationError):
        rig.service.create_note(bruno, "", "x")
    assert rig.notes.rows == {}
    note = rig.service.create_note(bruno, "ok", "x")
    with pytest.raises(ValidationError):
        rig.service.update_note(bruno, note.id, "t" * 500, "x")


def test_updating_a_missing_note_is_not_found(rig):
    with pytest.raises(NotFoundError):
        rig.service.update_note(actor(rig, "ada"), 999, "t", "b")


def test_only_an_admin_grants_roles_and_the_grant_is_recorded_with_its_target(rig):
    with pytest.raises(NotAllowedError):
        rig.service.grant_role(actor(rig, "bruno"), "chen", Role.ADMIN)
    granted = rig.service.grant_role(actor(rig, "ada"), "chen", Role.ADMIN)
    assert granted.role is Role.ADMIN
    event = rig.audit.events[-1]
    assert (event.action, event.username, event.detail) == (
        AuditAction.ROLE_GRANTED,
        "ada",
        {"role": "admin", "target": "chen"},
    )
    with pytest.raises(NotFoundError):
        rig.service.grant_role(actor(rig, "ada"), "nobody", Role.MEMBER)


def test_the_audit_trail_never_holds_note_text(rig):
    bruno = actor(rig, "bruno")
    note = rig.service.create_note(bruno, "Secret title", "Secret body text")
    rig.service.get_note(bruno, note.id)
    rig.service.update_note(bruno, note.id, "Other title", "Other body text")
    dump = " ".join(repr(e) for e in rig.audit.events)
    assert not any(text in dump for text in ("Secret", "Other title", "body text"))
