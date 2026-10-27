# Domain layer code

## What it is

The rules and values: plain Python that decides things and never touches a file, a network or a database. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

This is where the repository's domain work happens. Reading it file by file, with every line explained, is how a reader sees the work that was done.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/__init__.py` | 2 lines. Prove six security controls on a small notes service with evidence a system produced. |
| `src/notes_evidence/domain/__init__.py` | 1 lines. domain layer. |
| `src/notes_evidence/domain/access.py` | 49 lines. C1: who has which access, in which system. Generated from the systems, never typed. |
| `src/notes_evidence/domain/alerts.py` | 58 lines. Alert rules over the audit stream: the events that need a person. |
| `src/notes_evidence/domain/audit.py` | 37 lines. The audit event: who did what, to which note, when, with what outcome. Never the note's content. |
| `src/notes_evidence/domain/changes.py` | 62 lines. C2: every merged change with its approver and the deployment that shipped it. |
| `src/notes_evidence/domain/controls.py` | 47 lines. The control matrix: each control, the frameworks it answers to, and the evidence that proves it. |
| `src/notes_evidence/domain/errors.py` | 18 lines. Named errors of the notes service. The interfaces layer maps each to an HTTP status. |
| `src/notes_evidence/domain/evidence.py` | 206 lines. Verify the evidence pack: every control maps to evidence, and every file exists, says what it should, is uned… |
| `src/notes_evidence/domain/findings.py` | 38 lines. The result of a rule: a finding with a code, a severity and the document it is about. |
| `src/notes_evidence/domain/notes.py` | 49 lines. Users, notes and the validation of what a caller may send. |
| `src/notes_evidence/domain/restore.py` | 37 lines. C4: a backup is a hope until it is restored. The artifact records the restore and how long it took. |
| `src/notes_evidence/domain/review.py` | 71 lines. C6: the access review. Every principal gets a decision, leavers go, and the record shows before and after. |
| `src/notes_evidence/domain/roles.py` | 23 lines. Roles and what each may do: least privilege as a table that tests can read. |
| `src/notes_evidence/domain/scan.py` | 64 lines. C5: the dependency scan, as a report a build produced and a rule that decides whether it blocks. |

## How it works underneath

The domain layer is the centre of the design. Because it imports nothing from the outer layers, every rule can be tested with plain values, fast, without setting anything up. import-linter fails the build if a domain file imports an outer layer.

## Walkthrough of this repository's use

### `src/notes_evidence/__init__.py`

`src/notes_evidence/__init__.py` lines 1 to 1:

```python
"""Prove six security controls on a small notes service with evidence a system produced."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** Prove six security controls on a small notes service with evidence a system produced.

`src/notes_evidence/__init__.py` lines 3 to 3:

```python
__version__ = "0.1.0"
```

These module-level lines:

- Stores the text `'0.1.0'` in `__version__`.

### `src/notes_evidence/domain/__init__.py`

`src/notes_evidence/domain/__init__.py` lines 1 to 1:

```python
"""domain layer."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** domain layer.

### `src/notes_evidence/domain/access.py`

`src/notes_evidence/domain/access.py` lines 1 to 8:

```python
"""C1: who has which access, in which system. Generated from the systems, never typed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.audit import format_timestamp
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** C1: who has which access, in which system. Generated from the systems, never typed.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `datetime`.
- From `notes_evidence.domain.audit` it takes `format_timestamp`.

`src/notes_evidence/domain/access.py` lines 10 to 13:

```python
REPOSITORY = "repository (permission per person)"
DATABASE = "database roles"
CLOUD = "cloud account users"
SYSTEMS = (REPOSITORY, DATABASE, CLOUD)
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'repository (permission per person)'` in `REPOSITORY`.
- Stores the text `'database roles'` in `DATABASE`.
- Stores the text `'cloud account users'` in `CLOUD`.
- Stores the tuple `(REPOSITORY, DATABASE, CLOUD)` in `SYSTEMS`.

`src/notes_evidence/domain/access.py` lines 16 to 22:

```python
@dataclass(frozen=True)
class AccessEntry:
    """One principal in one system. `level` is empty where the system has only members (cloud users)."""

    system: str
    principal: str
    level: str = ""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `AccessEntry`**. One principal in one system. `level` is empty where the system has only members (cloud users). Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `system`: a `str`.
- Field `principal`: a `str`.
- Field `level`: a `str`, default `''`.

`src/notes_evidence/domain/access.py` lines 25 to 43:

```python
@dataclass(frozen=True)
class AccessList:
    """Every entry of every system, with the moment it was generated."""

    generated_at: datetime
    entries: tuple[AccessEntry, ...]

    def in_system(self, system: str) -> tuple[AccessEntry, ...]:
        """The entries of one system, in the order the system returned them."""
        return tuple(entry for entry in self.entries if entry.system == system)

    def counts(self) -> dict[str, int]:
        """Entries per system."""
        return {system: len(self.in_system(system)) for system in SYSTEMS}

    def without(self, system: str, principal: str) -> AccessList:
        """The same list with one principal removed from one system."""
        kept = tuple(entry for entry in self.entries if not (entry.system == system and entry.principal == principal))
        return AccessList(self.generated_at, kept)
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Class `AccessList`**. Every entry of every system, with the moment it was generated. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `generated_at`: a `datetime`.
- Field `entries`: a `tuple[AccessEntry, ...]`.

Its methods, in order:

**Method `in_system` of class `AccessList`.** The entries of one system, in the order the system returned them.

It takes: `system` (a `str`).

It gives back a `tuple[AccessEntry, ...]`.

Step by step:

- Gives back the result of calling `tuple((entry for entry in self.entries if entry.system == system))`.

**Method `counts` of class `AccessList`.** Entries per system.

It gives back a `dict[str, int]`.

Step by step:

- Gives back a new dictionary made by a loop (`{system: len(self.in_system(system)) for system in SYSTEMS}`).

**Method `without` of class `AccessList`.** The same list with one principal removed from one system.

It takes: `system` (a `str`); `principal` (a `str`).

It gives back a `AccessList`.

Step by step:

- Stores the result of calling `tuple((entry for entry in self.entries if not (entry.system == system and entry.principal…` in `kept`.
- Gives back the result of calling `AccessList(self.generated_at, kept)`.

`src/notes_evidence/domain/access.py` lines 46 to 53:

```python
def render_access_list(access: AccessList) -> str:
    """The artifact: a dated header and one block per system, `principal<TAB>level` per line."""
    lines = [f"# access list, generated {format_timestamp(access.generated_at)}"]
    for system in SYSTEMS:
        lines.append(f"## {system}")
        for entry in access.in_system(system):
            lines.append(f"{entry.principal}\t{entry.level}" if entry.level else entry.principal)
    return "\n".join(lines) + "\n"
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `render_access_list`.** The artifact: a dated header and one block per system, `principal<TAB>level` per line.

It takes: `access` (a `AccessList`).

It gives back a `str`.

Step by step:

- Stores the list `[f'# access list, generated {format_timestamp(access.generated_at)}']` in `lines`.
- For each `system` in `SYSTEMS`:
  - Calls `lines.append(f'## {system}')`.
  - For each `entry` in the result of calling `access.in_system(system)`:
    - Calls `lines.append(f'{entry.principal}\t{entry.level}' if entry.level else entry.principal)`.
- Gives back `'\n'.join(lines) + '\n'`.

`src/notes_evidence/domain/access.py` lines 56 to 66:

```python
def parse_access_list(text: str) -> dict[str, list[str]]:
    """Principals per system from a rendered list; empty when the text is not an access list."""
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            blocks[current] = []
        elif current is not None and line.strip() and not line.startswith("#"):
            blocks[current].append(line.split("\t")[0].strip())
    return blocks
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `parse_access_list`.** Principals per system from a rendered list; empty when the text is not an access list.

It takes: `text` (a `str`).

It gives back a `dict[str, list[str]]`.

Step by step:

- Declares `blocks` as a `dict[str, list[str]]` and stores the dictionary `{}` in it.
- Declares `current` as a `str | None` and stores nothing (`None`) in it.
- For each `line` in the result of calling `text.splitlines()`:
  - If `line.startswith('## ')`:
    - Stores the result of calling `line[3:].strip()` in `current`.
    - Stores the list `[]` in `blocks[current]`.
  - Otherwise, if `current` is not the same object as `None` and `line.strip()` and not (`line.startswith('#')`):
    - Calls `blocks[current].append(line.split('\t')[0].strip())`.
- Gives back `blocks`.

### `src/notes_evidence/domain/alerts.py`

`src/notes_evidence/domain/alerts.py` lines 1 to 10:

```python
"""Alert rules over the audit stream: the events that need a person."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from notes_evidence.domain.audit import AuditAction, AuditEvent, format_timestamp
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Alert rules over the audit stream: the events that need a person.

Imports:

- From `__future__` it takes `annotations`.
- From `collections` it takes `defaultdict, deque`.
- From `collections.abc` it takes `Iterable, Sequence`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `datetime, timedelta`.
- From `notes_evidence.domain.audit` it takes `AuditAction, AuditEvent, format_timestamp`.

`src/notes_evidence/domain/alerts.py` lines 13 to 24:

```python
@dataclass(frozen=True)
class Alert:
    """An alert message with the time of the event that triggered it."""

    rule: str
    subject: str
    at: datetime
    message: str

    def render(self) -> str:
        """One line a person can read in a chat channel."""
        return f"ALERT [{self.rule}] {format_timestamp(self.at)} {self.message}"
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Alert`**. An alert message with the time of the event that triggered it. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `rule`: a `str`.
- Field `subject`: a `str`.
- Field `at`: a `datetime`.
- Field `message`: a `str`.

Its methods, in order:

**Method `render` of class `Alert`.** One line a person can read in a chat channel.

It gives back a `str`.

Step by step:

- Gives back a text built with values filled in (`f'ALERT [{self.rule}] {format_timestamp(self.at)} {self.message}'`).

`src/notes_evidence/domain/alerts.py` lines 27 to 32:

```python
@dataclass(frozen=True)
class AlertRules:
    """Five failed logins for one account in two minutes, or an admin role granted."""

    failed_logins: int = 5
    window: timedelta = timedelta(minutes=2)
```

**Class `AlertRules`**. Five failed logins for one account in two minutes, or an admin role granted. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `failed_logins`: a `int`, default `5`.
- Field `window`: a `timedelta`, default `timedelta(minutes=2)`.

`src/notes_evidence/domain/alerts.py` lines 35 to 71:

```python
def detect_alerts(events: Iterable[AuditEvent], rules: AlertRules | None = None) -> list[Alert]:
    """Walk the events in time order and return the alerts they raise.

    A burst of failed logins raises one alert when the count reaches the threshold inside the window; that account's
    count then starts again, so a long attack raises an alert for each further burst and not for each attempt.
    """
    rules = rules or AlertRules()
    ordered: Sequence[AuditEvent] = sorted(events, key=lambda event: event.at)
    recent: dict[str, deque[datetime]] = defaultdict(deque)
    alerts: list[Alert] = []
    for event in ordered:
        if event.action is AuditAction.LOGIN_FAILED:
            window = recent[event.username]
            window.append(event.at)
            while window and event.at - window[0] > rules.window:
                window.popleft()
            if len(window) >= rules.failed_logins:
                minutes = int(rules.window.total_seconds() // 60)
                alerts.append(
                    Alert(
                        "failed-logins",
                        event.username,
                        event.at,
                        f"{len(window)} failed logins for account {event.username} within {minutes} minutes",
                    )
                )
                window.clear()
        elif event.action is AuditAction.ROLE_GRANTED and event.detail.get("role") == "admin":
            alerts.append(
                Alert(
                    "admin-granted",
                    event.username,
                    event.at,
                    f"admin role granted to {event.detail.get('target', '?')} by {event.username}",
                )
            )
    return alerts
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **`while` loop** repeats its steps as long as its condition stays true.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Function `detect_alerts`.** Walk the events in time order and return the alerts they raise. A burst of failed logins raises one alert when the count reaches the threshold inside the window; that account's count then starts again, so a long attack raises an alert for each further burst and not for each attempt.

It takes: `events` (a `Iterable[AuditEvent]`); `rules` (a `AlertRules | None`), default `None`.

It gives back a `list[Alert]`.

Step by step:

- Stores whether `rules` or `AlertRules()` in `rules`.
- Declares `ordered` as a `Sequence[AuditEvent]` and stores the result of calling `sorted(events, key=lambda event: event.at)` in it.
- Declares `recent` as a `dict[str, deque[datetime]]` and stores the result of calling `defaultdict(deque)` in it.
- Declares `alerts` as a `list[Alert]` and stores the list `[]` in it.
- For each `event` in `ordered`:
  - If `event.action` is the same object as `AuditAction.LOGIN_FAILED`:
    - Stores `recent[event.username]` in `window`.
    - Calls `window.append(event.at)`.
    - While `window` and `event.at - window[0]` is more than `rules.window`:
      - Calls `window.popleft()`.
    - If `len(window)` is at least `rules.failed_logins`:
      - Stores the result of calling `int(rules.window.total_seconds() // 60)` in `minutes`.
      - Calls `alerts.append(Alert('failed-logins', event.username, event.at, f'{len(window)} failed logins for account {eve…`.
      - Calls `window.clear()`.
  - Otherwise, if `event.action` is the same object as `AuditAction.ROLE_GRANTED` and `event.detail.get('role')` equals `'admin'`:
    - Calls `alerts.append(Alert('admin-granted', event.username, event.at, f"admin role granted to {event.detail.get('tar…`.
- Gives back `alerts`.

### `src/notes_evidence/domain/audit.py`

`src/notes_evidence/domain/audit.py` lines 1 to 7:

```python
"""The audit event: who did what, to which note, when, with what outcome. Never the note's content."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The audit event: who did what, to which note, when, with what outcome. Never the note's content.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass, field`.
- From `datetime` it takes `UTC, datetime`.
- From `enum` it takes `Enum`.

`src/notes_evidence/domain/audit.py` lines 10 to 20:

```python
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
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** An **Enum** is a class whose members are the only allowed values of a fixed set, such as `Severity.ERROR` and `Severity.WARNING`.

**Class `AuditAction`**, a kind of `Enum`. Every action the service records.

Its parts:

- Class value `LOGIN_OK` set to the text `'login_ok'`.
- Class value `LOGIN_FAILED` set to the text `'login_failed'`.
- Class value `NOTE_CREATED` set to the text `'note_created'`.
- Class value `NOTE_READ` set to the text `'note_read'`.
- Class value `NOTE_UPDATED` set to the text `'note_updated'`.
- Class value `NOTE_DELETED` set to the text `'note_deleted'`.
- Class value `ROLE_GRANTED` set to the text `'role_granted'`.
- Class value `ACCESS_DENIED` set to the text `'access_denied'`.

`src/notes_evidence/domain/audit.py` lines 23 to 33:

```python
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
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `AuditEvent`**. One line of the audit trail. `detail` holds short facts such as the role granted, never a caller's free text. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `at`: a `datetime`.
- Field `user_id`: a `int | None`.
- Field `username`: a `str`.
- Field `action`: a `AuditAction`.
- Field `note_id`: a `int | None`.
- Field `outcome`: a `str`.
- Field `detail`: a `dict[str, str]`, default `field(default_factory=dict)`.

`src/notes_evidence/domain/audit.py` lines 36 to 38:

```python
def format_timestamp(moment: datetime) -> str:
    """UTC, to the second, with a trailing Z: 2026-10-22T09:12:03Z."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `format_timestamp`.** UTC, to the second, with a trailing Z: 2026-10-22T09:12:03Z.

It takes: `moment` (a `datetime`).

It gives back a `str`.

Step by step:

- Gives back the result of calling `moment.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')`.

`src/notes_evidence/domain/audit.py` lines 41 to 49:

```python
def render_line(event: AuditEvent) -> str:
    """The log line: timestamp, user, action, note, outcome. Fixed fields, so no caller text can inject a line."""
    user = f"{event.user_id}" if event.user_id is not None else "-"
    note = f"{event.note_id}" if event.note_id is not None else "-"
    extra = "".join(f" {key}={value}" for key, value in sorted(event.detail.items()))
    return (
        f"{format_timestamp(event.at)} user={event.username} id={user} action={event.action.value} "
        f"note={note} outcome={event.outcome}{extra}"
    )
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Function `render_line`.** The log line: timestamp, user, action, note, outcome. Fixed fields, so no caller text can inject a line.

It takes: `event` (a `AuditEvent`).

It gives back a `str`.

Step by step:

- Stores `f'{event.user_id}'` if `event.user_id` is not the same object as `None`, otherwise `'-'` in `user`.
- Stores `f'{event.note_id}'` if `event.note_id` is not the same object as `None`, otherwise `'-'` in `note`.
- Stores the result of calling `''.join((f' {key}={value}' for key, value in sorted(event.detail.items())))` in `extra`.
- Gives back a text built with values filled in (`f'{format_timestamp(event.at)} user={event.username} id={user} action…`).

### `src/notes_evidence/domain/changes.py`

`src/notes_evidence/domain/changes.py` lines 1 to 10:

```python
"""C2: every merged change with its approver and the deployment that shipped it."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.audit import format_timestamp
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** C2: every merged change with its approver and the deployment that shipped it.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `csv`.
- It imports module `io`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `datetime`.
- From `notes_evidence.domain.audit` it takes `format_timestamp`.

`src/notes_evidence/domain/changes.py` lines 12 to 12:

```python
HEADER = ("number", "author", "merged_at", "commit", "approvers", "deploy_id")
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the tuple `('number', 'author', 'merged_at', 'commit', 'approvers', 'deploy_id')` in `HEADER`.

`src/notes_evidence/domain/changes.py` lines 15 to 24:

```python
@dataclass(frozen=True)
class MergedChange:
    """One merged pull request, as the hosting platform reports it."""

    number: int
    author: str
    merged_at: datetime
    commit: str
    approvers: tuple[str, ...]
    deploy_id: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `MergedChange`**. One merged pull request, as the hosting platform reports it. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `number`: a `int`.
- Field `author`: a `str`.
- Field `merged_at`: a `datetime`.
- Field `commit`: a `str`.
- Field `approvers`: a `tuple[str, ...]`.
- Field `deploy_id`: a `str`.

`src/notes_evidence/domain/changes.py` lines 27 to 32:

```python
@dataclass(frozen=True)
class ChangeException:
    """A change that broke the rule: no approver, only a self-approval, or no deployment record."""

    number: int
    reason: str
```

**Class `ChangeException`**. A change that broke the rule: no approver, only a self-approval, or no deployment record. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `number`: a `int`.
- Field `reason`: a `str`.

`src/notes_evidence/domain/changes.py` lines 35 to 37:

```python
def independent_approvers(change: MergedChange) -> tuple[str, ...]:
    """Approvers other than the author: a change approved only by its author was not reviewed."""
    return tuple(name for name in change.approvers if name != change.author)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `independent_approvers`.** Approvers other than the author: a change approved only by its author was not reviewed.

It takes: `change` (a `MergedChange`).

It gives back a `tuple[str, ...]`.

Step by step:

- Gives back the result of calling `tuple((name for name in change.approvers if name != change.author))`.

`src/notes_evidence/domain/changes.py` lines 40 to 48:

```python
def find_exceptions(changes: list[MergedChange]) -> list[ChangeException]:
    """Changes with no independent approver, or with no deployment id."""
    found: list[ChangeException] = []
    for change in changes:
        if not independent_approvers(change):
            found.append(ChangeException(change.number, "merged with no independent approver"))
        if not change.deploy_id:
            found.append(ChangeException(change.number, "no deployment record"))
    return found
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.

**Function `find_exceptions`.** Changes with no independent approver, or with no deployment id.

It takes: `changes` (a `list[MergedChange]`).

It gives back a `list[ChangeException]`.

Step by step:

- Declares `found` as a `list[ChangeException]` and stores the list `[]` in it.
- For each `change` in `changes`:
  - If not (`independent_approvers(change)`):
    - Calls `found.append(ChangeException(change.number, 'merged with no independent approver'))`.
  - If not (`change.deploy_id`):
    - Calls `found.append(ChangeException(change.number, 'no deployment record'))`.
- Gives back `found`.

`src/notes_evidence/domain/changes.py` lines 51 to 67:

```python
def render_changes(changes: list[MergedChange]) -> str:
    """The artifact as CSV: strings quoted, the number bare, approvers joined with '+'."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")
    writer.writerow(HEADER)
    for change in sorted(changes, key=lambda item: item.number):
        writer.writerow(
            [
                change.number,
                change.author,
                format_timestamp(change.merged_at),
                change.commit[:7],
                "+".join(change.approvers),
                change.deploy_id,
            ]
        )
    return buffer.getvalue()
```

> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `render_changes`.** The artifact as CSV: strings quoted, the number bare, approvers joined with '+'.

It takes: `changes` (a `list[MergedChange]`).

It gives back a `str`.

Step by step:

- Stores the result of calling `io.StringIO()` in `buffer`.
- Stores the result of calling `csv.writer(buffer, quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')` in `writer`.
- Calls `writer.writerow(HEADER)`.
- For each `change` in the result of calling `sorted(changes, key=lambda item: item.number)`:
  - Calls `writer.writerow([change.number, change.author, format_timestamp(change.merged_at), change.commit[:7], '+'.joi…`.
- Gives back the result of calling `buffer.getvalue()`.

`src/notes_evidence/domain/changes.py` lines 70 to 80:

```python
def exceptions_in_csv(text: str) -> list[ChangeException]:
    """Re-derive the exceptions from a rendered artifact, so the check does not trust the collector."""
    rows = list(csv.DictReader(io.StringIO(text)))
    found: list[ChangeException] = []
    for row in rows:
        approvers = [name for name in row["approvers"].split("+") if name and name != row["author"]]
        if not approvers:
            found.append(ChangeException(int(row["number"]), "merged with no independent approver"))
        if not row["deploy_id"]:
            found.append(ChangeException(int(row["number"]), "no deployment record"))
    return found
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Function `exceptions_in_csv`.** Re-derive the exceptions from a rendered artifact, so the check does not trust the collector.

It takes: `text` (a `str`).

It gives back a `list[ChangeException]`.

Step by step:

- Stores the result of calling `list(csv.DictReader(io.StringIO(text)))` in `rows`.
- Declares `found` as a `list[ChangeException]` and stores the list `[]` in it.
- For each `row` in `rows`:
  - Stores a new list made by a loop (`[name for name in row['approvers'].split('+') if name and name != row…`) in `approvers`.
  - If not (`approvers`):
    - Calls `found.append(ChangeException(int(row['number']), 'merged with no independent approver'))`.
  - If not (`row['deploy_id']`):
    - Calls `found.append(ChangeException(int(row['number']), 'no deployment record'))`.
- Gives back `found`.

### `src/notes_evidence/domain/controls.py`

`src/notes_evidence/domain/controls.py` lines 1 to 6:

```python
"""The control matrix: each control, the frameworks it answers to, and the evidence that proves it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The control matrix: each control, the frameworks it answers to, and the evidence that proves it.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `date`.

`src/notes_evidence/domain/controls.py` lines 8 to 9:

```python
KINDS = ("access_list", "changes", "log_sample", "alert_test", "restore", "scan", "review")
FRAMEWORKS = ("iso27001", "soc2")
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the tuple `('access_list', 'changes', 'log_sample', 'alert_test', 'restore', 'sc…` in `KINDS`.
- Stores the tuple `('iso27001', 'soc2')` in `FRAMEWORKS`.

`src/notes_evidence/domain/controls.py` lines 12 to 21:

```python
@dataclass(frozen=True)
class EvidenceSpec:
    """One artifact a control is shown by."""

    file: str
    kind: str
    proves: str
    period: str
    refresh_days: int
    refreshed: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `EvidenceSpec`**. One artifact a control is shown by. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `file`: a `str`.
- Field `kind`: a `str`.
- Field `proves`: a `str`.
- Field `period`: a `str`.
- Field `refresh_days`: a `int`.
- Field `refreshed`: a `str`.

`src/notes_evidence/domain/controls.py` lines 24 to 33:

```python
@dataclass(frozen=True)
class Control:
    """A control: what it requires, where it lives, the framework references it satisfies, its evidence."""

    id: str
    name: str
    requires: str
    where: str
    references: dict[str, tuple[str, ...]]
    evidence: tuple[EvidenceSpec, ...]
```

> **In plain words.** `obj[key]` looks a value up by key or position.

**Class `Control`**. A control: what it requires, where it lives, the framework references it satisfies, its evidence. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `id`: a `str`.
- Field `name`: a `str`.
- Field `requires`: a `str`.
- Field `where`: a `str`.
- Field `references`: a `dict[str, tuple[str, ...]]`.
- Field `evidence`: a `tuple[EvidenceSpec, ...]`.

`src/notes_evidence/domain/controls.py` lines 36 to 44:

```python
@dataclass(frozen=True)
class RecordedException:
    """A known deviation, with how it was handled. Hiding exceptions is the mistake the lesson names."""

    id: str
    control: str
    change: int | None
    description: str
    followup: str
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.

**Class `RecordedException`**. A known deviation, with how it was handled. Hiding exceptions is the mistake the lesson names. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `id`: a `str`.
- Field `control`: a `str`.
- Field `change`: a `int | None`.
- Field `description`: a `str`.
- Field `followup`: a `str`.

`src/notes_evidence/domain/controls.py` lines 47 to 54:

```python
@dataclass(frozen=True)
class Gap:
    """A control with no evidence yet, tracked on purpose."""

    control: str
    reason: str
    ticket: str
    due: date | None
```

**Class `Gap`**. A control with no evidence yet, tracked on purpose. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `control`: a `str`.
- Field `reason`: a `str`.
- Field `ticket`: a `str`.
- Field `due`: a `date | None`.

`src/notes_evidence/domain/controls.py` lines 57 to 64:

```python
def overlap(controls: list[Control]) -> dict[str, dict[str, list[str]]]:
    """For each framework, each reference and its controls. A reference with two controls is an overlap."""
    table: dict[str, dict[str, list[str]]] = {name: {} for name in FRAMEWORKS}
    for control in controls:
        for framework, refs in control.references.items():
            for ref in refs:
                table.setdefault(framework, {}).setdefault(ref, []).append(control.id)
    return {framework: dict(sorted(refs.items())) for framework, refs in table.items()}
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Function `overlap`.** For each framework, each reference and its controls. A reference with two controls is an overlap.

It takes: `controls` (a `list[Control]`).

It gives back a `dict[str, dict[str, list[str]]]`.

Step by step:

- Declares `table` as a `dict[str, dict[str, list[str]]]` and stores a new dictionary made by a loop (`{name: {} for name in FRAMEWORKS}`) in it.
- For each `control` in `controls`:
  - For each `(framework, refs)` in the result of calling `control.references.items()`:
    - For each `ref` in `refs`:
      - Calls `table.setdefault(framework, {}).setdefault(ref, []).append(control.id)`.
- Gives back a new dictionary made by a loop (`{framework: dict(sorted(refs.items())) for framework, refs in table.i…`).

### `src/notes_evidence/domain/errors.py`

`src/notes_evidence/domain/errors.py` lines 1 to 3:

```python
"""Named errors of the notes service. The interfaces layer maps each to an HTTP status."""

from __future__ import annotations
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Named errors of the notes service. The interfaces layer maps each to an HTTP status.

Imports:

- From `__future__` it takes `annotations`.

`src/notes_evidence/domain/errors.py` lines 6 to 7:

```python
class DomainError(Exception):
    """Base of every expected failure."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `DomainError`**, a kind of `Exception`. Base of every expected failure.

`src/notes_evidence/domain/errors.py` lines 10 to 16:

```python
class ValidationError(DomainError):
    """An input is not acceptable; `field` says which."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Class `ValidationError`**, a kind of `DomainError`. An input is not acceptable; `field` says which.

Its methods, in order:

**Method `__init__` of class `ValidationError`.**

It takes: `field` (a `str`); `message` (a `str`).

It gives back a `None`.

Step by step:

- Calls `super().__init__(f'{field}: {message}')`.
- Stores `field` in `self.field`.
- Stores `message` in `self.message`.

`src/notes_evidence/domain/errors.py` lines 19 to 20:

```python
class InvalidCredentialsError(DomainError):
    """The username or password is wrong, or the account is inactive. The message never says which."""
```

**Class `InvalidCredentialsError`**, a kind of `DomainError`. The username or password is wrong, or the account is inactive. The message never says which.

`src/notes_evidence/domain/errors.py` lines 23 to 24:

```python
class NotAuthenticatedError(DomainError):
    """A request carries no valid token."""
```

**Class `NotAuthenticatedError`**, a kind of `DomainError`. A request carries no valid token.

`src/notes_evidence/domain/errors.py` lines 27 to 28:

```python
class NotAllowedError(DomainError):
    """The role may not do this."""
```

**Class `NotAllowedError`**, a kind of `DomainError`. The role may not do this.

`src/notes_evidence/domain/errors.py` lines 31 to 32:

```python
class NotFoundError(DomainError):
    """The note does not exist, or the caller may not know that it does."""
```

**Class `NotFoundError`**, a kind of `DomainError`. The note does not exist, or the caller may not know that it does.

### `src/notes_evidence/domain/evidence.py`

`src/notes_evidence/domain/evidence.py` lines 1 to 17:

```python
"""Verify the evidence pack: every control maps to evidence, and every file exists, says what it should, is unedited."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime

from notes_evidence.domain.access import SYSTEMS, parse_access_list
from notes_evidence.domain.changes import HEADER, exceptions_in_csv
from notes_evidence.domain.controls import Control, EvidenceSpec, Gap, RecordedException, overlap
from notes_evidence.domain.findings import Finding, error, warning
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Verify the evidence pack: every control maps to evidence, and every file exists, says what it should, is unedited.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `csv`.
- It imports module `hashlib`.
- It imports module `io`.
- It imports module `json`.
- It imports module `re`.
- From `collections.abc` it takes `Mapping`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `date, datetime`.
- From `notes_evidence.domain.access` it takes `SYSTEMS, parse_access_list`.
- From `notes_evidence.domain.changes` it takes `HEADER, exceptions_in_csv`.
- From `notes_evidence.domain.controls` it takes `Control, EvidenceSpec, Gap, RecordedException, overlap`.
- From `notes_evidence.domain.findings` it takes `Finding, error, warning`.

`src/notes_evidence/domain/evidence.py` lines 19 to 24:

```python
LOG_LINE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z user=\S+ id=\S+ action=[a-z_]+ note=\S+ outcome=[a-z]+( \w+=\S+)*$"
)
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
SUPPORT_FILES = frozenset({"INDEX.md", "manifest.json"})
MIN_LOG_LINES = 5
```

> **In plain words.** A **regular expression** is a short pattern for text, such as `^## (.+)$` for "a line starting with ## ". `re.compile` prepares it once; `.match` tries it at the start of a string and returns a match object or `None`.
> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `re.compile('^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z user=\\S+ id=\\S+ action=[a-z_]+ …` in `LOG_LINE`.
- Stores the result of calling `re.compile('\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z')` in `TIMESTAMP`.
- Stores the result of calling `frozenset({'INDEX.md', 'manifest.json'})` in `SUPPORT_FILES`.
- Stores the number `5` in `MIN_LOG_LINES`.

`src/notes_evidence/domain/evidence.py` lines 27 to 36:

```python
@dataclass(frozen=True)
class ManifestEntry:
    """What a collector recorded about the file it wrote."""

    file: str
    control: str
    produced_at: datetime
    run_by: str
    source: str
    sha256: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `ManifestEntry`**. What a collector recorded about the file it wrote. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `file`: a `str`.
- Field `control`: a `str`.
- Field `produced_at`: a `datetime`.
- Field `run_by`: a `str`.
- Field `source`: a `str`.
- Field `sha256`: a `str`.

`src/notes_evidence/domain/evidence.py` lines 39 to 41:

```python
def digest(text: str) -> str:
    """The SHA-256 of a file's text, as the manifest records it."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `digest`.** The SHA-256 of a file's text, as the manifest records it.

It takes: `text` (a `str`).

It gives back a `str`.

Step by step:

- Gives back the result of calling `hashlib.sha256(text.encode('utf-8')).hexdigest()`.

`src/notes_evidence/domain/evidence.py` lines 44 to 76:

```python
def verify_pack(
    controls: list[Control],
    manifest: Mapping[str, ManifestEntry],
    files: Mapping[str, str],
    exceptions: list[RecordedException],
    gaps: list[Gap],
    today: date,
) -> list[Finding]:
    """EVD001 to EVD009. `files` holds the text of every file in the evidence folder."""
    found: list[Finding] = []
    gap_controls = {gap.control for gap in gaps}
    mapped: set[str] = set()
    for control in controls:
        if not control.evidence:
            if control.id not in gap_controls:
                found.append(error("EVD001", control.id, "the control has no evidence and no tracked gap"))
            continue
        if control.id in gap_controls:
            found.append(error("EVD008", control.id, "listed as a gap but it has evidence: close the gap record"))
        for spec in control.evidence:
            mapped.add(spec.file)
            found.extend(_check_file(control, spec, manifest, files, exceptions, today))
        if len(control.references.get("iso27001", ())) + len(control.references.get("soc2", ())) < 2:
            found.append(error("EVD009", control.id, "the control maps to fewer than two framework references"))
    for gap in gaps:
        if not gap.reason.strip() or not gap.ticket.strip() or gap.due is None:
            found.append(error("EVD008", gap.control, "a tracked gap needs a reason, a ticket and a due date"))
        if gap.control not in {control.id for control in controls}:
            found.append(error("EVD008", gap.control, "the gap names a control that does not exist"))
    for path in sorted(set(files) - mapped - SUPPORT_FILES):
        found.append(error("EVD004", path, "an evidence file that no control claims"))
    found.extend(_cross_checks(controls, files))
    return found
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Function `verify_pack`.** EVD001 to EVD009. `files` holds the text of every file in the evidence folder.

It takes: `controls` (a `list[Control]`); `manifest` (a `Mapping[str, ManifestEntry]`); `files` (a `Mapping[str, str]`); `exceptions` (a `list[RecordedException]`); `gaps` (a `list[Gap]`); `today` (a `date`).

It gives back a `list[Finding]`.

Step by step:

- Declares `found` as a `list[Finding]` and stores the list `[]` in it.
- Stores a new set made by a loop (`{gap.control for gap in gaps}`) in `gap_controls`.
- Declares `mapped` as a `set[str]` and stores the result of calling `set()` in it.
- For each `control` in `controls`:
  - If not (`control.evidence`):
    - If `control.id` is not in `gap_controls`:
      - Calls `found.append(error('EVD001', control.id, 'the control has no evidence and no tracked gap'))`.
    - Skips to the next item (`continue`).
  - If `control.id` is in `gap_controls`:
    - Calls `found.append(error('EVD008', control.id, 'listed as a gap but it has evidence: close the gap record'))`.
  - For each `spec` in `control.evidence`:
    - Calls `mapped.add(spec.file)`.
    - Calls `found.extend(_check_file(control, spec, manifest, files, exceptions, today))`.
  - If `len(control.references.get('iso27001', ())) + len…` is less than `2`:
    - Calls `found.append(error('EVD009', control.id, 'the control maps to fewer than two framework references'))`.
- For each `gap` in `gaps`:
  - If not (`gap.reason.strip()`) or not (`gap.ticket.strip()`) or `gap.due` is the same object as `None`:
    - Calls `found.append(error('EVD008', gap.control, 'a tracked gap needs a reason, a ticket and a due date'))`.
  - If `gap.control` is not in `{control.id for control in controls}`:
    - Calls `found.append(error('EVD008', gap.control, 'the gap names a control that does not exist'))`.
- For each `path` in the result of calling `sorted(set(files) - mapped - SUPPORT_FILES)`:
  - Calls `found.append(error('EVD004', path, 'an evidence file that no control claims'))`.
- Calls `found.extend(_cross_checks(controls, files))`.
- Gives back `found`.

`src/notes_evidence/domain/evidence.py` lines 79 to 110:

```python
def _check_file(
    control: Control,
    spec: EvidenceSpec,
    manifest: Mapping[str, ManifestEntry],
    files: Mapping[str, str],
    exceptions: list[RecordedException],
    today: date,
) -> list[Finding]:
    subject = f"{control.id} {spec.file}"
    text = files.get(spec.file)
    if text is None or not text.strip():
        return [
            error("EVD002", subject, "the evidence file is missing or empty: an empty file is worse than a missing one")
        ]
    found: list[Finding] = []
    entry = manifest.get(spec.file)
    if entry is None:
        found.append(error("EVD003", subject, "no manifest entry: nobody recorded who produced it or when"))
    else:
        if entry.sha256 != digest(text):
            found.append(
                error("EVD003", subject, "the file differs from the hash its collector recorded: it was edited by hand")
            )
        if entry.control != control.id:
            found.append(error("EVD003", subject, f"the manifest says it belongs to {entry.control}"))
        age = (today - entry.produced_at.date()).days
        if age > spec.refresh_days:
            found.append(
                warning("EVD005", subject, f"produced {age} days ago; the control refreshes every {spec.refresh_days}")
            )
    found.extend(_check_content(control, spec, text, exceptions))
    return found
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `_check_file`.**

It takes: `control` (a `Control`); `spec` (a `EvidenceSpec`); `manifest` (a `Mapping[str, ManifestEntry]`); `files` (a `Mapping[str, str]`); `exceptions` (a `list[RecordedException]`); `today` (a `date`).

It gives back a `list[Finding]`.

Step by step:

- Stores a text built with values filled in (`f'{control.id} {spec.file}'`) in `subject`.
- Stores the result of calling `files.get(spec.file)` in `text`.
- If `text` is the same object as `None` or not (`text.strip()`):
  - Gives back the list `[error('EVD002', subject, 'the evidence file is missing or empty: an …`.
- Declares `found` as a `list[Finding]` and stores the list `[]` in it.
- Stores the result of calling `manifest.get(spec.file)` in `entry`.
- If `entry` is the same object as `None`:
  - Calls `found.append(error('EVD003', subject, 'no manifest entry: nobody recorded who produced it or when'))`.
- Otherwise:
  - If `entry.sha256` is different from `digest(text)`:
    - Calls `found.append(error('EVD003', subject, 'the file differs from the hash its collector recorded: it was edited b…`.
  - If `entry.control` is different from `control.id`:
    - Calls `found.append(error('EVD003', subject, f'the manifest says it belongs to {entry.control}'))`.
  - Stores `(today - entry.produced_at.date()).days` in `age`.
  - If `age` is more than `spec.refresh_days`:
    - Calls `found.append(warning('EVD005', subject, f'produced {age} days ago; the control refreshes every {spec.refresh_…`.
- Calls `found.extend(_check_content(control, spec, text, exceptions))`.
- Gives back `found`.

`src/notes_evidence/domain/evidence.py` lines 113 to 127:

```python
def _check_content(
    control: Control, spec: EvidenceSpec, text: str, exceptions: list[RecordedException]
) -> list[Finding]:
    subject = f"{control.id} {spec.file}"
    if spec.kind == "changes":
        return [error(code, subject, message) for code, message in _changes(text, control.id, exceptions)]
    checks = {
        "access_list": _access_list,
        "log_sample": _log_sample,
        "alert_test": _alert_test,
        "restore": _restore,
        "scan": _scan,
        "review": _review,
    }
    return [error("EVD007", subject, problem) for problem in checks[spec.kind](text)]
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Function `_check_content`.**

It takes: `control` (a `Control`); `spec` (a `EvidenceSpec`); `text` (a `str`); `exceptions` (a `list[RecordedException]`).

It gives back a `list[Finding]`.

Step by step:

- Stores a text built with values filled in (`f'{control.id} {spec.file}'`) in `subject`.
- If `spec.kind` equals `'changes'`:
  - Gives back a new list made by a loop (`[error(code, subject, message) for code, message in _changes(text, co…`).
- Stores the dictionary `{'access_list': _access_list, 'log_sample': _log_sample, 'alert_test'…` in `checks`.
- Gives back a new list made by a loop (`[error('EVD007', subject, problem) for problem in checks[spec.kind](t…`).

`src/notes_evidence/domain/evidence.py` lines 130 to 135:

```python
def _access_list(text: str) -> list[str]:
    blocks = parse_access_list(text)
    problems = [f"no '## {system}' block" for system in SYSTEMS if system not in blocks]
    if not text.startswith("# access list, generated "):
        problems.append("no dated header")
    return problems
```

**Function `_access_list`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the result of calling `parse_access_list(text)` in `blocks`.
- Stores a new list made by a loop (`[f"no '## {system}' block" for system in SYSTEMS if system not in blo…`) in `problems`.
- If not (`text.startswith('# access list, generated ')`):
  - Calls `problems.append('no dated header')`.
- Gives back `problems`.

`src/notes_evidence/domain/evidence.py` lines 138 to 149:

```python
def _changes(text: str, control_id: str, exceptions: list[RecordedException]) -> list[tuple[str, str]]:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or tuple(rows[0]) != HEADER:
        return [("EVD007", f"the header must be {','.join(HEADER)}")]
    if len(rows) < 2:
        return [("EVD007", "no changes listed")]
    listed = {item.change for item in exceptions if item.control == control_id and item.followup.strip()}
    return [
        ("EVD006", f"change {item.number} ({item.reason}) is not listed in controls/exceptions.toml with a follow-up")
        for item in exceptions_in_csv(text)
        if item.number not in listed
    ]
```

**Function `_changes`.**

It takes: `text` (a `str`); `control_id` (a `str`); `exceptions` (a `list[RecordedException]`).

It gives back a `list[tuple[str, str]]`.

Step by step:

- Stores the result of calling `list(csv.reader(io.StringIO(text)))` in `rows`.
- If not (`rows`) or `tuple(rows[0])` is different from `HEADER`:
  - Gives back the list `[('EVD007', f"the header must be {','.join(HEADER)}")]`.
- If `len(rows)` is less than `2`:
  - Gives back the list `[('EVD007', 'no changes listed')]`.
- Stores a new set made by a loop (`{item.change for item in exceptions if item.control == control_id and…`) in `listed`.
- Gives back a new list made by a loop (`[('EVD006', f'change {item.number} ({item.reason}) is not listed in c…`).

`src/notes_evidence/domain/evidence.py` lines 152 to 158:

```python
def _log_sample(text: str) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    bad = [line for line in lines if not LOG_LINE.match(line)]
    problems = [f"not a log line: {line[:60]!r}" for line in bad[:3]]
    if len(lines) < MIN_LOG_LINES:
        problems.append(f"{len(lines)} lines; a sample needs at least {MIN_LOG_LINES}")
    return problems
```

> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `_log_sample`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores a new list made by a loop (`[line for line in text.splitlines() if line.strip()]`) in `lines`.
- Stores a new list made by a loop (`[line for line in lines if not LOG_LINE.match(line)]`) in `bad`.
- Stores a new list made by a loop (`[f'not a log line: {line[:60]!r}' for line in bad[:3]]`) in `problems`.
- If `len(lines)` is less than `MIN_LOG_LINES`:
  - Calls `problems.append(f'{len(lines)} lines; a sample needs at least {MIN_LOG_LINES}')`.
- Gives back `problems`.

`src/notes_evidence/domain/evidence.py` lines 161 to 171:

```python
def _alert_test(text: str) -> list[str]:
    problems: list[str] = []
    action = re.search(r"test action at (" + TIMESTAMP.pattern + ")", text)
    alert = re.search(r"ALERT \[[a-z-]+\] (" + TIMESTAMP.pattern + ")", text)
    if action is None:
        problems.append("no 'test action at <timestamp>' line")
    if alert is None:
        problems.append("no alert message with its timestamp: the alert did not fire")
    if action and alert and alert.group(1) < action.group(1):
        problems.append("the alert is dated before the test action")
    return problems
```

**Function `_alert_test`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Declares `problems` as a `list[str]` and stores the list `[]` in it.
- Stores the result of calling `re.search('test action at (' + TIMESTAMP.pattern + ')', text)` in `action`.
- Stores the result of calling `re.search('ALERT \\[[a-z-]+\\] (' + TIMESTAMP.pattern + ')', text)` in `alert`.
- If `action` is the same object as `None`:
  - Calls `problems.append("no 'test action at <timestamp>' line")`.
- If `alert` is the same object as `None`:
  - Calls `problems.append('no alert message with its timestamp: the alert did not fire')`.
- If `action` and `alert` and `alert.group(1)` is less than `action.group(1)`:
  - Calls `problems.append('the alert is dated before the test action')`.
- Gives back `problems`.

`src/notes_evidence/domain/evidence.py` lines 174 to 180:

```python
def _restore(text: str) -> list[str]:
    problems = []
    if "restore started " not in text or "restore finished " not in text:
        problems.append("no start and finish lines")
    if "result: verified" not in text:
        problems.append("the restore was not verified by row counts")
    return problems
```

**Function `_restore`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the list `[]` in `problems`.
- If `'restore started '` is not in `text` or `'restore finished '` is not in `text`:
  - Calls `problems.append('no start and finish lines')`.
- If `'result: verified'` is not in `text`:
  - Calls `problems.append('the restore was not verified by row counts')`.
- Gives back `problems`.

`src/notes_evidence/domain/evidence.py` lines 183 to 195:

```python
def _scan(text: str) -> list[str]:
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        return ["not JSON"]
    problems = []
    if not document.get("run_id"):
        problems.append("no run id: a scan report must name the CI run that produced it")
    if document.get("verdict") not in ("pass", "fail"):
        problems.append("no verdict")
    if document.get("verdict") == "fail":
        problems.append("the scan failed the blocking rule: the build would not have shipped")
    return problems
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.

**Function `_scan`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Tries:
  - Stores the result of calling `json.loads(text)` in `document`.
- If `json.JSONDecodeError` happens:
  - Gives back the list `['not JSON']`.
- Stores the list `[]` in `problems`.
- If not (`document.get('run_id')`):
  - Calls `problems.append('no run id: a scan report must name the CI run that produced it')`.
- If `document.get('verdict')` is not in `('pass', 'fail')`:
  - Calls `problems.append('no verdict')`.
- If `document.get('verdict')` equals `'fail'`:
  - Calls `problems.append('the scan failed the blocking rule: the build would not have shipped')`.
- Gives back `problems`.

`src/notes_evidence/domain/evidence.py` lines 198 to 206:

```python
def _review(text: str) -> list[str]:
    problems = [
        f"no '{label}' line" for label in ("Reviewer:", "Before:", "Removed:", "After:", "Proof:") if label not in text
    ]
    if "Removed: nothing" in text:
        problems.append("the review removed nothing: a review that finds nothing raises questions")
    if "still listed" in text:
        problems.append("a removed principal is still listed after the review")
    return problems
```

**Function `_review`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores a new list made by a loop (`[f"no '{label}' line" for label in ('Reviewer:', 'Before:', 'Removed:…`) in `problems`.
- If `'Removed: nothing'` is in `text`:
  - Calls `problems.append('the review removed nothing: a review that finds nothing raises questions')`.
- If `'still listed'` is in `text`:
  - Calls `problems.append('a removed principal is still listed after the review')`.
- Gives back `problems`.

`src/notes_evidence/domain/evidence.py` lines 209 to 230:

```python
def _cross_checks(controls: list[Control], files: Mapping[str, str]) -> list[Finding]:
    """The review's removed principals must be absent from the current access list."""
    review_files = [spec.file for control in controls for spec in control.evidence if spec.kind == "review"]
    access_files = [spec.file for control in controls for spec in control.evidence if spec.kind == "access_list"]
    found: list[Finding] = []
    for review_file in review_files:
        review = files.get(review_file, "")
        removed = re.findall(r"^Removed: (.+)\.$", review, re.MULTILINE)
        names = (
            {part.strip().split(" ")[-1] for part in removed[0].split(",")}
            if removed and removed[0] != "nothing"
            else set()
        )
        for access_file in access_files:
            present = {
                principal for block in parse_access_list(files.get(access_file, "")).values() for principal in block
            }
            for name in sorted(names & present):
                found.append(
                    error("EVD007", review_file, f"{name} was removed by the review but is still in {access_file}")
                )
    return found
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** On sets, `a | b` is the union (everything in either) and `a & b` the intersection (what both have).

**Function `_cross_checks`.** The review's removed principals must be absent from the current access list.

It takes: `controls` (a `list[Control]`); `files` (a `Mapping[str, str]`).

It gives back a `list[Finding]`.

Step by step:

- Stores a new list made by a loop (`[spec.file for control in controls for spec in control.evidence if sp…`) in `review_files`.
- Stores a new list made by a loop (`[spec.file for control in controls for spec in control.evidence if sp…`) in `access_files`.
- Declares `found` as a `list[Finding]` and stores the list `[]` in it.
- For each `review_file` in `review_files`:
  - Stores the result of calling `files.get(review_file, '')` in `review`.
  - Stores the result of calling `re.findall('^Removed: (.+)\\.$', review, re.MULTILINE)` in `removed`.
  - Stores `{part.strip().split(' ')[-1] for part i…` if `removed` and `removed[0]` is different from `'nothing'`, otherwise `set()` in `names`.
  - For each `access_file` in `access_files`:
    - Stores a new set made by a loop (`{principal for block in parse_access_list(files.get(access_file, ''))…`) in `present`.
    - For each `name` in the result of calling `sorted(names & present)`:
      - Calls `found.append(error('EVD007', review_file, f'{name} was removed by the review but is still in {access_file}'))`.
- Gives back `found`.

`src/notes_evidence/domain/evidence.py` lines 233 to 239:

```python
def framework_table(controls: list[Control]) -> str:
    """The overlap of the controls across the two frameworks, as Markdown."""
    lines = ["| Framework | Reference | Controls |", "| --- | --- | --- |"]
    for framework, refs in overlap(controls).items():
        for ref, ids in refs.items():
            lines.append(f"| {framework} | {ref} | {', '.join(ids)}{' (overlap)' if len(ids) > 1 else ''} |")
    return "\n".join(lines)
```

**Function `framework_table`.** The overlap of the controls across the two frameworks, as Markdown.

It takes: `controls` (a `list[Control]`).

It gives back a `str`.

Step by step:

- Stores the list `['| Framework | Reference | Controls |', '| --- | --- | --- |']` in `lines`.
- For each `(framework, refs)` in the result of calling `overlap(controls).items()`:
  - For each `(ref, ids)` in the result of calling `refs.items()`:
    - Calls `lines.append(f"| {framework} | {ref} | {', '.join(ids)}{(' (overlap)' if len(ids) > 1 else '')} |")`.
- Gives back the result of calling `'\n'.join(lines)`.

### `src/notes_evidence/domain/findings.py`

`src/notes_evidence/domain/findings.py` lines 1 to 6:

```python
"""The result of a rule: a finding with a code, a severity and the document it is about."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The result of a rule: a finding with a code, a severity and the document it is about.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass`.
- From `enum` it takes `Enum`.

`src/notes_evidence/domain/findings.py` lines 9 to 13:

```python
class Severity(Enum):
    """ERROR fails the check; WARNING is reported and does not."""

    ERROR = "error"
    WARNING = "warning"
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** An **Enum** is a class whose members are the only allowed values of a fixed set, such as `Severity.ERROR` and `Severity.WARNING`.

**Class `Severity`**, a kind of `Enum`. ERROR fails the check; WARNING is reported and does not.

Its parts:

- Class value `ERROR` set to the text `'error'`.
- Class value `WARNING` set to the text `'warning'`.

`src/notes_evidence/domain/findings.py` lines 16 to 23:

```python
@dataclass(frozen=True)
class Finding:
    """One rule violation. The code names the rule so a test and a reader can point at it."""

    code: str
    severity: Severity
    subject: str
    message: str
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Finding`**. One rule violation. The code names the rule so a test and a reader can point at it. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `code`: a `str`.
- Field `severity`: a `Severity`.
- Field `subject`: a `str`.
- Field `message`: a `str`.

`src/notes_evidence/domain/findings.py` lines 26 to 28:

```python
def error(code: str, subject: str, message: str) -> Finding:
    """Build an ERROR finding."""
    return Finding(code, Severity.ERROR, subject, message)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `error`.** Build an ERROR finding.

It takes: `code` (a `str`); `subject` (a `str`); `message` (a `str`).

It gives back a `Finding`.

Step by step:

- Gives back the result of calling `Finding(code, Severity.ERROR, subject, message)`.

`src/notes_evidence/domain/findings.py` lines 31 to 51:

```python
@dataclass(frozen=True)
class Report:
    """Every finding from one run, plus the subjects that were checked."""

    subjects: tuple[str, ...]
    findings: tuple[Finding, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        """The findings that fail the check."""
        return tuple(f for f in self.findings if f.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        """The findings that are reported without failing the check."""
        return tuple(f for f in self.findings if f.severity is Severity.WARNING)

    @property
    def ok(self) -> bool:
        """True when no finding is an error."""
        return not self.errors
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Class `Report`**. Every finding from one run, plus the subjects that were checked. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `subjects`: a `tuple[str, ...]`.
- Field `findings`: a `tuple[Finding, ...]`.

Its methods, in order:

**Method `errors` of class `Report`.** The findings that fail the check.

It gives back a `tuple[Finding, ...]`.

Decorators: `@property`.

Step by step:

- Gives back the result of calling `tuple((f for f in self.findings if f.severity is Severity.ERROR))`.

**Method `warnings` of class `Report`.** The findings that are reported without failing the check.

It gives back a `tuple[Finding, ...]`.

Decorators: `@property`.

Step by step:

- Gives back the result of calling `tuple((f for f in self.findings if f.severity is Severity.WARNING))`.

**Method `ok` of class `Report`.** True when no finding is an error.

It gives back a `bool`.

Decorators: `@property`.

Step by step:

- Gives back whether not (`self.errors`).

`src/notes_evidence/domain/findings.py` lines 54 to 56:

```python
def warning(code: str, subject: str, message: str) -> Finding:
    """Build a WARNING finding."""
    return Finding(code, Severity.WARNING, subject, message)
```

**Function `warning`.** Build a WARNING finding.

It takes: `code` (a `str`); `subject` (a `str`); `message` (a `str`).

It gives back a `Finding`.

Step by step:

- Gives back the result of calling `Finding(code, Severity.WARNING, subject, message)`.

### `src/notes_evidence/domain/notes.py`

`src/notes_evidence/domain/notes.py` lines 1 to 10:

```python
"""Users, notes and the validation of what a caller may send."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.errors import ValidationError
from notes_evidence.domain.roles import Role
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Users, notes and the validation of what a caller may send.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `re`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `datetime`.
- From `notes_evidence.domain.errors` it takes `ValidationError`.
- From `notes_evidence.domain.roles` it takes `Role`.

`src/notes_evidence/domain/notes.py` lines 12 to 15:

```python
USERNAME = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")
MIN_PASSWORD = 12
MAX_TITLE = 120
MAX_BODY = 10_000
```

> **In plain words.** A **regular expression** is a short pattern for text, such as `^## (.+)$` for "a line starting with ## ". `re.compile` prepares it once; `.match` tries it at the start of a string and returns a match object or `None`.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `re.compile('^[a-z][a-z0-9_-]{1,31}$')` in `USERNAME`.
- Stores the number `12` in `MIN_PASSWORD`.
- Stores the number `120` in `MAX_TITLE`.
- Stores the number `10000` in `MAX_BODY`.

`src/notes_evidence/domain/notes.py` lines 18 to 25:

```python
@dataclass(frozen=True)
class User:
    """An account. The password hash lives in the repository, never on this value."""

    id: int
    username: str
    role: Role
    active: bool
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `User`**. An account. The password hash lives in the repository, never on this value. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `id`: a `int`.
- Field `username`: a `str`.
- Field `role`: a `Role`.
- Field `active`: a `bool`.

`src/notes_evidence/domain/notes.py` lines 28 to 37:

```python
@dataclass(frozen=True)
class Note:
    """A customer note. It holds personal data, so the audit log never holds its content."""

    id: int
    owner_id: int
    title: str
    body: str
    created_at: datetime
    updated_at: datetime
```

**Class `Note`**. A customer note. It holds personal data, so the audit log never holds its content. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `id`: a `int`.
- Field `owner_id`: a `int`.
- Field `title`: a `str`.
- Field `body`: a `str`.
- Field `created_at`: a `datetime`.
- Field `updated_at`: a `datetime`.

`src/notes_evidence/domain/notes.py` lines 40 to 45:

```python
@dataclass(frozen=True)
class NoteInput:
    """A validated title and body."""

    title: str
    body: str
```

**Class `NoteInput`**. A validated title and body. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `title`: a `str`.
- Field `body`: a `str`.

`src/notes_evidence/domain/notes.py` lines 48 to 52:

```python
def validate_username(value: object) -> str:
    """A lower-case name of 2 to 32 characters starting with a letter."""
    if not isinstance(value, str) or not USERNAME.match(value):
        raise ValidationError("username", "2 to 32 lower-case letters, digits, '_' or '-', starting with a letter")
    return value
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

**Function `validate_username`.** A lower-case name of 2 to 32 characters starting with a letter.

It takes: `value` (a `object`).

It gives back a `str`.

Step by step:

- If not (`isinstance(value, str)`) or not (`USERNAME.match(value)`):
  - Stops here by raising `ValidationError('username', "2 to 32 lower-case letters, digits, '_' or '-', starting with a letter…`.
- Gives back `value`.

`src/notes_evidence/domain/notes.py` lines 55 to 59:

```python
def validate_password(value: object) -> str:
    """At least 12 characters."""
    if not isinstance(value, str) or len(value) < MIN_PASSWORD:
        raise ValidationError("password", f"at least {MIN_PASSWORD} characters")
    return value
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `validate_password`.** At least 12 characters.

It takes: `value` (a `object`).

It gives back a `str`.

Step by step:

- If not (`isinstance(value, str)`) or `len(value)` is less than `MIN_PASSWORD`:
  - Stops here by raising `ValidationError('password', f'at least {MIN_PASSWORD} characters')`.
- Gives back `value`.

`src/notes_evidence/domain/notes.py` lines 62 to 68:

```python
def validate_note(title: object, body: object) -> NoteInput:
    """A non-empty title of at most 120 characters and a body of at most 10,000."""
    if not isinstance(title, str) or not title.strip() or len(title) > MAX_TITLE:
        raise ValidationError("title", f"1 to {MAX_TITLE} characters")
    if not isinstance(body, str) or len(body) > MAX_BODY:
        raise ValidationError("body", f"at most {MAX_BODY} characters")
    return NoteInput(title.strip(), body)
```

**Function `validate_note`.** A non-empty title of at most 120 characters and a body of at most 10,000.

It takes: `title` (a `object`); `body` (a `object`).

It gives back a `NoteInput`.

Step by step:

- If not (`isinstance(title, str)`) or not (`title.strip()`) or `len(title)` is more than `MAX_TITLE`:
  - Stops here by raising `ValidationError('title', f'1 to {MAX_TITLE} characters')`.
- If not (`isinstance(body, str)`) or `len(body)` is more than `MAX_BODY`:
  - Stops here by raising `ValidationError('body', f'at most {MAX_BODY} characters')`.
- Gives back the result of calling `NoteInput(title.strip(), body)`.

### `src/notes_evidence/domain/restore.py`

`src/notes_evidence/domain/restore.py` lines 1 to 8:

```python
"""C4: a backup is a hope until it is restored. The artifact records the restore and how long it took."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.audit import format_timestamp
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** C4: a backup is a hope until it is restored. The artifact records the restore and how long it took.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `datetime`.
- From `notes_evidence.domain.audit` it takes `format_timestamp`.

`src/notes_evidence/domain/restore.py` lines 11 to 30:

```python
@dataclass(frozen=True)
class RestoreResult:
    """A restore into a scratch database, with the row counts at both ends."""

    backup_taken_at: datetime
    started_at: datetime
    finished_at: datetime
    table: str
    source_rows: int
    restored_rows: int

    @property
    def seconds(self) -> int:
        """Whole seconds the restore took."""
        return int((self.finished_at - self.started_at).total_seconds())

    @property
    def verified(self) -> bool:
        """True when the restored table has as many rows as the source had at backup time."""
        return self.source_rows == self.restored_rows
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `RestoreResult`**. A restore into a scratch database, with the row counts at both ends. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `backup_taken_at`: a `datetime`.
- Field `started_at`: a `datetime`.
- Field `finished_at`: a `datetime`.
- Field `table`: a `str`.
- Field `source_rows`: a `int`.
- Field `restored_rows`: a `int`.

Its methods, in order:

**Method `seconds` of class `RestoreResult`.** Whole seconds the restore took.

It gives back a `int`.

Decorators: `@property`.

Step by step:

- Gives back the result of calling `int((self.finished_at - self.started_at).total_seconds())`.

**Method `verified` of class `RestoreResult`.** True when the restored table has as many rows as the source had at backup time.

It gives back a `bool`.

Decorators: `@property`.

Step by step:

- Gives back whether `self.source_rows` equals `self.restored_rows`.

`src/notes_evidence/domain/restore.py` lines 33 to 36:

```python
def format_duration(seconds: int) -> str:
    """4 min 41 s, or 9 s under a minute."""
    minutes, rest = divmod(seconds, 60)
    return f"{minutes} min {rest} s" if minutes else f"{rest} s"
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `format_duration`.** 4 min 41 s, or 9 s under a minute.

It takes: `seconds` (a `int`).

It gives back a `str`.

Step by step:

- Unpacks the result of calling `divmod(seconds, 60)` into `(minutes, rest)`.
- Gives back `f'{minutes} min {rest} s'` if `minutes`, otherwise `f'{rest} s'`.

`src/notes_evidence/domain/restore.py` lines 39 to 49:

```python
def render_restore(result: RestoreResult) -> str:
    """The artifact, in the three lines the lesson shows, plus a verdict line."""
    verdict = "verified" if result.verified else "MISMATCH"
    return (
        f"restore started {format_timestamp(result.started_at)} "
        f"from backup {format_timestamp(result.backup_taken_at)}\n"
        f"restore finished {format_timestamp(result.finished_at)} ({format_duration(result.seconds)})\n"
        f"check: {result.table} table has {result.restored_rows:,} rows; "
        f"source had {result.source_rows:,} rows at backup time\n"
        f"result: {verdict}\n"
    )
```

**Function `render_restore`.** The artifact, in the three lines the lesson shows, plus a verdict line.

It takes: `result` (a `RestoreResult`).

It gives back a `str`.

Step by step:

- Stores `'verified'` if `result.verified`, otherwise `'MISMATCH'` in `verdict`.
- Gives back a text built with values filled in (`f'restore started {format_timestamp(result.started_at)} from backup {…`).

### `src/notes_evidence/domain/review.py`

`src/notes_evidence/domain/review.py` lines 1 to 9:

```python
"""C6: the access review. Every principal gets a decision, leavers go, and the record shows before and after."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from notes_evidence.domain.access import AccessList
from notes_evidence.domain.findings import Finding, error
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** C6: the access review. Every principal gets a decision, leavers go, and the record shows before and after.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `date`.
- From `notes_evidence.domain.access` it takes `AccessList`.
- From `notes_evidence.domain.findings` it takes `Finding, error`.

`src/notes_evidence/domain/review.py` lines 12 to 18:

```python
@dataclass(frozen=True)
class Person:
    """Someone who may hold access. `left_on` is set for a leaver."""

    name: str
    title: str
    left_on: date | None = None
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Person`**. Someone who may hold access. `left_on` is set for a leaver. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `name`: a `str`.
- Field `title`: a `str`.
- Field `left_on`: a `date | None`, default `None`.

`src/notes_evidence/domain/review.py` lines 21 to 28:

```python
@dataclass(frozen=True)
class Decision:
    """The reviewer's answer for one principal in one system."""

    system: str
    principal: str
    keep: bool
    reason: str
```

**Class `Decision`**. The reviewer's answer for one principal in one system. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `system`: a `str`.
- Field `principal`: a `str`.
- Field `keep`: a `bool`.
- Field `reason`: a `str`.

`src/notes_evidence/domain/review.py` lines 31 to 38:

```python
@dataclass(frozen=True)
class ReviewRequest:
    """The review as the reviewer filed it."""

    reviewer: str
    reviewed_on: date
    ticket: str
    decisions: tuple[Decision, ...]
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Class `ReviewRequest`**. The review as the reviewer filed it. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `reviewer`: a `str`.
- Field `reviewed_on`: a `date`.
- Field `ticket`: a `str`.
- Field `decisions`: a `tuple[Decision, ...]`.

`src/notes_evidence/domain/review.py` lines 41 to 63:

```python
def check_review(before: AccessList, request: ReviewRequest, people: dict[str, Person]) -> list[Finding]:
    """ARV001 to ARV003: complete, justified, and no leaver kept."""
    found: list[Finding] = []
    decided = {(d.system, d.principal): d for d in request.decisions}
    for entry in before.entries:
        decision = decided.get((entry.system, entry.principal))
        if decision is None:
            found.append(
                error(
                    "ARV001",
                    f"{entry.system}: {entry.principal}",
                    "no decision: an access review decides every principal",
                )
            )
            continue
        if not decision.reason.strip():
            found.append(error("ARV002", f"{entry.system}: {entry.principal}", "a decision needs its reason"))
        person = people.get(entry.principal)
        if person is not None and person.left_on is not None and decision.keep:
            found.append(error("ARV003", f"{entry.system}: {entry.principal}", f"left on {person.left_on}, yet kept"))
    if not request.ticket.strip():
        found.append(error("ARV002", "review", "the review needs a ticket the removals are recorded in"))
    return found
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `check_review`.** ARV001 to ARV003: complete, justified, and no leaver kept.

It takes: `before` (a `AccessList`); `request` (a `ReviewRequest`); `people` (a `dict[str, Person]`).

It gives back a `list[Finding]`.

Step by step:

- Declares `found` as a `list[Finding]` and stores the list `[]` in it.
- Stores a new dictionary made by a loop (`{(d.system, d.principal): d for d in request.decisions}`) in `decided`.
- For each `entry` in `before.entries`:
  - Stores the result of calling `decided.get((entry.system, entry.principal))` in `decision`.
  - If `decision` is the same object as `None`:
    - Calls `found.append(error('ARV001', f'{entry.system}: {entry.principal}', 'no decision: an access review decides eve…`.
    - Skips to the next item (`continue`).
  - If not (`decision.reason.strip()`):
    - Calls `found.append(error('ARV002', f'{entry.system}: {entry.principal}', 'a decision needs its reason'))`.
  - Stores the result of calling `people.get(entry.principal)` in `person`.
  - If `person` is not the same object as `None` and `person.left_on` is not the same object as `None` and `decision.keep`:
    - Calls `found.append(error('ARV003', f'{entry.system}: {entry.principal}', f'left on {person.left_on}, yet kept'))`.
- If not (`request.ticket.strip()`):
  - Calls `found.append(error('ARV002', 'review', 'the review needs a ticket the removals are recorded in'))`.
- Gives back `found`.

`src/notes_evidence/domain/review.py` lines 66 to 87:

```python
def render_review(before: AccessList, after: AccessList, request: ReviewRequest) -> str:
    """The artifact: reviewer, date, before counts, what was removed and why, and the re-run proof."""
    removed = [d for d in request.decisions if not d.keep]
    names = ", ".join(f"{d.system.split(' (')[0]} {d.principal}" for d in removed) or "nothing"
    reasons = "\n".join(f"  - {d.principal} ({d.system.split(' (')[0]}): {d.reason}" for d in removed)
    before_counts = ", ".join(f"{count} {system.split(' (')[0]}" for system, count in before.counts().items())
    after_counts = ", ".join(f"{count} {system.split(' (')[0]}" for system, count in after.counts().items())
    still = [
        d.principal for d in removed if any(e.principal == d.principal and e.system == d.system for e in after.entries)
    ]
    proof = "re-ran the C1 command; " + (
        ", ".join(still) + " is still listed" if still else "none of the removed principals is listed"
    )
    lines = [
        f"Reviewer: {request.reviewer}. Date: {request.reviewed_on.isoformat()}. Ticket: {request.ticket}.",
        f"Before: {before_counts}.",
        f"Removed: {names}.",
    ]
    if reasons:
        lines.append(reasons)
    lines += [f"After: {after_counts}.", f"Proof: {proof}."]
    return "\n".join(lines) + "\n"
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `render_review`.** The artifact: reviewer, date, before counts, what was removed and why, and the re-run proof.

It takes: `before` (a `AccessList`); `after` (a `AccessList`); `request` (a `ReviewRequest`).

It gives back a `str`.

Step by step:

- Stores a new list made by a loop (`[d for d in request.decisions if not d.keep]`) in `removed`.
- Stores whether `', '.join((f"{d.system.split(' (')[0]} {d.principal}" for d in remove…` or `'nothing'` in `names`.
- Stores the result of calling `'\n'.join((f" - {d.principal} ({d.system.split(' (')[0]}): {d.reason}" for d in removed))` in `reasons`.
- Stores the result of calling `', '.join((f"{count} {system.split(' (')[0]}" for system, count in before.counts().items(…` in `before_counts`.
- Stores the result of calling `', '.join((f"{count} {system.split(' (')[0]}" for system, count in after.counts().items()…` in `after_counts`.
- Stores a new list made by a loop (`[d.principal for d in removed if any((e.principal == d.principal and …`) in `still`.
- Stores `'re-ran the C1 command; ' + (', '.join(still) + ' is still listed' if still els…` in `proof`.
- Stores the list `[f'Reviewer: {request.reviewer}. Date: {request.reviewed_on.isoformat…` in `lines`.
- If `reasons`:
  - Calls `lines.append(reasons)`.
- Adds the list `[f'After: {after_counts}.', f'Proof: {proof}.']` to `lines`.
- Gives back `'\n'.join(lines) + '\n'`.

### `src/notes_evidence/domain/roles.py`

`src/notes_evidence/domain/roles.py` lines 1 to 5:

```python
"""Roles and what each may do: least privilege as a table that tests can read."""

from __future__ import annotations

from enum import Enum
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Roles and what each may do: least privilege as a table that tests can read.

Imports:

- From `__future__` it takes `annotations`.
- From `enum` it takes `Enum`.

`src/notes_evidence/domain/roles.py` lines 8 to 13:

```python
class Role(Enum):
    """member writes their own notes; readonly reads every note and writes none; admin does everything."""

    ADMIN = "admin"
    MEMBER = "member"
    READONLY = "readonly"
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** An **Enum** is a class whose members are the only allowed values of a fixed set, such as `Severity.ERROR` and `Severity.WARNING`.

**Class `Role`**, a kind of `Enum`. member writes their own notes; readonly reads every note and writes none; admin does everything.

Its parts:

- Class value `ADMIN` set to the text `'admin'`.
- Class value `MEMBER` set to the text `'member'`.
- Class value `READONLY` set to the text `'readonly'`.

`src/notes_evidence/domain/roles.py` lines 16 to 23:

```python
class Permission(Enum):
    """What a request needs."""

    READ_OWN = "read_own"
    WRITE_OWN = "write_own"
    READ_ANY = "read_any"
    WRITE_ANY = "write_any"
    GRANT_ROLE = "grant_role"
```

**Class `Permission`**, a kind of `Enum`. What a request needs.

Its parts:

- Class value `READ_OWN` set to the text `'read_own'`.
- Class value `WRITE_OWN` set to the text `'write_own'`.
- Class value `READ_ANY` set to the text `'read_any'`.
- Class value `WRITE_ANY` set to the text `'write_any'`.
- Class value `GRANT_ROLE` set to the text `'grant_role'`.

`src/notes_evidence/domain/roles.py` lines 26 to 30:

```python
GRANTS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.MEMBER: frozenset({Permission.READ_OWN, Permission.WRITE_OWN}),
    Role.READONLY: frozenset({Permission.READ_OWN, Permission.READ_ANY}),
}
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.

These module-level lines:

- Declares `GRANTS` as a `dict[Role, frozenset[Permission]]` and stores the dictionary `{Role.ADMIN: frozenset(Permission), Role.MEMBER: frozenset({Permissio…` in it.

`src/notes_evidence/domain/roles.py` lines 33 to 35:

```python
def allowed(role: Role, permission: Permission) -> bool:
    """True when the role holds the permission."""
    return permission in GRANTS[role]
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `allowed`.** True when the role holds the permission.

It takes: `role` (a `Role`); `permission` (a `Permission`).

It gives back a `bool`.

Step by step:

- Gives back whether `permission` is in `GRANTS[role]`.

### `src/notes_evidence/domain/scan.py`

`src/notes_evidence/domain/scan.py` lines 1 to 9:

```python
"""C5: the dependency scan, as a report a build produced and a rule that decides whether it blocks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.audit import format_timestamp
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** C5: the dependency scan, as a report a build produced and a rule that decides whether it blocks.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `datetime`.
- From `notes_evidence.domain.audit` it takes `format_timestamp`.

`src/notes_evidence/domain/scan.py` lines 11 to 11:

```python
BLOCKING_RULE = "any known vulnerability with a fixed version available fails the build"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'any known vulnerability with a fixed version available fai…` in `BLOCKING_RULE`.

`src/notes_evidence/domain/scan.py` lines 14 to 26:

```python
@dataclass(frozen=True)
class ScanFinding:
    """A vulnerable package version and the versions that fix it."""

    package: str
    version: str
    vulnerability: str
    fix_versions: tuple[str, ...]

    @property
    def blocking(self) -> bool:
        """True when a fix exists: the rule says upgrade, not accept."""
        return bool(self.fix_versions)
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `ScanFinding`**. A vulnerable package version and the versions that fix it. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `package`: a `str`.
- Field `version`: a `str`.
- Field `vulnerability`: a `str`.
- Field `fix_versions`: a `tuple[str, ...]`.

Its methods, in order:

**Method `blocking` of class `ScanFinding`.** True when a fix exists: the rule says upgrade, not accept.

It gives back a `bool`.

Decorators: `@property`.

Step by step:

- Gives back the result of calling `bool(self.fix_versions)`.

`src/notes_evidence/domain/scan.py` lines 29 to 39:

```python
@dataclass(frozen=True)
class ScanReport:
    """One scan run: who ran it, on what, when, and what it found."""

    run_id: str
    tool: str
    tool_version: str
    scanned_at: datetime
    target: str
    packages_scanned: int
    findings: tuple[ScanFinding, ...]
```

**Class `ScanReport`**. One scan run: who ran it, on what, when, and what it found. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `run_id`: a `str`.
- Field `tool`: a `str`.
- Field `tool_version`: a `str`.
- Field `scanned_at`: a `datetime`.
- Field `target`: a `str`.
- Field `packages_scanned`: a `int`.
- Field `findings`: a `tuple[ScanFinding, ...]`.

`src/notes_evidence/domain/scan.py` lines 41 to 44:

```python
    @property
    def verdict(self) -> str:
        """pass or fail under the blocking rule."""
        return "fail" if any(finding.blocking for finding in self.findings) else "pass"
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Method `verdict` of class `ScanReport`.** pass or fail under the blocking rule.

It gives back a `str`.

Decorators: `@property`.

Step by step:

- Gives back `'fail'` if `any((finding.blocking for finding in self.findings))`, otherwise `'pass'`.

`src/notes_evidence/domain/scan.py` lines 46 to 67:

```python
    def to_json(self) -> str:
        """The artifact: stable keys, sorted findings."""
        document = {
            "run_id": self.run_id,
            "tool": self.tool,
            "tool_version": self.tool_version,
            "scanned_at": format_timestamp(self.scanned_at),
            "target": self.target,
            "packages_scanned": self.packages_scanned,
            "blocking_rule": BLOCKING_RULE,
            "verdict": self.verdict,
            "findings": [
                {
                    "package": f.package,
                    "version": f.version,
                    "vulnerability": f.vulnerability,
                    "fix_versions": list(f.fix_versions),
                }
                for f in sorted(self.findings, key=lambda item: (item.package, item.vulnerability))
            ],
        }
        return json.dumps(document, indent=2) + "\n"
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Method `to_json` of class `ScanReport`.** The artifact: stable keys, sorted findings.

It gives back a `str`.

Step by step:

- Stores the dictionary `{'run_id': self.run_id, 'tool': self.tool, 'tool_version': self.tool_…` in `document`.
- Gives back `json.dumps(document, indent=2) + '\n'`.

`src/notes_evidence/domain/scan.py` lines 70 to 79:

```python
def parse_pip_audit(raw: str) -> tuple[int, tuple[ScanFinding, ...]]:
    """Packages scanned and findings from `pip-audit -f json` output."""
    data = json.loads(raw)
    dependencies = data["dependencies"] if isinstance(data, dict) else data
    findings = tuple(
        ScanFinding(dep["name"], dep.get("version", ""), vuln["id"], tuple(vuln.get("fix_versions", [])))
        for dep in dependencies
        for vuln in dep.get("vulns", [])
    )
    return len(dependencies), findings
```

**Function `parse_pip_audit`.** Packages scanned and findings from `pip-audit -f json` output.

It takes: `raw` (a `str`).

It gives back a `tuple[int, tuple[ScanFinding, ...]]`.

Step by step:

- Stores the result of calling `json.loads(raw)` in `data`.
- Stores `data['dependencies']` if `isinstance(data, dict)`, otherwise `data` in `dependencies`.
- Stores the result of calling `tuple((ScanFinding(dep['name'], dep.get('version', ''), vuln['id'], tuple(vuln.get('fix_v…` in `findings`.
- Gives back the tuple `(len(dependencies), findings)`.

## Try it yourself

```bash
.venv/bin/python -c "import notes_evidence.domain.access; print(notes_evidence.domain.access.__doc__)"
```
Prints the module's description: `C1: who has which access, in which system. Generated from the systems, never typed.`

```bash
.venv/bin/python -c "import notes_evidence.domain.alerts; print(notes_evidence.domain.alerts.__doc__)"
```
Prints the module's description: `Alert rules over the audit stream: the events that need a person.`

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check src/notes_evidence/__init__.py src/notes_evidence/domain/__init__.py src/notes_evidence/domain/access.py src/notes_evidence/domain/alerts.py src/notes_evidence/domain/audit.py src/notes_evidence/domain/changes.py
```
Prints `All checks passed!`.

```bash
grep -c "^def \|^class \|    def " src/notes_evidence/domain/access.py
```
Counts the functions, methods and classes in `src/notes_evidence/domain/access.py`.

## Mistakes people make

- Reading a file or printing from a domain function. Input and output belong to the outer layers.
- Importing a framework (Flask, psycopg) here; the contract in `pyproject.toml` forbids it.
- Changing a value in place. The domain uses frozen values, so a change makes a new value.

## Check yourself

1. What is `AccessEntry` for?
   **Answer:** One principal in one system. `level` is empty where the system has only members (cloud users).
2. What is `AccessList` for?
   **Answer:** Every entry of every system, with the moment it was generated.
3. What is `render_access_list` for?
   **Answer:** The artifact: a dated header and one block per system, `principal<TAB>level` per line.
4. What is `parse_access_list` for?
   **Answer:** Principals per system from a rendered list; empty when the text is not an access list.
5. What is `Alert` for?
   **Answer:** An alert message with the time of the event that triggered it.

## Further reading

- Python 3.12 tutorial, classes: <https://docs.python.org/3.12/tutorial/classes.html>
- Python 3.12 language reference: <https://docs.python.org/3.12/reference/>
- Type hints: <https://docs.python.org/3.12/library/typing.html>
