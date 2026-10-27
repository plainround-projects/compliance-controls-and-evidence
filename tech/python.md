# Python 3.12 (the language)

## What it is

Python is a programming language. You write instructions in plain text files that end in `.py`; a program called
the **interpreter** reads them and does what they say. A **module** is one `.py` file. A **package** is a folder of
modules with an `__init__.py` file. A **function** is a named block of instructions (`def name(...):`). A **class** is
a blueprint for objects that bundle data and functions.

This repository needs Python 3.12 or newer (`requires-python = ">=3.12"`); it is developed and tested on 3.13 and
runs on 3.12 in CI.

## Why this repository uses it

Python reads almost like English, which suits a service whose rules (who may read which note) should be easy to read. Its standard library covers most needs; the program adds three packages for the web (Flask), the server (gunicorn) and the database (psycopg).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/domain/` | The rules, written as plain functions and frozen dataclasses. Imports nothing of ours except the domain. |
| `src/notes_evidence/application/` | The use cases (`check_documents`) and the interfaces they need (`ports.py`). |
| `src/notes_evidence/infrastructure/` | The adapters: file system, Markdown parser, settings from the environment. |
| `src/notes_evidence/interfaces/cli.py` | The command line and exit codes. |
| `tests/` | pytest tests, also Python. |

## How it works underneath

1. You run `python file.py` (or a command created from it). The interpreter turns the text into **bytecode**
   (simple instructions) and runs them one by one.
2. Names point to objects. `x = 3` makes the name `x` point to the number 3.
3. `import a.b` finds the file `a/b.py` in the folders listed in `sys.path`, runs it once, and keeps it in memory
   for any later import.
4. Indentation (four spaces) groups lines into blocks. There are no braces.
5. Errors are **exceptions**. `raise SomeError("message")` stops the current function and goes up the call chain
   until a `try ... except` handles it, or the program ends with a traceback.
6. **Type hints** (`x: int`) are notes for people and tools; the interpreter ignores them. See `mypy.md`.

## Walkthrough of this repository's use

### A module, from top to bottom

`src/notes_evidence/domain/findings.py`:

```python
"""The result of a rule: a finding with a code, a severity and the document it is about."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
```

- The triple-quoted text at the top is the module's **docstring**: a description, kept by Python and checked by ruff.
- `from __future__ import annotations` makes all type hints in this file lazy text instead of values evaluated at
  load time. It lets a hint mention a class defined further down.
- `from dataclasses import dataclass` takes one name out of a module. `from enum import Enum` likewise.

### A class that names a fixed set of choices

`src/notes_evidence/domain/findings.py`:

```python
class Severity(Enum):
    """ERROR fails the check; WARNING is reported and does not."""

    ERROR = "error"
    WARNING = "warning"
```

`Enum` makes a class whose members are the only allowed values: `Severity.ERROR` and `Severity.WARNING`. The string
on the right of each is its stored value. Comparing with `is` (`finding.severity is Severity.ERROR`) is exact.

### Functions with type hints and docstrings

`src/notes_evidence/domain/findings.py`:

```python
def error(code: str, subject: str, message: str) -> Finding:
    """Build an ERROR finding."""
    return Finding(code, Severity.ERROR, subject, message)
```

- `code: str` means the parameter `code` should be text. `-> Finding` says the function returns a `Finding`.
- `Finding(code, Severity.ERROR, subject, message)` creates an object by calling the class.

### Properties, tuples and a generator expression

`src/notes_evidence/domain/findings.py`:

```python
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

- `@property` lets you write `report.errors` without parentheses; it runs the function.
- `tuple(f for f in self.findings if f.severity is Severity.ERROR)` is a **generator expression** inside `tuple(...)`:
  loop over `self.findings`, keep each `f` whose severity is ERROR, and make a tuple from the kept ones.
- `not self.errors` is `True` when the tuple is empty (an empty tuple counts as false).

### Raising an error and chaining it away

`src/notes_evidence/infrastructure/settings.py`:

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

- `env.get(name, str(default))` reads a value from a mapping, or the default when the name is missing.
- `try: ... except ValueError:` runs the `except` block only if `int(raw)` fails.
- `raise SettingsError(...) from None` raises a new error and hides the original traceback, so the user sees only the
  clear message.
- The `f"...{name}..."` is an **f-string**: text with expressions in braces. `{raw!r}` prints `raw` as Python would
  write it, with quotes, so `'lots'` shows clearly.

### The entry point

`src/notes_evidence/interfaces/cli.py`:

```python
def main(argv: Sequence[str] | None = None) -> int:
    """Run one command and return the exit code: 0 ok, 1 findings or a failed step, 2 bad configuration or input."""
    args = build_parser().parse_args(argv)
```


`src/notes_evidence/interfaces/cli.py`:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

`__name__` is `"__main__"` only when the file is run directly, not when it is imported. `SystemExit(code)` ends the
program with that exit status. The command `controls-evidence` (made by `[project.scripts]`) calls `main` and exits with its
return value.

### The walrus operator

`src/notes_evidence/infrastructure/catalog.py`:

```python
                if bad := [spec.kind for spec in specs if spec.kind not in KINDS]:
```

`:=` assigns and tests in one go: `(m := ...)` stores the match in `m`, and the condition is true only when there is
a match. `bad := [...]` builds a list of unknown kinds and tests it in one go: if the list is not empty the code raises an error that names the first unknown kind.

## Try it yourself

```bash
.venv/bin/python --version
```
Prints the interpreter version (`Python 3.13.x`).

```bash
.venv/bin/python -c "from notes_evidence.domain.findings import error; print(error('X1', 'file.md', 'oops'))"
```
Prints `Finding(code='X1', severity=<Severity.ERROR: 'error'>, subject='file.md', message='oops')`.

```bash
.venv/bin/python -c "import notes_evidence.domain.findings as f; print(f.Severity.ERROR is f.Severity('error'))"
```
Prints `True`: looking up an enum member by value gives the same object.

```bash
.venv/bin/python -m notes_evidence.interfaces.cli --help
```
Runs the command as a module: prints the usage text.

```bash
.venv/bin/python -c "x = [n * n for n in range(5) if n % 2 == 0]; print(x)"
```
Prints `[0, 4, 16]`: a list comprehension (squares of the even numbers below 5).

## Mistakes people make

- **Mixing tabs and spaces** for indentation. `.editorconfig` and `ruff format` prevent it.
- **Changing a list while looping over it.**
- **Using `==` to compare with `None`.** Use `is None`.
- **Mutable default arguments** (`def f(x=[])`). Ruff's `B` rules catch this.
- **Catching every error** with a bare `except:` and hiding bugs. This code catches the one named error it expects.

## Check yourself

1. What does `from __future__ import annotations` do?
   **Answer:** It makes type hints lazy text, so they need not be evaluable at load time.
2. What does `raise X from None` do?
   **Answer:** It raises a new error without showing the original one as its cause.
3. What does `@property` allow?
   **Answer:** Calling a method like an attribute, without parentheses.
4. What is `__name__ == "__main__"` for?
   **Answer:** To run code only when the file is started directly, not when imported.
5. What does `(m := pattern.match(line))` do in an `if`?
   **Answer:** It stores the match in `m` and tests whether there was one.

## Further reading

- Python 3.12 tutorial: <https://docs.python.org/3.12/tutorial/>
- Language reference: <https://docs.python.org/3.12/reference/>
- What's new in 3.12: <https://docs.python.org/3.12/whatsnew/3.12.html>
