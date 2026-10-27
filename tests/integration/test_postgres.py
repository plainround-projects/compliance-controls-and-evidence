from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from notes_evidence.application.notes_service import NotesService
from notes_evidence.domain.audit import AuditAction, AuditEvent
from notes_evidence.domain.errors import InvalidCredentialsError
from notes_evidence.domain.roles import Role
from notes_evidence.infrastructure.backup import DockerBackupRunner
from notes_evidence.infrastructure.clock import SystemClock
from notes_evidence.infrastructure.passwords import ScryptHasher
from notes_evidence.infrastructure.postgres import (
    Database,
    PostgresAuditLog,
    PostgresNotes,
    PostgresProvisioner,
    PostgresRoles,
    PostgresUsers,
)
from notes_evidence.infrastructure.tokens import HmacTokens
from notes_evidence.interfaces.http_app import create_app

pytestmark = pytest.mark.integration


def event(action=AuditAction.NOTE_READ, username="itest", **fields):
    return AuditEvent(datetime.now(UTC), None, username, action, None, "ok", fields)


def test_the_app_role_can_append_and_read_the_audit_log(app_db):
    log = PostgresAuditLog(app_db)
    marker = f"itest-{datetime.now(UTC).timestamp()}"
    log.append(event(username=marker, role="member"))
    found = [e for e in log.latest(50) if e.username == marker]
    assert len(found) == 1
    assert found[0].detail == {"role": "member"}
    assert found[0].at.tzinfo is not None


def test_the_app_role_cannot_update_or_delete_an_audit_row(app_db):
    PostgresAuditLog(app_db).append(event())
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_db.connection() as connection:
        connection.execute("UPDATE audit_log SET outcome = 'ok'")
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_db.connection() as connection:
        connection.execute("DELETE FROM audit_log")
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_db.connection() as connection:
        connection.execute("TRUNCATE audit_log")


def test_even_the_superuser_cannot_edit_or_truncate_the_audit_log(admin):
    PostgresAuditLog(admin).append(event())
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"), admin.connection() as connection:
        connection.execute("UPDATE audit_log SET outcome = 'ok'")
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"), admin.connection() as connection:
        connection.execute("TRUNCATE audit_log")


def test_a_row_younger_than_the_retention_period_cannot_be_deleted(admin):
    PostgresAuditLog(admin).append(event())
    with pytest.raises(psycopg.errors.RaiseException, match="kept for 365 days"), admin.connection() as connection:
        connection.execute("DELETE FROM audit_log WHERE id = (SELECT max(id) FROM audit_log)")


def test_the_retention_role_deletes_only_rows_past_the_retention_period(admin):
    old = datetime.now(UTC) - timedelta(days=400)
    marker = f"retention-{datetime.now(UTC).timestamp()}"
    with admin.connection() as connection:
        connection.execute(
            "INSERT INTO audit_log (ts, username, action, outcome) VALUES (%s, %s, 'note_read', 'ok')", (old, marker)
        )
    retention = Database(
        make_conninfo(
            os.environ["ADMIN_DATABASE_URL"], user="audit_retention", password=os.environ["RETENTION_PASSWORD"]
        )
    )
    with retention.connection() as connection:
        assert connection.execute("DELETE FROM audit_log WHERE username = %s", (marker,)).rowcount == 1
    with pytest.raises(psycopg.errors.RaiseException), retention.connection() as connection:
        connection.execute("DELETE FROM audit_log WHERE id = (SELECT max(id) FROM audit_log)")
    with pytest.raises(psycopg.errors.InsufficientPrivilege), retention.connection() as connection:
        connection.execute("UPDATE audit_log SET outcome = 'ok'")


def test_the_app_role_cannot_create_users_or_change_passwords_but_can_change_a_role(app_db, admin):
    PostgresProvisioner(admin).provision("itest-user", Role.MEMBER, "!")
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_db.connection() as connection:
        connection.execute("INSERT INTO users (username, role, password_hash) VALUES ('x-intruder', 'admin', '!')")
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_db.connection() as connection:
        connection.execute("UPDATE users SET password_hash = '!' WHERE username = 'itest-user'")
    users = PostgresUsers(app_db)
    found = users.find_by_username("itest-user")
    assert found is not None
    users.set_role(found[0].id, Role.READONLY)
    assert users.find_by_id(found[0].id).role is Role.READONLY  # type: ignore[union-attr]


def test_the_database_roles_list_shows_each_role_with_its_level(admin):
    levels = {entry.principal: entry.level for entry in PostgresRoles(admin).roles()}
    assert levels["app_rw"] == "standard"
    assert levels["audit_retention"] == "standard"
    assert levels["migrator"] == "createdb"
    assert "superuser" in levels.values()
    assert not any(name.startswith("pg_") for name in levels)


def test_notes_round_trip_through_postgres(app_db, admin):
    owner = PostgresProvisioner(admin).provision("itest-owner", Role.MEMBER, "!")
    notes, now = PostgresNotes(app_db), datetime.now(UTC)
    note = notes.add(owner.id, "Title", "Body", now)
    assert notes.get(note.id) == note
    assert note.id in [n.id for n in notes.list_for(owner.id)]
    assert note.id in [n.id for n in notes.list_for(None)]
    updated = notes.update(note.id, "New", "Text", now)
    assert updated is not None
    assert updated.title == "New"
    assert notes.delete(note.id)
    assert notes.get(note.id) is None
    assert not notes.delete(note.id)
    assert notes.update(note.id, "x", "y", now) is None


def test_the_service_and_the_http_app_work_against_postgres(app_db, admin, settings):
    hasher = ScryptHasher()
    PostgresProvisioner(admin).provision("itest-http", Role.MEMBER, hasher.hash("integration-password-1"))
    service = NotesService(
        PostgresUsers(app_db),
        PostgresNotes(app_db),
        PostgresAuditLog(app_db),
        hasher,
        HmacTokens(settings.secret, timedelta(minutes=5)),
        SystemClock(),
    )
    client = create_app(service, app_db.ping).test_client()
    assert client.get("/healthz").status_code == 200
    bad = client.post("/login", json={"username": "itest-http", "password": "wrong-password-1"})
    assert bad.status_code == 401
    token = client.post("/login", json={"username": "itest-http", "password": "integration-password-1"}).get_json()[
        "token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    note_id = client.post("/notes", json={"title": "Over HTTP", "body": "private text"}, headers=headers).get_json()[
        "id"
    ]
    assert client.get(f"/notes/{note_id}", headers=headers).get_json()["body"] == "private text"
    trail = PostgresAuditLog(app_db).latest(20)
    assert any(e.username == "itest-http" and e.action is AuditAction.LOGIN_FAILED for e in trail)
    assert not any("private text" in repr(e) for e in trail)
    with pytest.raises(InvalidCredentialsError):
        service.login("itest-http", "wrong-password-2")


def test_ping_is_false_and_connecting_retries_with_backoff_when_the_database_is_down():
    sleeps: list[float] = []
    database = Database("postgresql://nobody@127.0.0.1:1/none", sleep=sleeps.append)
    assert not database.ping()
    assert sleeps == [0.5, 1.0, 2.0, 4.0]


def test_a_real_backup_restores_into_a_scratch_database_with_the_same_row_count(settings):
    runner = DockerBackupRunner(settings.db_exec_prefix, settings.postgres_user, settings.postgres_db)
    runner.backup()
    source, restored = runner.restore_and_count("notes")
    assert source == restored
    assert source >= 12_400
