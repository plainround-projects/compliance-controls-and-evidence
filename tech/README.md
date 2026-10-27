# Technology notes: Controls and evidence

These notes teach every technology used by `compliance-controls-and-evidence`, from zero, through this repository's own files: a small notes API on Flask and PostgreSQL, and the tool that collects and verifies the evidence pack that proves six security controls. Each note says what the technology is, why the repository uses it, where it appears, how it works underneath, walks through the repository's own lines, and ends with commands to try, common mistakes, five questions with answers, and links to the official documentation for the pinned version. Notes that involve Docker say which commands were not run while they were written.

## Reading order

Read the language first, then the build tool, then the runtime pieces, then the tests and the checks.

1. [python.md](python.md): Python: the language the whole program is written in; read this first.
2. [python-standard-library.md](python-standard-library.md): Standard library: `enum`, `typing`, `collections.abc`, `contextlib`, `datetime`, `threading`, `time`, `base64`, `importlib.metadata`, `urllib`, `os`, `sys`, `io`.
3. [dataclasses.md](dataclasses.md): `dataclasses`: the small frozen value types (`Finding`, `Report`, settings, parsed documents).
4. [re.md](re.md): `re`: the patterns that find headings, labels, numbers and sentences in Markdown text.
5. [argparse.md](argparse.md): `argparse` and exit codes: how `controls-evidence` reads its subcommands and reports success.
6. [pathlib.md](pathlib.md): `pathlib`: how the program reads and writes files, and refuses to leave the repository root.
7. [json.md](json.md): JSON: fixtures, the evidence manifest, the scan report, the structured logs and the HTTP bodies.
8. [csv.md](csv.md): CSV: `evidence/C2-changes.csv`, the change record, written and read with Python's `csv` module.
9. [logging.md](logging.md): `logging`: JSON log lines on standard output, one per request, and the alert stand-in.
10. [subprocess.md](subprocess.md): `subprocess`: how Python starts `pip-audit`, `pg_dump`, `psql`, `pg_restore`, `gh` and `aws` and reads what they print.
11. [hashing-and-signing.md](hashing-and-signing.md): Hashing and signing: the manifest's SHA-256, signed session tokens, salted password hashes.
12. [tomllib.md](tomllib.md): `tomllib`: loads `controls/*.toml` (controls, exceptions, gaps, people, the access review) into typed values.
13. [http-and-rest.md](http-and-rest.md): HTTP: the notes API's routes, status codes and bearer tokens, and `curl` for `make smoke`.
14. [flask.md](flask.md): Flask: the web framework behind `http_app.py` (routes, request, error handlers, hooks).
15. [flask-support-libraries.md](flask-support-libraries.md): The packages Flask brings with it: Werkzeug, Jinja2, ItsDangerous, Blinker, Click, MarkupSafe.
16. [gunicorn.md](gunicorn.md): gunicorn: the production WSGI server that runs the Flask app (`make serve`, the Docker `CMD`).
17. [psycopg.md](psycopg.md): psycopg: the PostgreSQL driver used by `infrastructure/postgres.py`.
18. [postgresql.md](postgresql.md): PostgreSQL: the database that holds users, notes and the append-only audit log, run by Docker Compose.
19. [sql.md](sql.md): SQL: `sql/001_schema.sql`, `002_seed.sql`, `003_queries.sql`, `reset.sql` and the statements in the Python code.
20. [postgresql-tools.md](postgresql-tools.md): PostgreSQL's command-line tools: `psql` runs the SQL scripts, `pg_dump`/`pg_restore` make C4, `pg_isready` is the health check.
21. [docker.md](docker.md): Docker: containers for the database and the API (`docker compose`, `docker build`, `.dockerignore`).
22. [dockerfile.md](dockerfile.md): Dockerfile: the recipe for the API image, instruction by instruction.
23. [docker-compose.md](docker-compose.md): Docker Compose: `docker-compose.yml`, the database and the API as two services with health checks and a hardened API.
24. [markdown.md](markdown.md): Markdown: README, ARCHITECTURE, CHANGELOG, the decision records, and the evidence files `INDEX.md` and `C6-access-review.md`.
25. [toml.md](toml.md): TOML: the format of `pyproject.toml`.
26. [bash.md](bash.md): Shell: the small command-line programs (`grep`, `sed`, `sort`, `cp`, `rm`, `touch`, `command -v`) that the Makefile recipes run.
27. [make.md](make.md): Make: `Makefile`, the one place that names every command (`make run`, `make test`, `make lint`).
28. [venv-and-pip.md](venv-and-pip.md): venv and pip: the private `.venv/` folder and the installer that fills it from the lock file.
29. [setuptools.md](setuptools.md): setuptools and `pyproject.toml` packaging: how `src/notes_evidence` becomes an installable project with a `controls-evidence` command.
30. [hash-pinned-lock-files.md](hash-pinned-lock-files.md): Lock files: `requirements-dev.lock` and `requirements.lock`, the exact packages and file hashes pip installs.
31. [env-files.md](env-files.md): `.env` files: the database, secrets and evidence settings, read by Make, Docker Compose and the program.
32. [pytest.md](pytest.md): pytest: runs the 178 tests under `tests/`; one integration test per "Done when" line.
33. [pytest-cov.md](pytest-cov.md): Coverage: measures which lines the tests ran; `make test` fails under 95 percent in `domain/` and `application/`.
34. [ruff.md](ruff.md): ruff: the linter and formatter (`ruff check`, `ruff format --check`) with rules chosen in `pyproject.toml`.
35. [mypy.md](mypy.md): mypy: the static type checker, in strict mode, over `src/` and `tests/`.
36. [import-linter.md](import-linter.md): import-linter: enforces the layer rule `interfaces -> infrastructure -> application -> domain` (`lint-imports`).
37. [pip-audit.md](pip-audit.md): pip-audit: checks the pinned packages against vulnerability databases (`make audit`).
38. [editorconfig.md](editorconfig.md): EditorConfig: `.editorconfig`, the editor settings (encoding, line endings, tabs or spaces) shared by everyone.
39. [git.md](git.md): Git: the history of the repository (the commits) and `.gitignore`, the list of files it should not track.
40. [github-actions.md](github-actions.md): GitHub Actions: `ci.yml` (checks, then integration against PostgreSQL) and `evidence.yml` (a weekly evidence pack).
41. [yaml.md](yaml.md): YAML: the file format of `.github/workflows/ci.yml`.

## If you have ten minutes

Read these three, in this order:

- [postgresql.md](postgresql.md): PostgreSQL: the database that holds users, notes and the append-only audit log, run by Docker Compose.
- [sql.md](sql.md): SQL: `sql/001_schema.sql`, `002_seed.sql`, `003_queries.sql`, `reset.sql` and the statements in the Python code.
- [docker-compose.md](docker-compose.md): Docker Compose: `docker-compose.yml`, the database and the API as two services with health checks and a hardened API.
