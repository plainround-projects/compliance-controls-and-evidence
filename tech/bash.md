# Bash and the shell commands in the Makefile

## What it is

A **shell** is a program that reads a line you type, finds the program you named, and runs it. Bash is the most
common shell. The shell also has its own small language: `||` and `&&` to combine commands, `|` to feed one
command's output to the next, `$(...)` to use a command's output, quotes to group words, and an **exit status**
(0 means success, anything else means failure).

This repository has no `.sh` files. The shell appears in two places: inside the Makefile recipes and in the
`run:` lines of the CI file. Make runs recipe lines with `/bin/sh`, which on macOS and Ubuntu understands the simple
syntax used here.

## Why this repository uses it

The shell is the glue. A Makefile line such as `rm -rf state build`, `curl -fsS ...` or `[ -f .env ] || cp ...` is a shell command, and
the Compose health check runs through the shell of the container (`CMD-SHELL`). The repository has no `.sh` file; it keeps each
command tiny and standard so a reader can understand it in a minute.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` line 2 (`PYTHON ?= $(shell ...)`) | `command -v` and `||` to pick a Python version. |
| `Makefile` `help` | `grep`, `sed` and `sort` joined by pipes. |
| `Makefile` `env` | A test (`[ -f .env ]`), `||`, a group `{ ...; }`, `cp`, `echo`. |
| `Makefile` `smoke` | `curl -fsS`. |
| `Makefile` `db`, `queries` | Input redirection with `<` into `psql`. |
| `docker-compose.yml` | `CMD-SHELL` runs `pg_isready` through a shell, with escaped `$$` variables. |
| .github/workflows/*.yml | Each `run:` is a shell line. |

## How it works underneath

- When the shell runs `grep -hE 'x' file`, it splits the line into words, finds a program called `grep` on the
  `PATH` (a list of folders), and starts it with the other words as arguments. The program returns an **exit
  status**.
- Standard streams: every program has **stdin** (input), **stdout** (normal output) and **stderr** (errors).
  A pipe `a | b` connects `a`'s stdout to `b`'s stdin. `>` sends stdout to a file.
- `A || B` runs `B` only if `A` failed (status not 0). `A && B` runs `B` only if `A` succeeded.
- Quotes: single quotes `'...'` keep the text exactly; double quotes `"..."` allow `$variables` inside.
- `[ -f .env ]` is the `test` program written with brackets. `-f` asks "is this an existing regular file?". It
  returns 0 for yes and 1 for no.

## Walkthrough of this repository's use

`Makefile`:

```make
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
```

`$(shell ...)` is Make syntax, but what it runs is shell. `command -v python3.13` prints a path and returns 0 if
Python 3.13 is installed, otherwise it prints nothing and returns 1. Then `||` tries `python3.12`, then `python3`. The
first one that exists wins. If none exists, `PYTHON` is empty and the next `make up` fails with a clear error.

`Makefile`:

```make
help: ## list the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

This is a three-stage pipeline:
1. `grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST)` prints only lines that look like `target: ... ## text`.
   `-E` turns on extended regular expressions (so `+` works). `-h` hides the file name that `grep` would add when it
   reads more than one file. `$(MAKEFILE_LIST)` is Make's list of files it read: the `Makefile` and, once it exists,
   `.env`. Without `-h`, the output would start with `Makefile:` and the next step would cut the target name away.
   The pattern `^[a-z-]+:` means "start of line, lower-case letters or dashes, then a colon".
2. `sed -E 's/:.*## /\t/'` replaces everything from the first `:` up to `## ` with a tab, leaving `target<TAB>text`.
   `sed` is the stream editor; `s/old/new/` is substitute.
3. `sort` puts the lines in alphabetical order.

`Makefile`:

```make
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
```

`[ -f .env ]` is true when `.env` exists. When it is true, `||` skips everything after it. When it is false, the
group `{ cp .env.example .env; echo "..."; }` runs: `cp` copies the file and `echo` prints the message. The braces
group the two commands so the `||` covers both. The `;` before `}` is required in this form. The leading `@` is Make's
"do not print this line".

`Makefile`:

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

`touch $@` creates an empty file, or updates its date if it exists. Make replaces `$@` with the target name,
`.venv/.installed`, before the shell sees the line.

`Makefile`:

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage htmlcov
```

`rm -rf` removes files or folders. `-r` means recursive (go into folders), `-f` means "no error if it does not exist
and do not ask". It is safe here because every path is a fixed name inside the repository, not a variable that could
be empty.

`.github/workflows/ci.yml`:

```yaml
      - run: make check
      - run: make audit
      - name: C5 evidence — the dependency scan of this build, with this run's id
```

In CI, a `run:` value is handed to a shell. Each is a plain command, so the CI file never needs shell tricks.

### Shell in the database and API commands

`Makefile`:

```make
db: ## apply the schema (roles, tables, append-only audit log, grants) and the seed
	$(PSQL) -v app_rw_password='$(APP_RW_PASSWORD)' -v migrator_password='$(MIGRATOR_PASSWORD)' \
	  -v retention_password='$(RETENTION_PASSWORD)' < sql/001_schema.sql
	$(PSQL) < sql/002_seed.sql
```

`< sql/001_schema.sql` is **input redirection**: the file's contents become the program's standard input. The trailing `\` continues
the command on the next line. `'$(APP_RW_PASSWORD)'` is Make replacing the variable, inside single quotes the shell keeps as one
word.

`Makefile`:

```make
smoke: ## the API container answers /healthz
	curl -fsS http://127.0.0.1:$(HTTP_PORT)/healthz
```

`curl -fsS URL`: `-f` fail on an HTTP error, `-s` silent, `-S` still show errors.

`docker-compose.yml`:

```yaml
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
```

`CMD-SHELL` runs the string through the container's shell. `$${POSTGRES_USER}` is written with two dollar signs so **Compose** does
not substitute it; the shell inside the container expands it from its own environment.

## Try it yourself

```bash
command -v python3.13 || command -v python3
```
Prints the path of the first Python found.

```bash
[ -f .env ] && echo "have .env" || echo "no .env"
```
Prints `have .env` after `make up`, `no .env` before.

```bash
grep -hE '^[a-z-]+:.*## ' Makefile | sed -E 's/:.*## /\t/' | sort | head -3
```
Prints the first three targets with their descriptions: the `help` pipeline run by hand.

```bash
make -n clean
```
Prints the `rm -rf` commands without running them.

```bash
true; echo $?; false; echo $?
```
Prints `0` then `1`: the exit status of `true` and `false`.

## Mistakes people make

- **Forgetting quotes** around a value with spaces, so the shell splits it into several arguments.
- **Using `rm -rf $DIR` with an empty variable**, which can delete the wrong folder. This repository only uses
  fixed names.
- **Assuming `cd` lasts.** In a Makefile each line is a new shell.
- **Mixing up `||` and `&&`.** `A || B` runs B on failure; `A && B` runs B on success.
- **Using Bash-only features inside a Makefile.** Make uses `/bin/sh`. This repository only uses features that
  work in both.

## Check yourself

1. What does `command -v python3.13` return when Python 3.13 is missing?
   **Answer:** Nothing on stdout and a non-zero exit status, so `||` moves on to the next choice.
2. Why does the `help` pipeline use `grep -h`?
   **Answer:** When the `.env` file is part of `MAKEFILE_LIST`, `grep` would otherwise print `Makefile:` in front of each line, and the `sed` step would delete the target name.
3. What is the exit status of a successful command?
   **Answer:** 0.
4. What does `[ -f .env ] || { cp .env.example .env; ... }` do the second time you run it?
   **Answer:** Nothing: the test succeeds, so the copy is skipped.
5. What does `|` do?
   **Answer:** It connects the standard output of the command on its left to the standard input of the command on its right.

## Further reading

- GNU Bash manual: <https://www.gnu.org/software/bash/manual/bash.html>
- POSIX shell command language (what `/bin/sh` must understand): <https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>
- GNU grep: <https://www.gnu.org/software/grep/manual/grep.html>; GNU sed: <https://www.gnu.org/software/sed/manual/sed.html>
