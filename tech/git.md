# Git and .gitignore

## What it is

**Git** is a tool that records the history of a folder as a chain of **commits**. A commit is a saved snapshot with a
message, an author and a date. Git lets you see what changed, go back, and work in parallel. A file called
`.gitignore` lists names and patterns of files that Git must not track (generated files, caches, secrets).

## Why this repository uses it

The task asks for meaningful commits and a clean working tree: the history shows the work in steps (scaffolding,
documents, code, tests, CI, docs), and `git status` shows nothing left over. `.gitignore` keeps generated output out
of that history.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| .git/ | The history database (a folder Git manages). |
| .gitignore | Patterns of files to leave untracked. |
| `CHANGELOG.md` | Human summary of what each version added. |
| .github/workflows/ci.yml | Runs on pushes and pull requests. |

## How it works underneath

- Git stores each file's content under a hash of its bytes. A commit points to a tree of those hashes and to its
  parent commit. So history is a chain, and any change to the past changes every later hash.
- Three places matter: the **working tree** (your files), the **index** or staging area (what the next commit will
  contain, filled by `git add`), and the **repository** (commits).
- `git status` compares the three. A file that matches a `.gitignore` pattern is never listed as untracked.
- Git does not change files outside the repository, and it does not push anywhere unless you run `git push`.

## Walkthrough of this repository's use

`.gitignore`:

```text
.venv/
__pycache__/
*.pyc
*.egg-info/
build/
dist/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.import_linter_cache/
.coverage
htmlcov/
.env
.DS_Store
.omc/
state/
```

Line by line:
- `.venv/`: the virtual environment, rebuilt from the lock file. A trailing `/` matches folders only.
- `__pycache__/` and `*.pyc`: compiled Python caches. `*` matches any characters.
- `*.egg-info/`: metadata folders created by an editable install.
- `build/` and `dist/`: generated output (the report, built packages).
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.import_linter_cache/`: tool caches.
- `.coverage` and `htmlcov/`: coverage data and its web report.
- `.env`: the local settings copy.
- `.DS_Store`: a macOS folder-view file.
- `.omc/`: a local tool folder.

The commits in this repository follow a convention: a type, a colon and a short summary (`chore:`, `docs:`,
`feat:`, `test:`, `ci:`, `fix:`). Each commit adds one coherent piece.

This repository also ignores `state/` and `evidence/` is **committed** on purpose: the sample pack is part of the lesson. `.dockerignore` (see `docker.md`) is a separate file with the same idea for the Docker build context.

## Try it yourself

```bash
git log --oneline
```
Lists the commits, newest first (the scaffold commit is last).

```bash
git status --short
```
Prints nothing when the tree is clean.

```bash
git check-ignore -v .venv build .env
```
Shows which `.gitignore` line ignores each of those paths.

```bash
git show --stat HEAD | head -12
```
Shows the newest commit's message and the files it touched.

```bash
git ls-files | wc -l
```
Counts the files Git tracks.

## Mistakes people make

- **Committing generated files** (caches, `.venv`). `.gitignore` prevents it, but only for files not yet tracked.
- **Committing secrets.** Even if deleted later, they stay in history.
- **Vague commit messages** such as "fix". Here each message says what and why.
- **Using `git add .` blindly**, which stages whatever is there. Check `git status` first.
- **Thinking a commit is a backup elsewhere.** Until pushed, it exists only on this machine.

## Check yourself

1. What is a commit?
   **Answer:** A saved snapshot of the tracked files with a message, author and date, linked to its parent.
2. What does the `.gitignore` line `build/` do?
   **Answer:** It stops Git from tracking a folder named `build`.
3. Does a `.gitignore` entry remove a file already tracked?
   **Answer:** No; it only affects untracked files.
4. What does an empty `git status --short` mean?
   **Answer:** No changes and no untracked files: a clean tree.
5. Why are caches ignored?
   **Answer:** They are generated, differ per machine, and would add noise to every diff.

## Further reading

- Pro Git book: <https://git-scm.com/book/en/v2>
- gitignore pattern format: <https://git-scm.com/docs/gitignore>
- Git reference: <https://git-scm.com/docs>
