# setuptools and Python packaging

## What it is

**Packaging** is how a folder of Python files becomes something `pip` can install. A **build backend** is the program
that does the build. **setuptools** is the oldest and most common backend. It reads the project description in
`pyproject.toml`, finds the Python packages, and (for an editable install) creates the pointer that makes the code
importable.

## Why this repository uses it

Two things need packaging: the code under `src/notes_evidence/` must be importable as `notes_evidence` (so tests and the command can
import it), and the command `controls-evidence` must exist. Both come from a few lines of `pyproject.toml`.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` `[build-system]` | Names setuptools as the backend. |
| `pyproject.toml` `[project]` | Name, version, Python version, license, authors, dependencies. |
| `pyproject.toml` `[project.scripts]` | Creates the `controls-evidence` command. |
| `pyproject.toml` `[tool.setuptools.packages.find]` | Says the packages are under `src/`. |
| `src/notes_evidence/` | The package itself. |

## How it works underneath

1. `pip install -e .` reads `[build-system]` in `pyproject.toml`. It makes a temporary, isolated environment and
   installs `setuptools>=75` into it. That download is not covered by the hash lock.
2. It asks setuptools to prepare an editable install. setuptools finds the packages under `src/` and writes a small
   `.pth` file into `.venv/lib/python3.x/site-packages/`. A `.pth` file lists a folder that Python adds to its import
   path. After this, `import notes_evidence` finds `src/notes_evidence/`.
3. For each line under `[project.scripts]` pip writes an executable script into `.venv/bin/`. That script imports
   the named function and calls it.
4. The **src layout** (code under `src/`, not at the root) prevents tests from importing the code by accident from
   the current folder. They must import the installed package, as users would.

## Walkthrough of this repository's use

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

- `requires = ["setuptools>=75"]`: install this to build. `>=75` means version 75 or newer.
- `build-backend = "setuptools.build_meta"`: the Python object pip calls to build.

`pyproject.toml`:

```toml
[project]
name = "compliance-controls-and-evidence"
version = "0.1.0"
description = "A small notes service and the evidence pack that proves six security controls: access list, change record, log and alert, restore test, scan report, access review."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Sumit Srivastava" }]
dependencies = ["flask>=3.1,<4", "gunicorn>=23", "psycopg[binary]>=3.2,<4"]
```

- `name` is the distribution name pip shows (`pip show compliance-controls-and-evidence`). It differs from the import name `notes_evidence`.
- `version = "0.1.0"` is the version.
- `requires-python = ">=3.12"`: pip refuses older Pythons.
- `license = { text = "MIT" }` and `authors` are metadata.
- `dependencies = ["flask>=3.1,<4", "gunicorn>=23", "psycopg[binary]>=3.2,<4"]`: the three runtime packages, each with a version range (see `flask.md`, `gunicorn.md`, `psycopg.md`).

`pyproject.toml`:

```toml
[project.scripts]
controls-evidence = "notes_evidence.interfaces.cli:main"
```

The left side is the command name; the right side is `module.path:function`. pip's generated script is the one shown
in `.venv/bin/controls-evidence`: it imports `main` from `notes_evidence.interfaces.cli` and exits with the number it returns.

`pyproject.toml`:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

`where = ["src"]` tells setuptools to look for packages in `src/`, which finds `notes_evidence` and its sub-packages (each has
an `__init__.py`).

## Try it yourself

```bash
cat .venv/bin/controls-evidence
```
Shows the generated script: a `#!` line pointing at the venv's Python, `from notes_evidence.interfaces.cli import main`, and
`sys.exit(main())`.

```bash
ls .venv/lib/python3.*/site-packages | grep -i editable
```
Shows one `__editable__...pth` file. Print it with `cat` to see the path of `src/`.

```bash
.venv/bin/controls-evidence --help
```
Prints the command's usage and the subcommands.

```bash
.venv/bin/pip show -f compliance-controls-and-evidence | head -12
```
Shows the name `compliance-controls-and-evidence`, version `0.1.0`, and the files pip recorded.

## Mistakes people make

- **Putting `__init__.py` nowhere**, so setuptools finds no package. Every folder under `src/notes_evidence/` has one.
- **Confusing the distribution name and the import name.** `pip show compliance-controls-and-evidence` but `import notes_evidence`.
- **Forgetting to reinstall** after adding a new command under `[project.scripts]`. Run `make install` (touch
  `pyproject.toml` first, or delete `.venv/.installed`).
- **Trusting the lock file for the build backend.** The backend is downloaded fresh at install time.

## Check yourself

1. What does `[project.scripts]` do?
   **Answer:** It makes pip create a command in `.venv/bin/` that calls a named Python function.
2. Why use a `src/` layout?
   **Answer:** So code cannot be imported from the current folder by accident; tests use the installed package.
3. What is a `.pth` file?
   **Answer:** A file in `site-packages` that adds a folder to Python's import path; editable installs use one.
4. What are the distribution name and import name here?
   **Answer:** `compliance-controls-and-evidence` and `notes_evidence`.
5. Why is `setuptools` not in `requirements-dev.lock`?
   **Answer:** It is a build requirement, installed in an isolated build environment during `pip install -e .`.

## Further reading

- Python Packaging User Guide, `pyproject.toml`: <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>
- setuptools (version 75 and newer): <https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html>
- Entry points: <https://packaging.python.org/en/latest/specifications/entry-points/>
