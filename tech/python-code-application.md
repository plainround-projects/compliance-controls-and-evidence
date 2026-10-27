# Application layer code

## What it is

The use cases: the steps that join domain rules to the outside world through small interfaces (ports). (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

This is where the repository's application work happens. Reading it file by file, with every line explained, is how a reader sees the work that was done.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/application/__init__.py` | 1 lines. application layer. |
| `src/notes_evidence/application/evidence_collect.py` | 194 lines. The evidence collectors: each reads a real system through a port and writes one artifact and its manifest ent… |
| `src/notes_evidence/application/exercise.py` | 49 lines. A scripted day of use, so the audit trail holds real events from real calls into the service. |
| `src/notes_evidence/application/notes_service.py` | 112 lines. The notes service: every use case checks the role, then records what happened. |
| `src/notes_evidence/application/ports.py` | 155 lines. What the use cases need from the outside world: ports, implemented by adapters in infrastructure. |
| `src/notes_evidence/application/reporting.py` | 48 lines. Format the verification as text for the terminal and as Markdown for the build artifact. |

## How it works underneath

The application layer says *what* happens in what order (check every document, export a person's data, collect the evidence) and asks the outside world for what it needs only through `ports.py`, a list of `Protocol` classes. It imports the domain and nothing outer.

## Walkthrough of this repository's use

### `src/notes_evidence/application/__init__.py`

`src/notes_evidence/application/__init__.py` lines 1 to 1:

```python
"""application layer."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** application layer.

### `src/notes_evidence/application/evidence_collect.py`

`src/notes_evidence/application/evidence_collect.py` lines 1 to 34:

```python
"""The evidence collectors: each reads a real system through a port and writes one artifact and its manifest entry."""

from __future__ import annotations

import contextlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from notes_evidence.application.ports import (
    AlertSink,
    AuditLog,
    BackupRunner,
    ChangeSource,
    Clock,
    CloudDirectory,
    ControlCatalog,
    DatabaseAccess,
    EvidenceStore,
    Notes,
    RepositoryAccess,
    ScanRunner,
)
from notes_evidence.domain.access import AccessEntry, AccessList, render_access_list
from notes_evidence.domain.alerts import Alert, detect_alerts
from notes_evidence.domain.audit import format_timestamp, render_line
from notes_evidence.domain.changes import find_exceptions, render_changes
from notes_evidence.domain.controls import Control, Gap, RecordedException
from notes_evidence.domain.errors import InvalidCredentialsError
from notes_evidence.domain.evidence import verify_pack
from notes_evidence.domain.findings import Finding, Report, error
from notes_evidence.domain.restore import RestoreResult, render_restore
from notes_evidence.domain.review import ReviewRequest, check_review, render_review
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The evidence collectors: each reads a real system through a port and writes one artifact and its manifest entry.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `contextlib`.
- It imports module `secrets`.
- From `collections.abc` it takes `Callable`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `date`.
- From `notes_evidence.application.ports` it takes `AlertSink, AuditLog, BackupRunner, ChangeSource, Clock, CloudDirectory, ControlCatalog, DatabaseAccess, EvidenceStore, Notes, RepositoryAccess, ScanRunner`.
- From `notes_evidence.domain.access` it takes `AccessEntry, AccessList, render_access_list`.
- From `notes_evidence.domain.alerts` it takes `Alert, detect_alerts`.
- From `notes_evidence.domain.audit` it takes `format_timestamp, render_line`.
- From `notes_evidence.domain.changes` it takes `find_exceptions, render_changes`.
- From `notes_evidence.domain.controls` it takes `Control, Gap, RecordedException`.
- From `notes_evidence.domain.errors` it takes `InvalidCredentialsError`.
- From `notes_evidence.domain.evidence` it takes `verify_pack`.
- From `notes_evidence.domain.findings` it takes `Finding, Report, error`.
- From `notes_evidence.domain.restore` it takes `RestoreResult, render_restore`.
- From `notes_evidence.domain.review` it takes `ReviewRequest, check_review, render_review`.

`src/notes_evidence/application/evidence_collect.py` lines 36 to 42:

```python
ACCESS_FILE = "C1-access-list.txt"
CHANGES_FILE = "C2-changes.csv"
LOG_FILE = "C3-log-sample.txt"
ALERT_FILE = "C3-alert-test.txt"
RESTORE_FILE = "C4-restore-test.txt"
SCAN_FILE = "C5-scan-report.json"
REVIEW_FILE = "C6-access-review.md"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'C1-access-list.txt'` in `ACCESS_FILE`.
- Stores the text `'C2-changes.csv'` in `CHANGES_FILE`.
- Stores the text `'C3-log-sample.txt'` in `LOG_FILE`.
- Stores the text `'C3-alert-test.txt'` in `ALERT_FILE`.
- Stores the text `'C4-restore-test.txt'` in `RESTORE_FILE`.
- Stores the text `'C5-scan-report.json'` in `SCAN_FILE`.
- Stores the text `'C6-access-review.md'` in `REVIEW_FILE`.

`src/notes_evidence/application/evidence_collect.py` lines 45 to 52:

```python
@dataclass(frozen=True)
class Collector:
    """What every collector shares: where to write, what time it is, who runs it, and which sources it reads."""

    store: EvidenceStore
    clock: Clock
    run_by: str
    source: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Collector`**. What every collector shares: where to write, what time it is, who runs it, and which sources it reads. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `store`: a `EvidenceStore`.
- Field `clock`: a `Clock`.
- Field `run_by`: a `str`.
- Field `source`: a `str`.

`src/notes_evidence/application/evidence_collect.py` lines 55 to 64:

```python
def collect_access(
    collector: Collector, repository: RepositoryAccess, database: DatabaseAccess, cloud: CloudDirectory
) -> AccessList:
    """C1: ask each system who can reach it, and write the list."""
    entries: list[AccessEntry] = [*repository.collaborators(), *database.roles(), *cloud.users()]
    access = AccessList(collector.clock.now(), tuple(entries))
    collector.store.write(
        ACCESS_FILE, render_access_list(access), "C1", access.generated_at, collector.run_by, collector.source
    )
    return access
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `*items` **unpacks** a sequence into separate values; `**options` does the same for a dictionary's keys and values.

**Function `collect_access`.** C1: ask each system who can reach it, and write the list.

It takes: `collector` (a `Collector`); `repository` (a `RepositoryAccess`); `database` (a `DatabaseAccess`); `cloud` (a `CloudDirectory`).

It gives back a `AccessList`.

Step by step:

- Declares `entries` as a `list[AccessEntry]` and stores the list `[*repository.collaborators(), *database.roles(), *cloud.users()]` in it.
- Stores the result of calling `AccessList(collector.clock.now(), tuple(entries))` in `access`.
- Calls `collector.store.write(ACCESS_FILE, render_access_list(access), 'C1', access.generated_at, collector.run_by, c…`.
- Gives back `access`.

`src/notes_evidence/application/evidence_collect.py` lines 67 to 73:

```python
def collect_changes(collector: Collector, changes: ChangeSource) -> int:
    """C2: write every merged change with its approvers and its deployment; return how many have exceptions."""
    merged = changes.merged_changes()
    collector.store.write(
        CHANGES_FILE, render_changes(merged), "C2", collector.clock.now(), collector.run_by, collector.source
    )
    return len(find_exceptions(merged))
```

**Function `collect_changes`.** C2: write every merged change with its approvers and its deployment; return how many have exceptions.

It takes: `collector` (a `Collector`); `changes` (a `ChangeSource`).

It gives back a `int`.

Step by step:

- Stores the result of calling `changes.merged_changes()` in `merged`.
- Calls `collector.store.write(CHANGES_FILE, render_changes(merged), 'C2', collector.clock.now(), collector.run_by, co…`.
- Gives back the result of calling `len(find_exceptions(merged))`.

`src/notes_evidence/application/evidence_collect.py` lines 76 to 81:

```python
def collect_log_sample(collector: Collector, audit: AuditLog, limit: int = 20) -> int:
    """C3: the most recent audit events, rendered as the log lines the service writes."""
    events = audit.latest(limit)
    text = "\n".join(render_line(event) for event in events) + "\n"
    collector.store.write(LOG_FILE, text, "C3", collector.clock.now(), collector.run_by, collector.source)
    return len(events)
```

> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Function `collect_log_sample`.** C3: the most recent audit events, rendered as the log lines the service writes.

It takes: `collector` (a `Collector`); `audit` (a `AuditLog`); `limit` (a `int`), default `20`.

It gives back a `int`.

Step by step:

- Stores the result of calling `audit.latest(limit)` in `events`.
- Stores `'\n'.join((render_line(event) for event in events)) + '\n'` in `text`.
- Calls `collector.store.write(LOG_FILE, text, 'C3', collector.clock.now(), collector.run_by, collector.source)`.
- Gives back the result of calling `len(events)`.

`src/notes_evidence/application/evidence_collect.py` lines 84 to 115:

```python
def run_alert_test(
    collector: Collector,
    notes: Notes,
    audit: AuditLog,
    sink: AlertSink,
    grant_admin: Callable[[], object],
    username: str,
    attempts: int = 5,
) -> list[Alert]:
    """C3: do what the alert is for, read the trail back, and keep the alert message beside the time of the action.

    Five wrong passwords for one account, then an admin grant. Each is a real call into the service, so the alert fires
    on what the log really holds and not on the rule's configuration.
    """
    started = collector.clock.now()
    for _ in range(attempts):
        with contextlib.suppress(InvalidCredentialsError):
            notes.login(username, secrets.token_urlsafe(16))
    grant_admin()
    alerts = detect_alerts(audit.since(started))
    for alert in alerts:
        sink.send(alert.render())
    lines = [
        f"alert test: {attempts} wrong passwords for account {username}, then an admin role grant",
        f"test action at {format_timestamp(started)}",
        f"{len(alerts)} alert(s) delivered:",
        *[alert.render() for alert in alerts],
    ]
    collector.store.write(
        ALERT_FILE, "\n".join(lines) + "\n", "C3", collector.clock.now(), collector.run_by, collector.source
    )
    return alerts
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Function `run_alert_test`.** C3: do what the alert is for, read the trail back, and keep the alert message beside the time of the action. Five wrong passwords for one account, then an admin grant. Each is a real call into the service, so the alert fires on what the log really holds and not on the rule's configuration.

It takes: `collector` (a `Collector`); `notes` (a `Notes`); `audit` (a `AuditLog`); `sink` (a `AlertSink`); `grant_admin` (a `Callable[[], object]`); `username` (a `str`); `attempts` (a `int`), default `5`.

It gives back a `list[Alert]`.

Step by step:

- Stores the result of calling `collector.clock.now()` in `started`.
- For each `_` in the result of calling `range(attempts)`:
  - Inside a `with` block that opens `contextlib.suppress(InvalidCredentialsError)`:
    - Calls `notes.login(username, secrets.token_urlsafe(16))`.
- Calls `grant_admin()`.
- Stores the result of calling `detect_alerts(audit.since(started))` in `alerts`.
- For each `alert` in `alerts`:
  - Calls `sink.send(alert.render())`.
- Stores the list `[f'alert test: {attempts} wrong passwords for account {username}, the…` in `lines`.
- Calls `collector.store.write(ALERT_FILE, '\n'.join(lines) + '\n', 'C3', collector.clock.now(), collector.run_by, col…`.
- Gives back `alerts`.

`src/notes_evidence/application/evidence_collect.py` lines 118 to 127:

```python
def run_restore_test(collector: Collector, runner: BackupRunner, table: str = "notes") -> RestoreResult:
    """C4: back up, restore into a scratch database, count the rows, and time the restore."""
    backup_taken_at = runner.backup()
    started = collector.clock.now()
    source_rows, restored_rows = runner.restore_and_count(table)
    result = RestoreResult(backup_taken_at, started, collector.clock.now(), table, source_rows, restored_rows)
    collector.store.write(
        RESTORE_FILE, render_restore(result), "C4", result.finished_at, collector.run_by, collector.source
    )
    return result
```

**Function `run_restore_test`.** C4: back up, restore into a scratch database, count the rows, and time the restore.

It takes: `collector` (a `Collector`); `runner` (a `BackupRunner`); `table` (a `str`), default `'notes'`.

It gives back a `RestoreResult`.

Step by step:

- Stores the result of calling `runner.backup()` in `backup_taken_at`.
- Stores the result of calling `collector.clock.now()` in `started`.
- Unpacks the result of calling `runner.restore_and_count(table)` into `(source_rows, restored_rows)`.
- Stores the result of calling `RestoreResult(backup_taken_at, started, collector.clock.now(), table, source_rows, restor…` in `result`.
- Calls `collector.store.write(RESTORE_FILE, render_restore(result), 'C4', result.finished_at, collector.run_by, colle…`.
- Gives back `result`.

`src/notes_evidence/application/evidence_collect.py` lines 130 to 134:

```python
def collect_scan(collector: Collector, scanner: ScanRunner) -> str:
    """C5: run the dependency scan and keep the report; return its verdict."""
    report = scanner.scan()
    collector.store.write(SCAN_FILE, report.to_json(), "C5", report.scanned_at, collector.run_by, collector.source)
    return report.verdict
```

**Function `collect_scan`.** C5: run the dependency scan and keep the report; return its verdict.

It takes: `collector` (a `Collector`); `scanner` (a `ScanRunner`).

It gives back a `str`.

Step by step:

- Stores the result of calling `scanner.scan()` in `report`.
- Calls `collector.store.write(SCAN_FILE, report.to_json(), 'C5', report.scanned_at, collector.run_by, collector.sourc…`.
- Gives back `report.verdict`.

`src/notes_evidence/application/evidence_collect.py` lines 137 to 143:

```python
@dataclass(frozen=True)
class ReviewOutcome:
    """The access review: the problems with the reviewer's answers, or the lists before and after."""

    findings: tuple[Finding, ...]
    before: AccessList | None
    after: AccessList | None
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.

**Class `ReviewOutcome`**. The access review: the problems with the reviewer's answers, or the lists before and after. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `findings`: a `tuple[Finding, ...]`.
- Field `before`: a `AccessList | None`.
- Field `after`: a `AccessList | None`.

`src/notes_evidence/application/evidence_collect.py` lines 146 to 171:

```python
def review_access(
    collector: Collector,
    repository: RepositoryAccess,
    database: DatabaseAccess,
    cloud: CloudDirectory,
    catalog: ControlCatalog,
) -> ReviewOutcome:
    """C6: take the C1 list, check every access was decided, remove what was refused, prove it by running C1 again."""
    before = collect_access(collector, repository, database, cloud)
    request: ReviewRequest = catalog.review_request()
    problems = check_review(before, request, catalog.people())
    if problems:
        return ReviewOutcome(tuple(problems), before, None)
    for decision in request.decisions:
        if not decision.keep:
            _remove(decision.system, decision.principal, cloud)
    after = collect_access(collector, repository, database, cloud)
    collector.store.write(
        REVIEW_FILE,
        render_review(before, after, request),
        "C6",
        collector.clock.now(),
        collector.run_by,
        collector.source,
    )
    return ReviewOutcome((), before, after)
```

**Function `review_access`.** C6: take the C1 list, check every access was decided, remove what was refused, prove it by running C1 again.

It takes: `collector` (a `Collector`); `repository` (a `RepositoryAccess`); `database` (a `DatabaseAccess`); `cloud` (a `CloudDirectory`); `catalog` (a `ControlCatalog`).

It gives back a `ReviewOutcome`.

Step by step:

- Stores the result of calling `collect_access(collector, repository, database, cloud)` in `before`.
- Declares `request` as a `ReviewRequest` and stores the result of calling `catalog.review_request()` in it.
- Stores the result of calling `check_review(before, request, catalog.people())` in `problems`.
- If `problems`:
  - Gives back the result of calling `ReviewOutcome(tuple(problems), before, None)`.
- For each `decision` in `request.decisions`:
  - If not (`decision.keep`):
    - Calls `_remove(decision.system, decision.principal, cloud)`.
- Stores the result of calling `collect_access(collector, repository, database, cloud)` in `after`.
- Calls `collector.store.write(REVIEW_FILE, render_review(before, after, request), 'C6', collector.clock.now(), collec…`.
- Gives back the result of calling `ReviewOutcome((), before, after)`.

`src/notes_evidence/application/evidence_collect.py` lines 174 to 178:

```python
def _remove(system: str, principal: str, cloud: CloudDirectory) -> None:
    if system.startswith("cloud"):
        cloud.remove_user(principal)
        return
    raise NotImplementedError(f"removal from {system} is done by its owner; this build removes cloud users")
```

> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

**Function `_remove`.**

It takes: `system` (a `str`); `principal` (a `str`); `cloud` (a `CloudDirectory`).

It gives back a `None`.

Step by step:

- If `system.startswith('cloud')`:
  - Calls `cloud.remove_user(principal)`.
  - Ends the function and gives back nothing.
- Stops here by raising `NotImplementedError(f'removal from {system} is done by its owner; this build removes cloud users')`.

`src/notes_evidence/application/evidence_collect.py` lines 181 to 212:

```python
def build_index(collector: Collector, catalog: ControlCatalog, framework_markdown: str) -> str:
    """INDEX.md: one line per artifact (file, control, what it proves, who ran it, date), the exceptions, the gaps."""
    manifest = collector.store.manifest()
    controls, exceptions, gaps = catalog.controls(), catalog.exceptions(), catalog.gaps()
    lines = [
        "# Evidence pack index",
        "",
        f"Pack date: {format_timestamp(collector.clock.now())}. Each file below was produced by a command in this"
        " repository (`make evidence`); `manifest.json` records its hash, so a hand edit fails `make verify`.",
        "",
        "| File | Control | Proves | Run by | Date | Period | Refreshed |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for control in controls:
        for spec in control.evidence:
            entry = manifest.get(spec.file)
            ran = f"{entry.run_by} | {entry.produced_at.date().isoformat()}" if entry else "not produced | -"
            lines.append(
                f"| {spec.file} | {control.id} {control.name} | {spec.proves} | {ran} "
                f"| {spec.period} | {spec.refreshed} |"
            )
    lines += ["", "## Exceptions", ""]
    for item in exceptions:
        lines.append(f"- {item.id} ({item.control}): {item.description} Follow-up: {item.followup.rstrip('.')}.")
    if not exceptions:
        lines.append("None.")
    lines += ["", "## Tracked gaps", ""]
    lines += [f"- {gap.control}: {gap.reason} Ticket {gap.ticket}, due {gap.due}." for gap in gaps] or ["None."]
    lines += ["", "## Framework mapping", "", framework_markdown, ""]
    text = "\n".join(lines)
    collector.store.write("INDEX.md", text, "-", collector.clock.now(), collector.run_by, collector.source)
    return text
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `build_index`.** INDEX.md: one line per artifact (file, control, what it proves, who ran it, date), the exceptions, the gaps.

It takes: `collector` (a `Collector`); `catalog` (a `ControlCatalog`); `framework_markdown` (a `str`).

It gives back a `str`.

Step by step:

- Stores the result of calling `collector.store.manifest()` in `manifest`.
- Unpacks the tuple `(catalog.controls(), catalog.exceptions(), catalog.gaps())` into `(controls, exceptions, gaps)`.
- Stores the list `['# Evidence pack index', '', f'Pack date: {format_timestamp(collecto…` in `lines`.
- For each `control` in `controls`:
  - For each `spec` in `control.evidence`:
    - Stores the result of calling `manifest.get(spec.file)` in `entry`.
    - Stores `f'{entry.run_by} | {entry.produced_at.d…` if `entry`, otherwise `'not produced | -'` in `ran`.
    - Calls `lines.append(f'| {spec.file} | {control.id} {control.name} | {spec.proves} | {ran} | {spec.period} | {spec.re…`.
- Adds the list `['', '## Exceptions', '']` to `lines`.
- For each `item` in `exceptions`:
  - Calls `lines.append(f"- {item.id} ({item.control}): {item.description} Follow-up: {item.followup.rstrip('.')}.")`.
- If not (`exceptions`):
  - Calls `lines.append('None.')`.
- Adds the list `['', '## Tracked gaps', '']` to `lines`.
- Adds whether `[f'- {gap.control}: {gap.reason} Ticket {gap.ticket}, due {gap.due}.'…` or `['None.']` to `lines`.
- Adds the list `['', '## Framework mapping', '', framework_markdown, '']` to `lines`.
- Stores the result of calling `'\n'.join(lines)` in `text`.
- Calls `collector.store.write('INDEX.md', text, '-', collector.clock.now(), collector.run_by, collector.source)`.
- Gives back `text`.

`src/notes_evidence/application/evidence_collect.py` lines 215 to 225:

```python
def verify(
    store: EvidenceStore, controls: list[Control], exceptions: list[RecordedException], gaps: list[Gap], today: date
) -> Report:
    """Every control maps to evidence, every file exists and says what it should, nothing was edited by hand."""
    files = store.read_all()
    manifest = store.manifest()
    findings = verify_pack(controls, manifest, files, exceptions, gaps, today)
    if "INDEX.md" not in files:
        findings.append(error("EVD002", "INDEX.md", "the index is missing: run `make evidence`"))
    subjects = tuple(sorted(files))
    return Report(subjects, tuple(findings))
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `verify`.** Every control maps to evidence, every file exists and says what it should, nothing was edited by hand.

It takes: `store` (a `EvidenceStore`); `controls` (a `list[Control]`); `exceptions` (a `list[RecordedException]`); `gaps` (a `list[Gap]`); `today` (a `date`).

It gives back a `Report`.

Step by step:

- Stores the result of calling `store.read_all()` in `files`.
- Stores the result of calling `store.manifest()` in `manifest`.
- Stores the result of calling `verify_pack(controls, manifest, files, exceptions, gaps, today)` in `findings`.
- If `'INDEX.md'` is not in `files`:
  - Calls `findings.append(error('EVD002', 'INDEX.md', 'the index is missing: run `make evidence`'))`.
- Stores the result of calling `tuple(sorted(files))` in `subjects`.
- Gives back the result of calling `Report(subjects, tuple(findings))`.

### `src/notes_evidence/application/exercise.py`

`src/notes_evidence/application/exercise.py` lines 1 to 13:

```python
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
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** A scripted day of use, so the audit trail holds real events from real calls into the service.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `secrets`.
- From `collections.abc` it takes `Callable`.
- From `dataclasses` it takes `dataclass`.
- From `notes_evidence.application.notes_service` it takes `NotesService`.
- From `notes_evidence.application.ports` it takes `PasswordHasher, UserProvisioner`.
- From `notes_evidence.domain.errors` it takes `NotAllowedError, NotFoundError`.
- From `notes_evidence.domain.notes` it takes `User`.
- From `notes_evidence.domain.roles` it takes `Role`.

`src/notes_evidence/application/exercise.py` lines 15 to 15:

```python
ROSTER = (("ada", Role.ADMIN), ("bruno", Role.MEMBER), ("chen", Role.MEMBER), ("dana", Role.READONLY))
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the tuple `(('ada', Role.ADMIN), ('bruno', Role.MEMBER), ('chen', Role.MEMBER), …` in `ROSTER`.

`src/notes_evidence/application/exercise.py` lines 18 to 24:

```python
@dataclass(frozen=True)
class ExerciseSummary:
    """What the scripted day did: how many notes were written, and how many requests the service refused."""

    users: dict[str, User]
    notes_created: int
    refusals: int
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `ExerciseSummary`**. What the scripted day did: how many notes were written, and how many requests the service refused. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `users`: a `dict[str, User]`.
- Field `notes_created`: a `int`.
- Field `refusals`: a `int`.

`src/notes_evidence/application/exercise.py` lines 27 to 52:

```python
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
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.

**Function `exercise_service`.** Create the four accounts with throwaway passwords that exist only in this process, then use the service as each. The passwords are generated here, hashed, and dropped when the function returns; none is stored or printed.

It takes: `provisioner` (a `UserProvisioner`); `hasher` (a `PasswordHasher`); `service` (a `NotesService`); `new_password` (a `Callable[[], str]`), default `lambda: secrets.token_urlsafe…`.

It gives back a `ExerciseSummary`.

Step by step:

- Stores a new dictionary made by a loop (`{name: new_password() for name, _ in ROSTER}`) in `passwords`.
- For each `(name, role)` in `ROSTER`:
  - Calls `provisioner.provision(name, role, hasher.hash(passwords[name]))`.
- Stores a new dictionary made by a loop (`{name: service.authenticate(service.login(name, passwords[name])) for…`) in `actors`.
- Stores the number `0` in `created`.
- Stores the result of calling `service.create_note(actors['bruno'], 'Call back on Tuesday', 'Customer asked for a quote.…` in `first`.
- Stores the result of calling `service.create_note(actors['chen'], 'Delivery address check', 'Confirmed by phone.')` in `second`.
- Calls `service.create_note(actors['bruno'], 'Renewal reminder', 'Renewal is due next month.')`.
- Adds the number `3` to `created`.
- Calls `service.get_note(actors['bruno'], first.id)`.
- Calls `service.update_note(actors['bruno'], first.id, 'Call back on Wednesday', 'Customer moved the call.')`.
- Calls `service.get_note(actors['dana'], second.id)`.
- Stores the result of calling `_refused(lambda: service.get_note(actors['bruno'], second.id))` in `refusals`.
- Adds the result of calling `_refused(lambda: service.create_note(actors['dana'], 'Not allowed', 'No writing.'))` to `refusals`.
- Calls `service.delete_note(actors['chen'], second.id)`.
- Gives back the result of calling `ExerciseSummary(actors, created, refusals)`.

`src/notes_evidence/application/exercise.py` lines 55 to 61:

```python
def _refused(call: Callable[[], object]) -> int:
    """1 when the service refuses the call, 0 when it goes through."""
    try:
        call()
    except (NotFoundError, NotAllowedError):
        return 1
    return 0
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.

**Function `_refused`.** 1 when the service refuses the call, 0 when it goes through.

It takes: `call` (a `Callable[[], object]`).

It gives back a `int`.

Step by step:

- Tries:
  - Calls `call()`.
- If `(NotFoundError, NotAllowedError)` happens:
  - Gives back the number `1`.
- Gives back the number `0`.

### `src/notes_evidence/application/notes_service.py`

`src/notes_evidence/application/notes_service.py` lines 1 to 16:

```python
"""The notes service: every use case checks the role, then records what happened."""

from __future__ import annotations

from notes_evidence.application.ports import (
    AuditLog,
    Clock,
    NoteRepository,
    PasswordHasher,
    TokenService,
    UserRepository,
)
from notes_evidence.domain.audit import AuditAction, AuditEvent
from notes_evidence.domain.errors import InvalidCredentialsError, NotAllowedError, NotAuthenticatedError, NotFoundError
from notes_evidence.domain.notes import USERNAME, Note, User, validate_note, validate_username
from notes_evidence.domain.roles import Permission, Role, allowed
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The notes service: every use case checks the role, then records what happened.

Imports:

- From `__future__` it takes `annotations`.
- From `notes_evidence.application.ports` it takes `AuditLog, Clock, NoteRepository, PasswordHasher, TokenService, UserRepository`.
- From `notes_evidence.domain.audit` it takes `AuditAction, AuditEvent`.
- From `notes_evidence.domain.errors` it takes `InvalidCredentialsError, NotAllowedError, NotAuthenticatedError, NotFoundError`.
- From `notes_evidence.domain.notes` it takes `USERNAME, Note, User, validate_note, validate_username`.
- From `notes_evidence.domain.roles` it takes `Permission, Role, allowed`.

`src/notes_evidence/application/notes_service.py` lines 18 to 18:

```python
_UNKNOWN = "unknown"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'unknown'` in `_UNKNOWN`.

`src/notes_evidence/application/notes_service.py` lines 21 to 22:

```python
class NotesService:
    """Logins, notes and role grants for the notes API. The audit trail holds who and what, never the note's text."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.

**Class `NotesService`**. Logins, notes and role grants for the notes API. The audit trail holds who and what, never the note's text.

`src/notes_evidence/application/notes_service.py` lines 24 to 38:

```python
    def __init__(
        self,
        users: UserRepository,
        notes: NoteRepository,
        audit: AuditLog,
        hasher: PasswordHasher,
        tokens: TokenService,
        clock: Clock,
    ) -> None:
        self._users = users
        self._notes = notes
        self._audit = audit
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.

**Method `__init__` of class `NotesService`.**

It takes: `users` (a `UserRepository`); `notes` (a `NoteRepository`); `audit` (a `AuditLog`); `hasher` (a `PasswordHasher`); `tokens` (a `TokenService`); `clock` (a `Clock`).

It gives back a `None`.

Step by step:

- Stores `users` in `self._users`.
- Stores `notes` in `self._notes`.
- Stores `audit` in `self._audit`.
- Stores `hasher` in `self._hasher`.
- Stores `tokens` in `self._tokens`.
- Stores `clock` in `self._clock`.

`src/notes_evidence/application/notes_service.py` lines 40 to 49:

```python
    def login(self, username: str, password: str) -> str:
        """A token for a valid username and password. A failure is recorded and never says which half was wrong."""
        name = username if isinstance(username, str) and USERNAME.match(username) else _UNKNOWN
        found = self._users.find_by_username(name) if name != _UNKNOWN else None
        if found is None or not found[0].active or not self._hasher.verify(password, found[1]):
            self._record(found[0] if found else None, name, AuditAction.LOGIN_FAILED, None, "failed")
            raise InvalidCredentialsError("invalid username or password")
        user = found[0]
        self._record(user, user.username, AuditAction.LOGIN_OK, None, "ok")
        return self._tokens.issue(user, self._clock.now())
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **regular expression** is a short pattern for text, such as `^## (.+)$` for "a line starting with ## ". `re.compile` prepares it once; `.match` tries it at the start of a string and returns a match object or `None`.

**Method `login` of class `NotesService`.** A token for a valid username and password. A failure is recorded and never says which half was wrong.

It takes: `username` (a `str`); `password` (a `str`).

It gives back a `str`.

Step by step:

- Stores `username` if `isinstance(username, str)` and `USERNAME.match(username)`, otherwise `_UNKNOWN` in `name`.
- Stores `self._users.find_by_username(name)` if `name` is different from `_UNKNOWN`, otherwise `None` in `found`.
- If `found` is the same object as `None` or not (`found[0].active`) or not (`self._hasher.verify(password, found[1])`):
  - Calls `self._record(found[0] if found else None, name, AuditAction.LOGIN_FAILED, None, 'failed')`.
  - Stops here by raising `InvalidCredentialsError('invalid username or password')`.
- Stores `found[0]` in `user`.
- Calls `self._record(user, user.username, AuditAction.LOGIN_OK, None, 'ok')`.
- Gives back the result of calling `self._tokens.issue(user, self._clock.now())`.

`src/notes_evidence/application/notes_service.py` lines 51 to 57:

```python
    def authenticate(self, token: str) -> User:
        """The active user a token names; NotAuthenticatedError for a forged or expired token or a disabled account."""
        user_id = self._tokens.verify(token, self._clock.now())
        user = self._users.find_by_id(user_id) if user_id is not None else None
        if user is None or not user.active:
            raise NotAuthenticatedError("invalid or expired token")
        return user
```

**Method `authenticate` of class `NotesService`.** The active user a token names; NotAuthenticatedError for a forged or expired token or a disabled account.

It takes: `token` (a `str`).

It gives back a `User`.

Step by step:

- Stores the result of calling `self._tokens.verify(token, self._clock.now())` in `user_id`.
- Stores `self._users.find_by_id(user_id)` if `user_id` is not the same object as `None`, otherwise `None` in `user`.
- If `user` is the same object as `None` or not (`user.active`):
  - Stops here by raising `NotAuthenticatedError('invalid or expired token')`.
- Gives back `user`.

`src/notes_evidence/application/notes_service.py` lines 59 to 65:

```python
    def create_note(self, actor: User, title: object, body: object) -> Note:
        """Store a note owned by the actor."""
        self._require(actor, Permission.WRITE_OWN, None)
        data = validate_note(title, body)
        note = self._notes.add(actor.id, data.title, data.body, self._clock.now())
        self._record(actor, actor.username, AuditAction.NOTE_CREATED, note.id, "ok")
        return note
```

**Method `create_note` of class `NotesService`.** Store a note owned by the actor.

It takes: `actor` (a `User`); `title` (a `object`); `body` (a `object`).

It gives back a `Note`.

Step by step:

- Calls `self._require(actor, Permission.WRITE_OWN, None)`.
- Stores the result of calling `validate_note(title, body)` in `data`.
- Stores the result of calling `self._notes.add(actor.id, data.title, data.body, self._clock.now())` in `note`.
- Calls `self._record(actor, actor.username, AuditAction.NOTE_CREATED, note.id, 'ok')`.
- Gives back `note`.

`src/notes_evidence/application/notes_service.py` lines 67 to 71:

```python
    def get_note(self, actor: User, note_id: int) -> Note:
        """A note the actor may read. A note that belongs to someone else reads as not found to a member."""
        note = self._visible(actor, note_id, Permission.READ_ANY)
        self._record(actor, actor.username, AuditAction.NOTE_READ, note.id, "ok")
        return note
```

**Method `get_note` of class `NotesService`.** A note the actor may read. A note that belongs to someone else reads as not found to a member.

It takes: `actor` (a `User`); `note_id` (a `int`).

It gives back a `Note`.

Step by step:

- Stores the result of calling `self._visible(actor, note_id, Permission.READ_ANY)` in `note`.
- Calls `self._record(actor, actor.username, AuditAction.NOTE_READ, note.id, 'ok')`.
- Gives back `note`.

`src/notes_evidence/application/notes_service.py` lines 73 to 76:

```python
    def list_notes(self, actor: User) -> list[Note]:
        """Every note for a role that may read any, otherwise the actor's own."""
        owner = None if allowed(actor.role, Permission.READ_ANY) else actor.id
        return self._notes.list_for(owner)
```

**Method `list_notes` of class `NotesService`.** Every note for a role that may read any, otherwise the actor's own.

It takes: `actor` (a `User`).

It gives back a `list[Note]`.

Step by step:

- Stores `None` if `allowed(actor.role, Permission.READ_ANY)`, otherwise `actor.id` in `owner`.
- Gives back the result of calling `self._notes.list_for(owner)`.

`src/notes_evidence/application/notes_service.py` lines 78 to 87:

```python
    def update_note(self, actor: User, note_id: int, title: object, body: object) -> Note:
        """Replace a note the actor may write."""
        self._require(actor, Permission.WRITE_OWN, note_id)
        data = validate_note(title, body)
        self._visible(actor, note_id, Permission.WRITE_ANY)
        note = self._notes.update(note_id, data.title, data.body, self._clock.now())
        if note is None:
            raise NotFoundError("note not found")
        self._record(actor, actor.username, AuditAction.NOTE_UPDATED, note.id, "ok")
        return note
```

**Method `update_note` of class `NotesService`.** Replace a note the actor may write.

It takes: `actor` (a `User`); `note_id` (a `int`); `title` (a `object`); `body` (a `object`).

It gives back a `Note`.

Step by step:

- Calls `self._require(actor, Permission.WRITE_OWN, note_id)`.
- Stores the result of calling `validate_note(title, body)` in `data`.
- Calls `self._visible(actor, note_id, Permission.WRITE_ANY)`.
- Stores the result of calling `self._notes.update(note_id, data.title, data.body, self._clock.now())` in `note`.
- If `note` is the same object as `None`:
  - Stops here by raising `NotFoundError('note not found')`.
- Calls `self._record(actor, actor.username, AuditAction.NOTE_UPDATED, note.id, 'ok')`.
- Gives back `note`.

`src/notes_evidence/application/notes_service.py` lines 89 to 94:

```python
    def delete_note(self, actor: User, note_id: int) -> None:
        """Delete a note the actor may write."""
        self._require(actor, Permission.WRITE_OWN, note_id)
        self._visible(actor, note_id, Permission.WRITE_ANY)
        self._notes.delete(note_id)
        self._record(actor, actor.username, AuditAction.NOTE_DELETED, note_id, "ok")
```

**Method `delete_note` of class `NotesService`.** Delete a note the actor may write.

It takes: `actor` (a `User`); `note_id` (a `int`).

It gives back a `None`.

Step by step:

- Calls `self._require(actor, Permission.WRITE_OWN, note_id)`.
- Calls `self._visible(actor, note_id, Permission.WRITE_ANY)`.
- Calls `self._notes.delete(note_id)`.
- Calls `self._record(actor, actor.username, AuditAction.NOTE_DELETED, note_id, 'ok')`.

`src/notes_evidence/application/notes_service.py` lines 96 to 114:

```python
    def grant_role(self, actor: User, target_username: str, role: Role) -> User:
        """Change another user's role; an admin grant is what the alert watches for."""
        self._require(actor, Permission.GRANT_ROLE, None)
        found = self._users.find_by_username(validate_username(target_username))
        if found is None:
            raise NotFoundError("user not found")
        self._users.set_role(found[0].id, role)
        self._audit.append(
            AuditEvent(
                self._clock.now(),
                actor.id,
                actor.username,
                AuditAction.ROLE_GRANTED,
                None,
                "ok",
                {"role": role.value, "target": found[0].username},
            )
        )
        return User(found[0].id, found[0].username, role, found[0].active)
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Method `grant_role` of class `NotesService`.** Change another user's role; an admin grant is what the alert watches for.

It takes: `actor` (a `User`); `target_username` (a `str`); `role` (a `Role`).

It gives back a `User`.

Step by step:

- Calls `self._require(actor, Permission.GRANT_ROLE, None)`.
- Stores the result of calling `self._users.find_by_username(validate_username(target_username))` in `found`.
- If `found` is the same object as `None`:
  - Stops here by raising `NotFoundError('user not found')`.
- Calls `self._users.set_role(found[0].id, role)`.
- Calls `self._audit.append(AuditEvent(self._clock.now(), actor.id, actor.username, AuditAction.ROLE_GRANTED, None, 'o…`.
- Gives back the result of calling `User(found[0].id, found[0].username, role, found[0].active)`.

`src/notes_evidence/application/notes_service.py` lines 116 to 121:

```python
    def _visible(self, actor: User, note_id: int, override: Permission) -> Note:
        note = self._notes.get(note_id)
        if note is None or (note.owner_id != actor.id and not allowed(actor.role, override)):
            self._record(actor, actor.username, AuditAction.ACCESS_DENIED, note_id, "denied")
            raise NotFoundError("note not found")
        return note
```

**Method `_visible` of class `NotesService`.**

It takes: `actor` (a `User`); `note_id` (a `int`); `override` (a `Permission`).

It gives back a `Note`.

Step by step:

- Stores the result of calling `self._notes.get(note_id)` in `note`.
- If `note` is the same object as `None` or `note.owner_id` is different from `actor.id` and not (`allowed(actor.role, override)`):
  - Calls `self._record(actor, actor.username, AuditAction.ACCESS_DENIED, note_id, 'denied')`.
  - Stops here by raising `NotFoundError('note not found')`.
- Gives back `note`.

`src/notes_evidence/application/notes_service.py` lines 123 to 126:

```python
    def _require(self, actor: User, permission: Permission, note_id: int | None) -> None:
        if not allowed(actor.role, permission):
            self._record(actor, actor.username, AuditAction.ACCESS_DENIED, note_id, "denied")
            raise NotAllowedError(f"role {actor.role.value} may not do this")
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Method `_require` of class `NotesService`.**

It takes: `actor` (a `User`); `permission` (a `Permission`); `note_id` (a `int | None`).

It gives back a `None`.

Step by step:

- If not (`allowed(actor.role, permission)`):
  - Calls `self._record(actor, actor.username, AuditAction.ACCESS_DENIED, note_id, 'denied')`.
  - Stops here by raising `NotAllowedError(f'role {actor.role.value} may not do this')`.

`src/notes_evidence/application/notes_service.py` lines 128 to 129:

```python
    def _record(self, user: User | None, username: str, action: AuditAction, note_id: int | None, outcome: str) -> None:
        self._audit.append(AuditEvent(self._clock.now(), user.id if user else None, username, action, note_id, outcome))
```

**Method `_record` of class `NotesService`.**

It takes: `user` (a `User | None`); `username` (a `str`); `action` (a `AuditAction`); `note_id` (a `int | None`); `outcome` (a `str`).

It gives back a `None`.

Step by step:

- Calls `self._audit.append(AuditEvent(self._clock.now(), user.id if user else None, username, action, note_id, outcom…`.

### `src/notes_evidence/application/ports.py`

`src/notes_evidence/application/ports.py` lines 1 to 16:

```python
"""What the use cases need from the outside world: ports, implemented by adapters in infrastructure."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from notes_evidence.domain.access import AccessEntry
from notes_evidence.domain.audit import AuditEvent
from notes_evidence.domain.changes import MergedChange
from notes_evidence.domain.controls import Control, Gap, RecordedException
from notes_evidence.domain.evidence import ManifestEntry
from notes_evidence.domain.notes import Note, User
from notes_evidence.domain.review import Person, ReviewRequest
from notes_evidence.domain.roles import Role
from notes_evidence.domain.scan import ScanReport
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** What the use cases need from the outside world: ports, implemented by adapters in infrastructure.

Imports:

- From `__future__` it takes `annotations`.
- From `datetime` it takes `datetime`.
- From `typing` it takes `Protocol`.
- From `notes_evidence.domain.access` it takes `AccessEntry`.
- From `notes_evidence.domain.audit` it takes `AuditEvent`.
- From `notes_evidence.domain.changes` it takes `MergedChange`.
- From `notes_evidence.domain.controls` it takes `Control, Gap, RecordedException`.
- From `notes_evidence.domain.evidence` it takes `ManifestEntry`.
- From `notes_evidence.domain.notes` it takes `Note, User`.
- From `notes_evidence.domain.review` it takes `Person, ReviewRequest`.
- From `notes_evidence.domain.roles` it takes `Role`.
- From `notes_evidence.domain.scan` it takes `ScanReport`.

`src/notes_evidence/application/ports.py` lines 19 to 24:

```python
class Clock(Protocol):
    """The current time, injected so tests are deterministic."""

    def now(self) -> datetime:
        """The current moment, timezone aware."""
        ...
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **Protocol** describes the methods an object must have, without requiring inheritance. Any class with those methods fits. A body of `...` means "no code here, only the shape".
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.

**Class `Clock`**, a kind of `Protocol`. The current time, injected so tests are deterministic.

Its methods, in order:

**Method `now` of class `Clock`.** The current moment, timezone aware.

It gives back a `datetime`.

`src/notes_evidence/application/ports.py` lines 27 to 40:

```python
class UserRepository(Protocol):
    """Accounts and their password hashes."""

    def find_by_username(self, username: str) -> tuple[User, str] | None:
        """The user and the stored password hash, or None."""
        ...

    def find_by_id(self, user_id: int) -> User | None:
        """The user, or None."""
        ...

    def set_role(self, user_id: int, role: Role) -> None:
        """Change a user's role."""
        ...
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Class `UserRepository`**, a kind of `Protocol`. Accounts and their password hashes.

Its methods, in order:

**Method `find_by_username` of class `UserRepository`.** The user and the stored password hash, or None.

It takes: `username` (a `str`).

It gives back a `tuple[User, str] | None`.

**Method `find_by_id` of class `UserRepository`.** The user, or None.

It takes: `user_id` (a `int`).

It gives back a `User | None`.

**Method `set_role` of class `UserRepository`.** Change a user's role.

It takes: `user_id` (a `int`); `role` (a `Role`).

It gives back a `None`.

`src/notes_evidence/application/ports.py` lines 43 to 48:

```python
class UserProvisioner(Protocol):
    """Creates accounts with a given password hash. Only an administrative connection holds this power."""

    def provision(self, username: str, role: Role, password_hash: str) -> User:
        """Create the user, or reset its role and password hash when it exists."""
        ...
```

**Class `UserProvisioner`**, a kind of `Protocol`. Creates accounts with a given password hash. Only an administrative connection holds this power.

Its methods, in order:

**Method `provision` of class `UserProvisioner`.** Create the user, or reset its role and password hash when it exists.

It takes: `username` (a `str`); `role` (a `Role`); `password_hash` (a `str`).

It gives back a `User`.

`src/notes_evidence/application/ports.py` lines 51 to 72:

```python
class NoteRepository(Protocol):
    """Notes."""

    def add(self, owner_id: int, title: str, body: str, at: datetime) -> Note:
        """Store a new note."""
        ...

    def get(self, note_id: int) -> Note | None:
        """One note or None."""
        ...

    def list_for(self, owner_id: int | None) -> list[Note]:
        """One owner's notes, or every note when the owner is None."""
        ...

    def update(self, note_id: int, title: str, body: str, at: datetime) -> Note | None:
        """Replace a note's text; None when it does not exist."""
        ...

    def delete(self, note_id: int) -> bool:
        """Delete a note; False when it did not exist."""
        ...
```

**Class `NoteRepository`**, a kind of `Protocol`. Notes.

Its methods, in order:

**Method `add` of class `NoteRepository`.** Store a new note.

It takes: `owner_id` (a `int`); `title` (a `str`); `body` (a `str`); `at` (a `datetime`).

It gives back a `Note`.

**Method `get` of class `NoteRepository`.** One note or None.

It takes: `note_id` (a `int`).

It gives back a `Note | None`.

**Method `list_for` of class `NoteRepository`.** One owner's notes, or every note when the owner is None.

It takes: `owner_id` (a `int | None`).

It gives back a `list[Note]`.

**Method `update` of class `NoteRepository`.** Replace a note's text; None when it does not exist.

It takes: `note_id` (a `int`); `title` (a `str`); `body` (a `str`); `at` (a `datetime`).

It gives back a `Note | None`.

**Method `delete` of class `NoteRepository`.** Delete a note; False when it did not exist.

It takes: `note_id` (a `int`).

It gives back a `bool`.

`src/notes_evidence/application/ports.py` lines 75 to 88:

```python
class AuditLog(Protocol):
    """An append-only trail. There is deliberately no update and no delete."""

    def append(self, event: AuditEvent) -> None:
        """Record one event."""
        ...

    def since(self, moment: datetime) -> list[AuditEvent]:
        """Events at or after the moment, oldest first."""
        ...

    def latest(self, limit: int) -> list[AuditEvent]:
        """The most recent events, oldest first."""
        ...
```

**Class `AuditLog`**, a kind of `Protocol`. An append-only trail. There is deliberately no update and no delete.

Its methods, in order:

**Method `append` of class `AuditLog`.** Record one event.

It takes: `event` (a `AuditEvent`).

It gives back a `None`.

**Method `since` of class `AuditLog`.** Events at or after the moment, oldest first.

It takes: `moment` (a `datetime`).

It gives back a `list[AuditEvent]`.

**Method `latest` of class `AuditLog`.** The most recent events, oldest first.

It takes: `limit` (a `int`).

It gives back a `list[AuditEvent]`.

`src/notes_evidence/application/ports.py` lines 91 to 100:

```python
class PasswordHasher(Protocol):
    """Slow, salted password hashing."""

    def hash(self, password: str) -> str:
        """A self-describing hash."""
        ...

    def verify(self, password: str, stored: str) -> bool:
        """Constant-time comparison."""
        ...
```

**Class `PasswordHasher`**, a kind of `Protocol`. Slow, salted password hashing.

Its methods, in order:

**Method `hash` of class `PasswordHasher`.** A self-describing hash.

It takes: `password` (a `str`).

It gives back a `str`.

**Method `verify` of class `PasswordHasher`.** Constant-time comparison.

It takes: `password` (a `str`); `stored` (a `str`).

It gives back a `bool`.

`src/notes_evidence/application/ports.py` lines 103 to 112:

```python
class TokenService(Protocol):
    """Signed, expiring session tokens."""

    def issue(self, user: User, now: datetime) -> str:
        """A token for the user."""
        ...

    def verify(self, token: str, now: datetime) -> int | None:
        """The user id the token names, or None when it is forged or expired."""
        ...
```

**Class `TokenService`**, a kind of `Protocol`. Signed, expiring session tokens.

Its methods, in order:

**Method `issue` of class `TokenService`.** A token for the user.

It takes: `user` (a `User`); `now` (a `datetime`).

It gives back a `str`.

**Method `verify` of class `TokenService`.** The user id the token names, or None when it is forged or expired.

It takes: `token` (a `str`); `now` (a `datetime`).

It gives back a `int | None`.

`src/notes_evidence/application/ports.py` lines 115 to 120:

```python
class RepositoryAccess(Protocol):
    """Who can reach the repository, as the hosting platform reports it."""

    def collaborators(self) -> list[AccessEntry]:
        """Collaborators and their permission."""
        ...
```

**Class `RepositoryAccess`**, a kind of `Protocol`. Who can reach the repository, as the hosting platform reports it.

Its methods, in order:

**Method `collaborators` of class `RepositoryAccess`.** Collaborators and their permission.

It gives back a `list[AccessEntry]`.

`src/notes_evidence/application/ports.py` lines 123 to 128:

```python
class DatabaseAccess(Protocol):
    """Who can reach the database, from its own catalog."""

    def roles(self) -> list[AccessEntry]:
        """Roles and their level."""
        ...
```

**Class `DatabaseAccess`**, a kind of `Protocol`. Who can reach the database, from its own catalog.

Its methods, in order:

**Method `roles` of class `DatabaseAccess`.** Roles and their level.

It gives back a `list[AccessEntry]`.

`src/notes_evidence/application/ports.py` lines 131 to 140:

```python
class CloudDirectory(Protocol):
    """The cloud account's users."""

    def users(self) -> list[AccessEntry]:
        """Users in the account."""
        ...

    def remove_user(self, name: str) -> None:
        """Delete one user."""
        ...
```

**Class `CloudDirectory`**, a kind of `Protocol`. The cloud account's users.

Its methods, in order:

**Method `users` of class `CloudDirectory`.** Users in the account.

It gives back a `list[AccessEntry]`.

**Method `remove_user` of class `CloudDirectory`.** Delete one user.

It takes: `name` (a `str`).

It gives back a `None`.

`src/notes_evidence/application/ports.py` lines 143 to 148:

```python
class ChangeSource(Protocol):
    """Merged pull requests with their reviews and deployments."""

    def merged_changes(self) -> list[MergedChange]:
        """Merged changes, any order."""
        ...
```

**Class `ChangeSource`**, a kind of `Protocol`. Merged pull requests with their reviews and deployments.

Its methods, in order:

**Method `merged_changes` of class `ChangeSource`.** Merged changes, any order.

It gives back a `list[MergedChange]`.

`src/notes_evidence/application/ports.py` lines 151 to 160:

```python
class BackupRunner(Protocol):
    """Take a backup and restore it into a scratch database."""

    def backup(self) -> datetime:
        """Take a backup and return the moment it was taken."""
        ...

    def restore_and_count(self, table: str) -> tuple[int, int]:
        """Restore into a scratch database; the rows of the table at backup time and after the restore."""
        ...
```

**Class `BackupRunner`**, a kind of `Protocol`. Take a backup and restore it into a scratch database.

Its methods, in order:

**Method `backup` of class `BackupRunner`.** Take a backup and return the moment it was taken.

It gives back a `datetime`.

**Method `restore_and_count` of class `BackupRunner`.** Restore into a scratch database; the rows of the table at backup time and after the restore.

It takes: `table` (a `str`).

It gives back a `tuple[int, int]`.

`src/notes_evidence/application/ports.py` lines 163 to 168:

```python
class ScanRunner(Protocol):
    """Run the dependency scan."""

    def scan(self) -> ScanReport:
        """Scan the locked dependencies."""
        ...
```

**Class `ScanRunner`**, a kind of `Protocol`. Run the dependency scan.

Its methods, in order:

**Method `scan` of class `ScanRunner`.** Scan the locked dependencies.

It gives back a `ScanReport`.

`src/notes_evidence/application/ports.py` lines 171 to 188:

```python
class EvidenceStore(Protocol):
    """The evidence folder and its manifest."""

    def write(self, name: str, text: str, control: str, produced_at: datetime, run_by: str, source: str) -> None:
        """Write a file and record it in the manifest."""
        ...

    def read(self, name: str) -> str | None:
        """A file's text, or None when it does not exist."""
        ...

    def read_all(self) -> dict[str, str]:
        """Every file in the folder."""
        ...

    def manifest(self) -> dict[str, ManifestEntry]:
        """The manifest entries by file name."""
        ...
```

**Class `EvidenceStore`**, a kind of `Protocol`. The evidence folder and its manifest.

Its methods, in order:

**Method `write` of class `EvidenceStore`.** Write a file and record it in the manifest.

It takes: `name` (a `str`); `text` (a `str`); `control` (a `str`); `produced_at` (a `datetime`); `run_by` (a `str`); `source` (a `str`).

It gives back a `None`.

**Method `read` of class `EvidenceStore`.** A file's text, or None when it does not exist.

It takes: `name` (a `str`).

It gives back a `str | None`.

**Method `read_all` of class `EvidenceStore`.** Every file in the folder.

It gives back a `dict[str, str]`.

**Method `manifest` of class `EvidenceStore`.** The manifest entries by file name.

It gives back a `dict[str, ManifestEntry]`.

`src/notes_evidence/application/ports.py` lines 191 to 196:

```python
class AlertSink(Protocol):
    """Where an alert message goes: a chat channel, a pager, a file."""

    def send(self, message: str) -> None:
        """Deliver one alert message."""
        ...
```

**Class `AlertSink`**, a kind of `Protocol`. Where an alert message goes: a chat channel, a pager, a file.

Its methods, in order:

**Method `send` of class `AlertSink`.** Deliver one alert message.

It takes: `message` (a `str`).

It gives back a `None`.

`src/notes_evidence/application/ports.py` lines 199 to 220:

```python
class ControlCatalog(Protocol):
    """The control matrix, the recorded exceptions, the tracked gaps, the people and the review's decisions."""

    def controls(self) -> list[Control]:
        """The controls and their evidence."""
        ...

    def exceptions(self) -> list[RecordedException]:
        """Known deviations."""
        ...

    def gaps(self) -> list[Gap]:
        """Tracked gaps."""
        ...

    def people(self) -> dict[str, Person]:
        """People who may hold access, by principal name."""
        ...

    def review_request(self) -> ReviewRequest:
        """The reviewer's decisions."""
        ...
```

**Class `ControlCatalog`**, a kind of `Protocol`. The control matrix, the recorded exceptions, the tracked gaps, the people and the review's decisions.

Its methods, in order:

**Method `controls` of class `ControlCatalog`.** The controls and their evidence.

It gives back a `list[Control]`.

**Method `exceptions` of class `ControlCatalog`.** Known deviations.

It gives back a `list[RecordedException]`.

**Method `gaps` of class `ControlCatalog`.** Tracked gaps.

It gives back a `list[Gap]`.

**Method `people` of class `ControlCatalog`.** People who may hold access, by principal name.

It gives back a `dict[str, Person]`.

**Method `review_request` of class `ControlCatalog`.** The reviewer's decisions.

It gives back a `ReviewRequest`.

`src/notes_evidence/application/ports.py` lines 223 to 228:

```python
class Notes(Protocol):
    """The slice of the notes service the alert test drives."""

    def login(self, username: str, password: str) -> str:
        """Return a token or raise InvalidCredentialsError."""
        ...
```

**Class `Notes`**, a kind of `Protocol`. The slice of the notes service the alert test drives.

Its methods, in order:

**Method `login` of class `Notes`.** Return a token or raise InvalidCredentialsError.

It takes: `username` (a `str`); `password` (a `str`).

It gives back a `str`.

### `src/notes_evidence/application/reporting.py`

`src/notes_evidence/application/reporting.py` lines 1 to 9:

```python
"""Format the verification as text for the terminal and as Markdown for the build artifact."""

from __future__ import annotations

from collections.abc import Mapping

from notes_evidence.domain.controls import Control
from notes_evidence.domain.evidence import ManifestEntry, framework_table
from notes_evidence.domain.findings import Report
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Format the verification as text for the terminal and as Markdown for the build artifact.

Imports:

- From `__future__` it takes `annotations`.
- From `collections.abc` it takes `Mapping`.
- From `notes_evidence.domain.controls` it takes `Control`.
- From `notes_evidence.domain.evidence` it takes `ManifestEntry, framework_table`.
- From `notes_evidence.domain.findings` it takes `Report`.

`src/notes_evidence/application/reporting.py` lines 12 to 20:

```python
def render_text(report: Report) -> str:
    """One line per finding, then the verdict."""
    lines = [
        f"{finding.severity.value.upper():7} {finding.code} {finding.subject}: {finding.message}"
        for finding in report.findings
    ]
    counts = f"{len(report.subjects)} files checked, {len(report.errors)} errors, {len(report.warnings)} warnings"
    lines.append(f"{'OK' if report.ok else 'FAILED'}: {counts}")
    return "\n".join(lines)
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `render_text`.** One line per finding, then the verdict.

It takes: `report` (a `Report`).

It gives back a `str`.

Step by step:

- Stores a new list made by a loop (`[f'{finding.severity.value.upper():7} {finding.code} {finding.subject…`) in `lines`.
- Stores a text built with values filled in (`f'{len(report.subjects)} files checked, {len(report.errors)} errors, …`) in `counts`.
- Calls `lines.append(f"{('OK' if report.ok else 'FAILED')}: {counts}")`.
- Gives back the result of calling `'\n'.join(lines)`.

`src/notes_evidence/application/reporting.py` lines 23 to 55:

```python
def render_report(report: Report, controls: list[Control], manifest: Mapping[str, ManifestEntry]) -> str:
    """The control-to-evidence report: one row per control and file, the findings, the framework overlap."""
    verdict = "OK" if report.ok else "FAILED"
    lines = [
        "# Evidence report",
        "",
        f"**Verdict:** {verdict} ({len(report.errors)} errors, {len(report.warnings)} warnings)",
        "",
        "## Controls and their evidence",
        "",
        "| Control | Evidence file | Produced | Run by | Hash recorded |",
        "| --- | --- | --- | --- | --- |",
    ]
    for control in controls:
        if not control.evidence:
            lines.append(f"| {control.id} {control.name} | none | - | - | - |")
        for spec in control.evidence:
            entry = manifest.get(spec.file)
            if entry is None:
                lines.append(f"| {control.id} {control.name} | {spec.file} | missing | - | - |")
            else:
                produced = entry.produced_at.strftime("%Y-%m-%d")
                lines.append(
                    f"| {control.id} {control.name} | {spec.file} | {produced} | {entry.run_by} | {entry.sha256[:12]} |"
                )
    lines += ["", "## Findings", ""]
    if report.findings:
        lines += ["| Severity | Code | Subject | Message |", "| --- | --- | --- | --- |"]
        lines += [f"| {f.severity.value} | {f.code} | `{f.subject}` | {f.message} |" for f in report.findings]
    else:
        lines.append("None.")
    lines += ["", "## Framework mapping", "", framework_table(controls), ""]
    return "\n".join(lines)
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `render_report`.** The control-to-evidence report: one row per control and file, the findings, the framework overlap.

It takes: `report` (a `Report`); `controls` (a `list[Control]`); `manifest` (a `Mapping[str, ManifestEntry]`).

It gives back a `str`.

Step by step:

- Stores `'OK'` if `report.ok`, otherwise `'FAILED'` in `verdict`.
- Stores the list `['# Evidence report', '', f'**Verdict:** {verdict} ({len(report.error…` in `lines`.
- For each `control` in `controls`:
  - If not (`control.evidence`):
    - Calls `lines.append(f'| {control.id} {control.name} | none | - | - | - |')`.
  - For each `spec` in `control.evidence`:
    - Stores the result of calling `manifest.get(spec.file)` in `entry`.
    - If `entry` is the same object as `None`:
      - Calls `lines.append(f'| {control.id} {control.name} | {spec.file} | missing | - | - |')`.
    - Otherwise:
      - Stores the result of calling `entry.produced_at.strftime('%Y-%m-%d')` in `produced`.
      - Calls `lines.append(f'| {control.id} {control.name} | {spec.file} | {produced} | {entry.run_by} | {entry.sha256[:12]…`.
- Adds the list `['', '## Findings', '']` to `lines`.
- If `report.findings`:
  - Adds the list `['| Severity | Code | Subject | Message |', '| --- | --- | --- | --- …` to `lines`.
  - Adds a new list made by a loop (`[f'| {f.severity.value} | {f.code} | `{f.subject}` | {f.message} |' f…`) to `lines`.
- Otherwise:
  - Calls `lines.append('None.')`.
- Adds the list `['', '## Framework mapping', '', framework_table(controls), '']` to `lines`.
- Gives back the result of calling `'\n'.join(lines)`.

## Try it yourself

```bash
.venv/bin/python -c "import notes_evidence.application.evidence_collect; print(notes_evidence.application.evidence_collect.__doc__)"
```
Prints the module's description: `The evidence collectors: each reads a real system through a port and writes one artifact and its manifest entry.`

```bash
.venv/bin/python -c "import notes_evidence.application.exercise; print(notes_evidence.application.exercise.__doc__)"
```
Prints the module's description: `A scripted day of use, so the audit trail holds real events from real calls into the service.`

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check src/notes_evidence/application/__init__.py src/notes_evidence/application/evidence_collect.py src/notes_evidence/application/exercise.py src/notes_evidence/application/notes_service.py src/notes_evidence/application/ports.py src/notes_evidence/application/reporting.py
```
Prints `All checks passed!`.

```bash
grep -c "^def \|^class \|    def " src/notes_evidence/application/evidence_collect.py
```
Counts the functions, methods and classes in `src/notes_evidence/application/evidence_collect.py`.

## Mistakes people make

- Importing an adapter directly. Use the port; the adapter is passed in from the outside.
- Putting a rule here that belongs in the domain, where it can be tested without any setup.
- Catching an error too early. Use cases let named errors travel up to the interfaces layer.

## Check yourself

1. What is `Collector` for?
   **Answer:** What every collector shares: where to write, what time it is, who runs it, and which sources it reads.
2. What is `collect_access` for?
   **Answer:** C1: ask each system who can reach it, and write the list.
3. What is `collect_changes` for?
   **Answer:** C2: write every merged change with its approvers and its deployment; return how many have exceptions.
4. What is `collect_log_sample` for?
   **Answer:** C3: the most recent audit events, rendered as the log lines the service writes.
5. What is `run_alert_test` for?
   **Answer:** C3: do what the alert is for, read the trail back, and keep the alert message beside the time of the action.

## Further reading

- Python 3.12 tutorial, classes: <https://docs.python.org/3.12/tutorial/classes.html>
- Python 3.12 language reference: <https://docs.python.org/3.12/reference/>
- Type hints: <https://docs.python.org/3.12/library/typing.html>
