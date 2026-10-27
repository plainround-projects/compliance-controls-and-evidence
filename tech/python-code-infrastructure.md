# Infrastructure layer code

## What it is

The adapters: the code that really reads files, talks to a database or a network, and reads the environment. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

This is where the repository's infrastructure work happens. Reading it file by file, with every line explained, is how a reader sees the work that was done.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/infrastructure/__init__.py` | 1 lines. infrastructure layer. |
| `src/notes_evidence/infrastructure/alerting.py` | 15 lines. Where alerts go in this build: the log stream and a file, the stand-in for a chat channel or a pager. |
| `src/notes_evidence/infrastructure/backup.py` | 58 lines. C4: a pg_dump backup and a pg_restore into a scratch database, both run inside the database container. |
| `src/notes_evidence/infrastructure/catalog.py` | 84 lines. The control matrix and its companions, read from TOML files under `controls/`. |
| `src/notes_evidence/infrastructure/clock.py` | 8 lines. The system clock, behind the Clock port. |
| `src/notes_evidence/infrastructure/evidence_store.py` | 58 lines. The evidence folder on disk, with a manifest that records who produced each file, when, and its hash. |
| `src/notes_evidence/infrastructure/logging_setup.py` | 26 lines. Structured JSON logs on standard output: level, time, logger, message and a few safe fields. No secrets. |
| `src/notes_evidence/infrastructure/passwords.py` | 27 lines. Password hashing with scrypt from the standard library: salted, slow, compared in constant time. |
| `src/notes_evidence/infrastructure/postgres.py` | 218 lines. PostgreSQL adapters: the notes service's repositories (as app_rw) and the catalog reader (as an administrator… |
| `src/notes_evidence/infrastructure/scanner.py` | 38 lines. C5: run pip-audit over the locked dependencies and wrap its JSON with the run that produced it. |
| `src/notes_evidence/infrastructure/settings.py` | 69 lines. Settings from the environment, validated once at start-up (twelve-factor). Secrets come only from here. |
| `src/notes_evidence/infrastructure/sources.py` | 97 lines. Where C1 and C2 read from: the hosting platform and the cloud account, as files or as `gh` and `aws` commands. |
| `src/notes_evidence/infrastructure/tokens.py` | 25 lines. Signed, expiring session tokens: `user_id.expires.signature`, HMAC-SHA256 over the first two parts. |

## How it works underneath

Each adapter implements a port from the application layer using a real technology (the file system, SQLite or PostgreSQL, HTTP, the environment). They are kept thin, so that swapping one changes nothing above. Tests exercise them on real temporary files or a real database.

## Walkthrough of this repository's use

### `src/notes_evidence/infrastructure/__init__.py`

`src/notes_evidence/infrastructure/__init__.py` lines 1 to 1:

```python
"""infrastructure layer."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** infrastructure layer.

### `src/notes_evidence/infrastructure/alerting.py`

`src/notes_evidence/infrastructure/alerting.py` lines 1 to 6:

```python
"""Where alerts go in this build: the log stream and a file, the stand-in for a chat channel or a pager."""

from __future__ import annotations

import logging
from pathlib import Path
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Where alerts go in this build: the log stream and a file, the stand-in for a chat channel or a pager.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `logging`.
- From `pathlib` it takes `Path`.

`src/notes_evidence/infrastructure/alerting.py` lines 8 to 8:

```python
logger = logging.getLogger("notes.alerts")
```

These module-level lines:

- Stores the result of calling `logging.getLogger('notes.alerts')` in `logger`.

`src/notes_evidence/infrastructure/alerting.py` lines 11 to 22:

```python
class FileAlertSink:
    """Appends each alert message to a file and logs it at WARNING."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def send(self, message: str) -> None:
        """Deliver one alert."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(message + "\n")
        logger.warning("%s", message)
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Class `FileAlertSink`**. Appends each alert message to a file and logs it at WARNING.

Its methods, in order:

**Method `__init__` of class `FileAlertSink`.**

It takes: `path` (a `Path`).

It gives back a `None`.

Step by step:

- Stores `path` in `self._path`.

**Method `send` of class `FileAlertSink`.** Deliver one alert.

It takes: `message` (a `str`).

It gives back a `None`.

Step by step:

- Calls `self._path.parent.mkdir(parents=True, exist_ok=True)`.
- Inside a `with` block that opens `self._path.open('a', encoding='utf-8')` (named `stream`):
  - Calls `stream.write(message + '\n')`.
- Calls `logger.warning('%s', message)`.

### `src/notes_evidence/infrastructure/backup.py`

`src/notes_evidence/infrastructure/backup.py` lines 1 to 7:

```python
"""C4: a pg_dump backup and a pg_restore into a scratch database, both run inside the database container."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** C4: a pg_dump backup and a pg_restore into a scratch database, both run inside the database container.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `subprocess`.
- From `collections.abc` it takes `Callable`.
- From `datetime` it takes `UTC, datetime`.

`src/notes_evidence/infrastructure/backup.py` lines 9 to 10:

```python
SCRATCH = "notes_restore_test"
Execute = Callable[[list[str], bytes | None], bytes]
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** On sets, `a | b` is the union (everything in either) and `a & b` the intersection (what both have).
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'notes_restore_test'` in `SCRATCH`.
- Stores `Callable[[list[str], bytes | None], bytes]` in `Execute`.

`src/notes_evidence/infrastructure/backup.py` lines 13 to 14:

```python
class BackupError(RuntimeError):
    """pg_dump, pg_restore or psql failed."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `BackupError`**, a kind of `RuntimeError`. pg_dump, pg_restore or psql failed.

`src/notes_evidence/infrastructure/backup.py` lines 17 to 27:

```python
def run_in_container(argv: list[str], stdin: bytes | None) -> bytes:
    """Run a command, optionally feeding stdin, with a timeout; a non-zero exit is a BackupError."""
    try:
        done = subprocess.run(argv, input=stdin, capture_output=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as problem:
        raise BackupError(f"{argv[0]}: {problem}") from None
    if done.returncode != 0:
        raise BackupError(
            f"{' '.join(argv[:6])} exited {done.returncode}: {done.stderr.decode(errors='replace').strip()[:300]}"
        )
    return done.stdout
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `run_in_container`.** Run a command, optionally feeding stdin, with a timeout; a non-zero exit is a BackupError.

It takes: `argv` (a `list[str]`); `stdin` (a `bytes | None`).

It gives back a `bytes`.

Step by step:

- Tries:
  - Stores the result of calling `subprocess.run(argv, input=stdin, capture_output=True, timeout=300, check=False)` in `done`.
- If `(OSError, subprocess.TimeoutExpired)` happens (named `problem`):
  - Stops here by raising `BackupError(f'{argv[0]}: {problem}')` (`from None` hides the earlier error).
- If `done.returncode` is different from `0`:
  - Stops here by raising `BackupError(f"{' '.join(argv[:6])} exited {done.returncode}: {done.stderr.decode(errors='replace').…`.
- Gives back `done.stdout`.

`src/notes_evidence/infrastructure/backup.py` lines 30 to 31:

```python
class DockerBackupRunner:
    """Backs up the database and restores it into `notes_restore_test`, then drops the scratch database."""
```

**Class `DockerBackupRunner`**. Backs up the database and restores it into `notes_restore_test`, then drops the scratch database.

`src/notes_evidence/infrastructure/backup.py` lines 33 to 39:

```python
    def __init__(self, prefix: tuple[str, ...], user: str, database: str, execute: Execute = run_in_container) -> None:
        self._prefix = list(prefix)
        self._user = user
        self._database = database
        self._execute = execute
        self._dump: bytes = b""
        self._count_at_backup = 0
```

**Method `__init__` of class `DockerBackupRunner`.**

It takes: `prefix` (a `tuple[str, ...]`); `user` (a `str`); `database` (a `str`); `execute` (a `Execute`), default `run_in_container`.

It gives back a `None`.

Step by step:

- Stores the result of calling `list(prefix)` in `self._prefix`.
- Stores `user` in `self._user`.
- Stores `database` in `self._database`.
- Stores `execute` in `self._execute`.
- Declares `self._dump` as a `bytes` and stores the number `b''` in it.
- Stores the number `0` in `self._count_at_backup`.

`src/notes_evidence/infrastructure/backup.py` lines 41 to 48:

```python
    def backup(self) -> datetime:
        """pg_dump in custom format; remember the row count at the same moment."""
        taken = datetime.now(UTC)
        self._count_at_backup = self._count(self._database, "notes")
        self._dump = self._execute(
            [*self._prefix, "pg_dump", "-U", self._user, "-d", self._database, "--format=custom"], None
        )
        return taken
```

> **In plain words.** `*items` **unpacks** a sequence into separate values; `**options` does the same for a dictionary's keys and values.

**Method `backup` of class `DockerBackupRunner`.** pg_dump in custom format; remember the row count at the same moment.

It gives back a `datetime`.

Step by step:

- Stores the result of calling `datetime.now(UTC)` in `taken`.
- Stores the result of calling `self._count(self._database, 'notes')` in `self._count_at_backup`.
- Stores the result of calling `self._execute([*self._prefix, 'pg_dump', '-U', self._user, '-d', self._database, '--forma…` in `self._dump`.
- Gives back `taken`.

`src/notes_evidence/infrastructure/backup.py` lines 50 to 61:

```python
    def restore_and_count(self, table: str) -> tuple[int, int]:
        """Restore the dump into a fresh scratch database and count the rows there."""
        self._psql("postgres", f"DROP DATABASE IF EXISTS {SCRATCH}")
        self._psql("postgres", f"CREATE DATABASE {SCRATCH}")
        try:
            self._execute(
                [*self._prefix, "pg_restore", "-U", self._user, "-d", SCRATCH, "--no-owner", "--no-privileges"],
                self._dump,
            )
            return self._count_at_backup, self._count(SCRATCH, table)
        finally:
            self._psql("postgres", f"DROP DATABASE IF EXISTS {SCRATCH}")
```

**Method `restore_and_count` of class `DockerBackupRunner`.** Restore the dump into a fresh scratch database and count the rows there.

It takes: `table` (a `str`).

It gives back a `tuple[int, int]`.

Step by step:

- Calls `self._psql('postgres', f'DROP DATABASE IF EXISTS {SCRATCH}')`.
- Calls `self._psql('postgres', f'CREATE DATABASE {SCRATCH}')`.
- Tries:
  - Calls `self._execute([*self._prefix, 'pg_restore', '-U', self._user, '-d', SCRATCH, '--no-owner', '--no-privileges']…`.
  - Gives back the tuple `(self._count_at_backup, self._count(SCRATCH, table))`.
- Always, at the end:
  - Calls `self._psql('postgres', f'DROP DATABASE IF EXISTS {SCRATCH}')`.

`src/notes_evidence/infrastructure/backup.py` lines 63 to 67:

```python
    def _psql(self, database: str, sql: str) -> str:
        out = self._execute(
            [*self._prefix, "psql", "-U", self._user, "-d", database, "-At", "-v", "ON_ERROR_STOP=1", "-c", sql], None
        )
        return out.decode().strip()
```

**Method `_psql` of class `DockerBackupRunner`.**

It takes: `database` (a `str`); `sql` (a `str`).

It gives back a `str`.

Step by step:

- Stores the result of calling `self._execute([*self._prefix, 'psql', '-U', self._user, '-d', database, '-At', '-v', 'ON_…` in `out`.
- Gives back the result of calling `out.decode().strip()`.

`src/notes_evidence/infrastructure/backup.py` lines 69 to 72:

```python
    def _count(self, database: str, table: str) -> int:
        if table != "notes":
            raise BackupError(f"unsupported table {table!r}")
        return int(self._psql(database, "SELECT count(*) FROM notes"))
```

**Method `_count` of class `DockerBackupRunner`.**

It takes: `database` (a `str`); `table` (a `str`).

It gives back a `int`.

Step by step:

- If `table` is different from `'notes'`:
  - Stops here by raising `BackupError(f'unsupported table {table!r}')`.
- Gives back the result of calling `int(self._psql(database, 'SELECT count(*) FROM notes'))`.

### `src/notes_evidence/infrastructure/catalog.py`

`src/notes_evidence/infrastructure/catalog.py` lines 1 to 11:

```python
"""The control matrix and its companions, read from TOML files under `controls/`."""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path
from typing import Any

from notes_evidence.domain.controls import FRAMEWORKS, KINDS, Control, EvidenceSpec, Gap, RecordedException
from notes_evidence.domain.review import Decision, Person, ReviewRequest
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The control matrix and its companions, read from TOML files under `controls/`.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `tomllib`.
- From `datetime` it takes `date`.
- From `pathlib` it takes `Path`.
- From `typing` it takes `Any`.
- From `notes_evidence.domain.controls` it takes `FRAMEWORKS, KINDS, Control, EvidenceSpec, Gap, RecordedException`.
- From `notes_evidence.domain.review` it takes `Decision, Person, ReviewRequest`.

`src/notes_evidence/infrastructure/catalog.py` lines 14 to 15:

```python
class CatalogError(ValueError):
    """A controls file is missing a field or holds an unknown value."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `CatalogError`**, a kind of `ValueError`. A controls file is missing a field or holds an unknown value.

`src/notes_evidence/infrastructure/catalog.py` lines 18 to 24:

```python
def _load(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CatalogError(f"{path} does not exist") from None
    except tomllib.TOMLDecodeError as problem:
        raise CatalogError(f"{path} is not valid TOML: {problem}") from None
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `_load`.**

It takes: `path` (a `Path`).

It gives back a `dict[str, Any]`.

Step by step:

- Tries:
  - Gives back the result of calling `tomllib.loads(path.read_text(encoding='utf-8'))`.
- If `FileNotFoundError` happens:
  - Stops here by raising `CatalogError(f'{path} does not exist')` (`from None` hides the earlier error).
- If `tomllib.TOMLDecodeError` happens (named `problem`):
  - Stops here by raising `CatalogError(f'{path} is not valid TOML: {problem}')` (`from None` hides the earlier error).

`src/notes_evidence/infrastructure/catalog.py` lines 27 to 28:

```python
def _date(raw: object) -> date | None:
    return raw if isinstance(raw, date) else None
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `_date`.**

It takes: `raw` (a `object`).

It gives back a `date | None`.

Step by step:

- Gives back `raw` if `isinstance(raw, date)`, otherwise `None`.

`src/notes_evidence/infrastructure/catalog.py` lines 31 to 32:

```python
class TomlCatalog:
    """Reads `controls.toml`, `exceptions.toml`, `gaps.toml`, `people.toml` and `access-review.toml` from one folder."""
```

**Class `TomlCatalog`**. Reads `controls.toml`, `exceptions.toml`, `gaps.toml`, `people.toml` and `access-review.toml` from one folder.

`src/notes_evidence/infrastructure/catalog.py` lines 34 to 36:

```python
    def __init__(self, controls_file: Path) -> None:
        self._dir = controls_file.parent
        self._controls_file = controls_file
```

**Method `__init__` of class `TomlCatalog`.**

It takes: `controls_file` (a `Path`).

It gives back a `None`.

Step by step:

- Stores `controls_file.parent` in `self._dir`.
- Stores `controls_file` in `self._controls_file`.

`src/notes_evidence/infrastructure/catalog.py` lines 38 to 61:

```python
    def controls(self) -> list[Control]:
        """The controls with their evidence specs; an unknown evidence kind is an error."""
        found: list[Control] = []
        for item in _load(self._controls_file).get("control", []):
            try:
                specs = tuple(
                    EvidenceSpec(e["file"], e["kind"], e["proves"], e["period"], int(e["refresh_days"]), e["refreshed"])
                    for e in item.get("evidence", [])
                )
                if bad := [spec.kind for spec in specs if spec.kind not in KINDS]:
                    raise CatalogError(f"{item['id']}: unknown evidence kind {bad[0]!r}")
                found.append(
                    Control(
                        item["id"],
                        item["name"],
                        item["requires"],
                        item["where"],
                        {name: tuple(item.get(name, ())) for name in FRAMEWORKS},
                        specs,
                    )
                )
            except KeyError as missing:
                raise CatalogError(f"{self._controls_file}: control is missing {missing}") from None
        return found
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** The **walrus operator** `:=` stores a value in a name and uses it in the same expression.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Method `controls` of class `TomlCatalog`.** The controls with their evidence specs; an unknown evidence kind is an error.

It gives back a `list[Control]`.

Step by step:

- Declares `found` as a `list[Control]` and stores the list `[]` in it.
- For each `item` in the result of calling `_load(self._controls_file).get('control', [])`:
  - Tries:
    - Stores the result of calling `tuple((EvidenceSpec(e['file'], e['kind'], e['proves'], e['period'], int(e['refresh_days']…` in `specs`.
    - If `(bad := [spec.kind for spec in specs if spec.kind not in KINDS])`:
      - Stops here by raising `CatalogError(f"{item['id']}: unknown evidence kind {bad[0]!r}")`.
    - Calls `found.append(Control(item['id'], item['name'], item['requires'], item['where'], {name: tuple(item.get(name, (…`.
  - If `KeyError` happens (named `missing`):
    - Stops here by raising `CatalogError(f'{self._controls_file}: control is missing {missing}')` (`from None` hides the earlier error).
- Gives back `found`.

`src/notes_evidence/infrastructure/catalog.py` lines 63 to 68:

```python
    def exceptions(self) -> list[RecordedException]:
        """Known deviations from `exceptions.toml`."""
        return [
            RecordedException(e["id"], e["control"], e.get("change"), e["description"], e.get("followup", ""))
            for e in _load(self._dir / "exceptions.toml").get("exception", [])
        ]
```

**Method `exceptions` of class `TomlCatalog`.** Known deviations from `exceptions.toml`.

It gives back a `list[RecordedException]`.

Step by step:

- Gives back a new list made by a loop (`[RecordedException(e['id'], e['control'], e.get('change'), e['descrip…`).

`src/notes_evidence/infrastructure/catalog.py` lines 70 to 75:

```python
    def gaps(self) -> list[Gap]:
        """Tracked gaps from `gaps.toml`."""
        return [
            Gap(g["control"], g.get("reason", ""), g.get("ticket", ""), _date(g.get("due")))
            for g in _load(self._dir / "gaps.toml").get("gap", [])
        ]
```

**Method `gaps` of class `TomlCatalog`.** Tracked gaps from `gaps.toml`.

It gives back a `list[Gap]`.

Step by step:

- Gives back a new list made by a loop (`[Gap(g['control'], g.get('reason', ''), g.get('ticket', ''), _date(g.…`).

`src/notes_evidence/infrastructure/catalog.py` lines 77 to 84:

```python
    def people(self) -> dict[str, Person]:
        """People and the principal names they hold, from `people.toml`."""
        people: dict[str, Person] = {}
        for item in _load(self._dir / "people.toml").get("person", []):
            person = Person(item["name"], item["title"], _date(item.get("left_on")))
            for principal in item.get("principals", [item["name"]]):
                people[principal] = person
        return people
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Method `people` of class `TomlCatalog`.** People and the principal names they hold, from `people.toml`.

It gives back a `dict[str, Person]`.

Step by step:

- Declares `people` as a `dict[str, Person]` and stores the dictionary `{}` in it.
- For each `item` in the result of calling `_load(self._dir / 'people.toml').get('person', [])`:
  - Stores the result of calling `Person(item['name'], item['title'], _date(item.get('left_on')))` in `person`.
  - For each `principal` in the result of calling `item.get('principals', [item['name']])`:
    - Stores `person` in `people[principal]`.
- Gives back `people`.

`src/notes_evidence/infrastructure/catalog.py` lines 86 to 101:

```python
    def review_request(self) -> ReviewRequest:
        """The reviewer's decisions from `access-review.toml`."""
        data = _load(self._dir / "access-review.toml")
        review = data.get("review", {})
        try:
            return ReviewRequest(
                review["reviewer"],
                review["reviewed_on"],
                review["ticket"],
                tuple(
                    Decision(d["system"], d["principal"], bool(d["keep"]), d.get("reason", ""))
                    for d in data.get("decision", [])
                ),
            )
        except KeyError as missing:
            raise CatalogError(f"access-review.toml is missing {missing}") from None
```

**Method `review_request` of class `TomlCatalog`.** The reviewer's decisions from `access-review.toml`.

It gives back a `ReviewRequest`.

Step by step:

- Stores the result of calling `_load(self._dir / 'access-review.toml')` in `data`.
- Stores the result of calling `data.get('review', {})` in `review`.
- Tries:
  - Gives back the result of calling `ReviewRequest(review['reviewer'], review['reviewed_on'], review['ticket'], tuple((Decisio…`.
- If `KeyError` happens (named `missing`):
  - Stops here by raising `CatalogError(f'access-review.toml is missing {missing}')` (`from None` hides the earlier error).

### `src/notes_evidence/infrastructure/clock.py`

`src/notes_evidence/infrastructure/clock.py` lines 1 to 5:

```python
"""The system clock, behind the Clock port."""

from __future__ import annotations

from datetime import UTC, datetime
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The system clock, behind the Clock port.

Imports:

- From `__future__` it takes `annotations`.
- From `datetime` it takes `UTC, datetime`.

`src/notes_evidence/infrastructure/clock.py` lines 8 to 13:

```python
class SystemClock:
    """The current time in UTC."""

    def now(self) -> datetime:
        """Now, timezone aware."""
        return datetime.now(UTC)
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Class `SystemClock`**. The current time in UTC.

Its methods, in order:

**Method `now` of class `SystemClock`.** Now, timezone aware.

It gives back a `datetime`.

Step by step:

- Gives back the result of calling `datetime.now(UTC)`.

### `src/notes_evidence/infrastructure/evidence_store.py`

`src/notes_evidence/infrastructure/evidence_store.py` lines 1 to 9:

```python
"""The evidence folder on disk, with a manifest that records who produced each file, when, and its hash."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from notes_evidence.domain.evidence import ManifestEntry, digest
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The evidence folder on disk, with a manifest that records who produced each file, when, and its hash.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- From `datetime` it takes `UTC, datetime`.
- From `pathlib` it takes `Path`.
- From `notes_evidence.domain.evidence` it takes `ManifestEntry, digest`.

`src/notes_evidence/infrastructure/evidence_store.py` lines 11 to 12:

```python
MANIFEST = "manifest.json"
_TIME = "%Y-%m-%dT%H:%M:%SZ"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'manifest.json'` in `MANIFEST`.
- Stores the text `'%Y-%m-%dT%H:%M:%SZ'` in `_TIME`.

`src/notes_evidence/infrastructure/evidence_store.py` lines 15 to 16:

```python
class FileEvidenceStore:
    """Files under one folder. Names may not leave it."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.

**Class `FileEvidenceStore`**. Files under one folder. Names may not leave it.

`src/notes_evidence/infrastructure/evidence_store.py` lines 18 to 19:

```python
    def __init__(self, directory: Path) -> None:
        self._dir = directory.resolve()
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.

**Method `__init__` of class `FileEvidenceStore`.**

It takes: `directory` (a `Path`).

It gives back a `None`.

Step by step:

- Stores the result of calling `directory.resolve()` in `self._dir`.

`src/notes_evidence/infrastructure/evidence_store.py` lines 21 to 25:

```python
    def _path(self, name: str) -> Path:
        path = (self._dir / name).resolve()
        if path.parent != self._dir:
            raise ValueError(f"evidence files live directly in {self._dir.name}: {name}")
        return path
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Method `_path` of class `FileEvidenceStore`.**

It takes: `name` (a `str`).

It gives back a `Path`.

Step by step:

- Stores the result of calling `(self._dir / name).resolve()` in `path`.
- If `path.parent` is different from `self._dir`:
  - Stops here by raising `ValueError(f'evidence files live directly in {self._dir.name}: {name}')`.
- Gives back `path`.

`src/notes_evidence/infrastructure/evidence_store.py` lines 27 to 39:

```python
    def write(self, name: str, text: str, control: str, produced_at: datetime, run_by: str, source: str) -> None:
        """Write the file and record it in the manifest (the index itself is recorded under control '-')."""
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path(name).write_text(text, encoding="utf-8")
        entries = self._load()
        entries[name] = {
            "control": control,
            "produced_at": produced_at.astimezone(UTC).strftime(_TIME),
            "run_by": run_by,
            "source": source,
            "sha256": digest(text),
        }
        self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Method `write` of class `FileEvidenceStore`.** Write the file and record it in the manifest (the index itself is recorded under control '-').

It takes: `name` (a `str`); `text` (a `str`); `control` (a `str`); `produced_at` (a `datetime`); `run_by` (a `str`); `source` (a `str`).

It gives back a `None`.

Step by step:

- Calls `self._dir.mkdir(parents=True, exist_ok=True)`.
- Calls `self._path(name).write_text(text, encoding='utf-8')`.
- Stores the result of calling `self._load()` in `entries`.
- Stores the dictionary `{'control': control, 'produced_at': produced_at.astimezone(UTC).strft…` in `entries[name]`.
- Calls `self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + '\n', encoding='utf-8')`.

`src/notes_evidence/infrastructure/evidence_store.py` lines 41 to 44:

```python
    def read(self, name: str) -> str | None:
        """A file's text, or None when it does not exist."""
        path = self._path(name)
        return path.read_text(encoding="utf-8") if path.is_file() else None
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Method `read` of class `FileEvidenceStore`.** A file's text, or None when it does not exist.

It takes: `name` (a `str`).

It gives back a `str | None`.

Step by step:

- Stores the result of calling `self._path(name)` in `path`.
- Gives back `path.read_text(encoding='utf-8')` if `path.is_file()`, otherwise `None`.

`src/notes_evidence/infrastructure/evidence_store.py` lines 46 to 50:

```python
    def read_all(self) -> dict[str, str]:
        """Every file in the folder."""
        if not self._dir.is_dir():
            return {}
        return {path.name: path.read_text(encoding="utf-8") for path in sorted(self._dir.iterdir()) if path.is_file()}
```

> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Method `read_all` of class `FileEvidenceStore`.** Every file in the folder.

It gives back a `dict[str, str]`.

Step by step:

- If not (`self._dir.is_dir()`):
  - Gives back the dictionary `{}`.
- Gives back a new dictionary made by a loop (`{path.name: path.read_text(encoding='utf-8') for path in sorted(self.…`).

`src/notes_evidence/infrastructure/evidence_store.py` lines 52 to 64:

```python
    def manifest(self) -> dict[str, ManifestEntry]:
        """The manifest entries by file name."""
        return {
            name: ManifestEntry(
                name,
                item["control"],
                datetime.strptime(item["produced_at"], _TIME).replace(tzinfo=UTC),
                item["run_by"],
                item["source"],
                item["sha256"],
            )
            for name, item in self._load().items()
        }
```

**Method `manifest` of class `FileEvidenceStore`.** The manifest entries by file name.

It gives back a `dict[str, ManifestEntry]`.

Step by step:

- Gives back a new dictionary made by a loop (`{name: ManifestEntry(name, item['control'], datetime.strptime(item['p…`).

`src/notes_evidence/infrastructure/evidence_store.py` lines 66 to 71:

```python
    def _load(self) -> dict[str, dict[str, str]]:
        path = self._path(MANIFEST)
        if not path.is_file():
            return {}
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return {str(name): dict(item) for name, item in loaded.items()}
```

**Method `_load` of class `FileEvidenceStore`.**

It gives back a `dict[str, dict[str, str]]`.

Step by step:

- Stores the result of calling `self._path(MANIFEST)` in `path`.
- If not (`path.is_file()`):
  - Gives back the dictionary `{}`.
- Stores the result of calling `json.loads(path.read_text(encoding='utf-8'))` in `loaded`.
- Gives back a new dictionary made by a loop (`{str(name): dict(item) for name, item in loaded.items()}`).

### `src/notes_evidence/infrastructure/logging_setup.py`

`src/notes_evidence/infrastructure/logging_setup.py` lines 1 to 8:

```python
"""Structured JSON logs on standard output: level, time, logger, message and a few safe fields. No secrets."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Structured JSON logs on standard output: level, time, logger, message and a few safe fields. No secrets.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- It imports module `logging`.
- It imports module `sys`.
- From `datetime` it takes `UTC, datetime`.

`src/notes_evidence/infrastructure/logging_setup.py` lines 10 to 10:

```python
_SAFE_FIELDS = ("method", "path", "status", "user_id", "duration_ms")
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the tuple `('method', 'path', 'status', 'user_id', 'duration_ms')` in `_SAFE_FIELDS`.

`src/notes_evidence/infrastructure/logging_setup.py` lines 13 to 25:

```python
class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a record; only the whitelisted extra fields are included."""
        document = {
            "time": datetime.fromtimestamp(record.created, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})
        return json.dumps(document)
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.

**Class `JsonFormatter`**, a kind of `logging.Formatter`. One JSON object per line.

Its methods, in order:

**Method `format` of class `JsonFormatter`.** Render a record; only the whitelisted extra fields are included.

It takes: `record` (a `logging.LogRecord`).

It gives back a `str`.

Step by step:

- Stores the dictionary `{'time': datetime.fromtimestamp(record.created, UTC).strftime('%Y-%m-…` in `document`.
- Calls `document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})`.
- Gives back the result of calling `json.dumps(document)`.

`src/notes_evidence/infrastructure/logging_setup.py` lines 28 to 34:

```python
def configure_logging(level: str) -> None:
    """Send JSON logs to stdout at the given level."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `configure_logging`.** Send JSON logs to stdout at the given level.

It takes: `level` (a `str`).

It gives back a `None`.

Step by step:

- Stores the result of calling `logging.StreamHandler(sys.stdout)` in `handler`.
- Calls `handler.setFormatter(JsonFormatter())`.
- Stores the result of calling `logging.getLogger()` in `root`.
- Stores the list `[handler]` in `root.handlers[:]`.
- Calls `root.setLevel(level)`.

### `src/notes_evidence/infrastructure/passwords.py`

`src/notes_evidence/infrastructure/passwords.py` lines 1 to 8:

```python
"""Password hashing with scrypt from the standard library: salted, slow, compared in constant time."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Password hashing with scrypt from the standard library: salted, slow, compared in constant time.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `base64`.
- It imports module `hashlib`.
- It imports module `hmac`.
- It imports module `secrets`.

`src/notes_evidence/infrastructure/passwords.py` lines 10 to 11:

```python
_N, _R, _P = 2**14, 8, 1
_SCHEME = "scrypt"
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Unpacks the tuple `(2 ** 14, 8, 1)` into `(_N, _R, _P)`.
- Stores the text `'scrypt'` in `_SCHEME`.

`src/notes_evidence/infrastructure/passwords.py` lines 14 to 35:

```python
class ScryptHasher:
    """`scrypt$<salt>$<hash>`, both base64. The cost parameters are fixed so a stored hash can always be verified."""

    def hash(self, password: str) -> str:
        """Hash a password with a fresh 16-byte salt."""
        salt = secrets.token_bytes(16)
        return f"{_SCHEME}${base64.b64encode(salt).decode()}${base64.b64encode(self._derive(password, salt)).decode()}"

    def verify(self, password: str, stored: str) -> bool:
        """True when the password matches. An unusable or malformed stored value never matches."""
        parts = stored.split("$")
        if len(parts) != 3 or parts[0] != _SCHEME:
            return False
        try:
            salt, expected = base64.b64decode(parts[1]), base64.b64decode(parts[2])
        except ValueError:
            return False
        return hmac.compare_digest(self._derive(password, salt), expected)

    @staticmethod
    def _derive(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.

**Class `ScryptHasher`**. `scrypt$<salt>$<hash>`, both base64. The cost parameters are fixed so a stored hash can always be verified.

Its methods, in order:

**Method `hash` of class `ScryptHasher`.** Hash a password with a fresh 16-byte salt.

It takes: `password` (a `str`).

It gives back a `str`.

Step by step:

- Stores the result of calling `secrets.token_bytes(16)` in `salt`.
- Gives back a text built with values filled in (`f'{_SCHEME}${base64.b64encode(salt).decode()}${base64.b64encode(self.…`).

**Method `verify` of class `ScryptHasher`.** True when the password matches. An unusable or malformed stored value never matches.

It takes: `password` (a `str`); `stored` (a `str`).

It gives back a `bool`.

Step by step:

- Stores the result of calling `stored.split('$')` in `parts`.
- If `len(parts)` is different from `3` or `parts[0]` is different from `_SCHEME`:
  - Gives back `False`.
- Tries:
  - Unpacks the tuple `(base64.b64decode(parts[1]), base64.b64decode(parts[2]))` into `(salt, expected)`.
- If `ValueError` happens:
  - Gives back `False`.
- Gives back the result of calling `hmac.compare_digest(self._derive(password, salt), expected)`.

**Method `_derive` of class `ScryptHasher`.**

It takes: `password` (a `str`); `salt` (a `bytes`).

It gives back a `bytes`.

Decorators: `@staticmethod`.

Step by step:

- Gives back the result of calling `hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)`.

### `src/notes_evidence/infrastructure/postgres.py`

`src/notes_evidence/infrastructure/postgres.py` lines 1 to 18:

```python
"""PostgreSQL adapters: the notes service's repositories (as app_rw) and the catalog reader (as an administrator)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from notes_evidence.domain.access import DATABASE, AccessEntry
from notes_evidence.domain.audit import AuditAction, AuditEvent
from notes_evidence.domain.notes import Note, User
from notes_evidence.domain.roles import Role
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** PostgreSQL adapters: the notes service's repositories (as app_rw) and the catalog reader (as an administrator).

Imports:

- From `__future__` it takes `annotations`.
- It imports module `threading`.
- It imports module `time`.
- From `collections.abc` it takes `Callable, Iterator`.
- From `contextlib` it takes `contextmanager`.
- From `datetime` it takes `UTC, datetime`.
- From `typing` it takes `Any`.
- It imports module `psycopg`.
- From `psycopg.types.json` it takes `Jsonb`.
- From `notes_evidence.domain.access` it takes `DATABASE, AccessEntry`.
- From `notes_evidence.domain.audit` it takes `AuditAction, AuditEvent`.
- From `notes_evidence.domain.notes` it takes `Note, User`.
- From `notes_evidence.domain.roles` it takes `Role`.

`src/notes_evidence/infrastructure/postgres.py` lines 20 to 21:

```python
CONNECT_ATTEMPTS = 5
DEFAULT_STATEMENT_TIMEOUT_MS = 30_000
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the number `5` in `CONNECT_ATTEMPTS`.
- Stores the number `30000` in `DEFAULT_STATEMENT_TIMEOUT_MS`.

`src/notes_evidence/infrastructure/postgres.py` lines 24 to 29:

```python
class Database:
    """One long-lived connection per instance (one per worker process), reopened with backoff when it breaks.

    A connection per query would open thousands of short TCP connections in a collector run; a pool is the production
    answer for threaded servers, and gunicorn's synchronous workers need only this.
    """
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.

**Class `Database`**. One long-lived connection per instance (one per worker process), reopened with backoff when it breaks. A connection per query would open thousands of short TCP connections in a collector run; a pool is the production answer for threaded servers, and gunicorn's synchronous workers need only this.

`src/notes_evidence/infrastructure/postgres.py` lines 31 to 41:

```python
    def __init__(
        self,
        url: str,
        sleep: Callable[[float], None] = time.sleep,
        statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
    ) -> None:
        self._url = url
        self._statement_timeout_ms = statement_timeout_ms
        self._sleep = sleep
        self._connection: psycopg.Connection[tuple[Any, ...]] | None = None
        self._lock = threading.RLock()
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Method `__init__` of class `Database`.**

It takes: `url` (a `str`); `sleep` (a `Callable[[float], None]`), default `time.sleep`; `statement_timeout_ms` (a `int`), default `DEFAULT_STATEMENT_TIMEOUT_MS`.

It gives back a `None`.

Step by step:

- Stores `url` in `self._url`.
- Stores `statement_timeout_ms` in `self._statement_timeout_ms`.
- Stores `sleep` in `self._sleep`.
- Declares `self._connection` as a `psycopg.Connection[tuple[Any, ...]] | None` and stores nothing (`None`) in it.
- Stores the result of calling `threading.RLock()` in `self._lock`.

`src/notes_evidence/infrastructure/postgres.py` lines 43 to 54:

```python
    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection[tuple[Any, ...]]]:
        """The connection inside a transaction: committed on success, rolled back on any error."""
        with self._lock:
            connection = self._ensure()
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()
```

> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `yield` makes a function a **generator**: calling it returns an iterator that hands out one value at a time and remembers where it stopped.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

**Method `connection` of class `Database`.** The connection inside a transaction: committed on success, rolled back on any error.

It gives back a `Iterator[psycopg.Connection[tuple[Any, ...]]]`.

Decorators: `@contextmanager`.

Step by step:

- Inside a `with` block that opens `self._lock`:
  - Stores the result of calling `self._ensure()` in `connection`.
  - Tries:
    - Hands out `connection` to the caller (`yield`).
  - If `BaseException` happens:
    - Calls `connection.rollback()`.
    - Raises the error being handled again (`raise`).
  - If no error happened:
    - Calls `connection.commit()`.

`src/notes_evidence/infrastructure/postgres.py` lines 56 to 61:

```python
    def close(self) -> None:
        """Close the connection if it is open."""
        with self._lock:
            if self._connection is not None and not self._connection.closed:
                self._connection.close()
            self._connection = None
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Method `close` of class `Database`.** Close the connection if it is open.

It gives back a `None`.

Step by step:

- Inside a `with` block that opens `self._lock`:
  - If `self._connection` is not the same object as `None` and not (`self._connection.closed`):
    - Calls `self._connection.close()`.
  - Stores nothing (`None`) in `self._connection`.

`src/notes_evidence/infrastructure/postgres.py` lines 63 to 78:

```python
    def _ensure(self) -> psycopg.Connection[tuple[Any, ...]]:
        if self._connection is not None and not self._connection.closed and not self._connection.broken:
            return self._connection
        delay = 0.5
        for attempt in range(1, CONNECT_ATTEMPTS + 1):
            try:
                self._connection = psycopg.connect(
                    self._url, connect_timeout=5, options=f"-c statement_timeout={self._statement_timeout_ms}"
                )
                return self._connection
            except psycopg.OperationalError:
                if attempt == CONNECT_ATTEMPTS:
                    raise
                self._sleep(delay)
                delay *= 2
        raise AssertionError("unreachable")  # pragma: no cover
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Method `_ensure` of class `Database`.**

It gives back a `psycopg.Connection[tuple[Any, ...]]`.

Step by step:

- If `self._connection` is not the same object as `None` and not (`self._connection.closed`) and not (`self._connection.broken`):
  - Gives back `self._connection`.
- Stores the number `0.5` in `delay`.
- For each `attempt` in the result of calling `range(1, CONNECT_ATTEMPTS + 1)`:
  - Tries:
    - Stores the result of calling `psycopg.connect(self._url, connect_timeout=5, options=f'-c statement_timeout={self._state…` in `self._connection`.
    - Gives back `self._connection`.
  - If `psycopg.OperationalError` happens:
    - If `attempt` equals `CONNECT_ATTEMPTS`:
      - Raises the error being handled again (`raise`).
    - Calls `self._sleep(delay)`.
    - Multiplies the number `2` into/from `delay`.
- Stops here by raising `AssertionError('unreachable')`.

`src/notes_evidence/infrastructure/postgres.py` lines 80 to 87:

```python
    def ping(self) -> bool:
        """True when a trivial query works."""
        try:
            with self.connection() as connection:
                connection.execute("SELECT 1")
        except psycopg.Error:
            return False
        return True
```

**Method `ping` of class `Database`.** True when a trivial query works.

It gives back a `bool`.

Step by step:

- Tries:
  - Inside a `with` block that opens `self.connection()` (named `connection`):
    - Calls `connection.execute('SELECT 1')`.
- If `psycopg.Error` happens:
  - Gives back `False`.
- Gives back `True`.

`src/notes_evidence/infrastructure/postgres.py` lines 90 to 91:

```python
def _user(row: tuple[Any, ...]) -> User:
    return User(row[0], row[1], Role(row[2]), row[3])
```

**Function `_user`.**

It takes: `row` (a `tuple[Any, ...]`).

It gives back a `User`.

Step by step:

- Gives back the result of calling `User(row[0], row[1], Role(row[2]), row[3])`.

`src/notes_evidence/infrastructure/postgres.py` lines 94 to 95:

```python
def _note(row: tuple[Any, ...]) -> Note:
    return Note(row[0], row[1], row[2], row[3], row[4], row[5])
```

**Function `_note`.**

It takes: `row` (a `tuple[Any, ...]`).

It gives back a `Note`.

Step by step:

- Gives back the result of calling `Note(row[0], row[1], row[2], row[3], row[4], row[5])`.

`src/notes_evidence/infrastructure/postgres.py` lines 98 to 123:

```python
class PostgresUsers:
    """Users as the app reads them. The app role can read users and change roles; it cannot create users."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def find_by_username(self, username: str) -> tuple[User, str] | None:
        """The user and the stored hash, or None."""
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT id, username, role, active, password_hash FROM users WHERE username = %s", (username,)
            ).fetchone()
        return (_user(row), row[4]) if row else None

    def find_by_id(self, user_id: int) -> User | None:
        """The user or None."""
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT id, username, role, active FROM users WHERE id = %s", (user_id,)
            ).fetchone()
        return _user(row) if row else None

    def set_role(self, user_id: int, role: Role) -> None:
        """Change a role."""
        with self._db.connection() as connection:
            connection.execute("UPDATE users SET role = %s WHERE id = %s", (role.value, user_id))
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Class `PostgresUsers`**. Users as the app reads them. The app role can read users and change roles; it cannot create users.

Its methods, in order:

**Method `__init__` of class `PostgresUsers`.**

It takes: `database` (a `Database`).

It gives back a `None`.

Step by step:

- Stores `database` in `self._db`.

**Method `find_by_username` of class `PostgresUsers`.** The user and the stored hash, or None.

It takes: `username` (a `str`).

It gives back a `tuple[User, str] | None`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute('SELECT id, username, role, active, password_hash FROM users WHERE use…` in `row`.
- Gives back `(_user(row), row[4])` if `row`, otherwise `None`.

**Method `find_by_id` of class `PostgresUsers`.** The user or None.

It takes: `user_id` (a `int`).

It gives back a `User | None`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute('SELECT id, username, role, active FROM users WHERE id = %s', (user_id…` in `row`.
- Gives back `_user(row)` if `row`, otherwise `None`.

**Method `set_role` of class `PostgresUsers`.** Change a role.

It takes: `user_id` (a `int`); `role` (a `Role`).

It gives back a `None`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Calls `connection.execute('UPDATE users SET role = %s WHERE id = %s', (role.value, user_id))`.

`src/notes_evidence/infrastructure/postgres.py` lines 126 to 143:

```python
class PostgresProvisioner:
    """Creates accounts. Used only with the administrative connection."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def provision(self, username: str, role: Role, password_hash: str) -> User:
        """Insert the user, or update its role and password hash when the name exists."""
        with self._db.connection() as connection:
            row = connection.execute(
                "INSERT INTO users (username, role, password_hash) VALUES (%s, %s, %s) "
                "ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role, "
                "password_hash = EXCLUDED.password_hash, active = TRUE "
                "RETURNING id, username, role, active",
                (username, role.value, password_hash),
            ).fetchone()
        assert row is not None
        return _user(row)
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.

**Class `PostgresProvisioner`**. Creates accounts. Used only with the administrative connection.

Its methods, in order:

**Method `__init__` of class `PostgresProvisioner`.**

It takes: `database` (a `Database`).

It gives back a `None`.

Step by step:

- Stores `database` in `self._db`.

**Method `provision` of class `PostgresProvisioner`.** Insert the user, or update its role and password hash when the name exists.

It takes: `username` (a `str`); `role` (a `Role`); `password_hash` (a `str`).

It gives back a `User`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute('INSERT INTO users (username, role, password_hash) VALUES (%s, %s, %s)…` in `row`.
- Checks that `row` is not the same object as `None`; if not, the test fails.
- Gives back the result of calling `_user(row)`.

`src/notes_evidence/infrastructure/postgres.py` lines 146 to 147:

```python
class PostgresNotes:
    """Notes."""
```

**Class `PostgresNotes`**. Notes.

`src/notes_evidence/infrastructure/postgres.py` lines 149 to 150:

```python
    def __init__(self, database: Database) -> None:
        self._db = database
```

**Method `__init__` of class `PostgresNotes`.**

It takes: `database` (a `Database`).

It gives back a `None`.

Step by step:

- Stores `database` in `self._db`.

`src/notes_evidence/infrastructure/postgres.py` lines 152 to 161:

```python
    def add(self, owner_id: int, title: str, body: str, at: datetime) -> Note:
        """Insert a note."""
        with self._db.connection() as connection:
            row = connection.execute(
                "INSERT INTO notes (owner_id, title, body, created_at, updated_at) VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, owner_id, title, body, created_at, updated_at",
                (owner_id, title, body, at, at),
            ).fetchone()
        assert row is not None
        return _note(row)
```

**Method `add` of class `PostgresNotes`.** Insert a note.

It takes: `owner_id` (a `int`); `title` (a `str`); `body` (a `str`); `at` (a `datetime`).

It gives back a `Note`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute('INSERT INTO notes (owner_id, title, body, created_at, updated_at) VAL…` in `row`.
- Checks that `row` is not the same object as `None`; if not, the test fails.
- Gives back the result of calling `_note(row)`.

`src/notes_evidence/infrastructure/postgres.py` lines 163 to 169:

```python
    def get(self, note_id: int) -> Note | None:
        """One note or None."""
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT id, owner_id, title, body, created_at, updated_at FROM notes WHERE id = %s", (note_id,)
            ).fetchone()
        return _note(row) if row else None
```

**Method `get` of class `PostgresNotes`.** One note or None.

It takes: `note_id` (a `int`).

It gives back a `Note | None`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute('SELECT id, owner_id, title, body, created_at, updated_at FROM notes W…` in `row`.
- Gives back `_note(row)` if `row`, otherwise `None`.

`src/notes_evidence/infrastructure/postgres.py` lines 171 to 184:

```python
    def list_for(self, owner_id: int | None) -> list[Note]:
        """One owner's notes, or the newest 100 of everyone's."""
        with self._db.connection() as connection:
            if owner_id is None:
                rows = connection.execute(
                    "SELECT id, owner_id, title, body, created_at, updated_at FROM notes ORDER BY id DESC LIMIT 100"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT id, owner_id, title, body, created_at, updated_at FROM notes "
                    "WHERE owner_id = %s ORDER BY id DESC LIMIT 100",
                    (owner_id,),
                ).fetchall()
        return [_note(row) for row in rows]
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Method `list_for` of class `PostgresNotes`.** One owner's notes, or the newest 100 of everyone's.

It takes: `owner_id` (a `int | None`).

It gives back a `list[Note]`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - If `owner_id` is the same object as `None`:
    - Stores the result of calling `connection.execute('SELECT id, owner_id, title, body, created_at, updated_at FROM notes O…` in `rows`.
  - Otherwise:
    - Stores the result of calling `connection.execute('SELECT id, owner_id, title, body, created_at, updated_at FROM notes W…` in `rows`.
- Gives back a new list made by a loop (`[_note(row) for row in rows]`).

`src/notes_evidence/infrastructure/postgres.py` lines 186 to 194:

```python
    def update(self, note_id: int, title: str, body: str, at: datetime) -> Note | None:
        """Replace a note's text."""
        with self._db.connection() as connection:
            row = connection.execute(
                "UPDATE notes SET title = %s, body = %s, updated_at = %s WHERE id = %s "
                "RETURNING id, owner_id, title, body, created_at, updated_at",
                (title, body, at, note_id),
            ).fetchone()
        return _note(row) if row else None
```

**Method `update` of class `PostgresNotes`.** Replace a note's text.

It takes: `note_id` (a `int`); `title` (a `str`); `body` (a `str`); `at` (a `datetime`).

It gives back a `Note | None`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute('UPDATE notes SET title = %s, body = %s, updated_at = %s WHERE id = %s…` in `row`.
- Gives back `_note(row)` if `row`, otherwise `None`.

`src/notes_evidence/infrastructure/postgres.py` lines 196 to 199:

```python
    def delete(self, note_id: int) -> bool:
        """Delete a note."""
        with self._db.connection() as connection:
            return connection.execute("DELETE FROM notes WHERE id = %s", (note_id,)).rowcount > 0
```

**Method `delete` of class `PostgresNotes`.** Delete a note.

It takes: `note_id` (a `int`).

It gives back a `bool`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Gives back whether `connection.execute('DELETE FROM notes WHERE id = …` is more than `0`.

`src/notes_evidence/infrastructure/postgres.py` lines 202 to 203:

```python
class PostgresAuditLog:
    """The audit trail. The app role may only insert and select: the database refuses an update or a delete."""
```

**Class `PostgresAuditLog`**. The audit trail. The app role may only insert and select: the database refuses an update or a delete.

`src/notes_evidence/infrastructure/postgres.py` lines 205 to 206:

```python
    def __init__(self, database: Database) -> None:
        self._db = database
```

**Method `__init__` of class `PostgresAuditLog`.**

It takes: `database` (a `Database`).

It gives back a `None`.

Step by step:

- Stores `database` in `self._db`.

`src/notes_evidence/infrastructure/postgres.py` lines 208 to 223:

```python
    def append(self, event: AuditEvent) -> None:
        """Insert one event."""
        with self._db.connection() as connection:
            connection.execute(
                "INSERT INTO audit_log (ts, user_id, username, action, note_id, outcome, detail) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    event.at,
                    event.user_id,
                    event.username,
                    event.action.value,
                    event.note_id,
                    event.outcome,
                    Jsonb(event.detail),
                ),
            )
```

**Method `append` of class `PostgresAuditLog`.** Insert one event.

It takes: `event` (a `AuditEvent`).

It gives back a `None`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Calls `connection.execute('INSERT INTO audit_log (ts, user_id, username, action, note_id, outcome, detail) VALUES (%…`.

`src/notes_evidence/infrastructure/postgres.py` lines 225 to 233:

```python
    def since(self, moment: datetime) -> list[AuditEvent]:
        """Events at or after the moment, oldest first."""
        with self._db.connection() as connection:
            rows = connection.execute(
                "SELECT ts, user_id, username, action, note_id, outcome, detail FROM audit_log "
                "WHERE ts >= %s ORDER BY ts, id",
                (moment,),
            ).fetchall()
        return [_event(row) for row in rows]
```

**Method `since` of class `PostgresAuditLog`.** Events at or after the moment, oldest first.

It takes: `moment` (a `datetime`).

It gives back a `list[AuditEvent]`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute('SELECT ts, user_id, username, action, note_id, outcome, detail FROM a…` in `rows`.
- Gives back a new list made by a loop (`[_event(row) for row in rows]`).

`src/notes_evidence/infrastructure/postgres.py` lines 235 to 243:

```python
    def latest(self, limit: int) -> list[AuditEvent]:
        """The newest events, oldest first."""
        with self._db.connection() as connection:
            rows = connection.execute(
                "SELECT ts, user_id, username, action, note_id, outcome, detail FROM "
                "(SELECT * FROM audit_log ORDER BY id DESC LIMIT %s) AS newest ORDER BY id",
                (limit,),
            ).fetchall()
        return [_event(row) for row in rows]
```

**Method `latest` of class `PostgresAuditLog`.** The newest events, oldest first.

It takes: `limit` (a `int`).

It gives back a `list[AuditEvent]`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute('SELECT ts, user_id, username, action, note_id, outcome, detail FROM (…` in `rows`.
- Gives back a new list made by a loop (`[_event(row) for row in rows]`).

`src/notes_evidence/infrastructure/postgres.py` lines 246 to 248:

```python
def _event(row: tuple[Any, ...]) -> AuditEvent:
    at = row[0] if row[0].tzinfo else row[0].replace(tzinfo=UTC)
    return AuditEvent(at, row[1], row[2], AuditAction(row[3]), row[4], row[5], dict(row[6] or {}))
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Function `_event`.**

It takes: `row` (a `tuple[Any, ...]`).

It gives back a `AuditEvent`.

Step by step:

- Stores `row[0]` if `row[0].tzinfo`, otherwise `row[0].replace(tzinfo=UTC)` in `at`.
- Gives back the result of calling `AuditEvent(at, row[1], row[2], AuditAction(row[3]), row[4], row[5], dict(row[6] or {}))`.

`src/notes_evidence/infrastructure/postgres.py` lines 251 to 265:

```python
class PostgresRoles:
    """C1 for the database: the roles in the catalog, with their level. Names starting with pg_ are the server's own."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def roles(self) -> list[AccessEntry]:
        """Roles and their level: superuser, createdb or standard."""
        with self._db.connection() as connection:
            rows = connection.execute(
                "SELECT rolname, "
                "CASE WHEN rolsuper THEN 'superuser' WHEN rolcreatedb THEN 'createdb' ELSE 'standard' END "
                "FROM pg_roles WHERE rolname NOT LIKE 'pg\\_%' AND rolcanlogin ORDER BY 1"
            ).fetchall()
        return [AccessEntry(DATABASE, row[0], row[1]) for row in rows]
```

**Class `PostgresRoles`**. C1 for the database: the roles in the catalog, with their level. Names starting with pg_ are the server's own.

Its methods, in order:

**Method `__init__` of class `PostgresRoles`.**

It takes: `database` (a `Database`).

It gives back a `None`.

Step by step:

- Stores `database` in `self._db`.

**Method `roles` of class `PostgresRoles`.** Roles and their level: superuser, createdb or standard.

It gives back a `list[AccessEntry]`.

Step by step:

- Inside a `with` block that opens `self._db.connection()` (named `connection`):
  - Stores the result of calling `connection.execute("SELECT rolname, CASE WHEN rolsuper THEN 'superuser' WHEN rolcreatedb …` in `rows`.
- Gives back a new list made by a loop (`[AccessEntry(DATABASE, row[0], row[1]) for row in rows]`).

### `src/notes_evidence/infrastructure/scanner.py`

`src/notes_evidence/infrastructure/scanner.py` lines 1 to 11:

```python
"""C5: run pip-audit over the locked dependencies and wrap its JSON with the run that produced it."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import datetime
from importlib import metadata

from notes_evidence.domain.scan import ScanReport, parse_pip_audit
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** C5: run pip-audit over the locked dependencies and wrap its JSON with the run that produced it.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `subprocess`.
- It imports module `sys`.
- From `collections.abc` it takes `Callable, Mapping`.
- From `datetime` it takes `datetime`.
- From `importlib` it takes `metadata`.
- From `notes_evidence.domain.scan` it takes `ScanReport, parse_pip_audit`.

`src/notes_evidence/infrastructure/scanner.py` lines 13 to 13:

```python
Run = Callable[[list[str]], str]
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

These module-level lines:

- Stores `Callable[[list[str]], str]` in `Run`.

`src/notes_evidence/infrastructure/scanner.py` lines 16 to 17:

```python
class ScanError(RuntimeError):
    """pip-audit produced no usable report."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `ScanError`**, a kind of `RuntimeError`. pip-audit produced no usable report.

`src/notes_evidence/infrastructure/scanner.py` lines 20 to 28:

```python
def run_pip_audit(argv: list[str]) -> str:
    """Run pip-audit; exit code 1 means it found vulnerabilities and still prints the report."""
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as problem:
        raise ScanError(f"pip-audit: {problem}") from None
    if done.returncode not in (0, 1) or not done.stdout.strip():
        raise ScanError(f"pip-audit exited {done.returncode}: {done.stderr.strip()[-300:]}")
    return done.stdout
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `run_pip_audit`.** Run pip-audit; exit code 1 means it found vulnerabilities and still prints the report.

It takes: `argv` (a `list[str]`).

It gives back a `str`.

Step by step:

- Tries:
  - Stores the result of calling `subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)` in `done`.
- If `(OSError, subprocess.TimeoutExpired)` happens (named `problem`):
  - Stops here by raising `ScanError(f'pip-audit: {problem}')` (`from None` hides the earlier error).
- If `done.returncode` is not in `(0, 1)` or not (`done.stdout.strip()`):
  - Stops here by raising `ScanError(f'pip-audit exited {done.returncode}: {done.stderr.strip()[-300:]}')`.
- Gives back `done.stdout`.

`src/notes_evidence/infrastructure/scanner.py` lines 31 to 50:

```python
class PipAuditScanner:
    """Scan one lock file. The run id is the CI run when there is one, else a local stamp."""

    def __init__(
        self, lock_file: str, env: Mapping[str, str], now: Callable[[], datetime], run: Run = run_pip_audit
    ) -> None:
        self._lock = lock_file
        self._env = env
        self._now = now
        self._run = run

    def scan(self) -> ScanReport:
        """Run the scan."""
        started = self._now()
        raw = self._run(
            [sys.executable, "-m", "pip_audit", "-f", "json", "--no-deps", "--disable-pip", "-r", self._lock]
        )
        count, findings = parse_pip_audit(raw)
        run_id = self._env.get("GITHUB_RUN_ID") or f"local-{started.strftime('%Y%m%dT%H%M%SZ')}"
        return ScanReport(run_id, "pip-audit", metadata.version("pip-audit"), started, self._lock, count, findings)
```

**Class `PipAuditScanner`**. Scan one lock file. The run id is the CI run when there is one, else a local stamp.

Its methods, in order:

**Method `__init__` of class `PipAuditScanner`.**

It takes: `lock_file` (a `str`); `env` (a `Mapping[str, str]`); `now` (a `Callable[[], datetime]`); `run` (a `Run`), default `run_pip_audit`.

It gives back a `None`.

Step by step:

- Stores `lock_file` in `self._lock`.
- Stores `env` in `self._env`.
- Stores `now` in `self._now`.
- Stores `run` in `self._run`.

**Method `scan` of class `PipAuditScanner`.** Run the scan.

It gives back a `ScanReport`.

Step by step:

- Stores the result of calling `self._now()` in `started`.
- Stores the result of calling `self._run([sys.executable, '-m', 'pip_audit', '-f', 'json', '--no-deps', '--disable-pip',…` in `raw`.
- Unpacks the result of calling `parse_pip_audit(raw)` into `(count, findings)`.
- Stores whether `self._env.get('GITHUB_RUN_ID')` or `f"local-{started.strftime('%Y%m%dT%H%M%SZ')}"` in `run_id`.
- Gives back the result of calling `ScanReport(run_id, 'pip-audit', metadata.version('pip-audit'), started, self._lock, count…`.

### `src/notes_evidence/infrastructure/settings.py`

`src/notes_evidence/infrastructure/settings.py` lines 1 to 7:

```python
"""Settings from the environment, validated once at start-up (twelve-factor). Secrets come only from here."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Settings from the environment, validated once at start-up (twelve-factor). Secrets come only from here.

Imports:

- From `__future__` it takes `annotations`.
- From `collections.abc` it takes `Mapping`.
- From `dataclasses` it takes `dataclass`.
- From `pathlib` it takes `Path`.

`src/notes_evidence/infrastructure/settings.py` lines 10 to 11:

```python
class SettingsError(ValueError):
    """An environment variable is missing or holds a value the program cannot use."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `SettingsError`**, a kind of `ValueError`. An environment variable is missing or holds a value the program cannot use.

`src/notes_evidence/infrastructure/settings.py` lines 14 to 33:

```python
@dataclass(frozen=True)
class Settings:
    """Everything the programs read from the environment."""

    database_url: str
    admin_database_url: str
    secret: str
    token_ttl_seconds: int
    retention_days: int
    statement_timeout_ms: int
    evidence_dir: Path
    controls_file: Path
    evidence_source: str
    run_by: str
    state_dir: Path
    log_level: str
    http_port: int
    db_exec_prefix: tuple[str, ...]
    postgres_user: str
    postgres_db: str
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Settings`**. Everything the programs read from the environment. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `database_url`: a `str`.
- Field `admin_database_url`: a `str`.
- Field `secret`: a `str`.
- Field `token_ttl_seconds`: a `int`.
- Field `retention_days`: a `int`.
- Field `statement_timeout_ms`: a `int`.
- Field `evidence_dir`: a `Path`.
- Field `controls_file`: a `Path`.
- Field `evidence_source`: a `str`.
- Field `run_by`: a `str`.
- Field `state_dir`: a `Path`.
- Field `log_level`: a `str`.
- Field `http_port`: a `int`.
- Field `db_exec_prefix`: a `tuple[str, ...]`.
- Field `postgres_user`: a `str`.
- Field `postgres_db`: a `str`.

`src/notes_evidence/infrastructure/settings.py` lines 36 to 40:

```python
def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value:
        raise SettingsError(f"{name} is required")
    return value
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `_required`.**

It takes: `env` (a `Mapping[str, str]`); `name` (a `str`).

It gives back a `str`.

Step by step:

- Stores the result of calling `env.get(name, '')` in `value`.
- If not (`value`):
  - Stops here by raising `SettingsError(f'{name} is required')`.
- Gives back `value`.

`src/notes_evidence/infrastructure/settings.py` lines 43 to 51:

```python
def _positive_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        raise SettingsError(f"{name} must be a whole number, got {raw!r}") from None
    if value <= 0:
        raise SettingsError(f"{name} must be positive, got {value}")
    return value
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `_positive_int`.**

It takes: `env` (a `Mapping[str, str]`); `name` (a `str`); `default` (a `int`).

It gives back a `int`.

Step by step:

- Stores the result of calling `env.get(name, str(default))` in `raw`.
- Tries:
  - Stores the result of calling `int(raw)` in `value`.
- If `ValueError` happens:
  - Stops here by raising `SettingsError(f'{name} must be a whole number, got {raw!r}')` (`from None` hides the earlier error).
- If `value` is at most `0`:
  - Stops here by raising `SettingsError(f'{name} must be positive, got {value}')`.
- Gives back `value`.

`src/notes_evidence/infrastructure/settings.py` lines 54 to 82:

```python
def load_settings(env: Mapping[str, str]) -> Settings:
    """Validate and collect the settings. A signing secret shorter than 32 characters is refused."""
    secret = _required(env, "NOTES_SECRET")
    if len(secret) < 32:
        raise SettingsError("NOTES_SECRET must be at least 32 characters")
    source = env.get("EVIDENCE_SOURCE", "fixture")
    if source not in ("fixture", "live"):
        raise SettingsError(f"EVIDENCE_SOURCE must be fixture or live, got {source!r}")
    level = env.get("LOG_LEVEL", "INFO").upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        raise SettingsError(f"LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR, got {level!r}")
    return Settings(
        database_url=_required(env, "DATABASE_URL"),
        admin_database_url=env.get("ADMIN_DATABASE_URL", ""),
        secret=secret,
        token_ttl_seconds=_positive_int(env, "TOKEN_TTL_SECONDS", 900),
        retention_days=_positive_int(env, "AUDIT_RETENTION_DAYS", 365),
        statement_timeout_ms=_positive_int(env, "DB_STATEMENT_TIMEOUT_MS", 30_000),
        evidence_dir=Path(env.get("EVIDENCE_DIR", "evidence")),
        controls_file=Path(env.get("CONTROLS_FILE", "controls/controls.toml")),
        evidence_source=source,
        run_by=env.get("EVIDENCE_RUN_BY", "ada"),
        state_dir=Path(env.get("STATE_DIR", "state")),
        log_level=level,
        http_port=_positive_int(env, "HTTP_PORT", 8080),
        db_exec_prefix=tuple(env.get("DB_EXEC_PREFIX", "docker compose exec -T db").split()),
        postgres_user=env.get("POSTGRES_USER", "postgres"),
        postgres_db=env.get("POSTGRES_DB", "notes"),
    )
```

**Function `load_settings`.** Validate and collect the settings. A signing secret shorter than 32 characters is refused.

It takes: `env` (a `Mapping[str, str]`).

It gives back a `Settings`.

Step by step:

- Stores the result of calling `_required(env, 'NOTES_SECRET')` in `secret`.
- If `len(secret)` is less than `32`:
  - Stops here by raising `SettingsError('NOTES_SECRET must be at least 32 characters')`.
- Stores the result of calling `env.get('EVIDENCE_SOURCE', 'fixture')` in `source`.
- If `source` is not in `('fixture', 'live')`:
  - Stops here by raising `SettingsError(f'EVIDENCE_SOURCE must be fixture or live, got {source!r}')`.
- Stores the result of calling `env.get('LOG_LEVEL', 'INFO').upper()` in `level`.
- If `level` is not in `('DEBUG', 'INFO', 'WARNING', 'ERROR')`:
  - Stops here by raising `SettingsError(f'LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR, got {level!r}')`.
- Gives back the result of calling `Settings(database_url=_required(env, 'DATABASE_URL'), admin_database_url=env.get('ADMIN_D…`.

### `src/notes_evidence/infrastructure/sources.py`

`src/notes_evidence/infrastructure/sources.py` lines 1 to 17:

```python
"""Where C1 and C2 read from: the hosting platform and the cloud account, as files or as `gh` and `aws` commands.

Both modes parse the same JSON shapes, so the parsers are tested against recorded output of the real tools and the
live adapters only add the command.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from notes_evidence.domain.access import CLOUD, REPOSITORY, AccessEntry
from notes_evidence.domain.changes import MergedChange
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Where C1 and C2 read from: the hosting platform and the cloud account, as files or as `gh` and `aws` commands. Both modes parse the same JSON shapes, so the parsers are tested against recorded output of the real tools and the live adapters only add the command.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- It imports module `subprocess`.
- From `collections.abc` it takes `Callable`.
- From `datetime` it takes `datetime`.
- From `pathlib` it takes `Path`.
- From `typing` it takes `Any`.
- From `notes_evidence.domain.access` it takes `CLOUD, REPOSITORY, AccessEntry`.
- From `notes_evidence.domain.changes` it takes `MergedChange`.

`src/notes_evidence/infrastructure/sources.py` lines 19 to 20:

```python
JsonLoader = Callable[[], Any]
Runner = Callable[[list[str]], str]
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

These module-level lines:

- Stores `Callable[[], Any]` in `JsonLoader`.
- Stores `Callable[[list[str]], str]` in `Runner`.

`src/notes_evidence/infrastructure/sources.py` lines 23 to 24:

```python
class SourceError(RuntimeError):
    """A source did not give what the parser needs."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `SourceError`**, a kind of `RuntimeError`. A source did not give what the parser needs.

`src/notes_evidence/infrastructure/sources.py` lines 27 to 35:

```python
def run_command(argv: list[str]) -> str:
    """Run a command with a timeout and return its standard output; a failure is a SourceError."""
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as problem:
        raise SourceError(f"{argv[0]}: {problem}") from None
    if done.returncode != 0:
        raise SourceError(f"{argv[0]} exited {done.returncode}: {done.stderr.strip()[:200]}")
    return done.stdout
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `run_command`.** Run a command with a timeout and return its standard output; a failure is a SourceError.

It takes: `argv` (a `list[str]`).

It gives back a `str`.

Step by step:

- Tries:
  - Stores the result of calling `subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)` in `done`.
- If `(OSError, subprocess.TimeoutExpired)` happens (named `problem`):
  - Stops here by raising `SourceError(f'{argv[0]}: {problem}')` (`from None` hides the earlier error).
- If `done.returncode` is different from `0`:
  - Stops here by raising `SourceError(f'{argv[0]} exited {done.returncode}: {done.stderr.strip()[:200]}')`.
- Gives back `done.stdout`.

`src/notes_evidence/infrastructure/sources.py` lines 38 to 40:

```python
def file_json(path: Path) -> JsonLoader:
    """Load JSON from a file."""
    return lambda: json.loads(path.read_text(encoding="utf-8"))
```

> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Function `file_json`.** Load JSON from a file.

It takes: `path` (a `Path`).

It gives back a `JsonLoader`.

Step by step:

- Gives back a small function (`lambda: json.loads(path.read_text(encoding='utf-8'))`).

`src/notes_evidence/infrastructure/sources.py` lines 43 to 45:

```python
def command_json(runner: Runner, argv: list[str]) -> JsonLoader:
    """Load JSON from a command's output."""
    return lambda: json.loads(runner(argv))
```

**Function `command_json`.** Load JSON from a command's output.

It takes: `runner` (a `Runner`); `argv` (a `list[str]`).

It gives back a `JsonLoader`.

Step by step:

- Gives back a small function (`lambda: json.loads(runner(argv))`).

`src/notes_evidence/infrastructure/sources.py` lines 48 to 50:

```python
def parse_collaborators(data: Any) -> list[AccessEntry]:
    """`gh api repos/OWNER/REPO/collaborators`: login and role_name."""
    return [AccessEntry(REPOSITORY, item["login"], item["role_name"]) for item in data]
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Function `parse_collaborators`.** `gh api repos/OWNER/REPO/collaborators`: login and role_name.

It takes: `data` (a `Any`).

It gives back a `list[AccessEntry]`.

Step by step:

- Gives back a new list made by a loop (`[AccessEntry(REPOSITORY, item['login'], item['role_name']) for item i…`).

`src/notes_evidence/infrastructure/sources.py` lines 53 to 55:

```python
def parse_iam_users(data: Any) -> list[AccessEntry]:
    """`aws iam list-users`: the user names."""
    return [AccessEntry(CLOUD, item["UserName"]) for item in data["Users"]]
```

**Function `parse_iam_users`.** `aws iam list-users`: the user names.

It takes: `data` (a `Any`).

It gives back a `list[AccessEntry]`.

Step by step:

- Gives back a new list made by a loop (`[AccessEntry(CLOUD, item['UserName']) for item in data['Users']]`).

`src/notes_evidence/infrastructure/sources.py` lines 58 to 73:

```python
def parse_merged_prs(prs: Any, deploys: Any) -> list[MergedChange]:
    """`gh pr list --state merged --json ...`, joined to the deployment log by the short commit."""
    deploy_by_commit = {item["commit"]: item["deploy_id"] for item in deploys}
    changes = []
    for pr in prs:
        commit = pr["mergeCommit"]["oid"]
        approvers = tuple(
            sorted({review["author"]["login"] for review in pr["reviews"] if review["state"] == "APPROVED"})
        )
        merged_at = datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))
        changes.append(
            MergedChange(
                pr["number"], pr["author"]["login"], merged_at, commit, approvers, deploy_by_commit.get(commit[:7], "")
            )
        )
    return changes
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.

**Function `parse_merged_prs`.** `gh pr list --state merged --json ...`, joined to the deployment log by the short commit.

It takes: `prs` (a `Any`); `deploys` (a `Any`).

It gives back a `list[MergedChange]`.

Step by step:

- Stores a new dictionary made by a loop (`{item['commit']: item['deploy_id'] for item in deploys}`) in `deploy_by_commit`.
- Stores the list `[]` in `changes`.
- For each `pr` in `prs`:
  - Stores `pr['mergeCommit']['oid']` in `commit`.
  - Stores the result of calling `tuple(sorted({review['author']['login'] for review in pr['reviews'] if review['state'] ==…` in `approvers`.
  - Stores the result of calling `datetime.fromisoformat(pr['mergedAt'].replace('Z', '+00:00'))` in `merged_at`.
  - Calls `changes.append(MergedChange(pr['number'], pr['author']['login'], merged_at, commit, approvers, deploy_by_comm…`.
- Gives back `changes`.

`src/notes_evidence/infrastructure/sources.py` lines 76 to 84:

```python
class GithubRepositoryAccess:
    """Collaborators from whichever loader it is given."""

    def __init__(self, load: JsonLoader) -> None:
        self._load = load

    def collaborators(self) -> list[AccessEntry]:
        """Collaborators and their permission."""
        return parse_collaborators(self._load())
```

**Class `GithubRepositoryAccess`**. Collaborators from whichever loader it is given.

Its methods, in order:

**Method `__init__` of class `GithubRepositoryAccess`.**

It takes: `load` (a `JsonLoader`).

It gives back a `None`.

Step by step:

- Stores `load` in `self._load`.

**Method `collaborators` of class `GithubRepositoryAccess`.** Collaborators and their permission.

It gives back a `list[AccessEntry]`.

Step by step:

- Gives back the result of calling `parse_collaborators(self._load())`.

`src/notes_evidence/infrastructure/sources.py` lines 87 to 96:

```python
class GithubChanges:
    """Merged pull requests joined with the deployment log."""

    def __init__(self, load_prs: JsonLoader, load_deploys: JsonLoader) -> None:
        self._prs = load_prs
        self._deploys = load_deploys

    def merged_changes(self) -> list[MergedChange]:
        """Merged changes with their approvers and deploy ids."""
        return parse_merged_prs(self._prs(), self._deploys())
```

**Class `GithubChanges`**. Merged pull requests joined with the deployment log.

Its methods, in order:

**Method `__init__` of class `GithubChanges`.**

It takes: `load_prs` (a `JsonLoader`); `load_deploys` (a `JsonLoader`).

It gives back a `None`.

Step by step:

- Stores `load_prs` in `self._prs`.
- Stores `load_deploys` in `self._deploys`.

**Method `merged_changes` of class `GithubChanges`.** Merged changes with their approvers and deploy ids.

It gives back a `list[MergedChange]`.

Step by step:

- Gives back the result of calling `parse_merged_prs(self._prs(), self._deploys())`.

`src/notes_evidence/infrastructure/sources.py` lines 99 to 120:

```python
class StateCloudDirectory:
    """The cloud account stand-in for fixture mode: a JSON file shaped like `aws iam list-users`, seeded from a fixture.

    `remove_user` rewrites the file, which is what `aws iam delete-user` does to the account.
    """

    def __init__(self, state_file: Path, seed_file: Path) -> None:
        self._state = state_file
        self._seed = seed_file

    def users(self) -> list[AccessEntry]:
        """Users currently in the account."""
        if not self._state.is_file():
            self._state.parent.mkdir(parents=True, exist_ok=True)
            self._state.write_text(self._seed.read_text(encoding="utf-8"), encoding="utf-8")
        return parse_iam_users(json.loads(self._state.read_text(encoding="utf-8")))

    def remove_user(self, name: str) -> None:
        """Delete one user from the account."""
        data = json.loads(self._state.read_text(encoding="utf-8"))
        data["Users"] = [user for user in data["Users"] if user["UserName"] != name]
        self._state.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
```

**Class `StateCloudDirectory`**. The cloud account stand-in for fixture mode: a JSON file shaped like `aws iam list-users`, seeded from a fixture. `remove_user` rewrites the file, which is what `aws iam delete-user` does to the account.

Its methods, in order:

**Method `__init__` of class `StateCloudDirectory`.**

It takes: `state_file` (a `Path`); `seed_file` (a `Path`).

It gives back a `None`.

Step by step:

- Stores `state_file` in `self._state`.
- Stores `seed_file` in `self._seed`.

**Method `users` of class `StateCloudDirectory`.** Users currently in the account.

It gives back a `list[AccessEntry]`.

Step by step:

- If not (`self._state.is_file()`):
  - Calls `self._state.parent.mkdir(parents=True, exist_ok=True)`.
  - Calls `self._state.write_text(self._seed.read_text(encoding='utf-8'), encoding='utf-8')`.
- Gives back the result of calling `parse_iam_users(json.loads(self._state.read_text(encoding='utf-8')))`.

**Method `remove_user` of class `StateCloudDirectory`.** Delete one user from the account.

It takes: `name` (a `str`).

It gives back a `None`.

Step by step:

- Stores the result of calling `json.loads(self._state.read_text(encoding='utf-8'))` in `data`.
- Stores a new list made by a loop (`[user for user in data['Users'] if user['UserName'] != name]`) in `data['Users']`.
- Calls `self._state.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')`.

`src/notes_evidence/infrastructure/sources.py` lines 123 to 135:

```python
class AwsCloudDirectory:
    """The real account through the `aws` command line."""

    def __init__(self, runner: Runner = run_command) -> None:
        self._runner = runner

    def users(self) -> list[AccessEntry]:
        """`aws iam list-users`."""
        return parse_iam_users(json.loads(self._runner(["aws", "iam", "list-users", "--output", "json"])))

    def remove_user(self, name: str) -> None:
        """`aws iam delete-user`. The user must have no keys or policies left; AWS refuses otherwise."""
        self._runner(["aws", "iam", "delete-user", "--user-name", name])
```

**Class `AwsCloudDirectory`**. The real account through the `aws` command line.

Its methods, in order:

**Method `__init__` of class `AwsCloudDirectory`.**

It takes: `runner` (a `Runner`), default `run_command`.

It gives back a `None`.

Step by step:

- Stores `runner` in `self._runner`.

**Method `users` of class `AwsCloudDirectory`.** `aws iam list-users`.

It gives back a `list[AccessEntry]`.

Step by step:

- Gives back the result of calling `parse_iam_users(json.loads(self._runner(['aws', 'iam', 'list-users', '--output', 'json'])…`.

**Method `remove_user` of class `AwsCloudDirectory`.** `aws iam delete-user`. The user must have no keys or policies left; AWS refuses otherwise.

It takes: `name` (a `str`).

It gives back a `None`.

Step by step:

- Calls `self._runner(['aws', 'iam', 'delete-user', '--user-name', name])`.

### `src/notes_evidence/infrastructure/tokens.py`

`src/notes_evidence/infrastructure/tokens.py` lines 1 to 9:

```python
"""Signed, expiring session tokens: `user_id.expires.signature`, HMAC-SHA256 over the first two parts."""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta

from notes_evidence.domain.notes import User
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Signed, expiring session tokens: `user_id.expires.signature`, HMAC-SHA256 over the first two parts.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `hashlib`.
- It imports module `hmac`.
- From `datetime` it takes `datetime, timedelta`.
- From `notes_evidence.domain.notes` it takes `User`.

`src/notes_evidence/infrastructure/tokens.py` lines 12 to 34:

```python
class HmacTokens:
    """Issue and verify tokens with a secret that comes from the environment."""

    def __init__(self, secret: str, ttl: timedelta) -> None:
        self._key = secret.encode()
        self._ttl = ttl

    def issue(self, user: User, now: datetime) -> str:
        """A token for the user that expires after the configured time."""
        body = f"{user.id}.{int((now + self._ttl).timestamp())}"
        return f"{body}.{self._sign(body)}"

    def verify(self, token: str, now: datetime) -> int | None:
        """The user id in a genuine, unexpired token; None for anything else."""
        parts = token.split(".")
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            return None
        if not hmac.compare_digest(parts[2], self._sign(f"{parts[0]}.{parts[1]}")):
            return None
        return int(parts[0]) if int(parts[1]) > now.timestamp() else None

    def _sign(self, body: str) -> str:
        return hmac.new(self._key, body.encode(), hashlib.sha256).hexdigest()
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.

**Class `HmacTokens`**. Issue and verify tokens with a secret that comes from the environment.

Its methods, in order:

**Method `__init__` of class `HmacTokens`.**

It takes: `secret` (a `str`); `ttl` (a `timedelta`).

It gives back a `None`.

Step by step:

- Stores the result of calling `secret.encode()` in `self._key`.
- Stores `ttl` in `self._ttl`.

**Method `issue` of class `HmacTokens`.** A token for the user that expires after the configured time.

It takes: `user` (a `User`); `now` (a `datetime`).

It gives back a `str`.

Step by step:

- Stores a text built with values filled in (`f'{user.id}.{int((now + self._ttl).timestamp())}'`) in `body`.
- Gives back a text built with values filled in (`f'{body}.{self._sign(body)}'`).

**Method `verify` of class `HmacTokens`.** The user id in a genuine, unexpired token; None for anything else.

It takes: `token` (a `str`); `now` (a `datetime`).

It gives back a `int | None`.

Step by step:

- Stores the result of calling `token.split('.')` in `parts`.
- If `len(parts)` is different from `3` or not (`parts[0].isdigit()`) or not (`parts[1].isdigit()`):
  - Gives back nothing (`None`).
- If not (`hmac.compare_digest(parts[2], self._sign(f'{parts[0]}.{parts[1]}'))`):
  - Gives back nothing (`None`).
- Gives back `int(parts[0])` if `int(parts[1])` is more than `now.timestamp()`, otherwise `None`.

**Method `_sign` of class `HmacTokens`.**

It takes: `body` (a `str`).

It gives back a `str`.

Step by step:

- Gives back the result of calling `hmac.new(self._key, body.encode(), hashlib.sha256).hexdigest()`.

## Try it yourself

```bash
.venv/bin/python -c "import notes_evidence.infrastructure.alerting; print(notes_evidence.infrastructure.alerting.__doc__)"
```
Prints the module's description: `Where alerts go in this build: the log stream and a file, the stand-in for a chat channel or a pager.`

```bash
.venv/bin/python -c "import notes_evidence.infrastructure.backup; print(notes_evidence.infrastructure.backup.__doc__)"
```
Prints the module's description: `C4: a pg_dump backup and a pg_restore into a scratch database, both run inside the database container.`

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check src/notes_evidence/infrastructure/__init__.py src/notes_evidence/infrastructure/alerting.py src/notes_evidence/infrastructure/backup.py src/notes_evidence/infrastructure/catalog.py src/notes_evidence/infrastructure/clock.py src/notes_evidence/infrastructure/evidence_store.py
```
Prints `All checks passed!`.

```bash
grep -c "^def \|^class \|    def " src/notes_evidence/infrastructure/alerting.py
```
Counts the functions, methods and classes in `src/notes_evidence/infrastructure/alerting.py`.

## Mistakes people make

- Putting a business rule in an adapter, where the domain tests cannot see it.
- Forgetting to close a connection or file. The adapters use `with` blocks and context managers.
- Trusting input from outside. Adapters check paths, shapes and ranges before handing values inward.

## Check yourself

1. What is `FileAlertSink` for?
   **Answer:** Appends each alert message to a file and logs it at WARNING.
2. What is `BackupError` for?
   **Answer:** pg_dump, pg_restore or psql failed.
3. What is `run_in_container` for?
   **Answer:** Run a command, optionally feeding stdin, with a timeout; a non-zero exit is a BackupError.
4. What is `DockerBackupRunner` for?
   **Answer:** Backs up the database and restores it into `notes_restore_test`, then drops the scratch database.
5. What is `CatalogError` for?
   **Answer:** A controls file is missing a field or holds an unknown value.

## Further reading

- Python 3.12 tutorial, classes: <https://docs.python.org/3.12/tutorial/classes.html>
- Python 3.12 language reference: <https://docs.python.org/3.12/reference/>
- Type hints: <https://docs.python.org/3.12/library/typing.html>
