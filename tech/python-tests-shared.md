# The tests (shared)

## What it is

The pytest tests in `tests/shared`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/conftest.py` | 111 lines. Shared fakes: a fixed clock and in-memory ports, so the domain and application are tested with no services. |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/conftest.py`

`tests/conftest.py` lines 1 to 13:

```python
"""Shared fakes: a fixed clock and in-memory ports, so the domain and application are tested with no services."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from notes_evidence.application.notes_service import NotesService
from notes_evidence.domain.audit import AuditEvent
from notes_evidence.domain.evidence import ManifestEntry, digest
from notes_evidence.domain.notes import Note, User
from notes_evidence.domain.roles import Role
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Shared fakes: a fixed clock and in-memory ports, so the domain and application are tested with no services.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `replace`.
- From `datetime` it takes `UTC, datetime, timedelta`.
- From `pathlib` it takes `Path`.
- From `notes_evidence.application.notes_service` it takes `NotesService`.
- From `notes_evidence.domain.audit` it takes `AuditEvent`.
- From `notes_evidence.domain.evidence` it takes `ManifestEntry, digest`.
- From `notes_evidence.domain.notes` it takes `Note, User`.
- From `notes_evidence.domain.roles` it takes `Role`.

`tests/conftest.py` lines 15 to 16:

```python
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 10, 22, 9, 0, 0, tzinfo=UTC)
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores `Path(__file__).resolve().parents[1]` in `REPOSITORY_ROOT`.
- Stores the result of calling `datetime(2026, 10, 22, 9, 0, 0, tzinfo=UTC)` in `T0`.

`tests/conftest.py` lines 19 to 29:

```python
class FixedClock:
    """A clock the test moves by hand."""

    def __init__(self, moment: datetime = T0) -> None:
        self.moment = moment

    def now(self) -> datetime:
        return self.moment

    def advance(self, **delta: float) -> None:
        self.moment += timedelta(**delta)
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Class `FixedClock`**. A clock the test moves by hand.

Its methods, in order:

**Method `__init__` of class `FixedClock`.**

It takes: `moment` (a `datetime`), default `T0`.

It gives back a `None`.

Step by step:

- Stores `moment` in `self.moment`.

**Method `now` of class `FixedClock`.**

It gives back a `datetime`.

Step by step:

- Gives back `self.moment`.

**Method `advance` of class `FixedClock`.**

It takes: `**delta` (any extra named values).

It gives back a `None`.

Step by step:

- Adds the result of calling `timedelta(**delta)` to `self.moment`.

`tests/conftest.py` lines 32 to 57:

```python
class MemoryUsers:
    """UserRepository and UserProvisioner in a dict."""

    def __init__(self) -> None:
        self.rows: dict[str, tuple[User, str]] = {}

    def provision(self, username: str, role: Role, password_hash: str) -> User:
        existing = self.rows.get(username)
        user = User(existing[0].id if existing else len(self.rows) + 1, username, role, True)
        self.rows[username] = (user, password_hash)
        return user

    def find_by_username(self, username: str) -> tuple[User, str] | None:
        return self.rows.get(username)

    def find_by_id(self, user_id: int) -> User | None:
        return next((user for user, _ in self.rows.values() if user.id == user_id), None)

    def set_role(self, user_id: int, role: Role) -> None:
        for name, (user, stored) in self.rows.items():
            if user.id == user_id:
                self.rows[name] = (replace(user, role=role), stored)

    def deactivate(self, username: str) -> None:
        user, stored = self.rows[username]
        self.rows[username] = (replace(user, active=False), stored)
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Class `MemoryUsers`**. UserRepository and UserProvisioner in a dict.

Its methods, in order:

**Method `__init__` of class `MemoryUsers`.**

It gives back a `None`.

Step by step:

- Declares `self.rows` as a `dict[str, tuple[User, str]]` and stores the dictionary `{}` in it.

**Method `provision` of class `MemoryUsers`.**

It takes: `username` (a `str`); `role` (a `Role`); `password_hash` (a `str`).

It gives back a `User`.

Step by step:

- Stores the result of calling `self.rows.get(username)` in `existing`.
- Stores the result of calling `User(existing[0].id if existing else len(self.rows) + 1, username, role, True)` in `user`.
- Stores the tuple `(user, password_hash)` in `self.rows[username]`.
- Gives back `user`.

**Method `find_by_username` of class `MemoryUsers`.**

It takes: `username` (a `str`).

It gives back a `tuple[User, str] | None`.

Step by step:

- Gives back the result of calling `self.rows.get(username)`.

**Method `find_by_id` of class `MemoryUsers`.**

It takes: `user_id` (a `int`).

It gives back a `User | None`.

Step by step:

- Gives back the result of calling `next((user for user, _ in self.rows.values() if user.id == user_id), None)`.

**Method `set_role` of class `MemoryUsers`.**

It takes: `user_id` (a `int`); `role` (a `Role`).

It gives back a `None`.

Step by step:

- For each `(name, (user, stored))` in the result of calling `self.rows.items()`:
  - If `user.id` equals `user_id`:
    - Stores the tuple `(replace(user, role=role), stored)` in `self.rows[name]`.

**Method `deactivate` of class `MemoryUsers`.**

It takes: `username` (a `str`).

It gives back a `None`.

Step by step:

- Unpacks `self.rows[username]` into `(user, stored)`.
- Stores the tuple `(replace(user, active=False), stored)` in `self.rows[username]`.

`tests/conftest.py` lines 60 to 84:

```python
class MemoryNotes:
    """NoteRepository in a dict."""

    def __init__(self) -> None:
        self.rows: dict[int, Note] = {}

    def add(self, owner_id: int, title: str, body: str, at: datetime) -> Note:
        note = Note(len(self.rows) + 1, owner_id, title, body, at, at)
        self.rows[note.id] = note
        return note

    def get(self, note_id: int) -> Note | None:
        return self.rows.get(note_id)

    def list_for(self, owner_id: int | None) -> list[Note]:
        return [n for n in self.rows.values() if owner_id is None or n.owner_id == owner_id]

    def update(self, note_id: int, title: str, body: str, at: datetime) -> Note | None:
        if note_id not in self.rows:
            return None
        self.rows[note_id] = replace(self.rows[note_id], title=title, body=body, updated_at=at)
        return self.rows[note_id]

    def delete(self, note_id: int) -> bool:
        return self.rows.pop(note_id, None) is not None
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Class `MemoryNotes`**. NoteRepository in a dict.

Its methods, in order:

**Method `__init__` of class `MemoryNotes`.**

It gives back a `None`.

Step by step:

- Declares `self.rows` as a `dict[int, Note]` and stores the dictionary `{}` in it.

**Method `add` of class `MemoryNotes`.**

It takes: `owner_id` (a `int`); `title` (a `str`); `body` (a `str`); `at` (a `datetime`).

It gives back a `Note`.

Step by step:

- Stores the result of calling `Note(len(self.rows) + 1, owner_id, title, body, at, at)` in `note`.
- Stores `note` in `self.rows[note.id]`.
- Gives back `note`.

**Method `get` of class `MemoryNotes`.**

It takes: `note_id` (a `int`).

It gives back a `Note | None`.

Step by step:

- Gives back the result of calling `self.rows.get(note_id)`.

**Method `list_for` of class `MemoryNotes`.**

It takes: `owner_id` (a `int | None`).

It gives back a `list[Note]`.

Step by step:

- Gives back a new list made by a loop (`[n for n in self.rows.values() if owner_id is None or n.owner_id == o…`).

**Method `update` of class `MemoryNotes`.**

It takes: `note_id` (a `int`); `title` (a `str`); `body` (a `str`); `at` (a `datetime`).

It gives back a `Note | None`.

Step by step:

- If `note_id` is not in `self.rows`:
  - Gives back nothing (`None`).
- Stores the result of calling `replace(self.rows[note_id], title=title, body=body, updated_at=at)` in `self.rows[note_id]`.
- Gives back `self.rows[note_id]`.

**Method `delete` of class `MemoryNotes`.**

It takes: `note_id` (a `int`).

It gives back a `bool`.

Step by step:

- Gives back whether `self.rows.pop(note_id, None)` is not the same object as `None`.

`tests/conftest.py` lines 87 to 100:

```python
class MemoryAudit:
    """AuditLog in a list. Like the real one it has no update and no delete."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)

    def since(self, moment: datetime) -> list[AuditEvent]:
        return [e for e in self.events if e.at >= moment]

    def latest(self, limit: int) -> list[AuditEvent]:
        return self.events[-limit:]
```

> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Class `MemoryAudit`**. AuditLog in a list. Like the real one it has no update and no delete.

Its methods, in order:

**Method `__init__` of class `MemoryAudit`.**

It gives back a `None`.

Step by step:

- Declares `self.events` as a `list[AuditEvent]` and stores the list `[]` in it.

**Method `append` of class `MemoryAudit`.**

It takes: `event` (a `AuditEvent`).

It gives back a `None`.

Step by step:

- Calls `self.events.append(event)`.

**Method `since` of class `MemoryAudit`.**

It takes: `moment` (a `datetime`).

It gives back a `list[AuditEvent]`.

Step by step:

- Gives back a new list made by a loop (`[e for e in self.events if e.at >= moment]`).

**Method `latest` of class `MemoryAudit`.**

It takes: `limit` (a `int`).

It gives back a `list[AuditEvent]`.

Step by step:

- Gives back `self.events[-limit:]`.

`tests/conftest.py` lines 103 to 110:

```python
class StubHasher:
    """Not a hash: lets tests read what was stored. The real scrypt hasher has its own tests."""

    def hash(self, password: str) -> str:
        return f"stub:{password}"

    def verify(self, password: str, stored: str) -> bool:
        return stored == f"stub:{password}"
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Class `StubHasher`**. Not a hash: lets tests read what was stored. The real scrypt hasher has its own tests.

Its methods, in order:

**Method `hash` of class `StubHasher`.**

It takes: `password` (a `str`).

It gives back a `str`.

Step by step:

- Gives back a text built with values filled in (`f'stub:{password}'`).

**Method `verify` of class `StubHasher`.**

It takes: `password` (a `str`); `stored` (a `str`).

It gives back a `bool`.

Step by step:

- Gives back whether `stored` equals `f'stub:{password}'`.

`tests/conftest.py` lines 113 to 125:

```python
class StubTokens:
    """Tokens that are just 'token-<id>', valid until a test expires them."""

    def __init__(self) -> None:
        self.expired = False

    def issue(self, user: User, now: datetime) -> str:
        return f"token-{user.id}"

    def verify(self, token: str, now: datetime) -> int | None:
        if self.expired or not token.startswith("token-") or not token[6:].isdigit():
            return None
        return int(token[6:])
```

**Class `StubTokens`**. Tokens that are just 'token-<id>', valid until a test expires them.

Its methods, in order:

**Method `__init__` of class `StubTokens`.**

It gives back a `None`.

Step by step:

- Stores `False` in `self.expired`.

**Method `issue` of class `StubTokens`.**

It takes: `user` (a `User`); `now` (a `datetime`).

It gives back a `str`.

Step by step:

- Gives back a text built with values filled in (`f'token-{user.id}'`).

**Method `verify` of class `StubTokens`.**

It takes: `token` (a `str`); `now` (a `datetime`).

It gives back a `int | None`.

Step by step:

- If `self.expired` or not (`token.startswith('token-')`) or not (`token[6:].isdigit()`):
  - Gives back nothing (`None`).
- Gives back the result of calling `int(token[6:])`.

`tests/conftest.py` lines 128 to 146:

```python
class MemoryEvidenceStore:
    """EvidenceStore in dicts, with the same manifest behavior as the file-based one."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.entries: dict[str, ManifestEntry] = {}

    def write(self, name: str, text: str, control: str, produced_at: datetime, run_by: str, source: str) -> None:
        self.files[name] = text
        self.entries[name] = ManifestEntry(name, control, produced_at, run_by, source, digest(text))

    def read(self, name: str) -> str | None:
        return self.files.get(name)

    def read_all(self) -> dict[str, str]:
        return dict(self.files)

    def manifest(self) -> dict[str, ManifestEntry]:
        return dict(self.entries)
```

**Class `MemoryEvidenceStore`**. EvidenceStore in dicts, with the same manifest behavior as the file-based one.

Its methods, in order:

**Method `__init__` of class `MemoryEvidenceStore`.**

It gives back a `None`.

Step by step:

- Declares `self.files` as a `dict[str, str]` and stores the dictionary `{}` in it.
- Declares `self.entries` as a `dict[str, ManifestEntry]` and stores the dictionary `{}` in it.

**Method `write` of class `MemoryEvidenceStore`.**

It takes: `name` (a `str`); `text` (a `str`); `control` (a `str`); `produced_at` (a `datetime`); `run_by` (a `str`); `source` (a `str`).

It gives back a `None`.

Step by step:

- Stores `text` in `self.files[name]`.
- Stores the result of calling `ManifestEntry(name, control, produced_at, run_by, source, digest(text))` in `self.entries[name]`.

**Method `read` of class `MemoryEvidenceStore`.**

It takes: `name` (a `str`).

It gives back a `str | None`.

Step by step:

- Gives back the result of calling `self.files.get(name)`.

**Method `read_all` of class `MemoryEvidenceStore`.**

It gives back a `dict[str, str]`.

Step by step:

- Gives back the result of calling `dict(self.files)`.

**Method `manifest` of class `MemoryEvidenceStore`.**

It gives back a `dict[str, ManifestEntry]`.

Step by step:

- Gives back the result of calling `dict(self.entries)`.

`tests/conftest.py` lines 149 to 162:

```python
class Rig:
    """A service wired to in-memory ports."""

    def __init__(self) -> None:
        self.clock = FixedClock()
        self.users = MemoryUsers()
        self.notes = MemoryNotes()
        self.audit = MemoryAudit()
        self.tokens = StubTokens()
        self.hasher = StubHasher()
        self.service = NotesService(self.users, self.notes, self.audit, self.hasher, self.tokens, self.clock)

    def add_user(self, name: str, role: Role = Role.MEMBER, password: str = "correct-horse-battery") -> User:
        return self.users.provision(name, role, self.hasher.hash(password))
```

**Class `Rig`**. A service wired to in-memory ports.

Its methods, in order:

**Method `__init__` of class `Rig`.**

It gives back a `None`.

Step by step:

- Stores the result of calling `FixedClock()` in `self.clock`.
- Stores the result of calling `MemoryUsers()` in `self.users`.
- Stores the result of calling `MemoryNotes()` in `self.notes`.
- Stores the result of calling `MemoryAudit()` in `self.audit`.
- Stores the result of calling `StubTokens()` in `self.tokens`.
- Stores the result of calling `StubHasher()` in `self.hasher`.
- Stores the result of calling `NotesService(self.users, self.notes, self.audit, self.hasher, self.tokens, self.clock)` in `self.service`.

**Method `add_user` of class `Rig`.**

It takes: `name` (a `str`); `role` (a `Role`), default `Role.MEMBER`; `password` (a `str`), default `'correct-horse-battery'`.

It gives back a `User`.

Step by step:

- Gives back the result of calling `self.users.provision(name, role, self.hasher.hash(password))`.

## Try it yourself

```bash
.venv/bin/pytest -q tests
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check tests/conftest.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `FixedClock` check?
   **Answer:** A clock the test moves by hand.
2. What does the test `MemoryUsers` check?
   **Answer:** UserRepository and UserProvisioner in a dict.
3. What does the test `MemoryNotes` check?
   **Answer:** NoteRepository in a dict.
4. What does the test `MemoryAudit` check?
   **Answer:** AuditLog in a list. Like the real one it has no update and no delete.
5. What does the test `StubHasher` check?
   **Answer:** Not a hash: lets tests read what was stored. The real scrypt hasher has its own tests.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
