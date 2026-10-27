# argparse (the command line)

## What it is

A **command-line program** is started by typing its name and some words: `controls-evidence check`. Those words are its
**arguments**. `argparse` is the standard Python module that reads them, checks them, builds the `--help` text and
reports mistakes. An **exit code** is the number a program returns to the shell when it ends: 0 means success, other
numbers mean different failures.

## Why this repository uses it

`make run` and CI decide pass or fail from the exit code, so the command must return the right number. `argparse`
gives subcommands (`check`, `report`...) and a free help text, with no extra packages.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/interfaces/cli.py` | `build_parser()` and `main()` for `controls-evidence`. |
| `src/notes_evidence/interfaces/health.py` | `notes-api-health`, the container's health check (no argument parsing; an exit code only). |
| `pyproject.toml` `[project.scripts]` | Registers both commands. |
| `Makefile` | `$(CLI) collect`, `$(CLI) verify`, `$(CLI) report`, `$(CLI) scan`. |
| `tests/unit/interfaces/test_cli.py` | Calls `main([...])` directly and checks the exit code. |

## How it works underneath

1. The shell starts the program with a list of words. Python puts them in `sys.argv`.
2. `parser.parse_args(argv)` walks that list: the first word picks a subcommand; options like `--write` are matched by
   name. Unknown words make `argparse` print an error and exit with code 2.
3. The result is a `Namespace` object whose attributes are the answers (`args.command`).
4. The program does its work and returns an integer. `raise SystemExit(main())` turns the integer into the process
   exit code. The shell stores it in `$?`.

## Walkthrough of this repository's use

`src/notes_evidence/interfaces/cli.py`:

```python
STEPS = ("exercise", "alert-test", "log-sample", "access", "changes", "restore-test", "scan", "review", "index")
```

`src/notes_evidence/interfaces/cli.py`:

```python
def build_parser() -> argparse.ArgumentParser:
    """One subcommand per collector, plus collect, verify and report."""
    parser = argparse.ArgumentParser(prog="controls-evidence", description="Produce and verify the evidence pack.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in (*STEPS, "collect", "verify", "report"):
        commands.add_parser(name)
    return parser
```

- `STEPS` is a tuple of the nine collector names. The loop `for name in (*STEPS, "collect", "verify", "report")` adds one
  subcommand per name. `*STEPS` **unpacks** the tuple into the new tuple.
- `add_subparsers(dest="command", required=True)` makes the subcommand group; the chosen one is `args.command`.
- There are no options: everything the program needs comes from the environment (see `env-files.md`).

`src/notes_evidence/interfaces/cli.py`:

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

- The docstring lists the exit codes: **0** ok, **1** findings or a failed step, **2** bad configuration or input.
- Settings and the controls catalog errors become `configuration error: ...` and exit 2; a failed source, backup or scan becomes
  `step failed: ...` and exit 1. Both go to **stderr**.
- `configure_logging("WARNING")` keeps the program quiet except for warnings (the alert stand-in logs at WARNING).

`src/notes_evidence/interfaces/cli.py`:

```python
def _dispatch(command: str, settings: Settings) -> int:
    store = FileEvidenceStore(settings.evidence_dir)
    catalog = TomlCatalog(settings.controls_file)
    if command == "verify":
        report = _verify(store, catalog)
        print(render_text(report))
        return 0 if report.ok else 1
```

`_dispatch` builds the evidence store and the catalog, then handles `verify` and `report`, which do not need a database. For every
other command it builds the runtime (database connections), runs the chosen step, or all nine for `collect`, and prints
`== step: summary` lines.

`src/notes_evidence/interfaces/health.py`:

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

The health check has no parser at all. It asks the local API for `/healthz`, returns **0** if the answer is `200`, and **1**
otherwise. Docker uses the exit code (see `dockerfile.md`).

## Try it yourself

```bash
.venv/bin/controls-evidence --help | head -8
```
Prints the usage line and the list of subcommands: `exercise`, `alert-test`, `log-sample`, `access`, `changes`, `restore-test`,
`scan`, `review`, `index`, `collect`, `verify`, `report`.

```bash
.venv/bin/controls-evidence nonsense; echo "exit: $?"
```
`argparse` prints `error: argument command: invalid choice: 'nonsense'` and the shell shows `exit: 2`.

```bash
.venv/bin/controls-evidence verify; echo "exit: $?"
```
Without the settings in your shell this prints `configuration error: DATABASE_URL is required` or similar, and `exit: 2`. With them
loaded (`set -a; . ./.env; set +a`) it verifies the pack in `evidence/` and prints `OK: 9 files checked, 0 errors, 0 warnings`.

```bash
make verify
```
The same through Make, which loads `.env` for you. Needs no database.

```bash
.venv/bin/notes-api-health; echo "exit: $?"
```
With no API listening this prints `unhealthy` on stderr and `exit: 1`.

## Mistakes people make

- **Printing errors to stdout.** Errors belong on stderr so scripts can separate them.
- **Always exiting 0**, so CI cannot tell a failure. This program returns 1 for findings and 2 for bad setup.
- **Reading `sys.argv` by hand.** `argparse` handles quoting, options and help.
- **Calling `sys.exit` deep inside the code.** Only `main` decides the exit code; the rest returns values.

## Check yourself

1. What do the exit codes of `controls-evidence` mean?
   **Answer:** 0 ok, 1 findings or a failed step, 2 bad configuration or input.
2. What does `*STEPS` do in `(*STEPS, "collect", ...)`?
   **Answer:** It unpacks the tuple's items into the new tuple.
3. Why does `verify` need no database?
   **Answer:** It reads the evidence folder and the controls files only.
4. How does Docker learn whether the API is healthy?
   **Answer:** From the exit code of `notes-api-health`: 0 healthy, 1 unhealthy.
5. Where do error messages go?
   **Answer:** To stderr, so scripts can separate them from normal output.

## Further reading

- `argparse` (Python 3.12): <https://docs.python.org/3.12/library/argparse.html>
- Argparse tutorial: <https://docs.python.org/3.12/howto/argparse.html>
