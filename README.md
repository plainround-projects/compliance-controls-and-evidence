# compliance-controls-and-evidence

A small notes API and the evidence that six common security controls are in place and working: an access list generated from the systems, a change record that links approval to deployment, a log sample and an alert that fires on a test event, a backup restored into a scratch database and timed, a dependency scan from the build, and an access review that removes the contractor who left. The deliverable is an evidence pack an auditor could use, plus a check that every control maps to evidence and every evidence file is there, says what it should and has not been edited.

| | |
| --- | --- |
| **Lesson** | `/prep/compliance/project-controls-and-evidence`, "Controls and the evidence that proves them" (`data-structure-explainer/src/content/tracks/compliance/12-project-controls-and-evidence.md` in the Plainround app) |
| **Planned hours** | 6 |
| **Level** | Beginner |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), the control matrix: [controls/](controls), the pack: [evidence/](evidence), decisions: [docs/adr](docs/adr) |

All names are made up (ada, bruno, chen, dana, eli, contractor-lee; `example` accounts and ids).

## Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Docker with Compose v2 | 24 or newer (tested with 24.0.6) | PostgreSQL 18, and `pg_dump`, `psql` and `pg_restore` for the restore test |
| Python | 3.12 or 3.13 (tested with 3.13.12; the CI uses 3.12) | the API, the collectors and the tests |
| GNU Make | 3.81 or newer | every command below |
| Python packages | `flask` 3.1, `gunicorn` 23 and `psycopg[binary]` 3.2 or newer at run time; pytest, pytest-cov, ruff, mypy, import-linter and pip-audit for development; all pinned with hashes in `requirements.lock` and `requirements-dev.lock`; `make` installs them into `.venv/` | everything |
| `gh` and `aws` command lines | optional | only for `EVIDENCE_SOURCE=live` (below) |

No cloud account is needed: the repository host and the cloud account are fixtures shaped like the output of `gh` and `aws` (ADR 0003). The database passwords and the signing secret are throwaway values for a database that lives on your machine only while the container runs; `make up` copies `.env.example` to `.env` the first time, and the program refuses a signing secret shorter than 32 characters. Port 55440 (PostgreSQL) and 8080 (API) are used; change `POSTGRES_PORT` and `HTTP_PORT` in `.env` if they clash.

## Setup, run, test, stop

```bash
make up                # PostgreSQL 18, then sql/001_schema.sql (roles, tables, append-only audit log) and sql/002_seed.sql
make run               # the whole scenario on a clean database: use the service, collect six artifacts, review access, index, verify
make evidence          # collect the artifacts into evidence/ without resetting the database
make verify            # every control maps to evidence, every file exists, says what it should, and is unedited
make report            # build/report.md: controls, evidence, findings and the framework overlap
make test              # unit tests with coverage (domain and application at 95% or more; no services needed)
make test-integration  # the adapters, the grants and the append-only audit log against PostgreSQL
make test-e2e          # the scenario into a temporary folder, then tampering with a file
make lint              # ruff, ruff format, mypy --strict, import-linter
make audit             # pip-audit over the locked dependencies
make check             # lint and test, what the CI runs first
make queries           # sql/003_queries.sql: the access, grants, failed-login and retention queries
make down              # stop PostgreSQL and delete its data and state/
```

`make run` takes a few minutes: it restores a 12,400-row backup through a real `pg_dump` and `pg_restore` and hashes four passwords with scrypt, and both are slow when the machine is busy. It prints:

```text
== exercise: 4 accounts used the service, 3 notes written, 2 requests refused
== alert-test: 2 alert(s) delivered: failed-logins; admin-granted
== log-sample: 20 audit events in C3-log-sample.txt
== access: 4 repository, 4 database roles, 2 cloud account users
== changes: 1 change(s) with exceptions, written to C2-changes.csv
== restore-test: 12,402 of 12,402 rows restored in 149 s
== scan: verdict pass
== review: 1 access removed, recorded in C6-access-review.md
== index: wrote INDEX.md
OK: 9 files checked, 0 errors, 0 warnings
```

To use the real systems, set `EVIDENCE_SOURCE=live`, `GITHUB_REPOSITORY=owner/name` and your `gh` and `aws` credentials in the environment. The live adapters run `gh api repos/.../collaborators`, `gh pr list --state merged --json ...`, `aws iam list-users` and `aws iam delete-user`; they parse the same shapes as the fixtures but have **not** been run against a real account.

The notes API itself: `make serve` runs it with gunicorn on `127.0.0.1:8080` (`/login`, `/notes`, `/users/<name>/role`, `/healthz`), or `make api-up` builds the image and starts it beside the database (non-root, read-only file system, health check).

## The SQL

| Script | What it is |
| --- | --- |
| [sql/001_schema.sql](sql/001_schema.sql) | DDL: three login roles (`app_rw`, `migrator` with `CREATEDB`, `audit_retention`), the tables `users`, `notes`, `audit_log` and `audit_retention`, keys, checks, indexes, comments, the append-only trigger and the grants. |
| [sql/002_seed.sql](sql/002_seed.sql) | DML: four accounts (with a password hash that can never match) and 12,400 synthetic notes, the size where a restore takes a measurable moment. |
| [sql/003_queries.sql](sql/003_queries.sql) | The queries the controls run: database roles, grants per role, the audit trail, the failed-login alert rule in SQL, admin grants, retention. |
| [sql/reset.sql](sql/reset.sql) | Drops the schema so `make run` starts clean. |

The audit log is append-only **in the database**: `app_rw` can only `INSERT` and `SELECT`; a trigger refuses `UPDATE` and `TRUNCATE` for every role including the superuser, and refuses `DELETE` of any row younger than the retention period (365 days) even for the `audit_retention` role that holds the `DELETE` grant. The integration tests prove each refusal.

## The controls and the evidence

| # | Control | What it requires | Artifact | How it is produced |
| --- | --- | --- | --- | --- |
| C1 | Access control | only needed people have access, at the least level | [evidence/C1-access-list.txt](evidence/C1-access-list.txt) | `PostgresRoles` queries `pg_roles`; the repository and cloud parts come from `gh` and `aws` shapes. Regenerated after the review, so it shows the clean list. |
| C2 | Change management | every change is reviewed and traceable | [evidence/C2-changes.csv](evidence/C2-changes.csv) | merged pull requests joined to the deployment log by commit, with approvers; PR 43 has none and is a listed exception |
| C3 | Logging and monitoring | actions logged; a person told of important events | [evidence/C3-log-sample.txt](evidence/C3-log-sample.txt), [C3-alert-test.txt](evidence/C3-alert-test.txt) | the audit table rendered as log lines (no note content); five wrong passwords and an admin grant done through the service, then the alerts read from the trail |
| C4 | Backup and recovery | restorable, and how long it takes | [evidence/C4-restore-test.txt](evidence/C4-restore-test.txt) | `pg_dump`, restore into `notes_restore_test`, row counts at both ends, the time taken |
| C5 | Vulnerability management | known weaknesses found and handled | [evidence/C5-scan-report.json](evidence/C5-scan-report.json) | `pip-audit` over `requirements.lock`, wrapped with the CI run id (or a local stamp); the blocking rule is in the file |
| C6 | Access review | checked regularly, removed when not needed | [evidence/C6-access-review.md](evidence/C6-access-review.md) | the reviewer's decisions in [controls/access-review.toml](controls/access-review.toml) are checked for completeness; the refused access is removed and C1 is run again |
| C7 | Backup encryption | backups encrypted at rest | none, on purpose | a **tracked gap** ([controls/gaps.toml](controls/gaps.toml), SEC-21): the stretch goal "add a control that fails on purpose". An untracked missing control fails `verify`; a tracked one is reported. |

[evidence/INDEX.md](evidence/INDEX.md) lists each file, the control, what it proves, who ran it and when, the period and how often it is refreshed, then the exceptions, the gaps and the mapping to ISO/IEC 27001:2022 Annex A and the SOC 2 criteria. `evidence/manifest.json` holds each file's hash.

## Done when: the lesson's checklist and the proof for each line

| # | Done when (from the lesson) | Command | What proves it |
| --- | --- | --- | --- |
| 1 | Each control names a concrete artifact (a config, a log, a signed record), not "a policy says so". | `make verify` | [controls/controls.toml](controls/controls.toml) gives every control an evidence file and a kind of content check; EVD001 fails a control with neither evidence nor a tracked gap. The table above names the artifact for C1 to C6. |
| 2 | The access list is produced by a command or query, not maintained by hand, and shows who can do what. | `make evidence`; `pytest tests/integration -k roles` | `C1-access-list.txt` has a dated header and one block per system (`ada admin`, `app_rw standard`, `postgres superuser`, ...). The database block is a live `pg_roles` query. Running it twice differs by the timestamp and by whatever changed; the hash in the manifest fails `verify` if someone edits the file (EVD003). |
| 3 | A change has a reviewable record linking the approval to what was deployed. | `make evidence` | `C2-changes.csv`: for each merged PR the number, author, time, commit and approvers, and the deployment id from the deployment log (`43,"ada","2026-10-21T16:20:01Z","79e029c","","deploy-2026-10-21-43"`). The check re-derives the exceptions from the CSV itself: PR 43 has no independent approver and must be listed in [controls/exceptions.toml](controls/exceptions.toml) with a follow-up (EVD006). |
| 4 | You can show a log sample, the alert firing on a test event, and a successful restore from backup with the time it took. | `make run` | `C3-log-sample.txt` (fixed-field lines with user and id, no note text; a unit test checks the trail never contains a title or body). `C3-alert-test.txt`: `test action at 2026-10-27T01:34:04Z` and `ALERT [failed-logins] 2026-10-27T01:34:08Z 5 failed logins for account bruno within 2 minutes`. `C4-restore-test.txt`: `restore finished ... (2 min 29 s)`, `check: notes table has 12,402 rows; source had 12,402 rows at backup time`, `result: verified`. The alert is not read from its configuration: the failed logins are real calls and the alert comes from the audit table. |
| 5 | The scan report is an artifact of the build, and the access review has a before-and-after showing an access removed. | `make scan`; `make run` | `C5-scan-report.json` carries `run_id` (the GitHub Actions run when there is one), the tool version, the blocking rule ("any known vulnerability with a fixed version available fails the build") and the verdict; [the CI](.github/workflows/ci.yml) uploads it as an artifact. `C6-access-review.md`: `Before: 4 repository, 4 database roles, 2 cloud account users.` / `Removed: cloud account users contractor-lee.` / `After: ... 1 cloud account users.` / `Proof: re-ran the C1 command; none of the removed principals is listed.` EVD007 also fails if the removed name is still in the C1 file. |
| 6 | Someone could hand the pack to an auditor, and each artifact is current and self-explanatory. | `make verify`; `make report` | `verify` passes: seven controls, nine files, none empty, none edited, none unclaimed. The index describes each file in one line with its date; a file older than its refresh period is reported (EVD005). The exceptions (PR 43) and the gap (C7) are in the index, not hidden. |

## Stretch goals

| Stretch (from the lesson) | Built? |
| --- | --- |
| Automate collection so the evidence pack regenerates on a schedule. | Built, **not run on GitHub**: [.github/workflows/evidence.yml](.github/workflows/evidence.yml) runs `make evidence`, `verify` and `report` every Monday in fixture mode and uploads the pack. Locally `make evidence` is the same command. |
| Map your six controls to two frameworks at once and show the overlap. | Yes. Each control lists ISO/IEC 27001:2022 Annex A and SOC 2 references in `controls.toml`; the index and `build/report.md` show the table and mark overlaps (A.5.18 and A.8.2 satisfied by both C1 and C6; CC6.1 by C1 and C7; CC6.3 by C1 and C6). The references are the author's mapping for teaching, not an auditor's. |
| Add a control that fails on purpose and show how the gap would be found and tracked. | Yes. C7 (backup encryption) has no evidence; `controls/gaps.toml` tracks it with a ticket and a due date, and the tests show that without the record `verify` fails (EVD001) and with an incomplete record it fails (EVD008). |

## What is simplified for teaching

- **The repository host and the cloud account are fixtures** (JSON in the shape of `gh` and `aws` output), and the fixture cloud account is a state file that `remove_user` rewrites. C1's database part, everything in C3 and C4, and C5 are real. The live adapters exist and are untested against a real account (ADR 0003).
- The evidence pack in this repository is a sample from a verification run (dated in the index); `make run` rewrites it, so it changes on every run.
- The alert sink is a file (`state/alerts.log`) and the log stream; a real one pages a person.
- The review's reviewer, the people and the tickets are made up, and the review date is the one in `access-review.toml`.
- One connection per process rather than a pool: gunicorn's synchronous workers need no more.
- The hash in the manifest catches edits by mistake or by hand, not by an attacker who can also edit the manifest (ADR 0001).

## Project structure

```text
src/notes_evidence/
  domain/            roles and permissions, notes and their validation, the audit event, the alert rules,
                     the artifacts (access list, review, changes, restore, scan), the control matrix, the
                     evidence rules (EVD001 to EVD009), findings, named errors. Depends on the standard library only.
  application/       NotesService (login, notes, role grants, every action audited), the collectors, the index and
                     verification, the scripted day of use, report text, and the ports. Depends on domain only.
  infrastructure/    PostgreSQL repositories and the audit log (one connection per process, retry with backoff),
                     scrypt passwords, signed tokens, the gh and aws adapters and their fixtures, the backup runner,
                     the pip-audit runner, the evidence folder and manifest, the TOML catalog, settings, JSON logging.
                     Depends on application and domain.
  interfaces/        the Flask API, the controls-evidence command line, the composition root, the gunicorn entry
                     point and the container health check. Nothing depends on it.
sql/                 001_schema, 002_seed, 003_queries, reset.
controls/            controls.toml (the matrix), exceptions.toml, gaps.toml, people.toml, access-review.toml.
fixtures/            invented gh and aws output and the deployment log.
evidence/            the pack that `make run` produced.
tests/
  unit/              domain, application (in-memory ports), infrastructure, API over Flask's test client.
  integration/       the adapters, the grants and the append-only log against PostgreSQL.
  e2e/               the scenario, then a tampered file.
docker-compose.yml   PostgreSQL 18 (and the API under the `api` profile).   Dockerfile  the API as an image.
pyproject.toml       metadata and every tool's configuration.   requirements*.lock  hash-pinned dependencies.
Makefile             the only commands a reader needs.          .github/workflows  ci.yml and the weekly evidence.yml.
```

The dependency rule (domain depends on nothing; application on domain; infrastructure and interfaces on both; nothing on interfaces) is enforced by `make lint` through import-linter, and a second contract forbids `domain` and `application` from importing Flask or psycopg.

## Author and license

Written by Sumit Srivastava. Released under the MIT License, see [LICENSE](LICENSE). Changes are in [CHANGELOG.md](CHANGELOG.md).
