# Interfaces layer code

## What it is

The entry points: the command line, the web routes and the wiring that builds everything from settings. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

This is where the repository's interfaces work happens. Reading it file by file, with every line explained, is how a reader sees the work that was done.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/interfaces/__init__.py` | 1 lines. interfaces layer. |
| `src/notes_evidence/interfaces/cli.py` | 145 lines. `controls-evidence`: run the collectors, build the index, verify and report. Owns the exit codes. |
| `src/notes_evidence/interfaces/health.py` | 17 lines. `notes-api-health`: the container's health check. Exit 0 when /healthz answers 200. |
| `src/notes_evidence/interfaces/http_app.py` | 122 lines. The notes API over HTTP. Turns requests into service calls and errors into status codes; no rules of its own. |
| `src/notes_evidence/interfaces/wiring.py` | 90 lines. The composition root: build the adapters from settings and hand them to the use cases. |
| `src/notes_evidence/interfaces/wsgi.py` | 15 lines. The WSGI entry point for gunicorn: `gunicorn notes_evidence.interfaces.wsgi:app`. |

## How it works underneath

This outermost layer turns requests (a typed command, an HTTP call) into use-case calls and turns errors into exit codes or status codes. It is also where the adapters are created and connected (the composition root). Nothing depends on it.

## Walkthrough of this repository's use

### `src/notes_evidence/interfaces/__init__.py`

`src/notes_evidence/interfaces/__init__.py` lines 1 to 1:

```python
"""interfaces layer."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** interfaces layer.

### `src/notes_evidence/interfaces/cli.py`

`src/notes_evidence/interfaces/cli.py` lines 1 to 27:

```python
"""`controls-evidence`: run the collectors, build the index, verify and report. Owns the exit codes."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from notes_evidence.application import evidence_collect as collect
from notes_evidence.application.exercise import exercise_service
from notes_evidence.application.reporting import render_report, render_text
from notes_evidence.domain.controls import Gap, RecordedException
from notes_evidence.domain.evidence import framework_table
from notes_evidence.domain.findings import Report
from notes_evidence.domain.roles import Role
from notes_evidence.infrastructure.alerting import FileAlertSink
from notes_evidence.infrastructure.backup import BackupError, DockerBackupRunner
from notes_evidence.infrastructure.catalog import CatalogError, TomlCatalog
from notes_evidence.infrastructure.evidence_store import FileEvidenceStore
from notes_evidence.infrastructure.logging_setup import configure_logging
from notes_evidence.infrastructure.scanner import PipAuditScanner, ScanError
from notes_evidence.infrastructure.settings import Settings, SettingsError, load_settings
from notes_evidence.infrastructure.sources import SourceError
from notes_evidence.interfaces import wiring
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** `controls-evidence`: run the collectors, build the index, verify and report. Owns the exit codes.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `argparse`.
- It imports module `os`.
- It imports module `sys`.
- From `collections.abc` it takes `Callable, Sequence`.
- From `datetime` it takes `UTC, datetime`.
- From `pathlib` it takes `Path`.
- From `notes_evidence.application` it takes `evidence_collect as collect`.
- From `notes_evidence.application.exercise` it takes `exercise_service`.
- From `notes_evidence.application.reporting` it takes `render_report, render_text`.
- From `notes_evidence.domain.controls` it takes `Gap, RecordedException`.
- From `notes_evidence.domain.evidence` it takes `framework_table`.
- From `notes_evidence.domain.findings` it takes `Report`.
- From `notes_evidence.domain.roles` it takes `Role`.
- From `notes_evidence.infrastructure.alerting` it takes `FileAlertSink`.
- From `notes_evidence.infrastructure.backup` it takes `BackupError, DockerBackupRunner`.
- From `notes_evidence.infrastructure.catalog` it takes `CatalogError, TomlCatalog`.
- From `notes_evidence.infrastructure.evidence_store` it takes `FileEvidenceStore`.
- From `notes_evidence.infrastructure.logging_setup` it takes `configure_logging`.
- From `notes_evidence.infrastructure.scanner` it takes `PipAuditScanner, ScanError`.
- From `notes_evidence.infrastructure.settings` it takes `Settings, SettingsError, load_settings`.
- From `notes_evidence.infrastructure.sources` it takes `SourceError`.
- From `notes_evidence.interfaces` it takes `wiring`.

`src/notes_evidence/interfaces/cli.py` lines 29 to 29:

```python
STEPS = ("exercise", "alert-test", "log-sample", "access", "changes", "restore-test", "scan", "review", "index")
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the tuple `('exercise', 'alert-test', 'log-sample', 'access', 'changes', 'restor…` in `STEPS`.

`src/notes_evidence/interfaces/cli.py` lines 32 to 38:

```python
def build_parser() -> argparse.ArgumentParser:
    """One subcommand per collector, plus collect, verify and report."""
    parser = argparse.ArgumentParser(prog="controls-evidence", description="Produce and verify the evidence pack.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in (*STEPS, "collect", "verify", "report"):
        commands.add_parser(name)
    return parser
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `*items` **unpacks** a sequence into separate values; `**options` does the same for a dictionary's keys and values.

**Function `build_parser`.** One subcommand per collector, plus collect, verify and report.

It gives back a `argparse.ArgumentParser`.

Step by step:

- Stores the result of calling `argparse.ArgumentParser(prog='controls-evidence', description='Produce and verify the evi…` in `parser`.
- Stores the result of calling `parser.add_subparsers(dest='command', required=True)` in `commands`.
- For each `name` in the tuple `(*STEPS, 'collect', 'verify', 'report')`:
  - Calls `commands.add_parser(name)`.
- Gives back `parser`.

`src/notes_evidence/interfaces/cli.py` lines 41 to 53:

```python
def main(argv: Sequence[str] | None = None) -> int:
    """Run one command and return the exit code: 0 ok, 1 findings or a failed step, 2 bad configuration or input."""
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings(os.environ)
        configure_logging("WARNING")
        return _dispatch(args.command, settings)
    except (SettingsError, CatalogError) as problem:
        print(f"configuration error: {problem}", file=sys.stderr)
        return 2
    except (SourceError, BackupError, ScanError, OSError) as problem:
        print(f"step failed: {problem}", file=sys.stderr)
        return 1
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `main`.** Run one command and return the exit code: 0 ok, 1 findings or a failed step, 2 bad configuration or input.

It takes: `argv` (a `Sequence[str] | None`), default `None`.

It gives back a `int`.

Step by step:

- Stores the result of calling `build_parser().parse_args(argv)` in `args`.
- Tries:
  - Stores the result of calling `load_settings(os.environ)` in `settings`.
  - Calls `configure_logging('WARNING')`.
  - Gives back the result of calling `_dispatch(args.command, settings)`.
- If `(SettingsError, CatalogError)` happens (named `problem`):
  - Calls `print(f'configuration error: {problem}', file=sys.stderr)`.
  - Gives back the number `2`.
- If `(SourceError, BackupError, ScanError, OSError)` happens (named `problem`):
  - Calls `print(f'step failed: {problem}', file=sys.stderr)`.
  - Gives back the number `1`.

`src/notes_evidence/interfaces/cli.py` lines 56 to 79:

```python
def _dispatch(command: str, settings: Settings) -> int:
    store = FileEvidenceStore(settings.evidence_dir)
    catalog = TomlCatalog(settings.controls_file)
    if command == "verify":
        report = _verify(store, catalog)
        print(render_text(report))
        return 0 if report.ok else 1
    if command == "report":
        report = _verify(store, catalog)
        target = Path(os.environ.get("REPORT_DIR", "build")) / "report.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_report(report, catalog.controls(), store.manifest()), encoding="utf-8")
        print(f"wrote {target}")
        return 0 if report.ok else 1
    runtime = wiring.build_runtime(settings)
    collector = collect.Collector(store, runtime.clock, settings.run_by, settings.evidence_source)
    steps = STEPS if command == "collect" else (command,)
    for step in steps:
        print(f"== {step}: {_run_step(step, settings, runtime, collector, catalog)}")
    if command == "collect":
        report = _verify(store, catalog)
        print(render_text(report))
        return 0 if report.ok else 1
    return 0
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `_dispatch`.**

It takes: `command` (a `str`); `settings` (a `Settings`).

It gives back a `int`.

Step by step:

- Stores the result of calling `FileEvidenceStore(settings.evidence_dir)` in `store`.
- Stores the result of calling `TomlCatalog(settings.controls_file)` in `catalog`.
- If `command` equals `'verify'`:
  - Stores the result of calling `_verify(store, catalog)` in `report`.
  - Calls `print(render_text(report))`.
  - Gives back `0` if `report.ok`, otherwise `1`.
- If `command` equals `'report'`:
  - Stores the result of calling `_verify(store, catalog)` in `report`.
  - Stores `Path(os.environ.get('REPORT_DIR', 'build')) / 'report.md'` in `target`.
  - Calls `target.parent.mkdir(parents=True, exist_ok=True)`.
  - Calls `target.write_text(render_report(report, catalog.controls(), store.manifest()), encoding='utf-8')`.
  - Calls `print(f'wrote {target}')`.
  - Gives back `0` if `report.ok`, otherwise `1`.
- Stores the result of calling `wiring.build_runtime(settings)` in `runtime`.
- Stores the result of calling `collect.Collector(store, runtime.clock, settings.run_by, settings.evidence_source)` in `collector`.
- Stores `STEPS` if `command` equals `'collect'`, otherwise `(command,)` in `steps`.
- For each `step` in `steps`:
  - Calls `print(f'== {step}: {_run_step(step, settings, runtime, collector, catalog)}')`.
- If `command` equals `'collect'`:
  - Stores the result of calling `_verify(store, catalog)` in `report`.
  - Calls `print(render_text(report))`.
  - Gives back `0` if `report.ok`, otherwise `1`.
- Gives back the number `0`.

`src/notes_evidence/interfaces/cli.py` lines 82 to 85:

```python
def _verify(store: FileEvidenceStore, catalog: TomlCatalog) -> Report:
    exceptions: list[RecordedException] = catalog.exceptions()
    gaps: list[Gap] = catalog.gaps()
    return collect.verify(store, catalog.controls(), exceptions, gaps, datetime.now(UTC).date())
```

**Function `_verify`.**

It takes: `store` (a `FileEvidenceStore`); `catalog` (a `TomlCatalog`).

It gives back a `Report`.

Step by step:

- Declares `exceptions` as a `list[RecordedException]` and stores the result of calling `catalog.exceptions()` in it.
- Declares `gaps` as a `list[Gap]` and stores the result of calling `catalog.gaps()` in it.
- Gives back the result of calling `collect.verify(store, catalog.controls(), exceptions, gaps, datetime.now(UTC).date())`.

`src/notes_evidence/interfaces/cli.py` lines 88 to 107:

```python
def _run_step(
    step: str, settings: Settings, runtime: wiring.Runtime, collector: collect.Collector, catalog: TomlCatalog
) -> str:
    handlers: dict[str, Callable[[], str]] = {
        "exercise": lambda: _exercise(runtime),
        "alert-test": lambda: _alert_test(runtime, collector, settings),
        "log-sample": lambda: (
            f"{collect.collect_log_sample(collector, runtime.audit)} audit events in {collect.LOG_FILE}"
        ),
        "access": lambda: _access(settings, collector),
        "changes": lambda: (
            f"{collect.collect_changes(collector, wiring.change_source(settings))} change(s) with exceptions, "
            f"written to {collect.CHANGES_FILE}"
        ),
        "restore-test": lambda: _restore(settings, collector),
        "scan": lambda: _scan(settings, collector),
        "review": lambda: _review(settings, collector, catalog),
        "index": lambda: _index(collector, catalog),
    }
    return handlers[step]()
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Function `_run_step`.**

It takes: `step` (a `str`); `settings` (a `Settings`); `runtime` (a `wiring.Runtime`); `collector` (a `collect.Collector`); `catalog` (a `TomlCatalog`).

It gives back a `str`.

Step by step:

- Declares `handlers` as a `dict[str, Callable[[], str]]` and stores the dictionary `{'exercise': lambda: _exercise(runtime), 'alert-test': lambda: _alert…` in it.
- Gives back the result of calling `handlers[step]()`.

`src/notes_evidence/interfaces/cli.py` lines 110 to 115:

```python
def _exercise(runtime: wiring.Runtime) -> str:
    summary = exercise_service(wiring.provisioner(runtime.settings), runtime.hasher, runtime.service)
    return (
        f"{len(summary.users)} accounts used the service, {summary.notes_created} notes written, "
        f"{summary.refusals} requests refused"
    )
```

**Function `_exercise`.**

It takes: `runtime` (a `wiring.Runtime`).

It gives back a `str`.

Step by step:

- Stores the result of calling `exercise_service(wiring.provisioner(runtime.settings), runtime.hasher, runtime.service)` in `summary`.
- Gives back a text built with values filled in (`f'{len(summary.users)} accounts used the service, {summary.notes_crea…`).

`src/notes_evidence/interfaces/cli.py` lines 118 to 127:

```python
def _alert_test(runtime: wiring.Runtime, collector: collect.Collector, settings: Settings) -> str:
    found = runtime.users.find_by_username("ada")
    if found is None:
        raise SourceError("the alert test needs the account 'ada': run `exercise` first")
    admin = found[0]
    sink = FileAlertSink(settings.state_dir / "alerts.log")
    alerts = collect.run_alert_test(
        collector, runtime.service, runtime.audit, sink, lambda: _grant_and_revert(runtime, admin), "bruno"
    )
    return f"{len(alerts)} alert(s) delivered: " + "; ".join(alert.rule for alert in alerts)
```

> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Function `_alert_test`.**

It takes: `runtime` (a `wiring.Runtime`); `collector` (a `collect.Collector`); `settings` (a `Settings`).

It gives back a `str`.

Step by step:

- Stores the result of calling `runtime.users.find_by_username('ada')` in `found`.
- If `found` is the same object as `None`:
  - Stops here by raising `SourceError("the alert test needs the account 'ada': run `exercise` first")`.
- Stores `found[0]` in `admin`.
- Stores the result of calling `FileAlertSink(settings.state_dir / 'alerts.log')` in `sink`.
- Stores the result of calling `collect.run_alert_test(collector, runtime.service, runtime.audit, sink, lambda: _grant_an…` in `alerts`.
- Gives back `f'{len(alerts)} alert(s) delivered: ' + '; '.join((alert.rule for alert in aler…`.

`src/notes_evidence/interfaces/cli.py` lines 130 to 135:

```python
def _grant_and_revert(runtime: wiring.Runtime, admin: object) -> None:
    from notes_evidence.domain.notes import User

    assert isinstance(admin, User)
    runtime.service.grant_role(admin, "chen", Role.ADMIN)
    runtime.service.grant_role(admin, "chen", Role.MEMBER)
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.

**Function `_grant_and_revert`.**

It takes: `runtime` (a `wiring.Runtime`); `admin` (a `object`).

It gives back a `None`.

Step by step:

- Imports `from notes_evidence.domain.notes import User`.
- Checks that `isinstance(admin, User)`; if not, the test fails.
- Calls `runtime.service.grant_role(admin, 'chen', Role.ADMIN)`.
- Calls `runtime.service.grant_role(admin, 'chen', Role.MEMBER)`.

`src/notes_evidence/interfaces/cli.py` lines 138 to 142:

```python
def _access(settings: Settings, collector: collect.Collector) -> str:
    access = collect.collect_access(
        collector, wiring.repository_access(settings), wiring.database_roles(settings), wiring.cloud_directory(settings)
    )
    return ", ".join(f"{count} {system.split(' (')[0]}" for system, count in access.counts().items())
```

**Function `_access`.**

It takes: `settings` (a `Settings`); `collector` (a `collect.Collector`).

It gives back a `str`.

Step by step:

- Stores the result of calling `collect.collect_access(collector, wiring.repository_access(settings), wiring.database_rol…` in `access`.
- Gives back the result of calling `', '.join((f"{count} {system.split(' (')[0]}" for system, count in access.counts().items(…`.

`src/notes_evidence/interfaces/cli.py` lines 145 to 148:

```python
def _restore(settings: Settings, collector: collect.Collector) -> str:
    runner = DockerBackupRunner(settings.db_exec_prefix, settings.postgres_user, settings.postgres_db)
    result = collect.run_restore_test(collector, runner)
    return f"{result.restored_rows:,} of {result.source_rows:,} rows restored in {result.seconds} s"
```

**Function `_restore`.**

It takes: `settings` (a `Settings`); `collector` (a `collect.Collector`).

It gives back a `str`.

Step by step:

- Stores the result of calling `DockerBackupRunner(settings.db_exec_prefix, settings.postgres_user, settings.postgres_db)` in `runner`.
- Stores the result of calling `collect.run_restore_test(collector, runner)` in `result`.
- Gives back a text built with values filled in (`f'{result.restored_rows:,} of {result.source_rows:,} rows restored in…`).

`src/notes_evidence/interfaces/cli.py` lines 151 to 153:

```python
def _scan(settings: Settings, collector: collect.Collector) -> str:
    scanner = PipAuditScanner("requirements.lock", os.environ, collector.clock.now)
    return f"verdict {collect.collect_scan(collector, scanner)}"
```

**Function `_scan`.**

It takes: `settings` (a `Settings`); `collector` (a `collect.Collector`).

It gives back a `str`.

Step by step:

- Stores the result of calling `PipAuditScanner('requirements.lock', os.environ, collector.clock.now)` in `scanner`.
- Gives back a text built with values filled in (`f'verdict {collect.collect_scan(collector, scanner)}'`).

`src/notes_evidence/interfaces/cli.py` lines 156 to 169:

```python
def _review(settings: Settings, collector: collect.Collector, catalog: TomlCatalog) -> str:
    outcome = collect.review_access(
        collector,
        wiring.repository_access(settings),
        wiring.database_roles(settings),
        wiring.cloud_directory(settings),
        catalog,
    )
    if outcome.findings:
        raise SourceError("the access review is incomplete: " + "; ".join(f.message for f in outcome.findings))
    assert outcome.before is not None
    assert outcome.after is not None
    gone = len(outcome.before.entries) - len(outcome.after.entries)
    return f"{gone} access removed, recorded in {collect.REVIEW_FILE}"
```

**Function `_review`.**

It takes: `settings` (a `Settings`); `collector` (a `collect.Collector`); `catalog` (a `TomlCatalog`).

It gives back a `str`.

Step by step:

- Stores the result of calling `collect.review_access(collector, wiring.repository_access(settings), wiring.database_role…` in `outcome`.
- If `outcome.findings`:
  - Stops here by raising `SourceError('the access review is incomplete: ' + '; '.join((f.message for f in outcome.findings)))`.
- Checks that `outcome.before` is not the same object as `None`; if not, the test fails.
- Checks that `outcome.after` is not the same object as `None`; if not, the test fails.
- Stores `len(outcome.before.entries) - len(outcome.after.entries)` in `gone`.
- Gives back a text built with values filled in (`f'{gone} access removed, recorded in {collect.REVIEW_FILE}'`).

`src/notes_evidence/interfaces/cli.py` lines 172 to 174:

```python
def _index(collector: collect.Collector, catalog: TomlCatalog) -> str:
    collect.build_index(collector, catalog, framework_table(catalog.controls()))
    return "wrote INDEX.md"
```

**Function `_index`.**

It takes: `collector` (a `collect.Collector`); `catalog` (a `TomlCatalog`).

It gives back a `str`.

Step by step:

- Calls `collect.build_index(collector, catalog, framework_table(catalog.controls()))`.
- Gives back the text `'wrote INDEX.md'`.

`src/notes_evidence/interfaces/cli.py` lines 177 to 178:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

> **In plain words.** `if __name__ == "__main__":` runs its steps only when the file is started directly, not when another file imports it.

This statement:

- If `__name__` equals `'__main__'`:
  - Stops here by raising `SystemExit(main())`.

### `src/notes_evidence/interfaces/health.py`

`src/notes_evidence/interfaces/health.py` lines 1 to 8:

```python
"""`notes-api-health`: the container's health check. Exit 0 when /healthz answers 200."""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** `notes-api-health`: the container's health check. Exit 0 when /healthz answers 200.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `os`.
- It imports module `sys`.
- It imports module `urllib.error`.
- It imports module `urllib.request`.

`src/notes_evidence/interfaces/health.py` lines 11 to 19:

```python
def main() -> int:
    """Ask the local API if it is healthy."""
    port = os.environ.get("HTTP_PORT", "8080")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=3) as response:
            return 0 if response.status == 200 else 1
    except (urllib.error.URLError, OSError):
        print("unhealthy", file=sys.stderr)
        return 1
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `main`.** Ask the local API if it is healthy.

It gives back a `int`.

Step by step:

- Stores the result of calling `os.environ.get('HTTP_PORT', '8080')` in `port`.
- Tries:
  - Inside a `with` block that opens `urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=3)` (named `response`):
    - Gives back `0` if `response.status` equals `200`, otherwise `1`.
- If `(urllib.error.URLError, OSError)` happens:
  - Calls `print('unhealthy', file=sys.stderr)`.
  - Gives back the number `1`.

`src/notes_evidence/interfaces/health.py` lines 22 to 23:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

> **In plain words.** `if __name__ == "__main__":` runs its steps only when the file is started directly, not when another file imports it.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

This statement:

- If `__name__` equals `'__main__'`:
  - Stops here by raising `SystemExit(main())`.

### `src/notes_evidence/interfaces/http_app.py`

`src/notes_evidence/interfaces/http_app.py` lines 1 to 21:

```python
"""The notes API over HTTP. Turns requests into service calls and errors into status codes; no rules of its own."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from flask import Flask, Response, g, jsonify, request

from notes_evidence.application.notes_service import NotesService
from notes_evidence.domain.errors import (
    InvalidCredentialsError,
    NotAllowedError,
    NotAuthenticatedError,
    NotFoundError,
    ValidationError,
)
from notes_evidence.domain.notes import Note, User
from notes_evidence.domain.roles import Role
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The notes API over HTTP. Turns requests into service calls and errors into status codes; no rules of its own.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `logging`.
- It imports module `time`.
- From `collections.abc` it takes `Callable`.
- From `typing` it takes `Any`.
- From `flask` it takes `Flask, Response, g, jsonify, request`.
- From `notes_evidence.application.notes_service` it takes `NotesService`.
- From `notes_evidence.domain.errors` it takes `InvalidCredentialsError, NotAllowedError, NotAuthenticatedError, NotFoundError, ValidationError`.
- From `notes_evidence.domain.notes` it takes `Note, User`.
- From `notes_evidence.domain.roles` it takes `Role`.

`src/notes_evidence/interfaces/http_app.py` lines 23 to 24:

```python
logger = logging.getLogger("notes.http")
MAX_BODY_BYTES = 64 * 1024
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `logging.getLogger('notes.http')` in `logger`.
- Stores `64 * 1024` in `MAX_BODY_BYTES`.

`src/notes_evidence/interfaces/http_app.py` lines 27 to 35:

```python
def _note_json(note: Note) -> dict[str, Any]:
    return {
        "id": note.id,
        "owner_id": note.owner_id,
        "title": note.title,
        "body": note.body,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Function `_note_json`.**

It takes: `note` (a `Note`).

It gives back a `dict[str, Any]`.

Step by step:

- Gives back the dictionary `{'id': note.id, 'owner_id': note.owner_id, 'title': note.title, 'body…`.

`src/notes_evidence/interfaces/http_app.py` lines 38 to 42:

```python
def _payload() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "a JSON object is required")
    return data
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

**Function `_payload`.**

It gives back a `dict[str, Any]`.

Step by step:

- Stores the result of calling `request.get_json(silent=True)` in `data`.
- If not (`isinstance(data, dict)`):
  - Stops here by raising `ValidationError('body', 'a JSON object is required')`.
- Gives back `data`.

`src/notes_evidence/interfaces/http_app.py` lines 45 to 46:

```python
def create_app(service: NotesService, ping: Callable[[], bool]) -> Flask:
    """Build the Flask app around a service and a database ping."""
```

**Function `create_app`.** Build the Flask app around a service and a database ping.

It takes: `service` (a `NotesService`); `ping` (a `Callable[[], bool]`).

It gives back a `Flask`.

`src/notes_evidence/interfaces/http_app.py` lines 47 to 73:

```python
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES

    def actor() -> User:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise NotAuthenticatedError("bearer token required")
        return service.authenticate(header.removeprefix("Bearer ").strip())

    @app.before_request
    def start_timer() -> None:
        g.started = time.monotonic()

    @app.after_request
    def finish(response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": int((time.monotonic() - g.get("started", time.monotonic())) * 1000),
            },
        )
        return response
```

**`create_app`, part 1 of 4.**

Step by step:

- Stores the result of calling `Flask(__name__)` in `app`.
- Stores `MAX_BODY_BYTES` in `app.config['MAX_CONTENT_LENGTH']`.
- Defines a helper function `actor()`.
  - Stores the result of calling `request.headers.get('Authorization', '')` in `header`.
  - If not (`header.startswith('Bearer ')`):
    - Stops here by raising `NotAuthenticatedError('bearer token required')`.
  - Gives back the result of calling `service.authenticate(header.removeprefix('Bearer ').strip())`.
- Defines a helper function `start_timer()`.
  - Stores the result of calling `time.monotonic()` in `g.started`.
- Defines a helper function `finish(response)`.
  - Stores the text `'nosniff'` in `response.headers['X-Content-Type-Options']`.
  - Stores the text `'no-store'` in `response.headers['Cache-Control']`.
  - Calls `logger.info('request', extra={'method': request.method, 'path': request.path, 'status': response.status_code,…`.
  - Gives back `response`.

`src/notes_evidence/interfaces/http_app.py` lines 75 to 92:

```python
    @app.get("/healthz")
    def healthz() -> tuple[Response, int]:
        healthy = ping()
        return jsonify(status="ok" if healthy else "database unavailable"), 200 if healthy else 503

    @app.post("/login")
    def login() -> Response:
        data = _payload()
        return jsonify(token=service.login(data.get("username", ""), data.get("password", "")))

    @app.get("/notes")
    def list_notes() -> Response:
        return jsonify(notes=[_note_json(note) for note in service.list_notes(actor())])

    @app.post("/notes")
    def create_note() -> tuple[Response, int]:
        data = _payload()
        return jsonify(_note_json(service.create_note(actor(), data.get("title"), data.get("body")))), 201
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**`create_app`, part 2 of 4.**

Step by step:

- Defines a helper function `healthz()`.
  - Stores the result of calling `ping()` in `healthy`.
  - Gives back the tuple `(jsonify(status='ok' if healthy else 'database unavailable'), 200 if …`.
- Defines a helper function `login()`.
  - Stores the result of calling `_payload()` in `data`.
  - Gives back the result of calling `jsonify(token=service.login(data.get('username', ''), data.get('password', '')))`.
- Defines a helper function `list_notes()`.
  - Gives back the result of calling `jsonify(notes=[_note_json(note) for note in service.list_notes(actor())])`.
- Defines a helper function `create_note()`.
  - Stores the result of calling `_payload()` in `data`.
  - Gives back the tuple `(jsonify(_note_json(service.create_note(actor(), data.get('title'), d…`.

`src/notes_evidence/interfaces/http_app.py` lines 94 to 116:

```python
    @app.get("/notes/<int:note_id>")
    def get_note(note_id: int) -> Response:
        return jsonify(_note_json(service.get_note(actor(), note_id)))

    @app.put("/notes/<int:note_id>")
    def update_note(note_id: int) -> Response:
        data = _payload()
        return jsonify(_note_json(service.update_note(actor(), note_id, data.get("title"), data.get("body"))))

    @app.delete("/notes/<int:note_id>")
    def delete_note(note_id: int) -> tuple[str, int]:
        service.delete_note(actor(), note_id)
        return "", 204

    @app.put("/users/<username>/role")
    def grant_role(username: str) -> Response:
        data = _payload()
        try:
            role = Role(data.get("role"))
        except ValueError:
            raise ValidationError("role", "one of admin, member, readonly") from None
        user = service.grant_role(actor(), username, role)
        return jsonify(username=user.username, role=user.role.value)
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.

**`create_app`, part 3 of 4.**

Step by step:

- Defines a helper function `get_note(note_id)`.
  - Gives back the result of calling `jsonify(_note_json(service.get_note(actor(), note_id)))`.
- Defines a helper function `update_note(note_id)`.
  - Stores the result of calling `_payload()` in `data`.
  - Gives back the result of calling `jsonify(_note_json(service.update_note(actor(), note_id, data.get('title'), data.get('bod…`.
- Defines a helper function `delete_note(note_id)`.
  - Calls `service.delete_note(actor(), note_id)`.
  - Gives back the tuple `('', 204)`.
- Defines a helper function `grant_role(username)`.
  - Stores the result of calling `_payload()` in `data`.
  - Tries:
    - Stores the result of calling `Role(data.get('role'))` in `role`.
  - If `ValueError` happens:
    - Stops here by raising `ValidationError('role', 'one of admin, member, readonly')` (`from None` hides the earlier error).
  - Stores the result of calling `service.grant_role(actor(), username, role)` in `user`.
  - Gives back the result of calling `jsonify(username=user.username, role=user.role.value)`.

`src/notes_evidence/interfaces/http_app.py` lines 118 to 119:

```python
    _register_errors(app)
    return app
```

**`create_app`, part 4 of 4.**

Step by step:

- Calls `_register_errors(app)`.
- Gives back `app`.

`src/notes_evidence/interfaces/http_app.py` lines 122 to 154:

```python
def _register_errors(app: Flask) -> None:
    def answer(status: int, message: str) -> tuple[Response, int]:
        return jsonify(error=message), status

    @app.errorhandler(ValidationError)
    def invalid(problem: ValidationError) -> tuple[Response, int]:
        return answer(400, str(problem))

    @app.errorhandler(InvalidCredentialsError)
    @app.errorhandler(NotAuthenticatedError)
    def unauthenticated(problem: Exception) -> tuple[Response, int]:
        return answer(401, str(problem))

    @app.errorhandler(NotAllowedError)
    def forbidden(problem: NotAllowedError) -> tuple[Response, int]:
        return answer(403, str(problem))

    @app.errorhandler(NotFoundError)
    def missing(problem: NotFoundError) -> tuple[Response, int]:
        return answer(404, str(problem))

    @app.errorhandler(404)
    def no_route(_: Exception) -> tuple[Response, int]:
        return answer(404, "not found")

    @app.errorhandler(413)
    def too_large(_: Exception) -> tuple[Response, int]:
        return answer(413, "request too large")

    @app.errorhandler(Exception)
    def unexpected(problem: Exception) -> tuple[Response, int]:
        logger.error("unhandled %s", type(problem).__name__)
        return answer(500, "internal error")
```

**Function `_register_errors`.**

It takes: `app` (a `Flask`).

It gives back a `None`.

Step by step:

- Defines a helper function `answer(status, message)`.
  - Gives back the tuple `(jsonify(error=message), status)`.
- Defines a helper function `invalid(problem)`.
  - Gives back the result of calling `answer(400, str(problem))`.
- Defines a helper function `unauthenticated(problem)`.
  - Gives back the result of calling `answer(401, str(problem))`.
- Defines a helper function `forbidden(problem)`.
  - Gives back the result of calling `answer(403, str(problem))`.
- Defines a helper function `missing(problem)`.
  - Gives back the result of calling `answer(404, str(problem))`.
- Defines a helper function `no_route(_)`.
  - Gives back the result of calling `answer(404, 'not found')`.
- Defines a helper function `too_large(_)`.
  - Gives back the result of calling `answer(413, 'request too large')`.
- Defines a helper function `unexpected(problem)`.
  - Calls `logger.error('unhandled %s', type(problem).__name__)`.
  - Gives back the result of calling `answer(500, 'internal error')`.

### `src/notes_evidence/interfaces/wiring.py`

`src/notes_evidence/interfaces/wiring.py` lines 1 to 32:

```python
"""The composition root: build the adapters from settings and hand them to the use cases."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from notes_evidence.application.notes_service import NotesService
from notes_evidence.application.ports import ChangeSource, CloudDirectory, RepositoryAccess
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
from notes_evidence.infrastructure.settings import Settings
from notes_evidence.infrastructure.sources import (
    AwsCloudDirectory,
    GithubChanges,
    GithubRepositoryAccess,
    StateCloudDirectory,
    command_json,
    file_json,
    run_command,
)
from notes_evidence.infrastructure.tokens import HmacTokens
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The composition root: build the adapters from settings and hand them to the use cases.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `os`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `timedelta`.
- From `pathlib` it takes `Path`.
- From `notes_evidence.application.notes_service` it takes `NotesService`.
- From `notes_evidence.application.ports` it takes `ChangeSource, CloudDirectory, RepositoryAccess`.
- From `notes_evidence.infrastructure.clock` it takes `SystemClock`.
- From `notes_evidence.infrastructure.passwords` it takes `ScryptHasher`.
- From `notes_evidence.infrastructure.postgres` it takes `Database, PostgresAuditLog, PostgresNotes, PostgresProvisioner, PostgresRoles, PostgresUsers`.
- From `notes_evidence.infrastructure.settings` it takes `Settings`.
- From `notes_evidence.infrastructure.sources` it takes `AwsCloudDirectory, GithubChanges, GithubRepositoryAccess, StateCloudDirectory, command_json, file_json, run_command`.
- From `notes_evidence.infrastructure.tokens` it takes `HmacTokens`.

`src/notes_evidence/interfaces/wiring.py` lines 34 to 34:

```python
FIXTURES = Path("fixtures")
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `Path('fixtures')` in `FIXTURES`.

`src/notes_evidence/interfaces/wiring.py` lines 37 to 47:

```python
@dataclass(frozen=True)
class Runtime:
    """Everything the programs share."""

    settings: Settings
    clock: SystemClock
    hasher: ScryptHasher
    app_db: Database
    users: PostgresUsers
    audit: PostgresAuditLog
    service: NotesService
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Runtime`**. Everything the programs share. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `settings`: a `Settings`.
- Field `clock`: a `SystemClock`.
- Field `hasher`: a `ScryptHasher`.
- Field `app_db`: a `Database`.
- Field `users`: a `PostgresUsers`.
- Field `audit`: a `PostgresAuditLog`.
- Field `service`: a `NotesService`.

`src/notes_evidence/interfaces/wiring.py` lines 50 to 57:

```python
def build_runtime(settings: Settings) -> Runtime:
    """The notes service wired to PostgreSQL as the least-privileged `app_rw` role."""
    clock, hasher = SystemClock(), ScryptHasher()
    database = Database(settings.database_url, statement_timeout_ms=settings.statement_timeout_ms)
    users, audit = PostgresUsers(database), PostgresAuditLog(database)
    tokens = HmacTokens(settings.secret, timedelta(seconds=settings.token_ttl_seconds))
    service = NotesService(users, PostgresNotes(database), audit, hasher, tokens, clock)
    return Runtime(settings, clock, hasher, database, users, audit, service)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Function `build_runtime`.** The notes service wired to PostgreSQL as the least-privileged `app_rw` role.

It takes: `settings` (a `Settings`).

It gives back a `Runtime`.

Step by step:

- Unpacks the tuple `(SystemClock(), ScryptHasher())` into `(clock, hasher)`.
- Stores the result of calling `Database(settings.database_url, statement_timeout_ms=settings.statement_timeout_ms)` in `database`.
- Unpacks the tuple `(PostgresUsers(database), PostgresAuditLog(database))` into `(users, audit)`.
- Stores the result of calling `HmacTokens(settings.secret, timedelta(seconds=settings.token_ttl_seconds))` in `tokens`.
- Stores the result of calling `NotesService(users, PostgresNotes(database), audit, hasher, tokens, clock)` in `service`.
- Gives back the result of calling `Runtime(settings, clock, hasher, database, users, audit, service)`.

`src/notes_evidence/interfaces/wiring.py` lines 60 to 64:

```python
def admin_database(settings: Settings) -> Database:
    """The administrative connection, used by the collectors and the provisioner."""
    return Database(
        settings.admin_database_url or settings.database_url, statement_timeout_ms=settings.statement_timeout_ms
    )
```

**Function `admin_database`.** The administrative connection, used by the collectors and the provisioner.

It takes: `settings` (a `Settings`).

It gives back a `Database`.

Step by step:

- Gives back the result of calling `Database(settings.admin_database_url or settings.database_url, statement_timeout_ms=setti…`.

`src/notes_evidence/interfaces/wiring.py` lines 67 to 69:

```python
def provisioner(settings: Settings) -> PostgresProvisioner:
    """Creates accounts."""
    return PostgresProvisioner(admin_database(settings))
```

**Function `provisioner`.** Creates accounts.

It takes: `settings` (a `Settings`).

It gives back a `PostgresProvisioner`.

Step by step:

- Gives back the result of calling `PostgresProvisioner(admin_database(settings))`.

`src/notes_evidence/interfaces/wiring.py` lines 72 to 74:

```python
def database_roles(settings: Settings) -> PostgresRoles:
    """C1 for the database."""
    return PostgresRoles(admin_database(settings))
```

**Function `database_roles`.** C1 for the database.

It takes: `settings` (a `Settings`).

It gives back a `PostgresRoles`.

Step by step:

- Gives back the result of calling `PostgresRoles(admin_database(settings))`.

`src/notes_evidence/interfaces/wiring.py` lines 77 to 82:

```python
def repository_access(settings: Settings) -> RepositoryAccess:
    """Collaborators from a fixture file, or from `gh api` when EVIDENCE_SOURCE=live (set GITHUB_REPOSITORY)."""
    if settings.evidence_source == "live":
        repo = os.environ["GITHUB_REPOSITORY"]
        return GithubRepositoryAccess(command_json(run_command, ["gh", "api", f"repos/{repo}/collaborators"]))
    return GithubRepositoryAccess(file_json(FIXTURES / "github-collaborators.json"))
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `repository_access`.** Collaborators from a fixture file, or from `gh api` when EVIDENCE_SOURCE=live (set GITHUB_REPOSITORY).

It takes: `settings` (a `Settings`).

It gives back a `RepositoryAccess`.

Step by step:

- If `settings.evidence_source` equals `'live'`:
  - Stores `os.environ['GITHUB_REPOSITORY']` in `repo`.
  - Gives back the result of calling `GithubRepositoryAccess(command_json(run_command, ['gh', 'api', f'repos/{repo}/collaborato…`.
- Gives back the result of calling `GithubRepositoryAccess(file_json(FIXTURES / 'github-collaborators.json'))`.

`src/notes_evidence/interfaces/wiring.py` lines 85 to 104:

```python
def change_source(settings: Settings) -> ChangeSource:
    """Merged pull requests and the deployment log, from fixtures or from `gh pr list`."""
    deploys = file_json(FIXTURES / "deploy-log.json")
    if settings.evidence_source == "live":
        repo = os.environ["GITHUB_REPOSITORY"]
        argv = [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "merged",
            "--limit",
            "50",
            "--json",
            "number,title,author,mergedAt,mergeCommit,reviews",
        ]
        return GithubChanges(command_json(run_command, argv), deploys)
    return GithubChanges(file_json(FIXTURES / "github-merged-prs.json"), deploys)
```

**Function `change_source`.** Merged pull requests and the deployment log, from fixtures or from `gh pr list`.

It takes: `settings` (a `Settings`).

It gives back a `ChangeSource`.

Step by step:

- Stores the result of calling `file_json(FIXTURES / 'deploy-log.json')` in `deploys`.
- If `settings.evidence_source` equals `'live'`:
  - Stores `os.environ['GITHUB_REPOSITORY']` in `repo`.
  - Stores the list `['gh', 'pr', 'list', '--repo', repo, '--state', 'merged', '--limit', …` in `argv`.
  - Gives back the result of calling `GithubChanges(command_json(run_command, argv), deploys)`.
- Gives back the result of calling `GithubChanges(file_json(FIXTURES / 'github-merged-prs.json'), deploys)`.

`src/notes_evidence/interfaces/wiring.py` lines 107 to 111:

```python
def cloud_directory(settings: Settings) -> CloudDirectory:
    """The cloud account: a state file seeded from a fixture, or the real account through `aws`."""
    if settings.evidence_source == "live":
        return AwsCloudDirectory()
    return StateCloudDirectory(settings.state_dir / "cloud-users.json", FIXTURES / "aws-iam-users.json")
```

**Function `cloud_directory`.** The cloud account: a state file seeded from a fixture, or the real account through `aws`.

It takes: `settings` (a `Settings`).

It gives back a `CloudDirectory`.

Step by step:

- If `settings.evidence_source` equals `'live'`:
  - Gives back the result of calling `AwsCloudDirectory()`.
- Gives back the result of calling `StateCloudDirectory(settings.state_dir / 'cloud-users.json', FIXTURES / 'aws-iam-users.js…`.

### `src/notes_evidence/interfaces/wsgi.py`

`src/notes_evidence/interfaces/wsgi.py` lines 1 to 12:

```python
"""The WSGI entry point for gunicorn: `gunicorn notes_evidence.interfaces.wsgi:app`."""

from __future__ import annotations

import os

from flask import Flask

from notes_evidence.infrastructure.logging_setup import configure_logging
from notes_evidence.infrastructure.settings import load_settings
from notes_evidence.interfaces.http_app import create_app
from notes_evidence.interfaces.wiring import build_runtime
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The WSGI entry point for gunicorn: `gunicorn notes_evidence.interfaces.wsgi:app`.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `os`.
- From `flask` it takes `Flask`.
- From `notes_evidence.infrastructure.logging_setup` it takes `configure_logging`.
- From `notes_evidence.infrastructure.settings` it takes `load_settings`.
- From `notes_evidence.interfaces.http_app` it takes `create_app`.
- From `notes_evidence.interfaces.wiring` it takes `build_runtime`.

`src/notes_evidence/interfaces/wsgi.py` lines 15 to 20:

```python
def create() -> Flask:
    """Build the app from the environment."""
    settings = load_settings(os.environ)
    configure_logging(settings.log_level)
    runtime = build_runtime(settings)
    return create_app(runtime.service, runtime.app_db.ping)
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `create`.** Build the app from the environment.

It gives back a `Flask`.

Step by step:

- Stores the result of calling `load_settings(os.environ)` in `settings`.
- Calls `configure_logging(settings.log_level)`.
- Stores the result of calling `build_runtime(settings)` in `runtime`.
- Gives back the result of calling `create_app(runtime.service, runtime.app_db.ping)`.

`src/notes_evidence/interfaces/wsgi.py` lines 23 to 23:

```python
app = create()
```

These module-level lines:

- Stores the result of calling `create()` in `app`.

## Try it yourself

```bash
.venv/bin/python -c "import notes_evidence.interfaces.cli; print(notes_evidence.interfaces.cli.__doc__)"
```
Prints the module's description: ``controls-evidence`: run the collectors, build the index, verify and report. Owns the exit codes.`

```bash
.venv/bin/python -c "import notes_evidence.interfaces.health; print(notes_evidence.interfaces.health.__doc__)"
```
Prints the module's description: ``notes-api-health`: the container's health check. Exit 0 when /healthz answers 200.`

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check src/notes_evidence/interfaces/__init__.py src/notes_evidence/interfaces/cli.py src/notes_evidence/interfaces/health.py src/notes_evidence/interfaces/http_app.py src/notes_evidence/interfaces/wiring.py src/notes_evidence/interfaces/wsgi.py
```
Prints `All checks passed!`.

```bash
grep -c "^def \|^class \|    def " src/notes_evidence/interfaces/cli.py
```
Counts the functions, methods and classes in `src/notes_evidence/interfaces/cli.py`.

## Mistakes people make

- Putting rules in a route or a command handler. They call the use cases.
- Returning raw error text to the caller. Named errors map to fixed messages and codes.
- Creating adapters deep inside the code instead of here, which makes testing hard.

## Check yourself

1. What is `build_parser` for?
   **Answer:** One subcommand per collector, plus collect, verify and report.
2. What is `main` for?
   **Answer:** Run one command and return the exit code: 0 ok, 1 findings or a failed step, 2 bad configuration or input.
3. What is `main` for?
   **Answer:** Ask the local API if it is healthy.
4. What is `create_app` for?
   **Answer:** Build the Flask app around a service and a database ping.
5. What is `Runtime` for?
   **Answer:** Everything the programs share.

## Further reading

- Python 3.12 tutorial, classes: <https://docs.python.org/3.12/tutorial/classes.html>
- Python 3.12 language reference: <https://docs.python.org/3.12/reference/>
- Type hints: <https://docs.python.org/3.12/library/typing.html>
