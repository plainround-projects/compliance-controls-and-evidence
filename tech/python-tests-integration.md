# The tests (integration)

## What it is

The pytest tests in `tests/integration`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/integration/conftest.py` | 17 lines. Integration tests need the PostgreSQL of docker-compose.yml (make up); they skip, saying why, without it. |
| `tests/integration/test_postgres.py` | 141 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/integration/conftest.py`

`tests/integration/conftest.py` lines 1 to 10:

```python
"""Integration tests need the PostgreSQL of docker-compose.yml (make up); they skip, saying why, without it."""

from __future__ import annotations

import os

import pytest

from notes_evidence.infrastructure.postgres import Database
from notes_evidence.infrastructure.settings import Settings, load_settings
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Integration tests need the PostgreSQL of docker-compose.yml (make up); they skip, saying why, without it.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `os`.
- It imports module `pytest`.
- From `notes_evidence.infrastructure.postgres` it takes `Database`.
- From `notes_evidence.infrastructure.settings` it takes `Settings, load_settings`.

`tests/integration/conftest.py` lines 13 to 17:

```python
@pytest.fixture(scope="session")
def settings() -> Settings:
    if not os.environ.get("DATABASE_URL") or not os.environ.get("ADMIN_DATABASE_URL"):
        pytest.skip("DATABASE_URL and ADMIN_DATABASE_URL are not set: run `make up` and use `make test-integration`")
    return load_settings(os.environ)
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Function `settings`.**

It gives back a `Settings`.

Decorators: `@pytest.fixture(scope='session')`.

Step by step:

- If not (`os.environ.get('DATABASE_URL')`) or not (`os.environ.get('ADMIN_DATABASE_URL')`):
  - Calls `pytest.skip('DATABASE_URL and ADMIN_DATABASE_URL are not set: run `make up` and use `make test-integration`')`.
- Gives back the result of calling `load_settings(os.environ)`.

`tests/integration/conftest.py` lines 20 to 22:

```python
@pytest.fixture(scope="session")
def admin(settings: Settings) -> Database:
    return Database(settings.admin_database_url)
```

**Function `admin`.**

It takes: `settings` (a `Settings`).

It gives back a `Database`.

Decorators: `@pytest.fixture(scope='session')`.

Step by step:

- Gives back the result of calling `Database(settings.admin_database_url)`.

`tests/integration/conftest.py` lines 25 to 27:

```python
@pytest.fixture(scope="session")
def app_db(settings: Settings) -> Database:
    return Database(settings.database_url)
```

**Function `app_db`.**

It takes: `settings` (a `Settings`).

It gives back a `Database`.

Decorators: `@pytest.fixture(scope='session')`.

Step by step:

- Gives back the result of calling `Database(settings.database_url)`.

### `tests/integration/test_postgres.py`

`tests/integration/test_postgres.py` lines 1 to 26:

```python
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
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `os`.
- From `datetime` it takes `UTC, datetime, timedelta`.
- It imports module `psycopg`.
- It imports module `pytest`.
- From `psycopg.conninfo` it takes `make_conninfo`.
- From `notes_evidence.application.notes_service` it takes `NotesService`.
- From `notes_evidence.domain.audit` it takes `AuditAction, AuditEvent`.
- From `notes_evidence.domain.errors` it takes `InvalidCredentialsError`.
- From `notes_evidence.domain.roles` it takes `Role`.
- From `notes_evidence.infrastructure.backup` it takes `DockerBackupRunner`.
- From `notes_evidence.infrastructure.clock` it takes `SystemClock`.
- From `notes_evidence.infrastructure.passwords` it takes `ScryptHasher`.
- From `notes_evidence.infrastructure.postgres` it takes `Database, PostgresAuditLog, PostgresNotes, PostgresProvisioner, PostgresRoles, PostgresUsers`.
- From `notes_evidence.infrastructure.tokens` it takes `HmacTokens`.
- From `notes_evidence.interfaces.http_app` it takes `create_app`.

`tests/integration/test_postgres.py` lines 28 to 28:

```python
pytestmark = pytest.mark.integration
```

These module-level lines:

- Stores `pytest.mark.integration` in `pytestmark`.

`tests/integration/test_postgres.py` lines 31 to 32:

```python
def event(action=AuditAction.NOTE_READ, username="itest", **fields):
    return AuditEvent(datetime.now(UTC), None, username, action, None, "ok", fields)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `event`.**

It takes: `action`, default `AuditAction.NOTE_READ`; `username`, default `'itest'`; `**fields` (any extra named values).

Step by step:

- Gives back the result of calling `AuditEvent(datetime.now(UTC), None, username, action, None, 'ok', fields)`.

`tests/integration/test_postgres.py` lines 35 to 42:

```python
def test_the_app_role_can_append_and_read_the_audit_log(app_db):
    log = PostgresAuditLog(app_db)
    marker = f"itest-{datetime.now(UTC).timestamp()}"
    log.append(event(username=marker, role="member"))
    found = [e for e in log.latest(50) if e.username == marker]
    assert len(found) == 1
    assert found[0].detail == {"role": "member"}
    assert found[0].at.tzinfo is not None
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_the_app_role_can_append_and_read_the_audit_log`** checks: the app role can append and read the audit log.

It takes: `app_db`.

Step by step:

- Stores the result of calling `PostgresAuditLog(app_db)` in `log`.
- Stores a text built with values filled in (`f'itest-{datetime.now(UTC).timestamp()}'`) in `marker`.
- Calls `log.append(event(username=marker, role='member'))`.
- Stores a new list made by a loop (`[e for e in log.latest(50) if e.username == marker]`) in `found`.
- Checks that `len(found)` equals `1`; if not, the test fails.
- Checks that `found[0].detail` equals `{'role': 'member'}`; if not, the test fails.
- Checks that `found[0].at.tzinfo` is not the same object as `None`; if not, the test fails.

`tests/integration/test_postgres.py` lines 45 to 52:

```python
def test_the_app_role_cannot_update_or_delete_an_audit_row(app_db):
    PostgresAuditLog(app_db).append(event())
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_db.connection() as connection:
        connection.execute("UPDATE audit_log SET outcome = 'ok'")
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_db.connection() as connection:
        connection.execute("DELETE FROM audit_log")
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_db.connection() as connection:
        connection.execute("TRUNCATE audit_log")
```

> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.

**Test `test_the_app_role_cannot_update_or_delete_an_audit_row`** checks: the app role cannot update or delete an audit row.

It takes: `app_db`.

Step by step:

- Calls `PostgresAuditLog(app_db).append(event())`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.InsufficientPrivilege)`; `app_db.connection()` (named `connection`):
  - Calls `connection.execute("UPDATE audit_log SET outcome = 'ok'")`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.InsufficientPrivilege)`; `app_db.connection()` (named `connection`):
  - Calls `connection.execute('DELETE FROM audit_log')`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.InsufficientPrivilege)`; `app_db.connection()` (named `connection`):
  - Calls `connection.execute('TRUNCATE audit_log')`.

`tests/integration/test_postgres.py` lines 55 to 60:

```python
def test_even_the_superuser_cannot_edit_or_truncate_the_audit_log(admin):
    PostgresAuditLog(admin).append(event())
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"), admin.connection() as connection:
        connection.execute("UPDATE audit_log SET outcome = 'ok'")
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"), admin.connection() as connection:
        connection.execute("TRUNCATE audit_log")
```

**Test `test_even_the_superuser_cannot_edit_or_truncate_the_audit_log`** checks: even the superuser cannot edit or truncate the audit log.

It takes: `admin`.

Step by step:

- Calls `PostgresAuditLog(admin).append(event())`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.RaiseException, match='append-only')`; `admin.connection()` (named `connection`):
  - Calls `connection.execute("UPDATE audit_log SET outcome = 'ok'")`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.RaiseException, match='append-only')`; `admin.connection()` (named `connection`):
  - Calls `connection.execute('TRUNCATE audit_log')`.

`tests/integration/test_postgres.py` lines 63 to 66:

```python
def test_a_row_younger_than_the_retention_period_cannot_be_deleted(admin):
    PostgresAuditLog(admin).append(event())
    with pytest.raises(psycopg.errors.RaiseException, match="kept for 365 days"), admin.connection() as connection:
        connection.execute("DELETE FROM audit_log WHERE id = (SELECT max(id) FROM audit_log)")
```

**Test `test_a_row_younger_than_the_retention_period_cannot_be_deleted`** checks: a row younger than the retention period cannot be deleted.

It takes: `admin`.

Step by step:

- Calls `PostgresAuditLog(admin).append(event())`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.RaiseException, match='kept for 365 days…`; `admin.connection()` (named `connection`):
  - Calls `connection.execute('DELETE FROM audit_log WHERE id = (SELECT max(id) FROM audit_log)')`.

`tests/integration/test_postgres.py` lines 69 to 86:

```python
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
```

> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Test `test_the_retention_role_deletes_only_rows_past_the_retention_period`** checks: the retention role deletes only rows past the retention period.

It takes: `admin`.

Step by step:

- Stores `datetime.now(UTC) - timedelta(days=400)` in `old`.
- Stores a text built with values filled in (`f'retention-{datetime.now(UTC).timestamp()}'`) in `marker`.
- Inside a `with` block that opens `admin.connection()` (named `connection`):
  - Calls `connection.execute("INSERT INTO audit_log (ts, username, action, outcome) VALUES (%s, %s, 'note_read', 'ok')"…`.
- Stores the result of calling `Database(make_conninfo(os.environ['ADMIN_DATABASE_URL'], user='audit_retention', password…` in `retention`.
- Inside a `with` block that opens `retention.connection()` (named `connection`):
  - Checks that `connection.execute('DELETE FROM audit_log WHERE u…` equals `1`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.RaiseException)`; `retention.connection()` (named `connection`):
  - Calls `connection.execute('DELETE FROM audit_log WHERE id = (SELECT max(id) FROM audit_log)')`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.InsufficientPrivilege)`; `retention.connection()` (named `connection`):
  - Calls `connection.execute("UPDATE audit_log SET outcome = 'ok'")`.

`tests/integration/test_postgres.py` lines 89 to 99:

```python
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
```

**Test `test_the_app_role_cannot_create_users_or_change_passwords_but_can_change_a_role`** checks: the app role cannot create users or change passwords but can change a role.

It takes: `app_db`; `admin`.

Step by step:

- Calls `PostgresProvisioner(admin).provision('itest-user', Role.MEMBER, '!')`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.InsufficientPrivilege)`; `app_db.connection()` (named `connection`):
  - Calls `connection.execute("INSERT INTO users (username, role, password_hash) VALUES ('x-intruder', 'admin', '!')")`.
- Expects the steps inside to raise the error in `pytest.raises(psycopg.errors.InsufficientPrivilege)`; `app_db.connection()` (named `connection`):
  - Calls `connection.execute("UPDATE users SET password_hash = '!' WHERE username = 'itest-user'")`.
- Stores the result of calling `PostgresUsers(app_db)` in `users`.
- Stores the result of calling `users.find_by_username('itest-user')` in `found`.
- Checks that `found` is not the same object as `None`; if not, the test fails.
- Calls `users.set_role(found[0].id, Role.READONLY)`.
- Checks that `users.find_by_id(found[0].id).role` is the same object as `Role.READONLY`; if not, the test fails.

`tests/integration/test_postgres.py` lines 102 to 108:

```python
def test_the_database_roles_list_shows_each_role_with_its_level(admin):
    levels = {entry.principal: entry.level for entry in PostgresRoles(admin).roles()}
    assert levels["app_rw"] == "standard"
    assert levels["audit_retention"] == "standard"
    assert levels["migrator"] == "createdb"
    assert "superuser" in levels.values()
    assert not any(name.startswith("pg_") for name in levels)
```

> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Test `test_the_database_roles_list_shows_each_role_with_its_level`** checks: the database roles list shows each role with its level.

It takes: `admin`.

Step by step:

- Stores a new dictionary made by a loop (`{entry.principal: entry.level for entry in PostgresRoles(admin).roles…`) in `levels`.
- Checks that `levels['app_rw']` equals `'standard'`; if not, the test fails.
- Checks that `levels['audit_retention']` equals `'standard'`; if not, the test fails.
- Checks that `levels['migrator']` equals `'createdb'`; if not, the test fails.
- Checks that `'superuser'` is in `levels.values()`; if not, the test fails.
- Checks that not (`any((name.startswith('pg_') for name in levels))`); if not, the test fails.

`tests/integration/test_postgres.py` lines 111 to 124:

```python
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
```

**Test `test_notes_round_trip_through_postgres`** checks: notes round trip through postgres.

It takes: `app_db`; `admin`.

Step by step:

- Stores the result of calling `PostgresProvisioner(admin).provision('itest-owner', Role.MEMBER, '!')` in `owner`.
- Unpacks the tuple `(PostgresNotes(app_db), datetime.now(UTC))` into `(notes, now)`.
- Stores the result of calling `notes.add(owner.id, 'Title', 'Body', now)` in `note`.
- Checks that `notes.get(note.id)` equals `note`; if not, the test fails.
- Checks that `note.id` is in `[n.id for n in notes.list_for(owner.id)]`; if not, the test fails.
- Checks that `note.id` is in `[n.id for n in notes.list_for(None)]`; if not, the test fails.
- Stores the result of calling `notes.update(note.id, 'New', 'Text', now)` in `updated`.
- Checks that `updated` is not the same object as `None`; if not, the test fails.
- Checks that `updated.title` equals `'New'`; if not, the test fails.
- Checks that `notes.delete(note.id)`; if not, the test fails.
- Checks that `notes.get(note.id)` is the same object as `None`; if not, the test fails.
- Checks that not (`notes.delete(note.id)`); if not, the test fails.
- Checks that `notes.update(note.id, 'x', 'y', now)` is the same object as `None`; if not, the test fails.

`tests/integration/test_postgres.py` lines 127 to 154:

```python
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
```

**Test `test_the_service_and_the_http_app_work_against_postgres`** checks: the service and the http app work against postgres.

It takes: `app_db`; `admin`; `settings`.

Step by step:

- Stores the result of calling `ScryptHasher()` in `hasher`.
- Calls `PostgresProvisioner(admin).provision('itest-http', Role.MEMBER, hasher.hash('integration-password-1'))`.
- Stores the result of calling `NotesService(PostgresUsers(app_db), PostgresNotes(app_db), PostgresAuditLog(app_db), hash…` in `service`.
- Stores the result of calling `create_app(service, app_db.ping).test_client()` in `client`.
- Checks that `client.get('/healthz').status_code` equals `200`; if not, the test fails.
- Stores the result of calling `client.post('/login', json={'username': 'itest-http', 'password': 'wrong-password-1'})` in `bad`.
- Checks that `bad.status_code` equals `401`; if not, the test fails.
- Stores `client.post('/login', json={'username': 'itest-http', 'password': 'integration-…` in `token`.
- Stores the dictionary `{'Authorization': f'Bearer {token}'}` in `headers`.
- Stores `client.post('/notes', json={'title': 'Over HTTP', 'body': 'private text'}, head…` in `note_id`.
- Checks that `client.get(f'/notes/{note_id}', headers=headers).…` equals `'private text'`; if not, the test fails.
- Stores the result of calling `PostgresAuditLog(app_db).latest(20)` in `trail`.
- Checks that `any((e.username == 'itest-http' and e.action is AuditAction.LOGIN_FAI…`; if not, the test fails.
- Checks that not (`any(('private text' in repr(e) for e in trail))`); if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(InvalidCredentialsError)`:
  - Calls `service.login('itest-http', 'wrong-password-2')`.

`tests/integration/test_postgres.py` lines 157 to 161:

```python
def test_ping_is_false_and_connecting_retries_with_backoff_when_the_database_is_down():
    sleeps: list[float] = []
    database = Database("postgresql://nobody@127.0.0.1:1/none", sleep=sleeps.append)
    assert not database.ping()
    assert sleeps == [0.5, 1.0, 2.0, 4.0]
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.

**Test `test_ping_is_false_and_connecting_retries_with_backoff_when_the_database_is_down`** checks: ping is false and connecting retries with backoff when the database is down.

Step by step:

- Declares `sleeps` as a `list[float]` and stores the list `[]` in it.
- Stores the result of calling `Database('postgresql://nobody@127.0.0.1:1/none', sleep=sleeps.append)` in `database`.
- Checks that not (`database.ping()`); if not, the test fails.
- Checks that `sleeps` equals `[0.5, 1.0, 2.0, 4.0]`; if not, the test fails.

`tests/integration/test_postgres.py` lines 164 to 169:

```python
def test_a_real_backup_restores_into_a_scratch_database_with_the_same_row_count(settings):
    runner = DockerBackupRunner(settings.db_exec_prefix, settings.postgres_user, settings.postgres_db)
    runner.backup()
    source, restored = runner.restore_and_count("notes")
    assert source == restored
    assert source >= 12_400
```

**Test `test_a_real_backup_restores_into_a_scratch_database_with_the_same_row_count`** checks: a real backup restores into a scratch database with the same row count.

It takes: `settings`.

Step by step:

- Stores the result of calling `DockerBackupRunner(settings.db_exec_prefix, settings.postgres_user, settings.postgres_db)` in `runner`.
- Calls `runner.backup()`.
- Unpacks the result of calling `runner.restore_and_count('notes')` into `(source, restored)`.
- Checks that `source` equals `restored`; if not, the test fails.
- Checks that `source` is at least `12400`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/integration
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check tests/integration/conftest.py tests/integration/test_postgres.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_the_app_role_can_append_and_read_the_audit_log` check?
   **Answer:** it checks: the app role can append and read the audit log.
2. What does the test `test_the_app_role_cannot_update_or_delete_an_audit_row` check?
   **Answer:** it checks: the app role cannot update or delete an audit row.
3. What does the test `test_even_the_superuser_cannot_edit_or_truncate_the_audit_log` check?
   **Answer:** it checks: even the superuser cannot edit or truncate the audit log.
4. What does the test `test_a_row_younger_than_the_retention_period_cannot_be_deleted` check?
   **Answer:** it checks: a row younger than the retention period cannot be deleted.
5. What does the test `test_the_retention_role_deletes_only_rows_past_the_retention_period` check?
   **Answer:** it checks: the retention role deletes only rows past the retention period.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
