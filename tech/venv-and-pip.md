# venv and pip

## What it is

A **virtual environment** (venv) is a folder that holds its own copy of the Python program and its own set of
installed packages. **pip** is the standard tool that downloads and installs Python packages into it. Together they
let each project have exactly the packages it needs without touching the rest of the computer.

## Why this repository uses it

The project must give the same results on any machine and in CI. A venv built from a hash-pinned lock file
(`hash-pinned-lock-files.md`) guarantees the same tools, with the same versions, run the same checks.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` (`$(STAMP)` rule) | Creates `.venv` and runs pip twice. |
| `.venv/` | The environment: `bin/python`, `bin/pip`, `bin/ruff`, `bin/controls-evidence`, and `lib/python3.*/site-packages`. |
| `requirements-dev.lock`, `requirements.lock` | The exact packages pip installs. |
| `pyproject.toml` | Tells pip how to install this project (`[project]`, `[project.scripts]`). |
| .gitignore | Keeps `.venv/` out of git. |

## How it works underneath

- `python -m venv .venv` creates a folder with a `bin/python` that is a link to the real Python, plus an empty
  `lib/python3.x/site-packages/` folder. Python looks in that folder first for imports when started through
  `.venv/bin/python`.
- `pip install` downloads a **wheel** (a zip file of ready-made code) from the Python Package Index (PyPI), checks
  it, and unpacks it into `site-packages`. If a package has a command (like `ruff`), pip writes a small script into
  `.venv/bin/`.
- **Editable install** (`-e .`): instead of copying this project into `site-packages`, pip adds a pointer to the `src/`
  folder. Edits to the code take effect at once, and the command `controls-evidence` appears in `.venv/bin/`.
- You never need to "activate" the venv. Calling `.venv/bin/pytest` uses that environment's Python directly.

## Walkthrough of this repository's use

`Makefile`:

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

- `$(PYTHON) -m venv $(VENV)`: runs the module `venv` with the Python found earlier; creates `.venv`.
- `pip install -q --require-hashes -r requirements-dev.lock`:
  - `-q` is quiet.
  - `--require-hashes` makes pip refuse any requirement that does not have a `--hash=sha256:...` entry and an
    exact `==` version, and refuse a download whose hash does not match.
  - `-r FILE` reads the list of requirements from the file.
- `pip install -q --no-deps -e .`:
  - `.` is this project, read through `pyproject.toml`.
  - `-e` is editable mode.
  - `--no-deps` stops pip from resolving dependencies a second time. The lock file already installed them, so
    nothing unpinned can sneak in.
- `touch $@` records success.

`pyproject.toml`:

```toml
[project.scripts]
controls-evidence = "notes_evidence.interfaces.cli:main"
```

This is what creates the command. After the editable install, pip writes `.venv/bin/controls-evidence`, a tiny script that
imports `notes_evidence.interfaces.cli` and calls `main`. See `setuptools.md`.

`pyproject.toml`:

```toml
requires-python = ">=3.12"
```

pip refuses to install the project on a Python older than 3.12.

## Try it yourself

```bash
make up
.venv/bin/python --version
```
Prints the Python version the venv uses (for example `Python 3.13.12`).

```bash
.venv/bin/pip --version
```
Prints the pip version and the path inside `.venv` (`pip 26.2.2 from .../.venv/lib/python3.13/site-packages/pip`).

```bash
.venv/bin/pip list | head -12
```
Lists the installed packages and versions: `coverage`, `import-linter`, `mypy`, `pytest`, `ruff`, and this project.

```bash
.venv/bin/pip show compliance-controls-and-evidence
```
Shows the project's name, version `0.1.0`, and `Location` (the `.venv` site-packages folder).

```bash
.venv/bin/python -c "import notes_evidence, sys; print(notes_evidence.__file__)"
```
Prints a path under `src/notes_evidence/`: the editable install points at the source tree.

## Mistakes people make

- **Installing packages with the system Python**, which changes the whole machine. The Makefile always uses
  `.venv/bin/...`.
- **Forgetting to rebuild** after changing the lock file. The stamp rule handles it.
- **Running `pip install package`** by hand. The package is not in the lock file, so the next person will not have
  it. Add it to `pyproject.toml` and regenerate the lock file instead.
- **Committing `.venv/`.** It is machine-specific; `.gitignore` lists it.

## Check yourself

1. What does `-e` do in `pip install -e .`?
   **Answer:** It installs the project in editable mode: a pointer to `src/` instead of a copy, so code edits take effect at once.
2. Why `--no-deps` on the second pip command?
   **Answer:** All dependencies were already installed from the lock file; this command should add only the project, not resolve anything new.
3. How do you run the project's tools without activating the venv?
   **Answer:** Call them by path, for example `.venv/bin/pytest`.
4. What does `--require-hashes` protect against?
   **Answer:** A package that was changed or swapped on the index: the download is rejected if its hash is not the one in the lock file.
5. Where do installed packages live?
   **Answer:** In `.venv/lib/python3.x/site-packages/`.

## Further reading

- Python `venv` (3.12): <https://docs.python.org/3.12/library/venv.html>
- pip 26.2 user guide: <https://pip.pypa.io/en/stable/user_guide/>; hash-checking mode: <https://pip.pypa.io/en/stable/topics/secure-installs/>
- Editable installs: <https://setuptools.pypa.io/en/latest/userguide/development_mode.html>
