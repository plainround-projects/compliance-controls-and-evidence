from datetime import timedelta

import pytest

from notes_evidence.domain.alerts import AlertRules, detect_alerts
from notes_evidence.domain.audit import AuditAction, AuditEvent, format_timestamp, render_line
from notes_evidence.domain.errors import ValidationError
from notes_evidence.domain.notes import validate_note, validate_password, validate_username
from notes_evidence.domain.roles import Permission, Role, allowed
from tests.conftest import T0


@pytest.mark.parametrize(
    ("role", "granted"),
    [
        (Role.ADMIN, set(Permission)),
        (Role.MEMBER, {Permission.READ_OWN, Permission.WRITE_OWN}),
        (Role.READONLY, {Permission.READ_OWN, Permission.READ_ANY}),
    ],
)
def test_each_role_holds_exactly_its_permissions(role, granted):
    assert {p for p in Permission if allowed(role, p)} == granted


def test_a_valid_username_and_password_pass_through():
    assert validate_username("ada") == "ada"
    assert validate_password("twelve chars!") == "twelve chars!"


@pytest.mark.parametrize("bad", ["", "A", "1abc", "has space", "x" * 40, None, 7])
def test_bad_usernames_are_rejected(bad):
    with pytest.raises(ValidationError):
        validate_username(bad)


@pytest.mark.parametrize("bad", ["short", "", None])
def test_short_passwords_are_rejected(bad):
    with pytest.raises(ValidationError):
        validate_password(bad)


def test_a_note_is_trimmed_and_validated():
    data = validate_note("  Title  ", "body")
    assert (data.title, data.body) == ("Title", "body")


@pytest.mark.parametrize(
    ("title", "body"), [("", "x"), ("   ", "x"), ("t" * 121, "x"), (5, "x"), ("t", "b" * 10_001), ("t", None)]
)
def test_bad_notes_are_rejected(title, body):
    with pytest.raises(ValidationError):
        validate_note(title, body)


def event(action, seconds=0, user="bruno", outcome="ok", **detail):
    return AuditEvent(T0 + timedelta(seconds=seconds), 1, user, action, None, outcome, detail)


def test_a_log_line_has_fixed_fields_and_no_content():
    line = render_line(AuditEvent(T0, 7, "ada", AuditAction.NOTE_READ, 12, "ok"))
    assert line == "2026-10-22T09:00:00Z user=ada id=7 action=note_read note=12 outcome=ok"
    assert render_line(AuditEvent(T0, None, "unknown", AuditAction.LOGIN_FAILED, None, "failed")).endswith(
        "note=- outcome=failed"
    )
    assert render_line(event(AuditAction.ROLE_GRANTED, role="admin", target="chen")).endswith(
        "outcome=ok role=admin target=chen"
    )
    assert format_timestamp(T0) == "2026-10-22T09:00:00Z"


def failed(seconds, user="bruno"):
    return event(AuditAction.LOGIN_FAILED, seconds, user, "failed")


def test_five_failed_logins_in_two_minutes_raise_one_alert():
    alerts = detect_alerts([failed(0), failed(10), failed(20), failed(30), failed(40)])
    assert len(alerts) == 1
    assert alerts[0].rule == "failed-logins"
    assert alerts[0].at == T0 + timedelta(seconds=40)
    assert (
        alerts[0].render()
        == "ALERT [failed-logins] 2026-10-22T09:00:40Z 5 failed logins for account bruno within 2 minutes"
    )


def test_four_failed_logins_raise_nothing():
    assert detect_alerts([failed(s) for s in (0, 10, 20, 30)]) == []


def test_failures_spread_beyond_the_window_raise_nothing():
    assert detect_alerts([failed(s) for s in (0, 40, 80, 120, 160, 200)]) == []


def test_each_account_is_counted_on_its_own():
    assert detect_alerts([failed(s, "bruno") for s in (0, 1, 2)] + [failed(s, "chen") for s in (3, 4)]) == []


def test_a_long_attack_raises_an_alert_per_burst_not_per_attempt():
    assert len(detect_alerts([failed(s) for s in range(0, 12)])) == 2


def test_the_rule_is_configurable():
    rules = AlertRules(failed_logins=2, window=timedelta(minutes=1))
    assert len(detect_alerts([failed(0), failed(30)], rules)) == 1


def test_an_admin_grant_raises_an_alert_and_a_member_grant_does_not():
    assert [
        a.rule for a in detect_alerts([event(AuditAction.ROLE_GRANTED, 0, "ada", role="admin", target="chen")])
    ] == ["admin-granted"]
    assert detect_alerts([event(AuditAction.ROLE_GRANTED, 0, "ada", role="member", target="chen")]) == []


def test_events_out_of_order_are_sorted_first():
    assert len(detect_alerts([failed(40), failed(0), failed(30), failed(10), failed(20)])) == 1
