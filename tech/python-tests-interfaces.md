# The tests (interfaces)

## What it is

The pytest tests in `tests/unit/interfaces`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/interfaces/test_cli.py` | 34 lines.  |
| `tests/unit/interfaces/test_http_app.py` | 87 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/unit/interfaces/test_cli.py`

`tests/unit/interfaces/test_cli.py` lines 1 to 3:

```python
import pytest

from notes_evidence.interfaces.cli import build_parser, main
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `pytest`.
- From `notes_evidence.interfaces.cli` it takes `build_parser, main`.

`tests/unit/interfaces/test_cli.py` lines 6 to 22:

```python
def test_the_parser_knows_every_step():
    names = build_parser().parse_args(["collect"]).command
    assert names == "collect"
    for step in (
        "exercise",
        "alert-test",
        "log-sample",
        "access",
        "changes",
        "restore-test",
        "scan",
        "review",
        "index",
        "verify",
        "report",
    ):
        assert build_parser().parse_args([step]).command == step
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_the_parser_knows_every_step`** checks: the parser knows every step.

Step by step:

- Stores `build_parser().parse_args(['collect']).command` in `names`.
- Checks that `names` equals `'collect'`; if not, the test fails.
- For each `step` in the tuple `('exercise', 'alert-test', 'log-sample', 'access', 'changes', 'restor…`:
  - Checks that `build_parser().parse_args([step]).command` equals `step`; if not, the test fails.

`tests/unit/interfaces/test_cli.py` lines 25 to 28:

```python
def test_an_unknown_command_is_a_usage_error():
    with pytest.raises(SystemExit) as stop:
        build_parser().parse_args(["delete-everything"])
    assert stop.value.code == 2
```

> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.

**Test `test_an_unknown_command_is_a_usage_error`** checks: an unknown command is a usage error.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(SystemExit)` (named `stop`):
  - Calls `build_parser().parse_args(['delete-everything'])`.
- Checks that `stop.value.code` equals `2`; if not, the test fails.

`tests/unit/interfaces/test_cli.py` lines 31 to 34:

```python
def test_missing_settings_exit_2(monkeypatch, capsys):
    monkeypatch.delenv("NOTES_SECRET", raising=False)
    assert main(["verify"]) == 2
    assert "NOTES_SECRET is required" in capsys.readouterr().err
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `monkeypatch` is a built-in pytest fixture that changes something (an environment variable, an attribute) for this test only and undoes it afterwards.
> **In plain words.** `capsys` is a built-in pytest fixture that captures what the program prints, so the test can read it with `capsys.readouterr()`.

**Test `test_missing_settings_exit_2`** checks: missing settings exit 2.

It takes: `monkeypatch`; `capsys`.

Step by step:

- Calls `monkeypatch.delenv('NOTES_SECRET', raising=False)`.
- Checks that `main(['verify'])` equals `2`; if not, the test fails.
- Checks that `'NOTES_SECRET is required'` is in `capsys.readouterr().err`; if not, the test fails.

`tests/unit/interfaces/test_cli.py` lines 37 to 43:

```python
def test_a_missing_controls_file_exits_2(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("NOTES_SECRET", "s" * 32)
    monkeypatch.setenv("CONTROLS_FILE", str(tmp_path / "controls.toml"))
    monkeypatch.setenv("EVIDENCE_DIR", str(tmp_path / "evidence"))
    assert main(["verify"]) == 2
    assert "does not exist" in capsys.readouterr().err
```

> **In plain words.** `tmp_path` is a built-in pytest fixture: a fresh, empty temporary folder (a `Path`) that is removed after the test.

**Test `test_a_missing_controls_file_exits_2`** checks: a missing controls file exits 2.

It takes: `monkeypatch`; `tmp_path`; `capsys`.

Step by step:

- Calls `monkeypatch.setenv('DATABASE_URL', 'postgresql://x')`.
- Calls `monkeypatch.setenv('NOTES_SECRET', 's' * 32)`.
- Calls `monkeypatch.setenv('CONTROLS_FILE', str(tmp_path / 'controls.toml'))`.
- Calls `monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path / 'evidence'))`.
- Checks that `main(['verify'])` equals `2`; if not, the test fails.
- Checks that `'does not exist'` is in `capsys.readouterr().err`; if not, the test fails.

### `tests/unit/interfaces/test_http_app.py`

`tests/unit/interfaces/test_http_app.py` lines 1 to 5:

```python
import pytest

from notes_evidence.domain.roles import Role
from notes_evidence.interfaces.http_app import create_app
from tests.conftest import Rig
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `pytest`.
- From `notes_evidence.domain.roles` it takes `Role`.
- From `notes_evidence.interfaces.http_app` it takes `create_app`.
- From `tests.conftest` it takes `Rig`.

`tests/unit/interfaces/test_http_app.py` lines 8 to 14:

```python
@pytest.fixture
def rig() -> Rig:
    rig = Rig()
    rig.add_user("ada", Role.ADMIN, "admin-password-1")
    rig.add_user("bruno", Role.MEMBER, "member-password-1")
    rig.add_user("chen", Role.MEMBER, "member-password-2")
    return rig
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `rig`.**

It gives back a `Rig`.

Decorators: `@pytest.fixture`.

Step by step:

- Stores the result of calling `Rig()` in `rig`.
- Calls `rig.add_user('ada', Role.ADMIN, 'admin-password-1')`.
- Calls `rig.add_user('bruno', Role.MEMBER, 'member-password-1')`.
- Calls `rig.add_user('chen', Role.MEMBER, 'member-password-2')`.
- Gives back `rig`.

`tests/unit/interfaces/test_http_app.py` lines 17 to 24:

```python
@pytest.fixture
def client(rig):
    healthy = {"up": True}
    app = create_app(rig.service, lambda: healthy["up"])
    app.testing = False
    test_client = app.test_client()
    test_client.healthy = healthy  # type: ignore[attr-defined]
    return test_client
```

> **In plain words.** A **fixture** is a helper function marked `@pytest.fixture`. A test that names it as a parameter receives its return value, prepared fresh for that test.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.
> **In plain words.** `obj[key]` looks a value up by key or position.

**Function `client`.**

It takes: `rig`.

Decorators: `@pytest.fixture`.

Step by step:

- Stores the dictionary `{'up': True}` in `healthy`.
- Stores the result of calling `create_app(rig.service, lambda: healthy['up'])` in `app`.
- Stores `False` in `app.testing`.
- Stores the result of calling `app.test_client()` in `test_client`.
- Stores `healthy` in `test_client.healthy`.
- Gives back `test_client`.

`tests/unit/interfaces/test_http_app.py` lines 27 to 28:

```python
def token(client, name, password):
    return client.post("/login", json={"username": name, "password": password}).get_json()["token"]
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Function `token`.**

It takes: `client`; `name`; `password`.

Step by step:

- Gives back `client.post('/login', json={'username': name, 'password': password}).get_json()…`.

`tests/unit/interfaces/test_http_app.py` lines 31 to 32:

```python
def auth(client, name="bruno", password="member-password-1"):
    return {"Authorization": f"Bearer {token(client, name, password)}"}
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `auth`.**

It takes: `client`; `name`, default `'bruno'`; `password`, default `'member-password-1'`.

Step by step:

- Gives back the dictionary `{'Authorization': f'Bearer {token(client, name, password)}'}`.

`tests/unit/interfaces/test_http_app.py` lines 35 to 39:

```python
def test_health_reports_the_database(client):
    response = client.get("/healthz")
    assert (response.status_code, response.get_json()) == (200, {"status": "ok"})
    client.healthy["up"] = False
    assert client.get("/healthz").status_code == 503
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_health_reports_the_database`** checks: health reports the database.

It takes: `client`.

Step by step:

- Stores the result of calling `client.get('/healthz')` in `response`.
- Checks that `(response.status_code, response.get_json())` equals `(200, {'status': 'ok'})`; if not, the test fails.
- Stores `False` in `client.healthy['up']`.
- Checks that `client.get('/healthz').status_code` equals `503`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 42 to 45:

```python
def test_login_returns_a_token_and_a_wrong_password_is_401(client):
    assert client.post("/login", json={"username": "bruno", "password": "member-password-1"}).status_code == 200
    bad = client.post("/login", json={"username": "bruno", "password": "nope"})
    assert (bad.status_code, bad.get_json()) == (401, {"error": "invalid username or password"})
```

**Test `test_login_returns_a_token_and_a_wrong_password_is_401`** checks: login returns a token and a wrong password is 401.

It takes: `client`.

Step by step:

- Checks that `client.post('/login', json={'username': 'bruno', …` equals `200`; if not, the test fails.
- Stores the result of calling `client.post('/login', json={'username': 'bruno', 'password': 'nope'})` in `bad`.
- Checks that `(bad.status_code, bad.get_json())` equals `(401, {'error': 'invalid username or password'})`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 48 to 49:

```python
def test_a_login_that_is_not_json_is_400(client):
    assert client.post("/login", data="x", content_type="text/plain").status_code == 400
```

**Test `test_a_login_that_is_not_json_is_400`** checks: a login that is not json is 400.

It takes: `client`.

Step by step:

- Checks that `client.post('/login', data='x', content_type='tex…` equals `400`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 52 to 62:

```python
def test_the_notes_lifecycle_over_http(client):
    headers = auth(client)
    created = client.post("/notes", json={"title": "First", "body": "text"}, headers=headers)
    assert created.status_code == 201
    note_id = created.get_json()["id"]
    assert client.get(f"/notes/{note_id}", headers=headers).get_json()["title"] == "First"
    assert [n["id"] for n in client.get("/notes", headers=headers).get_json()["notes"]] == [note_id]
    updated = client.put(f"/notes/{note_id}", json={"title": "Second", "body": "more"}, headers=headers)
    assert updated.get_json()["title"] == "Second"
    assert client.delete(f"/notes/{note_id}", headers=headers).status_code == 204
    assert client.get(f"/notes/{note_id}", headers=headers).status_code == 404
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Test `test_the_notes_lifecycle_over_http`** checks: the notes lifecycle over http.

It takes: `client`.

Step by step:

- Stores the result of calling `auth(client)` in `headers`.
- Stores the result of calling `client.post('/notes', json={'title': 'First', 'body': 'text'}, headers=headers)` in `created`.
- Checks that `created.status_code` equals `201`; if not, the test fails.
- Stores `created.get_json()['id']` in `note_id`.
- Checks that `client.get(f'/notes/{note_id}', headers=headers).…` equals `'First'`; if not, the test fails.
- Checks that `[n['id'] for n in client.get('/notes', headers=he…` equals `[note_id]`; if not, the test fails.
- Stores the result of calling `client.put(f'/notes/{note_id}', json={'title': 'Second', 'body': 'more'}, headers=headers)` in `updated`.
- Checks that `updated.get_json()['title']` equals `'Second'`; if not, the test fails.
- Checks that `client.delete(f'/notes/{note_id}', headers=header…` equals `204`; if not, the test fails.
- Checks that `client.get(f'/notes/{note_id}', headers=headers).…` equals `404`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 65 to 68:

```python
def test_requests_without_a_valid_token_are_401(client):
    assert client.get("/notes").status_code == 401
    assert client.get("/notes", headers={"Authorization": "Basic abc"}).status_code == 401
    assert client.get("/notes", headers={"Authorization": "Bearer nonsense"}).status_code == 401
```

**Test `test_requests_without_a_valid_token_are_401`** checks: requests without a valid token are 401.

It takes: `client`.

Step by step:

- Checks that `client.get('/notes').status_code` equals `401`; if not, the test fails.
- Checks that `client.get('/notes', headers={'Authorization': 'B…` equals `401`; if not, the test fails.
- Checks that `client.get('/notes', headers={'Authorization': 'B…` equals `401`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 71 to 75:

```python
def test_validation_errors_are_400_with_the_field(client):
    response = client.post("/notes", json={"title": "", "body": "x"}, headers=auth(client))
    assert response.status_code == 400
    assert response.get_json()["error"].startswith("title:")
    assert client.post("/notes", data="[]", content_type="application/json", headers=auth(client)).status_code == 400
```

**Test `test_validation_errors_are_400_with_the_field`** checks: validation errors are 400 with the field.

It takes: `client`.

Step by step:

- Stores the result of calling `client.post('/notes', json={'title': '', 'body': 'x'}, headers=auth(client))` in `response`.
- Checks that `response.status_code` equals `400`; if not, the test fails.
- Checks that `response.get_json()['error'].startswith('title:')`; if not, the test fails.
- Checks that `client.post('/notes', data='[]', content_type='ap…` equals `400`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 78 to 83:

```python
def test_another_members_note_is_404_and_a_wrong_role_is_403(client):
    note_id = client.post(
        "/notes", json={"title": "Private", "body": "x"}, headers=auth(client, "chen", "member-password-2")
    ).get_json()["id"]
    assert client.get(f"/notes/{note_id}", headers=auth(client)).status_code == 404
    assert client.put("/users/chen/role", json={"role": "admin"}, headers=auth(client)).status_code == 403
```

**Test `test_another_members_note_is_404_and_a_wrong_role_is_403`** checks: another members note is 404 and a wrong role is 403.

It takes: `client`.

Step by step:

- Stores `client.post('/notes', json={'title': 'Private', 'body': 'x'}, headers=auth(clie…` in `note_id`.
- Checks that `client.get(f'/notes/{note_id}', headers=auth(clie…` equals `404`; if not, the test fails.
- Checks that `client.put('/users/chen/role', json={'role': 'adm…` equals `403`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 86 to 97:

```python
def test_an_admin_grants_a_role(client, rig):
    response = client.put("/users/chen/role", json={"role": "admin"}, headers=auth(client, "ada", "admin-password-1"))
    assert (response.status_code, response.get_json()) == (200, {"role": "admin", "username": "chen"})
    assert rig.audit.events[-1].detail == {"role": "admin", "target": "chen"}
    bad = client.put("/users/chen/role", json={"role": "root"}, headers=auth(client, "ada", "admin-password-1"))
    assert bad.status_code == 400
    assert (
        client.put(
            "/users/nobody/role", json={"role": "member"}, headers=auth(client, "ada", "admin-password-1")
        ).status_code
        == 404
    )
```

**Test `test_an_admin_grants_a_role`** checks: an admin grants a role.

It takes: `client`; `rig`.

Step by step:

- Stores the result of calling `client.put('/users/chen/role', json={'role': 'admin'}, headers=auth(client, 'ada', 'admin…` in `response`.
- Checks that `(response.status_code, response.get_json())` equals `(200, {'role': 'admin', 'username': 'chen'})`; if not, the test fails.
- Checks that `rig.audit.events[-1].detail` equals `{'role': 'admin', 'target': 'chen'}`; if not, the test fails.
- Stores the result of calling `client.put('/users/chen/role', json={'role': 'root'}, headers=auth(client, 'ada', 'admin-…` in `bad`.
- Checks that `bad.status_code` equals `400`; if not, the test fails.
- Checks that `client.put('/users/nobody/role', json={'role': 'm…` equals `404`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 100 to 102:

```python
def test_unknown_routes_and_oversized_bodies_get_json_errors(client):
    assert client.get("/nope").get_json() == {"error": "not found"}
    assert client.post("/login", data="x" * 70_000, content_type="application/json").status_code == 413
```

**Test `test_unknown_routes_and_oversized_bodies_get_json_errors`** checks: unknown routes and oversized bodies get json errors.

It takes: `client`.

Step by step:

- Checks that `client.get('/nope').get_json()` equals `{'error': 'not found'}`; if not, the test fails.
- Checks that `client.post('/login', data='x' * 70000, content_t…` equals `413`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 105 to 108:

```python
def test_responses_are_not_cached_and_not_sniffed(client):
    response = client.get("/healthz")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
```

**Test `test_responses_are_not_cached_and_not_sniffed`** checks: responses are not cached and not sniffed.

It takes: `client`.

Step by step:

- Stores the result of calling `client.get('/healthz')` in `response`.
- Checks that `response.headers['Cache-Control']` equals `'no-store'`; if not, the test fails.
- Checks that `response.headers['X-Content-Type-Options']` equals `'nosniff'`; if not, the test fails.

`tests/unit/interfaces/test_http_app.py` lines 111 to 119:

```python
def test_an_unexpected_error_is_a_generic_500_without_details(rig):
    def boom():
        raise RuntimeError("database password is hunter2")

    app = create_app(rig.service, boom)
    app.testing = False
    response = app.test_client().get("/healthz")
    assert response.status_code == 500
    assert response.get_json() == {"error": "internal error"}
```

> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

**Test `test_an_unexpected_error_is_a_generic_500_without_details`** checks: an unexpected error is a generic 500 without details.

It takes: `rig`.

Step by step:

- Defines a helper function `boom()`.
  - Stops here by raising `RuntimeError('database password is hunter2')`.
- Stores the result of calling `create_app(rig.service, boom)` in `app`.
- Stores `False` in `app.testing`.
- Stores the result of calling `app.test_client().get('/healthz')` in `response`.
- Checks that `response.status_code` equals `500`; if not, the test fails.
- Checks that `response.get_json()` equals `{'error': 'internal error'}`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/unit/interfaces
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check tests/unit/interfaces/test_cli.py tests/unit/interfaces/test_http_app.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_the_parser_knows_every_step` check?
   **Answer:** it checks: the parser knows every step.
2. What does the test `test_an_unknown_command_is_a_usage_error` check?
   **Answer:** it checks: an unknown command is a usage error.
3. What does the test `test_missing_settings_exit_2` check?
   **Answer:** it checks: missing settings exit 2.
4. What does the test `test_a_missing_controls_file_exits_2` check?
   **Answer:** it checks: a missing controls file exits 2.
5. What does the test `test_health_reports_the_database` check?
   **Answer:** it checks: health reports the database.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
