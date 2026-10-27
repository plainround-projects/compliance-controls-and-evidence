# ruff

## What it is

A **linter** reads source code without running it and reports likely mistakes and style problems. A **formatter**
rewrites code to one standard layout (spacing, line breaks, quote style). **ruff** does both in one fast program
written in Rust. It replaces several older tools (flake8, isort, pyupgrade, and a formatter like Black).

## Why this repository uses it

A repository meant to teach should read the same everywhere. Ruff catches unused imports, bugs such as a mutable
default argument, outdated syntax, and missing docstrings, and it formats the code the same way every time, so
reviews can talk about meaning.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` `[tool.ruff]` and `[tool.ruff.lint]` | Line length, target Python, rule groups, per-file exceptions. |
| `Makefile` `lint` | `ruff check .` and `ruff format --check .`. |
| `Makefile` `format` | `ruff check --fix .` and `ruff format .` to fix the files. |
| `requirements-dev.lock` | Pins `ruff==0.17.2`. |
| `tech/*.md` | Excluded from ruff with `extend-exclude`, because they quote code fragments. |

## How it works underneath

- Ruff parses each Python file into a syntax tree and runs each enabled **rule** on it. A rule has a code: a
  letter prefix and digits, such as `E501` (line too long) or `F401` (imported but unused).
- A **rule group** is a prefix: selecting `B` enables all the "bugbear" rules whose code starts with `B`.
- `ruff check` only reports. `ruff check --fix` also applies fixes that are safe.
- `ruff format --check` compares each file to what the formatter would write and reports the files that differ,
  without changing them. `ruff format` rewrites them.

## Walkthrough of this repository's use

`pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
src = ["src", "tests"]
```

- `line-length = 120`: lines longer than 120 characters are reported (rule `E501`) and the formatter wraps at 120.
- `target-version = "py312"`: write code valid for Python 3.12; modernization rules assume at least that.
- `src = ["src", "tests"]`: where first-party code lives, so the import-sorting rule can tell it from libraries.

`pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103", "D104"]
```

The groups switched on:
- `E` and `F`: the basic style and error rules (pycodestyle and pyflakes), such as unused imports.
- `I`: import ordering (isort).
- `B`: flake8-bugbear, likely bugs.
- `UP`: pyupgrade, use modern syntax (`list[str]` instead of `List[str]`).
- `SIM`: simplifications (for example a conditional that can be one expression).
- `N`: naming conventions (classes in CapWords, functions in snake_case).
- `C4`: cleaner comprehensions.
- `RUF`: ruff's own rules.
- `PT`: pytest style.
- `D100`, `D101`, `D103`, `D104`: a docstring is required for every public module, class, function and package.

`pyproject.toml`:

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D"]
```

`"tests/**" = ["D"]` turns off the docstring rules for everything under `tests/`: test names already explain
themselves.

`pyproject.toml`:

```toml
extend-exclude = ["tech"]  # tech/ quotes fragments of code inside Markdown; ruff 0.17 would try to format them
```

`extend-exclude` adds folders ruff must skip. This version of ruff also reads Markdown files (`*.md`) and formats the
Python code blocks inside them. The notes in `tech/` quote single lines and pieces of classes that are not complete
programs, so ruff cannot format them. Excluding `tech` keeps `make lint` green. The other Markdown files contain no Python
blocks and are still checked.

## Try it yourself

```bash
.venv/bin/ruff --version
```
Prints `ruff 0.17.2`.

```bash
.venv/bin/ruff check .
```
Prints `All checks passed!`.

```bash
.venv/bin/ruff format --check .
```
Prints `69 files already formatted`.

```bash
printf 'import os\nx=1\n' > /tmp/demo.py && .venv/bin/ruff check --isolated --select F /tmp/demo.py
```
`--isolated` ignores the repository's config. Ruff reports `F401 [*] os imported but unused`. The `[*]` marks a fix
that `--fix` can apply.

```bash
.venv/bin/ruff rule E501
```
Prints the documentation of one rule, with the reason it exists.

## Mistakes people make

- **Running only the checker, not the formatter** (or the other way). CI runs both.
- **Silencing a rule everywhere** to fix one line. Prefer a narrow, commented exception.
- **Disagreeing about style in review.** The formatter decides; nobody argues.
- **Skipping `--check` in CI.** Without it `ruff format` would rewrite files in CI and pass.
- **Forgetting that Markdown is checked too.** A Python code block in a `.md` file is formatted like a source file.

## Check yourself

1. What is the difference between `ruff check` and `ruff format`?
   **Answer:** `check` finds problems by rules; `format` rewrites layout to one standard.
2. What does `D103` require?
   **Answer:** A docstring on every public function.
3. Why does `tests/**` ignore the `D` group?
   **Answer:** Test function names already describe the test; docstrings would be noise.
4. What does `--check` do on `ruff format`?
   **Answer:** It reports files that would change and changes nothing.
5. What does `line-length = 120` affect?
   **Answer:** The `E501` rule and where the formatter wraps lines.

## Further reading

- Ruff 0.17 documentation: <https://docs.astral.sh/ruff/>
- Rules list: <https://docs.astral.sh/ruff/rules/>
- Configuration: <https://docs.astral.sh/ruff/configuration/>
