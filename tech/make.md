# Make

## What it is

Make is a command-line tool from the 1970s. You describe **targets** (things you want) in a file called `Makefile`.
Each target lists what it needs first and the commands that produce it. You then type `make <target>` and Make runs
the commands. It also skips work that is already done, by comparing file dates.

People use it today less to compile programs and more as a short, standard name for project commands.

## Why this repository uses it

Every repository in this series answers three questions with the same three commands: `make run`, `make test`,
`make lint`. A reader who has never seen the project can type them without reading anything else. Make also keeps
the commands the same on a laptop and in CI.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` | Defines the targets listed in `make help`. |
| .github/workflows/ci.yml, evidence.yml | Call `make check`, `make audit`, `make scan`, `make up`, `make evidence`, `make verify`, `make report`. |
| .editorconfig | Tells editors to use real tab characters in `Makefile`. |
| .env / .env.example | Make reads `.env` with `-include` and exports it; Docker Compose reads it too. |
| README.md | Every command in the proof table is a `make` target. |

## How it works underneath

1. You run `make test`. Make reads `Makefile` from the current folder.
2. It finds the rule whose target is `test`. It looks at the prerequisites (`$(STAMP)`).
3. For each prerequisite it checks whether there is a rule to build it and whether the file is older than its own
   prerequisites. If so it builds it first. A prerequisite that is not a file (a `.PHONY` name) always runs.
4. It then runs the recipe. **Each recipe line runs in its own new shell** (`/bin/sh`, not your terminal). So a `cd`
   on one line does not affect the next line, and shell variables do not carry over.
5. If a line exits with a status other than 0, Make stops and reports `Error 1` (or similar). Success is status 0.

Make expands `$(NAME)` itself before the shell sees the line. A single `$` in front of a shell variable would have to
be written `$$`; this Makefile does not need that.

## Walkthrough of this repository's use

Make reads the file `Makefile`. A Makefile is a list of **rules**. A rule has a target (a name), optional
prerequisites (what must be ready first) and a recipe (the shell commands that build the target). The recipe lines
start with a tab, not spaces. That is why `.editorconfig` sets `indent_style = tab` for this file.

### The variables at the top

`Makefile`:

```make
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
CLI := $(VENV)/bin/controls-evidence
POSTGRES_USER ?= postgres
```

- `# make up | run | ...` on the first line is only a comment (a line that starts with `#`).
- `PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)` sets `PYTHON` only if it
  is not already set (`?=`). `$(shell ...)` runs a shell command and uses its output. `command -v NAME` prints the
  path of a program if it exists and prints nothing (and fails) if it does not. The `||` means "if the left side
  failed, try the right side". So the line picks Python 3.13, else 3.12, else any `python3`.
- `VENV := .venv` uses `:=`, which evaluates the right side once, right now. `.venv` is the folder of the
  virtual environment (see `venv-and-pip.md`).
- `PY := $(VENV)/bin/python` and `CLI := $(VENV)/bin/controls-evidence` build paths from earlier variables. `$(VENV)` means
  "the value of VENV". Using these paths means no one has to "activate" the environment.
- `STAMP := $(VENV)/.installed` names an empty marker file. Its date says when the install last finished.

`Makefile`:

```make
-include .env
export
```

- `-include .env` reads the file `.env` if it exists. The leading `-` means "do not fail if it is missing". The
  file holds lines like `EVIDENCE_DIR=.`, which Make reads as variable assignments.
- `export` with nothing after it makes every Make variable visible to the programs Make starts. That is how
  `controls-evidence` sees `EVIDENCE_DIR` and the other settings without any extra code.

`Makefile`:

```make
.PHONY: help install env up db queries reset-db run evidence scan verify report serve api-up smoke test test-integration \
```

`.PHONY` lists targets that are **not files**. Without it, a file called `test` or `check` in the folder would make
Make think the target is already built and skip it.

### The targets

`Makefile`:

```make
help: ## list the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

`help` prints every target with its `##` description. The pipeline is explained in `bash.md`. The `@` at the start of
the recipe line tells Make not to echo the command before running it.

`Makefile`:

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

This is the one rule that builds a real file. `$(STAMP): requirements-dev.lock pyproject.toml` says: the marker
`.venv/.installed` depends on the lock file and `pyproject.toml`. Make compares file dates. If either input is newer
than the marker, or the marker is missing, Make runs the recipe. Otherwise it skips it. That makes every other target
fast after the first time.
- Line 1 makes the virtual environment folder.
- Line 2 installs the exact, hash-checked packages from the lock file (`pip install --require-hashes`).
- Line 3 installs this project itself in editable mode without touching dependencies (`--no-deps -e .`).
- `touch $@` creates or refreshes the marker. `$@` is Make's automatic variable for "the target of this rule".

`Makefile`:

```make
install: $(STAMP) ## create .venv from the hash-pinned lock file
```

`install` is just a friendly name for the stamp: it has the stamp as a prerequisite and no recipe of its own.

`Makefile`:

```make
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
```

`env` copies `.env.example` to `.env` the first time, and does nothing afterwards. It has no `##`, so `make help`
hides it: it is a helper, not a command for people.

`Makefile`:

```make
up: env $(STAMP) ## start PostgreSQL and apply sql/001_schema.sql and sql/002_seed.sql
```

`up` means "get ready to run". Here that is the `.env` file and the virtual environment. The lesson template calls
the target `up` for every repository, even when there are no services to start.


`Makefile`:

```make
up: env $(STAMP) ## start PostgreSQL and apply sql/001_schema.sql and sql/002_seed.sql
	docker compose up -d --wait --wait-timeout 900 db
	$(MAKE) --no-print-directory db
```

`up` starts PostgreSQL with Docker Compose and waits until it is healthy (`--wait`, at most 900 seconds), then calls `make db` through
`$(MAKE)`. `$(MAKE) --no-print-directory db` runs Make again for the `db` target, and the flag hides the "entering directory"
message. (See `postgresql.md`.)

`Makefile`:

```make
db: ## apply the schema (roles, tables, append-only audit log, grants) and the seed
	$(PSQL) -v app_rw_password='$(APP_RW_PASSWORD)' -v migrator_password='$(MIGRATOR_PASSWORD)' \
	  -v retention_password='$(RETENTION_PASSWORD)' < sql/001_schema.sql
	$(PSQL) < sql/002_seed.sql
```

`db` feeds the two SQL files to `psql` (see `postgresql-tools.md`). The long first line is continued with a trailing `\`.

`Makefile`:

```make
run: up ## the lesson's scenario: use the service, collect the six artifacts, review access, index, verify
	$(MAKE) --no-print-directory reset-db
	rm -rf state $(EVIDENCE_DIR)
	$(CLI) collect
```

`run` is a clean run: it needs `up`, resets the database, deletes `state` and the evidence folder, and runs the collectors. The
comment line above the target is plain documentation. `$(EVIDENCE_DIR)` is a Make variable from `.env`.

`Makefile`:

```make
evidence: $(STAMP) ## collect every artifact into evidence/ (needs make up)
	$(CLI) collect

scan: env $(STAMP) ## C5 only: scan the locked dependencies and write the dated report (no database needed)
	$(CLI) scan

verify: $(STAMP) ## check every control maps to evidence and every file exists and says what it should
```

`evidence` collects without resetting; `scan` is the dependency scan only and needs no database; `verify` and `report` read the
evidence folder only.

`Makefile`:

```make
serve: $(STAMP) ## run the notes API with gunicorn on localhost (needs make up)
	$(VENV)/bin/gunicorn --bind 127.0.0.1:$(HTTP_PORT) --workers 2 notes_evidence.interfaces.wsgi:app

api-up: ## build the image and start the API container beside the database
	docker compose --profile api up -d --build --wait api

smoke: ## the API container answers /healthz
	curl -fsS http://127.0.0.1:$(HTTP_PORT)/healthz
```

`serve` runs gunicorn on localhost (see `gunicorn.md`); `api-up` builds and starts the API container; `smoke` asks `/healthz` with curl.

`Makefile`:

```make
test: $(STAMP) ## unit tests with coverage (no services needed)
	$(PY) -m pytest tests/unit --cov=notes_evidence --cov-report=term
	$(PY) -m coverage report --include='src/notes_evidence/domain/*,src/notes_evidence/application/*' --fail-under=95

test-integration: $(STAMP) ## adapters and the HTTP app against PostgreSQL (make up first)
	$(PY) -m pytest tests/integration -m integration

test-e2e: $(STAMP) ## the whole scenario into a temporary folder (make up first)
	$(PY) -m pytest tests/e2e -m e2e
```

`test` runs the unit tests only (`tests/unit`) under coverage and requires 95 percent in `domain/` and `application/`.
`test-integration` and `test-e2e` need the database (`make up` first) and select tests by marker with `-m`.

`Makefile`:

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

`lint` runs ruff, the format check, mypy and import-linter. The document checker of the other repositories does not exist here.


`Makefile`:

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

`Makefile`:

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

`Makefile`:

```make
check: lint test ## everything that needs no services
```

`check: lint test` has no recipe. It only lists two prerequisites, so `make check` means "run `lint` and then `test`".
The CI file calls `make check` so that CI and a laptop run the same thing.

`Makefile`:

```make
down: ## stop PostgreSQL and delete its data and the generated state
	docker compose --profile api down -v
```

`Makefile`:

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage htmlcov
```

`down` deletes generated output. `clean` has `down` as a prerequisite and also deletes the virtual environment and
every cache folder. `rm -rf` removes a folder and everything in it without asking.

### The complete file `Makefile`, line by line

`Makefile` lines 1 to 9:

```make
# make up | run | evidence | verify | report | test | test-integration | test-e2e | lint | audit | check | down   (make help lists all)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
CLI := $(VENV)/bin/controls-evidence
POSTGRES_USER ?= postgres
POSTGRES_DB ?= notes
PSQL := docker compose exec -T db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 -q
```

> **In plain words.** A Makefile is a list of **rules**. A rule has a target (a name), the things it needs first, and a recipe (shell commands, each line starting with a tab). `make name` runs the recipe after making sure the needs are ready. `$(NAME)` means "the value of the Make variable NAME"; `$@` means "this rule's target".

- Sets the Make variable `PYTHON` only if it is not already set to `$(shell command -v python3.13 || command -v python3.12 || command -v python3)`. The `$(shell ...)` part runs a shell command and uses its output.
- Sets the Make variable `VENV` once, right now to `.venv`.
- Sets the Make variable `PY` once, right now to `$(VENV)/bin/python`.
- Sets the Make variable `STAMP` once, right now to `$(VENV)/.installed`.
- Sets the Make variable `CLI` once, right now to `$(VENV)/bin/controls-evidence`.
- Sets the Make variable `POSTGRES_USER` only if it is not already set to `postgres`.
- Sets the Make variable `POSTGRES_DB` only if it is not already set to `notes`.
- Sets the Make variable `PSQL` once, right now to `docker compose exec -T db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 -q`.

`Makefile` lines 11 to 12:

```make
-include .env
export
```

- `-include .env` reads that file if it exists; the leading `-` means "do not fail if it is missing". Its `NAME=value` lines become Make variables.
- `export` on its own passes every Make variable to the programs Make starts, so they see the settings from `.env`.

`Makefile` lines 14 to 15:

```make
.PHONY: help install env up db queries reset-db run evidence scan verify report serve api-up smoke test test-integration \
        test-e2e lint format audit check docker-build down clean
```

- `.PHONY` lists names that are commands, not files, so Make always runs them even if a file of that name exists.

`Makefile` lines 17 to 18:

```make
help: ## list the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

- Defines the target `help`. It has no prerequisites. Its help text is "list the targets".
- Recipe line: runs grep, which searches text with `-hE` (hide file names, extended regex), `^[a-z-]+:.*##`, `$(MAKEFILE_LIST)`; then its output is passed to a command that runs sed, the stream editor with `-E` (extended regular expressions), `s/:.*## /\t/`; then its output is passed to a command that runs sort, which orders lines. (the leading `@` stops Make from printing the command first)

`Makefile` lines 20 to 24:

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

- Defines the target `$(STAMP)`. It needs `requirements-dev.lock pyproject.toml` to be ready first.
- Recipe line: runs `venv` with `$(VENV)` (run through Python with `-m`).
- Recipe line: runs pip, the package installer, subcommand `install` with `-q` (quiet: print less), `--require-hashes` (refuse any package without a pinned hash), `-r requirements-dev.lock` (read the list from the named file).
- Recipe line: runs pip, the package installer, subcommand `install` with `-q` (quiet: print less), `--no-deps` (do not install or resolve dependencies), `-e` (editable install (link to the source) / extended regex / stop on error, by program), `.`.
- Recipe line: runs touch, which creates an empty file or refreshes its date with `$@`.

`Makefile` lines 26 to 26:

```make
install: $(STAMP) ## create .venv from the hash-pinned lock file
```

- Defines the target `install`. It needs `$(STAMP)` to be ready first. Its help text is "create .venv from the hash-pinned lock file".

`Makefile` lines 28 to 29:

```make
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
```

- Defines the target `env`. It has no prerequisites.
- Recipe line: tests a condition: `-f .env`; if that fails, it runs cp, which copies files with `.env.example`, `.env`; then it prints `created .env from .env.example`. (the leading `@` stops Make from printing the command first)

`Makefile` lines 31 to 33:

```make
up: env $(STAMP) ## start PostgreSQL and apply sql/001_schema.sql and sql/002_seed.sql
	docker compose up -d --wait --wait-timeout 900 db
	$(MAKE) --no-print-directory db
```

- Defines the target `up`. It needs `env $(STAMP)` to be ready first. Its help text is "start PostgreSQL and apply sql/001_schema.sql and sql/002_seed.sql".
- Recipe line: runs Docker Compose with the subcommand `up` with `-d` (database name / detach, by program), `--wait` (wait until the service is healthy), `--wait-timeout 900` (give up waiting after this many seconds), `db`.
- Recipe line: runs `$(MAKE)` with `--no-print-directory` (do not print 'entering directory' lines), `db`.

`Makefile` lines 35 to 38:

```make
db: ## apply the schema (roles, tables, append-only audit log, grants) and the seed
	$(PSQL) -v app_rw_password='$(APP_RW_PASSWORD)' -v migrator_password='$(MIGRATOR_PASSWORD)' \
	  -v retention_password='$(RETENTION_PASSWORD)' < sql/001_schema.sql
	$(PSQL) < sql/002_seed.sql
```

- Defines the target `db`. It has no prerequisites. Its help text is "apply the schema (roles, tables, append-only audit log, grants) and the seed".
- Recipe line: runs `$(PSQL)` with `-v app_rw_password=$(APP_RW_PASSWORD)` (verbose / set a variable, by program), `-v migrator_password=$(MIGRATOR_PASSWORD)` (verbose / set a variable, by program), `-v retention_password=$(RETENTION_PASSWORD)` (verbose / set a variable, by program), reading its input from `sql/001_schema.sql`.
- Recipe line: runs `$(PSQL)`, reading its input from `sql/002_seed.sql`.

`Makefile` lines 40 to 41:

```make
queries: ## run sql/003_queries.sql
	docker compose exec -T db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql
```

- Defines the target `queries`. It has no prerequisites. Its help text is "run sql/003_queries.sql".
- Recipe line: runs Docker Compose with the subcommand `exec` with `-T` (no terminal), `db`, `psql`, `-U $(POSTGRES_USER)` (log in as this database user), `-d $(POSTGRES_DB)` (database name / detach, by program), `-v ON_ERROR_STOP=1` (verbose / set a variable, by program), reading its input from `sql/003_queries.sql`.

`Makefile` lines 43 to 45:

```make
reset-db: ## drop the public schema and rebuild it from the SQL scripts
	$(PSQL) < sql/reset.sql
	$(MAKE) --no-print-directory db
```

- Defines the target `reset-db`. It has no prerequisites. Its help text is "drop the public schema and rebuild it from the SQL scripts".
- Recipe line: runs `$(PSQL)`, reading its input from `sql/reset.sql`.
- Recipe line: runs `$(MAKE)` with `--no-print-directory` (do not print 'entering directory' lines), `db`.

`Makefile` lines 47 to 51:

```make
# A clean run: empty database, the cloud account back as the fixture has it, the pack rebuilt from scratch.
run: up ## the lesson's scenario: use the service, collect the six artifacts, review access, index, verify
	$(MAKE) --no-print-directory reset-db
	rm -rf state $(EVIDENCE_DIR)
	$(CLI) collect
```

- Defines the target `run`. It needs `up` to be ready first. Its help text is "the lesson's scenario: use the service, collect the six artifacts, review access, index, verify".
- Recipe line: runs `$(MAKE)` with `--no-print-directory` (do not print 'entering directory' lines), `reset-db`.
- Recipe line: runs rm, which deletes files with `-rf` (delete folders and everything inside without asking), `state`, `$(EVIDENCE_DIR)`.
- Recipe line: runs the project's command-line program with the subcommand `collect`.

`Makefile` lines 53 to 54:

```make
evidence: $(STAMP) ## collect every artifact into evidence/ (needs make up)
	$(CLI) collect
```

- Defines the target `evidence`. It needs `$(STAMP)` to be ready first. Its help text is "collect every artifact into evidence/ (needs make up)".
- Recipe line: runs the project's command-line program with the subcommand `collect`.

`Makefile` lines 56 to 57:

```make
scan: env $(STAMP) ## C5 only: scan the locked dependencies and write the dated report (no database needed)
	$(CLI) scan
```

- Defines the target `scan`. It needs `env $(STAMP)` to be ready first. Its help text is "C5 only: scan the locked dependencies and write the dated report (no database needed)".
- Recipe line: runs the project's command-line program with the subcommand `scan`.

`Makefile` lines 59 to 60:

```make
verify: $(STAMP) ## check every control maps to evidence and every file exists and says what it should
	$(CLI) verify
```

- Defines the target `verify`. It needs `$(STAMP)` to be ready first. Its help text is "check every control maps to evidence and every file exists and says what it should".
- Recipe line: runs the project's command-line program with the subcommand `verify`.

`Makefile` lines 62 to 63:

```make
report: $(STAMP) ## write build/report.md: controls, evidence, findings, framework overlap
	$(CLI) report
```

- Defines the target `report`. It needs `$(STAMP)` to be ready first. Its help text is "write build/report.md: controls, evidence, findings, framework overlap".
- Recipe line: runs the project's command-line program with the subcommand `report`.

`Makefile` lines 65 to 66:

```make
serve: $(STAMP) ## run the notes API with gunicorn on localhost (needs make up)
	$(VENV)/bin/gunicorn --bind 127.0.0.1:$(HTTP_PORT) --workers 2 notes_evidence.interfaces.wsgi:app
```

- Defines the target `serve`. It needs `$(STAMP)` to be ready first. Its help text is "run the notes API with gunicorn on localhost (needs make up)".
- Recipe line: runs gunicorn, the production web server with `--bind 127.0.0.1:$(HTTP_PORT)` (address and port to listen on), `--workers 2` (number of worker processes), `notes_evidence.interfaces.wsgi:app`.

`Makefile` lines 68 to 69:

```make
api-up: ## build the image and start the API container beside the database
	docker compose --profile api up -d --build --wait api
```

- Defines the target `api-up`. It has no prerequisites. Its help text is "build the image and start the API container beside the database".
- Recipe line: runs Docker Compose with the subcommand `--profile` with `api`, `up`, `-d` (database name / detach, by program), `--build` (build the image first), `--wait` (wait until the service is healthy), `api`.

`Makefile` lines 71 to 72:

```make
smoke: ## the API container answers /healthz
	curl -fsS http://127.0.0.1:$(HTTP_PORT)/healthz
```

- Defines the target `smoke`. It has no prerequisites. Its help text is "the API container answers /healthz".
- Recipe line: runs curl, a command-line HTTP client with `-fsS` (fail on HTTP errors, silent, but show errors), `http://127.0.0.1:$(HTTP_PORT)/healthz`.

`Makefile` lines 74 to 76:

```make
test: $(STAMP) ## unit tests with coverage (no services needed)
	$(PY) -m pytest tests/unit --cov=notes_evidence --cov-report=term
	$(PY) -m coverage report --include='src/notes_evidence/domain/*,src/notes_evidence/application/*' --fail-under=95
```

- Defines the target `test`. It needs `$(STAMP)` to be ready first. Its help text is "unit tests with coverage (no services needed)".
- Recipe line: runs pytest, the test runner with `tests/unit`, `--cov=notes_evidence` (measure coverage of this package), `--cov-report=term` (how to print the coverage report) (run through the project's Python with `-m`).
- Recipe line: runs coverage.py, which measures which lines the tests ran with `report`, `--include=src/notes_evidence/domain/*,src/notes_evidence/application/*` (only these files), `--fail-under=95` (exit with an error if the total is lower than this percent) (run through the project's Python with `-m`).

`Makefile` lines 78 to 79:

```make
test-integration: $(STAMP) ## adapters and the HTTP app against PostgreSQL (make up first)
	$(PY) -m pytest tests/integration -m integration
```

- Defines the target `test-integration`. It needs `$(STAMP)` to be ready first. Its help text is "adapters and the HTTP app against PostgreSQL (make up first)".
- Recipe line: runs pytest, the test runner with `tests/integration`, `-m integration` (run a module (or select tests by marker for pytest)) (run through the project's Python with `-m`).

`Makefile` lines 81 to 82:

```make
test-e2e: $(STAMP) ## the whole scenario into a temporary folder (make up first)
	$(PY) -m pytest tests/e2e -m e2e
```

- Defines the target `test-e2e`. It needs `$(STAMP)` to be ready first. Its help text is "the whole scenario into a temporary folder (make up first)".
- Recipe line: runs pytest, the test runner with `tests/e2e`, `-m e2e` (run a module (or select tests by marker for pytest)) (run through the project's Python with `-m`).

`Makefile` lines 84 to 88:

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

- Defines the target `lint`. It needs `$(STAMP)` to be ready first. Its help text is "ruff check, ruff format check, mypy, import-linter".
- Recipe line: runs ruff, the linter and formatter with `check`, `.`.
- Recipe line: runs ruff, the linter and formatter with `format`, `--check` (report only; change nothing), `.`.
- Recipe line: runs mypy, the type checker.
- Recipe line: runs import-linter, the architecture rule checker.

`Makefile` lines 90 to 92:

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

- Defines the target `format`. It needs `$(STAMP)` to be ready first. Its help text is "apply ruff's formatting and safe fixes".
- Recipe line: runs ruff, the linter and formatter with `check`, `--fix` (apply the fixes that are safe), `.`.
- Recipe line: runs ruff, the linter and formatter with `format`, `.`.

`Makefile` lines 94 to 95:

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- Defines the target `audit`. It needs `$(STAMP)` to be ready first. Its help text is "check the locked dependencies for known vulnerabilities".
- Recipe line: runs pip-audit, the vulnerability scanner with `--no-deps` (do not install or resolve dependencies), `--disable-pip` (do not use pip to resolve), `-r requirements-dev.lock` (read the list from the named file).

`Makefile` lines 97 to 97:

```make
check: lint test ## everything that needs no services
```

- Defines the target `check`. It needs `lint test` to be ready first. Its help text is "everything that needs no services".

`Makefile` lines 99 to 100:

```make
docker-build: ## build the API image
	docker build -t compliance-controls-and-evidence:dev .
```

- Defines the target `docker-build`. It has no prerequisites. Its help text is "build the API image".
- Recipe line: runs Docker with the subcommand `build` with `-t compliance-controls-and-evidence:dev` (tag (name) the image / tuples only, by program), `.`.

`Makefile` lines 102 to 104:

```make
down: ## stop PostgreSQL and delete its data and the generated state
	docker compose --profile api down -v
	rm -rf state build
```

- Defines the target `down`. It has no prerequisites. Its help text is "stop PostgreSQL and delete its data and the generated state".
- Recipe line: runs Docker Compose with the subcommand `--profile` with `api`, `down`, `-v` (verbose / set a variable, by program).
- Recipe line: runs rm, which deletes files with `-rf` (delete folders and everything inside without asking), `state`, `build`.

`Makefile` lines 106 to 107:

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage htmlcov
```

- Defines the target `clean`. It needs `down` to be ready first.
- Recipe line: runs rm, which deletes files with `-rf` (delete folders and everything inside without asking), `$(VENV)`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.import_linter_cache`, `.coverage`, `htmlcov`.

## Try it yourself

From the repository root:

```bash
make help
```
Expect one line per documented target: `api-up`, `audit`, `check`, `db`, `docker-build`, `down`, `evidence`, `format`, `help`, `install`, `lint`, `queries`, `report`, `reset-db`, `run`, `scan`, `serve`, `smoke`, `test`, `test-e2e`, `test-integration`, `up`, `verify`, each followed by a tab and its description.

```bash
make -n test
```
`-n` is a dry run: Make prints the commands it would run and runs none. Expect two lines: the `pytest` line and the
`coverage report` line, with `.venv/bin/python` at the start.

```bash
make -n down
```
Expect `docker compose --profile api down -v` and then `rm -rf state build`.

```bash
ls -l .venv/.installed
```
Expect a file of size 0 (after a first `make up`). Run `touch pyproject.toml`, then `make -n up`: Make now shows the
install commands again, because `pyproject.toml` is newer than the marker.

```bash
make run
```
Needs Docker (see `docker.md`). Expect the six collectors' lines (`== exercise: ...` to `== index: wrote INDEX.md`) and `OK: 9 files checked, 0 errors, 0 warnings`.

## Mistakes people make

- **Spaces instead of a tab** in a recipe. Make answers `missing separator`. The `.editorconfig` entry for
  `Makefile` prevents it in most editors.
- **Expecting `cd` to carry over** between recipe lines. It does not; each line has its own shell.
- **Forgetting `.PHONY`** for a target that is not a file. This Makefile lists every command target there.
- **Typing `$VAR` instead of `$(VAR)`** for a Make variable.
- **Running `make` with no target.** It builds the first target in the file, which here is `help`, a harmless choice
  on purpose.

## Check yourself

1. Why does `make test` not reinstall the packages every time?
   **Answer:** The `.venv/.installed` marker is a prerequisite. Make only reruns the install recipe when the lock file or `pyproject.toml` is newer than the marker.
2. What does `export` on its own line do?
   **Answer:** It passes every Make variable, including those read from `.env`, to the programs Make starts.
3. What would break if `.PHONY` did not list `test` and someone created a file named `test`?
   **Answer:** Make would see an existing file with no newer prerequisites and say `test` is up to date, skipping the tests.
4. What does the `@` at the start of a recipe line do?
   **Answer:** It stops Make from printing the command before running it.
5. Why is `check` written with no recipe?
   **Answer:** It only names `lint` and `test` as prerequisites, so running it runs both.

## Further reading

- GNU Make manual: <https://www.gnu.org/software/make/manual/make.html> (this repository is developed with the GNU-compatible Make that ships with macOS and with Ubuntu).
