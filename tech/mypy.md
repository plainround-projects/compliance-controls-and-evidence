# mypy

## What it is

Python lets you write **type hints**, such as `def squash(text: str) -> str`. Python itself ignores them when the
program runs. **mypy** reads them before the program runs and reports places where the types do not fit, such as
passing a number where a string is expected. This is called **static** checking (static means "without running").

## Why this repository uses it

The documents are parsed into typed values (`Adr`, `Finding`, `Report`). Types make the rules readable (a function
says what it takes and gives back) and catch a wrong field name or a missing `None` check at once. Strict mode is
chosen so that nothing is left untyped.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` `[tool.mypy]` | `strict = true`, the Python version and the files to check. |
| `pyproject.toml` `[[tool.mypy.overrides]]` | A relaxed setting for `tests.*`. |
| `Makefile` `lint` | Runs `.venv/bin/mypy`. |
| `src/notes_evidence/**` | Every function has parameter and return types. |

## How it works underneath

mypy parses all files, builds a model of every function's signature, and then checks every call and assignment
against it. It never imports or runs your program. When it sees `x: int | None`, it makes you handle `None` before
you use `x` as an `int`. It keeps a cache in `.mypy_cache/` to speed up repeated runs.

## Walkthrough of this repository's use

`pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["src", "tests"]
```

- `python_version = "3.12"`: check as if running Python 3.12.
- `strict = true`: turn on a bundle of strict flags. Among them: `--disallow-untyped-defs` (every function needs
  hints), `--disallow-incomplete-defs`, `--disallow-any-generics` (write `list[str]`, not bare `list`),
  `--warn-return-any`, `--warn-unused-ignores`, `--strict-equality`, `--no-implicit-reexport` and `--extra-checks`.
  `mypy --help` lists the full bundle for the pinned version.
- `files = ["src", "tests"]`: what to check when run with no arguments.

`pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false
```

`[[...]]` (double brackets) is a TOML list of tables. This entry relaxes four strict flags only for modules matching
`tests.*`, so test functions may omit hints while the source stays fully typed.

A few hints from the code, to read them as mypy does:
`src/notes_evidence/interfaces/cli.py`:

```python
def main(argv: Sequence[str] | None = None) -> int:
```

`argv: Sequence[str] | None = None` means "a list-like of strings, or nothing". `-> int` says it returns an exit code.

`src/notes_evidence/domain/findings.py`:

```python
class Report:
    """Every finding from one run, plus the subjects that were checked."""

    subjects: tuple[str, ...]
    findings: tuple[Finding, ...]
```

`tuple[Finding, ...]` is a tuple of any length whose items are all `Finding`.

## Try it yourself

```bash
.venv/bin/mypy
```
Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/mypy --version
```
Prints `mypy 2.4.0 (compiled: yes)`.

```bash
printf 'def add(a: int, b: int) -> int:\n    return a + b\n\nadd("1", 2)\n' > /tmp/demo_types.py && .venv/bin/mypy --strict /tmp/demo_types.py
```
mypy reports `Argument 1 to "add" has incompatible type "str"; expected "int"`.

```bash
.venv/bin/mypy --help | grep -A3 -- "--strict "
```
Shows what `--strict` turns on for this version.

## Mistakes people make

- **Sprinkling `# type: ignore`** to make errors vanish. This repository avoids it; the strict setting also warns
  about ignores that no longer do anything.
- **Using `Any` everywhere.** It switches checking off for that value.
- **Thinking hints change runtime behavior.** They do not; `main("x")` would still run.
- **Ignoring `None`.** `int | None` means the code must handle the missing case.

## Check yourself

1. Does Python enforce type hints when the program runs?
   **Answer:** No. Only a checker such as mypy does.
2. What does `strict = true` change?
   **Answer:** It turns on a bundle of stricter flags, such as requiring a type on every function.
3. What does `X | None` mean?
   **Answer:** A value that is either an `X` or `None`.
4. Why are tests allowed fewer hints?
   **Answer:** The override relaxes four flags for `tests.*`, so test functions need no annotations.
5. Where does mypy keep its cache?
   **Answer:** In `.mypy_cache/`, which is git-ignored.

## Further reading

- mypy 2.4 documentation: <https://mypy.readthedocs.io/en/stable/>
- Command line flags: <https://mypy.readthedocs.io/en/stable/command_line.html>
- Type hints cheat sheet: <https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html>
