# pytest-cov and coverage.py

## What it is

**Code coverage** is the share of a program's lines that ran while the tests ran. **coverage.py** is the Python
tool that measures it. **pytest-cov** is a plug-in that lets pytest start coverage.py with the option `--cov`.
Coverage does not prove the tests are good. It does show, with certainty, which lines no test touched.

## Why this repository uses it

The rules in `domain/` and `application/` are the heart of this repository. If a rule is never run by a test, nobody
knows it works. The Makefile therefore fails when those two folders drop under 95 percent.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` `test` | Runs `pytest --cov=notes_evidence` and then `coverage report --fail-under=95`. |
| `pyproject.toml` `[tool.coverage.run]` | Which package to measure and to measure branches too. |
| `pyproject.toml` `[tool.coverage.report]` | What the report prints. |
| .coverage (generated, git-ignored) | The data file coverage.py writes. |

## How it works underneath

1. coverage.py installs a hook in the Python interpreter that records every line (and, with branch measurement,
   every jump from one line to another) as it executes.
2. When the process ends, the data is saved to a file called `.coverage`.
3. `coverage report` reads that file, compares it to the source files, and prints a table of statements, misses,
   branches, partial branches and a percentage per file.
4. `--fail-under=95` makes the command exit with status 2 if the total is lower. Make sees the failure and stops.
5. A **branch** is a choice such as an `if`. Branch measurement notices when only one side of an `if` was ever taken.

## Walkthrough of this repository's use

`Makefile`:

```make
test: $(STAMP) ## unit tests with coverage (no services needed)
	$(PY) -m pytest tests/unit --cov=notes_evidence --cov-report=term
	$(PY) -m coverage report --include='src/notes_evidence/domain/*,src/notes_evidence/application/*' --fail-under=95
```

- Line 1: `pytest tests/unit --cov=notes_evidence --cov-report=term` runs the tests, measures the package `notes_evidence`, and prints the
  table in the terminal (`term`).
- Line 2: `coverage report --include='...' --fail-under=95` prints again, but only for files matching the patterns
  `src/notes_evidence/domain/*` and `src/notes_evidence/application/*`, and fails under 95. The single quotes stop the shell from
  expanding the `*`.

`pyproject.toml`:

```toml
[tool.coverage.run]
source = ["notes_evidence"]
branch = true
```

`source` names the package. `branch = true` also measures decisions, so `if` with no `else` test is noticed.

`pyproject.toml`:

```toml
[tool.coverage.report]
show_missing = true
skip_covered = false
```

`show_missing` adds a column listing missed line numbers. `skip_covered = false` keeps fully covered files in the
table, so the whole picture is visible.

How to read a row: `application/check_documents.py  68  0  20  1  99%  70->73` means 68 statements, 0 missed, 20
branches, 1 partly covered, 99 percent; the branch from line 70 to line 73 was never taken.

## Try it yourself

```bash
make test
```
Prints the pytest result, then the coverage table, ending with a `TOTAL` row near `99%` or `100%`.

```bash
.venv/bin/python -m coverage report --include='src/notes_evidence/domain/*' | tail -4
```
Shows only the domain files.

```bash
.venv/bin/python -m coverage report --fail-under=100 > /dev/null; echo $?
```
Prints `2` if the total is under 100 and `0` otherwise: this shows the exit status that Make relies on.

```bash
.venv/bin/python -m coverage html && ls htmlcov | head -3
```
Writes a web page of the report (open `htmlcov/index.html`). `htmlcov/` is git-ignored.

## Mistakes people make

- **Chasing 100 percent with weak tests.** A line that ran is not a line that was checked. The tests here also
  assert results.
- **Measuring the tests themselves**, which inflates the number. `source` limits it to the package.
- **Forgetting the quotes** around a pattern with `*`, so the shell expands it first.
- **Ignoring branches.** A function can have all lines run and still never take an `else`.

## Check yourself

1. What is the difference between line and branch coverage?
   **Answer:** Line coverage asks if a line ran; branch coverage asks if each way out of a decision was taken.
2. Which file holds the measurements?
   **Answer:** `.coverage`.
3. What does `--fail-under=95` do?
   **Answer:** The command exits non-zero if the total is below 95 percent.
4. Why does the second command use `--include`?
   **Answer:** To hold only `domain/` and `application/` to 95 percent, not the adapters.
5. Does 100 percent coverage prove there are no bugs?
   **Answer:** No. It only shows every line ran at least once.

## Further reading

- coverage.py 7.17: <https://coverage.readthedocs.io/en/7.17.0/>
- Configuration reference: <https://coverage.readthedocs.io/en/7.17.0/config.html>
- pytest-cov 7.1: <https://pytest-cov.readthedocs.io/en/stable/ (the page for the 7.1 line)>
