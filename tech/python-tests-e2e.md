# The tests (e2e)

## What it is

The pytest tests in `tests/e2e`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/e2e/test_scenario.py` | 47 lines. The lesson's scenario end to end: use the service, collect the artifacts, review access, verify, catch tamper… |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/e2e/test_scenario.py`

`tests/e2e/test_scenario.py` lines 1 to 12:

```python
"""The lesson's scenario end to end: use the service, collect the artifacts, review access, verify, catch tampering.

Runs from the repository root against the PostgreSQL of `make up` and writes into a temporary folder.
"""

from __future__ import annotations

import os

import pytest

from notes_evidence.interfaces.cli import main
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The lesson's scenario end to end: use the service, collect the artifacts, review access, verify, catch tampering. Runs from the repository root against the PostgreSQL of `make up` and writes into a temporary folder.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `os`.
- It imports module `pytest`.
- From `notes_evidence.interfaces.cli` it takes `main`.

`tests/e2e/test_scenario.py` lines 14 to 14:

```python
pytestmark = pytest.mark.e2e
```

These module-level lines:

- Stores `pytest.mark.e2e` in `pytestmark`.

`tests/e2e/test_scenario.py` lines 17 to 27:

```python
@pytest.fixture
def scenario(tmp_path, monkeypatch):
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not set: run `make up` and use `make test-e2e`")
    for name, value in (
        ("EVIDENCE_DIR", tmp_path / "evidence"),
        ("STATE_DIR", tmp_path / "state"),
        ("REPORT_DIR", tmp_path / "build"),
    ):
        monkeypatch.setenv(name, str(value))
    return tmp_path
```

> **In plain words.** A **fixture** is a helper function marked `@pytest.fixture`. A test that names it as a parameter receives its return value, prepared fresh for that test.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `tmp_path` is a built-in pytest fixture: a fresh, empty temporary folder (a `Path`) that is removed after the test.
> **In plain words.** `monkeypatch` is a built-in pytest fixture that changes something (an environment variable, an attribute) for this test only and undoes it afterwards.

**Function `scenario`.**

It takes: `tmp_path`; `monkeypatch`.

Decorators: `@pytest.fixture`.

Step by step:

- If not (`os.environ.get('DATABASE_URL')`):
  - Calls `pytest.skip('DATABASE_URL is not set: run `make up` and use `make test-e2e`')`.
- For each `(name, value)` in the tuple `(('EVIDENCE_DIR', tmp_path / 'evidence'), ('STATE_DIR', tmp_path / 's…`:
  - Calls `monkeypatch.setenv(name, str(value))`.
- Gives back `tmp_path`.

`tests/e2e/test_scenario.py` lines 30 to 60:

```python
def test_collect_produces_a_pack_that_verifies_and_tampering_is_caught(scenario, capsys):
    assert main(["collect"]) == 0
    out = capsys.readouterr().out
    assert "== exercise: 4 accounts used the service, 3 notes written, 2 requests refused" in out
    assert "== alert-test: 2 alert(s) delivered: failed-logins; admin-granted" in out
    assert "== review: 1 access removed" in out
    assert out.splitlines()[-1].startswith("OK:")

    pack = scenario / "evidence"
    names = {path.name for path in pack.iterdir()}
    assert names == {
        "C1-access-list.txt", "C2-changes.csv", "C3-log-sample.txt", "C3-alert-test.txt",
        "C4-restore-test.txt", "C5-scan-report.json", "C6-access-review.md", "INDEX.md", "manifest.json",
    }  # fmt: skip
    assert "contractor-lee" not in (pack / "C1-access-list.txt").read_text()
    assert "Removed: cloud account users contractor-lee." in (pack / "C6-access-review.md").read_text()
    assert "result: verified" in (pack / "C4-restore-test.txt").read_text()
    assert "ALERT [failed-logins]" in (pack / "C3-alert-test.txt").read_text()
    assert "EXC-1 (C2)" in (pack / "INDEX.md").read_text()
    assert (scenario / "state" / "alerts.log").read_text().count("ALERT") == 2

    assert main(["verify"]) == 0
    assert main(["report"]) == 0
    assert "| iso27001 | A.5.18 | C1, C6 (overlap) |" in (scenario / "build" / "report.md").read_text()

    capsys.readouterr()
    (pack / "C2-changes.csv").write_text(
        (pack / "C2-changes.csv").read_text() + '99,"ada","2026-10-22T00:00:00Z","abc1234","ada","d"\n'
    )
    assert main(["verify"]) == 1
    assert "EVD003" in capsys.readouterr().out
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.
> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.
> **In plain words.** `capsys` is a built-in pytest fixture that captures what the program prints, so the test can read it with `capsys.readouterr()`.

**Test `test_collect_produces_a_pack_that_verifies_and_tampering_is_caught`** checks: collect produces a pack that verifies and tampering is caught.

It takes: `scenario`; `capsys`.

Step by step:

- Checks that `main(['collect'])` equals `0`; if not, the test fails.
- Stores `capsys.readouterr().out` in `out`.
- Checks that `'== exercise: 4 accounts used the service, 3 note…` is in `out`; if not, the test fails.
- Checks that `'== alert-test: 2 alert(s) delivered: failed-logi…` is in `out`; if not, the test fails.
- Checks that `'== review: 1 access removed'` is in `out`; if not, the test fails.
- Checks that `out.splitlines()[-1].startswith('OK:')`; if not, the test fails.
- Stores `scenario / 'evidence'` in `pack`.
- Stores a new set made by a loop (`{path.name for path in pack.iterdir()}`) in `names`.
- Checks that `names` equals `{'C1-access-list.txt', 'C2-changes.csv', 'C3-log-…`; if not, the test fails.
- Checks that `'contractor-lee'` is not in `(pack / 'C1-access-list.txt').read_text()`; if not, the test fails.
- Checks that `'Removed: cloud account users contractor-lee.'` is in `(pack / 'C6-access-review.md').read_text()`; if not, the test fails.
- Checks that `'result: verified'` is in `(pack / 'C4-restore-test.txt').read_text()`; if not, the test fails.
- Checks that `'ALERT [failed-logins]'` is in `(pack / 'C3-alert-test.txt').read_text()`; if not, the test fails.
- Checks that `'EXC-1 (C2)'` is in `(pack / 'INDEX.md').read_text()`; if not, the test fails.
- Checks that `(scenario / 'state' / 'alerts.log').read_text().c…` equals `2`; if not, the test fails.
- Checks that `main(['verify'])` equals `0`; if not, the test fails.
- Checks that `main(['report'])` equals `0`; if not, the test fails.
- Checks that `'| iso27001 | A.5.18 | C1, C6 (overlap) |'` is in `(scenario / 'build' / 'report.md').read_text()`; if not, the test fails.
- Calls `capsys.readouterr()`.
- Calls `(pack / 'C2-changes.csv').write_text((pack / 'C2-changes.csv').read_text() + '99,"ada","2026-10-22T00:00:00Z"…`.
- Checks that `main(['verify'])` equals `1`; if not, the test fails.
- Checks that `'EVD003'` is in `capsys.readouterr().out`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/e2e
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check tests/e2e/test_scenario.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_collect_produces_a_pack_that_verifies_and_tampering_is_caught` check?
   **Answer:** it checks: collect produces a pack that verifies and tampering is caught.
2. What is a docstring?
   **Answer:** A text in triple quotes at the start of a module, class or function that describes it.
3. What does `frozen=True` do on a dataclass?
   **Answer:** It forbids changing a field after the object is created.
4. What does a type hint do at run time?
   **Answer:** Nothing; mypy reads hints before the program runs.
5. What is a fixture?
   **Answer:** A helper function whose return value pytest passes to tests that name it as a parameter.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
