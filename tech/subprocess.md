# subprocess

## What it is

A **process** is a running program. `subprocess.run([...])` lets a Python program start another program, wait for it, give it
input and collect its output and **return code** (0 means success). The command is a **list** of words, so no shell is involved
and nothing is split or expanded by accident.

## Why this repository uses it

Some evidence comes from other tools: the dependency scan (`pip-audit`), a backup and restore (`pg_dump`, `pg_restore`, `psql`
inside the database container), and in live mode the repository and cloud lists (`gh`, `aws`). The wrappers keep the calls
small, time-limited and testable.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/infrastructure/backup.py` | `run_in_container` and `DockerBackupRunner`. |
| `src/notes_evidence/infrastructure/scanner.py` | `run_pip_audit`. |
| `src/notes_evidence/infrastructure/sources.py` | `run_command` for `gh` and `aws`. |

## How it works underneath

`subprocess.run` asks the operating system to start the program with the given arguments. `capture_output=True` connects its
stdout and stderr to pipes that Python reads. `input=` is sent to its stdin. `timeout=` kills it if it takes too long (raising
`TimeoutExpired`). `check=False` means a non-zero return code does not raise: the code decides what to do with it. `text=True`
returns text instead of bytes.

## Walkthrough of this repository's use

`src/notes_evidence/infrastructure/backup.py`:

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

- `subprocess.run(argv, input=stdin, capture_output=True, timeout=300, check=False)`: run, feed `stdin` (bytes or `None`), wait at
  most 300 seconds.
- `except (OSError, subprocess.TimeoutExpired)`: the program is missing or too slow; it becomes a `BackupError`.
- A non-zero `returncode` becomes a `BackupError` that includes the first words of the command and the first 300 characters of the
  error output.
- The function returns `done.stdout`, the bytes the tool printed (for `pg_dump`, the dump itself).

`src/notes_evidence/infrastructure/scanner.py`:

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

`pip-audit` exits with **1** when it finds vulnerabilities and still prints the report, so the wrapper accepts 0 and 1 and treats
any other code, or empty output, as a failure.

`src/notes_evidence/infrastructure/sources.py`:

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

The same pattern for `gh` and `aws`, with `text=True` and a 60-second limit. Tests pass a fake runner (`Callable[[list[str]], str]`),
so no real command runs in the unit tests.

`src/notes_evidence/infrastructure/backup.py`:

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

`[*self._prefix, "pg_dump", "-U", ...]` builds the command: the prefix (`docker compose exec -T db` by default, see
`DB_EXEC_PREFIX` in `.env.example`) followed by the tool and its flags (see `postgresql-tools.md`).

## Try it yourself

```bash
.venv/bin/python -c "import subprocess; d = subprocess.run(['echo', 'hello'], capture_output=True, text=True); print(d.returncode, repr(d.stdout))"
```
Prints `0 'hello\n'`.

```bash
.venv/bin/python -c "import subprocess; print(subprocess.run(['false']).returncode)"
```
Prints `1`.

```bash
.venv/bin/python -c "import subprocess; print(subprocess.run(['cat'], input=b'abc', capture_output=True).stdout)"
```
Prints `b'abc'`: the input was fed to the program's stdin.

```bash
.venv/bin/python -c "import subprocess; subprocess.run(['sleep', '5'], timeout=1)" 2>&1 | tail -1
```
Prints `subprocess.TimeoutExpired: Command '['sleep', '5']' timed out after 1 seconds`.

```bash
make scan
```
Runs the scan collector (needs network): prints `== scan: verdict pass`.

## Mistakes people make

- **Passing one string with `shell=True`**, which lets a space or a `;` change the command. Use a list.
- **No timeout**, so a stuck tool hangs the run.
- **Ignoring the return code.** Here every non-zero code is handled on purpose.
- **Treating pip-audit's exit 1 as a crash.** It means "found something"; the report is still on stdout.

## Check yourself

1. Why pass the command as a list?
   **Answer:** No shell is involved, so spaces and special characters cannot change the command.
2. What does `check=False` mean?
   **Answer:** A non-zero exit does not raise; the code reads `returncode` itself.
3. What does `timeout=300` do?
   **Answer:** Kills the process and raises `TimeoutExpired` after 300 seconds.
4. Why does `run_pip_audit` accept exit code 1?
   **Answer:** pip-audit uses 1 for 'vulnerabilities found' and still prints the report.
5. How do the unit tests avoid running real tools?
   **Answer:** They pass a fake runner function in place of `run_command`.

## Further reading

- `subprocess` (Python 3.12): <https://docs.python.org/3.12/library/subprocess.html>
