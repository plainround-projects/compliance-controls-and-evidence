# import-linter

## What it is

In Python, `import` lets one file use another. **import-linter** reads all the imports in a package, draws the map
of who imports whom, and checks the map against **contracts** you write in `pyproject.toml`. A broken contract fails
the check, like a failing test, but for the shape of the code.

## Why this repository uses it

`ARCHITECTURE.md` says the code has four layers and that the inner layers must not know about the outer ones:
the rules in `domain/` must not read files or print. Words in a document can be forgotten; a contract in the
build cannot.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` `[tool.importlinter]` | The root package. |
| `pyproject.toml` `[[tool.importlinter.contracts]]` (two) | A layers contract and a forbidden-imports contract. |
| `Makefile` `lint` | Runs `.venv/bin/lint-imports`. |
| `.import_linter_cache/` | A cache folder (git-ignored). |

## How it works underneath

import-linter uses a library called `grimp` to scan the source files (without running them) and build a **graph**:
a dot per module and an arrow wherever one module imports another. A **layers** contract says an upper layer may
import a lower one, never the reverse. A **forbidden** contract lists modules that must not be reachable from
other modules, directly or through a chain of imports. The tool searches the graph and reports any path that breaks
a contract.

## Walkthrough of this repository's use

`pyproject.toml`:

```toml
[tool.importlinter]
root_package = "notes_evidence"
```

`root_package` names the package to analyze (only imports inside it count).

`pyproject.toml`:

```toml
name = "Layers: interfaces -> infrastructure -> application -> domain, never upward"
type = "layers"
layers = [
    "notes_evidence.interfaces",
    "notes_evidence.infrastructure",
    "notes_evidence.application",
    "notes_evidence.domain",
]
```

- `type = "layers"`: modules are listed from highest to lowest.
- The list reads top to bottom: `interfaces` may import `infrastructure`, `application` and `domain`;
  `infrastructure` may import `application` and `domain`; `application` may import `domain`; `domain` imports none
  of the others. Any upward import breaks the contract.

`pyproject.toml`:

```toml
name = "Domain and application know nothing about Flask or PostgreSQL"
type = "forbidden"
source_modules = ["notes_evidence.domain", "notes_evidence.application"]
forbidden_modules = ["notes_evidence.infrastructure", "notes_evidence.interfaces", "flask", "psycopg"]
```

- `type = "forbidden"`: nothing in `source_modules` may import (even through other modules) anything in
  `forbidden_modules`. So the rules and use cases can never depend on the file system code or the command line.
  The contract's name says they use only the standard library and each other.

The result, as it prints:

```text
Layers: interfaces -> infrastructure -> application -> domain, never upward KEPT
Domain and application use only the standard library and each other KEPT
Contracts: 2 kept, 0 broken.
```

This repository's second contract is stricter than the usual one:

`pyproject.toml`:

```toml
include_external_packages = true
```

`pyproject.toml`:

```toml
name = "Domain and application know nothing about Flask or PostgreSQL"
type = "forbidden"
source_modules = ["notes_evidence.domain", "notes_evidence.application"]
forbidden_modules = ["notes_evidence.infrastructure", "notes_evidence.interfaces", "flask", "psycopg"]
```

`include_external_packages = true` lets the contracts mention installed packages. The `forbidden` contract here bans `flask` and
`psycopg` as well as our own `infrastructure` and `interfaces`: the rules and use cases cannot import the web framework or the
database driver, directly or through another module. (The name of the contract says so; the text above that explains the
generic contract applies the same way.)

## Try it yourself

```bash
.venv/bin/lint-imports --no-logo
```
Prints `Analyzed 68 files, 236 dependencies.` and two `KEPT` lines.

```bash
.venv/bin/lint-imports --show-timings --no-logo | tail -5
```
Adds how long building the graph and each check took.

To see a contract break, add the line `import notes_evidence.infrastructure.filesystem` to the top of
`src/notes_evidence/domain/text.py`, then run:

```bash
.venv/bin/lint-imports --no-logo | tail -12
```
Both contracts report `BROKEN`, with the import chain. Undo the edit with `git checkout src/notes_evidence/domain/text.py`.

```bash
.venv/bin/lint-imports --help | head -12
```
Lists the options of version 2.15.

## Mistakes people make

- **Fixing a broken contract by editing the contract.** Move the code or invert the dependency instead.
- **Forgetting that indirect imports count.** `A -> B -> C` breaks a rule between `A` and `C`.
- **Leaving out `root_package`**, so nothing is analyzed.
- **Thinking it checks anything but imports.** It does not see function calls through objects passed in; the repository
  uses small interfaces (Protocols, see `python.md`) for that.

## Check yourself

1. What is a `layers` contract?
   **Answer:** A list of modules from highest to lowest; higher ones may import lower ones, never the reverse.
2. Why is `domain` the lowest layer?
   **Answer:** It holds the rules and imports nothing else of ours, so it can be tested alone.
3. What does the `forbidden` contract add?
   **Answer:** It bans domain and application from importing infrastructure or interfaces, directly or indirectly.
4. Does import-linter run the code?
   **Answer:** No, it reads imports from the source files.
5. What does `KEPT` mean?
   **Answer:** The contract holds.

## Further reading

- import-linter 2.15: <https://import-linter.readthedocs.io/en/v2.15/>
- Contract types: <https://import-linter.readthedocs.io/en/v2.15/contract_types/>
- grimp: <https://grimp.readthedocs.io/>
