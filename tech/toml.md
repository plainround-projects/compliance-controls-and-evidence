# TOML

## What it is

TOML (Tom's Obvious, Minimal Language) is a text format for settings. It has `key = value` pairs, `[tables]`
(named groups), lists in square brackets and comments after `#`. Python's own packaging tools and most Python
tools read it.

## Why this repository uses it

`pyproject.toml` is where Python projects state their name, dependencies and tool settings, in TOML. This
repository keeps all tool settings there (ruff, mypy, pytest, coverage, import-linter), so there is one file to read.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | Project metadata and the settings of every tool. |

## How it works underneath

A TOML reader turns the text into nested dictionaries. `[tool.ruff]` becomes the key `tool` holding the key `ruff`.
`[[tool.mypy.overrides]]` (double brackets) adds one more item to a **list of tables**. Values have types: text in
double quotes, integers, floats, booleans (`true`/`false`) and lists. Tools read only their own `tool.NAME` table and
ignore the rest.

## Walkthrough of this repository's use

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

[project.optional-dependencies]
dev = [
```

- `[project]` is a table. Each line inside is a key and a value.
- `dependencies = []` is an empty list.
- `license = { text = "MIT" }` is an **inline table**: a small table on one line.
- `authors = [{ name = "Sumit Srivastava" }]` is a list holding one inline table.

`pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<10",
    "pytest-cov>=5",
    "ruff>=0.6",
    "mypy>=1.11",
    "import-linter>=2.0",
    "pip-audit>=2.7",
]
```

A list can span lines. Each string is a requirement with a version range: `pytest>=8,<10` means "at least 8 and
below 10". The group name `dev` is what `uv pip compile --extra dev` used (see `hash-pinned-lock-files.md`).

`pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["src", "tests"]
```

`[tool.mypy]` is for mypy only. `files = ["src", "tests"]` is a list of strings.

Other tables in the same file are covered in the notes for each tool: `setuptools.md`, `pytest.md`, `pytest-cov.md`,
`ruff.md`, `mypy.md` and `import-linter.md`.


### The other TOML files

`controls/controls.toml`:

```toml
[[control]]
id = "C1"
name = "Access control"
requires = "only needed people have access, at the least level"
where = "repository, database, cloud account"
iso27001 = ["A.5.15", "A.5.18", "A.8.2"]
soc2 = ["CC6.1", "CC6.3"]

  [[control.evidence]]
  file = "C1-access-list.txt"
  kind = "access_list"
  proves = "who can do what today, in each system"
  period = "point in time"
  refresh_days = 7
  refreshed = "weekly"

[[control]]
```

`[[control]]` starts one control. Inside it, `[[control.evidence]]` (double brackets, nested name) adds an evidence item to **that
control's** list. `iso27001 = [...]` and `soc2 = [...]` are lists of strings: the framework references each control answers to.
The indentation of the nested table is only for readers; TOML does not need it.

The other files in `controls/` are lists of tables in the same style: `people.toml` (`[[person]]`), `exceptions.toml`
(`[[exception]]`), `gaps.toml` (`[[gap]]`) and `access-review.toml` (`[review]` and `[[decision]]`). `tomllib.md` shows how
they are read.

### The complete file `controls/access-review.toml`, line by line

`controls/access-review.toml` lines 1 to 1:

```toml
# The reviewer's decisions for the quarterly access review. Every principal in the C1 list needs a line.
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- These lines are comments written by the author; they are quoted above.

`controls/access-review.toml` lines 3 to 6:

```toml
[review]
reviewer = "eli"
reviewed_on = 2026-10-26
ticket = "SEC-17"
```

- `[review]` starts the table `review`; the lines below belong to it.
- `reviewer` is set to the text `"eli"`: who reviewed.
- `reviewed_on` is set to the date `2026-10-26`: the date.
- `ticket` is set to the text `"SEC-17"`: the ticket.

`controls/access-review.toml` lines 8 to 12:

```toml
[[decision]]
system = "repository (permission per person)"
principal = "ada"
keep = true
reason = "Developer and repository admin; needed to merge and release."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"repository (permission per person)"`: the system.
- `principal` is set to the text `"ada"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"Developer and repository admin; needed to merge and release."`: why.

`controls/access-review.toml` lines 14 to 18:

```toml
[[decision]]
system = "repository (permission per person)"
principal = "bruno"
keep = true
reason = "Developer; write access is needed to open and merge reviewed changes."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"repository (permission per person)"`: the system.
- `principal` is set to the text `"bruno"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"Developer; write access is needed to open and merge reviewed changes…`: why.

`controls/access-review.toml` lines 20 to 24:

```toml
[[decision]]
system = "repository (permission per person)"
principal = "chen"
keep = true
reason = "Developer; write access is needed to open and merge reviewed changes."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"repository (permission per person)"`: the system.
- `principal` is set to the text `"chen"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"Developer; write access is needed to open and merge reviewed changes…`: why.

`controls/access-review.toml` lines 26 to 30:

```toml
[[decision]]
system = "repository (permission per person)"
principal = "dana"
keep = true
reason = "Operations engineer; read access is enough to follow deployments."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"repository (permission per person)"`: the system.
- `principal` is set to the text `"dana"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"Operations engineer; read access is enough to follow deployments."`: why.

`controls/access-review.toml` lines 32 to 36:

```toml
[[decision]]
system = "database roles"
principal = "app_rw"
keep = true
reason = "The API's own role: reads users, writes notes, appends to the audit log, nothing else."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"database roles"`: the system.
- `principal` is set to the text `"app_rw"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"The API's own role: reads users, writes notes, appends to the audit …`: why.

`controls/access-review.toml` lines 38 to 42:

```toml
[[decision]]
system = "database roles"
principal = "audit_retention"
keep = true
reason = "The retention job's role: it may delete audit rows only after the retention period."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"database roles"`: the system.
- `principal` is set to the text `"audit_retention"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"The retention job's role: it may delete audit rows only after the re…`: why.

`controls/access-review.toml` lines 44 to 48:

```toml
[[decision]]
system = "database roles"
principal = "migrator"
keep = true
reason = "Applies schema changes and creates scratch databases for the restore test."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"database roles"`: the system.
- `principal` is set to the text `"migrator"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"Applies schema changes and creates scratch databases for the restore…`: why.

`controls/access-review.toml` lines 50 to 54:

```toml
[[decision]]
system = "database roles"
principal = "postgres"
keep = true
reason = "The administrative role the collectors use; only the operations engineer holds its password."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"database roles"`: the system.
- `principal` is set to the text `"postgres"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"The administrative role the collectors use; only the operations engi…`: why.

`controls/access-review.toml` lines 56 to 60:

```toml
[[decision]]
system = "cloud account users"
principal = "ada"
keep = true
reason = "Developer who deploys."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"cloud account users"`: the system.
- `principal` is set to the text `"ada"`: the account.
- `keep` is set to `true`: whether the access stays.
- `reason` is set to the text `"Developer who deploys."`: why.

`controls/access-review.toml` lines 62 to 66:

```toml
[[decision]]
system = "cloud account users"
principal = "contractor-lee"
keep = false
reason = "Contractor who left on 2026-09-18; the account was never closed."
```

- `[[decision]]` starts a new item in the list of tables named `decision`.
- `system` is set to the text `"cloud account users"`: the system.
- `principal` is set to the text `"contractor-lee"`: the account.
- `keep` is set to `false`: whether the access stays.
- `reason` is set to the text `"Contractor who left on 2026-09-18; the account was never closed."`: why.

### The complete file `controls/controls.toml`, line by line

`controls/controls.toml` lines 1 to 3:

```toml
# The control matrix for notes-api: six controls with the evidence that proves each, the framework references each
# answers to (ISO/IEC 27001:2022 Annex A and the SOC 2 trust services criteria), and one control that is a tracked gap.
# `controls-evidence verify` checks that every control maps to evidence, every file exists and says what it should.
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- These lines are comments written by the author; they are quoted above.

`controls/controls.toml` lines 5 to 11:

```toml
[[control]]
id = "C1"
name = "Access control"
requires = "only needed people have access, at the least level"
where = "repository, database, cloud account"
iso27001 = ["A.5.15", "A.5.18", "A.8.2"]
soc2 = ["CC6.1", "CC6.3"]
```

- `[[control]]` starts a new item in the list of tables named `control`.
- `id` is set to the text `"C1"`: the identifier.
- `name` is set to the text `"Access control"`: the project's or item's name.
- `requires` is set to the text `"only needed people have access, at the least level"`: what must be installed first (for a control: what it demands).
- `where` is set to the text `"repository, database, cloud account"`: the folder to search for packages.
- `iso27001` is set to a list `["A.5.15", "A.5.18", "A.8.2"]`: ISO 27001 clauses it answers.
- `soc2` is set to a list `["CC6.1", "CC6.3"]`: SOC 2 criteria it answers.

`controls/controls.toml` lines 13 to 19:

```toml
  [[control.evidence]]
  file = "C1-access-list.txt"
  kind = "access_list"
  proves = "who can do what today, in each system"
  period = "point in time"
  refresh_days = 7
  refreshed = "weekly"
```

- `[[control.evidence]]` starts a new item in the list of tables named `control.evidence`.
- `file` is set to the text `"C1-access-list.txt"`: the file.
- `kind` is set to the text `"access_list"`: the kind.
- `proves` is set to the text `"who can do what today, in each system"`: what it proves.
- `period` is set to the text `"point in time"`: how long the evidence covers.
- `refresh_days` is set to the number `7`: days before it is stale.
- `refreshed` is set to the text `"weekly"`: how often it is refreshed.

`controls/controls.toml` lines 21 to 27:

```toml
[[control]]
id = "C2"
name = "Change management"
requires = "every change is reviewed and traceable to what was deployed"
where = "repository, CI"
iso27001 = ["A.8.32"]
soc2 = ["CC8.1"]
```

- `[[control]]` starts a new item in the list of tables named `control`.
- `id` is set to the text `"C2"`: the identifier.
- `name` is set to the text `"Change management"`: the project's or item's name.
- `requires` is set to the text `"every change is reviewed and traceable to what was deployed"`: what must be installed first (for a control: what it demands).
- `where` is set to the text `"repository, CI"`: the folder to search for packages.
- `iso27001` is set to a list `["A.8.32"]`: ISO 27001 clauses it answers.
- `soc2` is set to a list `["CC8.1"]`: SOC 2 criteria it answers.

`controls/controls.toml` lines 29 to 35:

```toml
  [[control.evidence]]
  file = "C2-changes.csv"
  kind = "changes"
  proves = "reviewed, traceable changes, from approval to deployment"
  period = "sample of recent merges"
  refresh_days = 7
  refreshed = "weekly"
```

- `[[control.evidence]]` starts a new item in the list of tables named `control.evidence`.
- `file` is set to the text `"C2-changes.csv"`: the file.
- `kind` is set to the text `"changes"`: the kind.
- `proves` is set to the text `"reviewed, traceable changes, from approval to deployment"`: what it proves.
- `period` is set to the text `"sample of recent merges"`: how long the evidence covers.
- `refresh_days` is set to the number `7`: days before it is stale.
- `refreshed` is set to the text `"weekly"`: how often it is refreshed.

`controls/controls.toml` lines 37 to 43:

```toml
[[control]]
id = "C3"
name = "Logging and monitoring"
requires = "actions are logged and a person is told about important events"
where = "audit log, alert"
iso27001 = ["A.8.15", "A.8.16"]
soc2 = ["CC7.2"]
```

- `[[control]]` starts a new item in the list of tables named `control`.
- `id` is set to the text `"C3"`: the identifier.
- `name` is set to the text `"Logging and monitoring"`: the project's or item's name.
- `requires` is set to the text `"actions are logged and a person is told about important events"`: what must be installed first (for a control: what it demands).
- `where` is set to the text `"audit log, alert"`: the folder to search for packages.
- `iso27001` is set to a list `["A.8.15", "A.8.16"]`: ISO 27001 clauses it answers.
- `soc2` is set to a list `["CC7.2"]`: SOC 2 criteria it answers.

`controls/controls.toml` lines 45 to 51:

```toml
  [[control.evidence]]
  file = "C3-log-sample.txt"
  kind = "log_sample"
  proves = "who did what and when, without note content"
  period = "sample"
  refresh_days = 7
  refreshed = "weekly"
```

- `[[control.evidence]]` starts a new item in the list of tables named `control.evidence`.
- `file` is set to the text `"C3-log-sample.txt"`: the file.
- `kind` is set to the text `"log_sample"`: the kind.
- `proves` is set to the text `"who did what and when, without note content"`: what it proves.
- `period` is set to the text `"sample"`: how long the evidence covers.
- `refresh_days` is set to the number `7`: days before it is stale.
- `refreshed` is set to the text `"weekly"`: how often it is refreshed.

`controls/controls.toml` lines 53 to 59:

```toml
  [[control.evidence]]
  file = "C3-alert-test.txt"
  kind = "alert_test"
  proves = "the alert fires on a test event, with its timestamp beside the action"
  period = "point in time"
  refresh_days = 30
  refreshed = "monthly"
```

- `[[control.evidence]]` starts a new item in the list of tables named `control.evidence`.
- `file` is set to the text `"C3-alert-test.txt"`: the file.
- `kind` is set to the text `"alert_test"`: the kind.
- `proves` is set to the text `"the alert fires on a test event, with its timestamp beside the actio…`: what it proves.
- `period` is set to the text `"point in time"`: how long the evidence covers.
- `refresh_days` is set to the number `30`: days before it is stale.
- `refreshed` is set to the text `"monthly"`: how often it is refreshed.

`controls/controls.toml` lines 61 to 67:

```toml
[[control]]
id = "C4"
name = "Backup and recovery"
requires = "data can be restored, and the time it takes is known"
where = "database"
iso27001 = ["A.8.13"]
soc2 = ["A1.2", "A1.3"]
```

- `[[control]]` starts a new item in the list of tables named `control`.
- `id` is set to the text `"C4"`: the identifier.
- `name` is set to the text `"Backup and recovery"`: the project's or item's name.
- `requires` is set to the text `"data can be restored, and the time it takes is known"`: what must be installed first (for a control: what it demands).
- `where` is set to the text `"database"`: the folder to search for packages.
- `iso27001` is set to a list `["A.8.13"]`: ISO 27001 clauses it answers.
- `soc2` is set to a list `["A1.2", "A1.3"]`: SOC 2 criteria it answers.

`controls/controls.toml` lines 69 to 75:

```toml
  [[control.evidence]]
  file = "C4-restore-test.txt"
  kind = "restore"
  proves = "a real restore into a scratch database, verified by row count, with its duration"
  period = "point in time"
  refresh_days = 30
  refreshed = "monthly"
```

- `[[control.evidence]]` starts a new item in the list of tables named `control.evidence`.
- `file` is set to the text `"C4-restore-test.txt"`: the file.
- `kind` is set to the text `"restore"`: the kind.
- `proves` is set to the text `"a real restore into a scratch database, verified by row count, with …`: what it proves.
- `period` is set to the text `"point in time"`: how long the evidence covers.
- `refresh_days` is set to the number `30`: days before it is stale.
- `refreshed` is set to the text `"monthly"`: how often it is refreshed.

`controls/controls.toml` lines 77 to 83:

```toml
[[control]]
id = "C5"
name = "Vulnerability management"
requires = "known weaknesses in dependencies are found and handled"
where = "CI"
iso27001 = ["A.8.8"]
soc2 = ["CC7.1"]
```

- `[[control]]` starts a new item in the list of tables named `control`.
- `id` is set to the text `"C5"`: the identifier.
- `name` is set to the text `"Vulnerability management"`: the project's or item's name.
- `requires` is set to the text `"known weaknesses in dependencies are found and handled"`: what must be installed first (for a control: what it demands).
- `where` is set to the text `"CI"`: the folder to search for packages.
- `iso27001` is set to a list `["A.8.8"]`: ISO 27001 clauses it answers.
- `soc2` is set to a list `["CC7.1"]`: SOC 2 criteria it answers.

`controls/controls.toml` lines 85 to 91:

```toml
  [[control.evidence]]
  file = "C5-scan-report.json"
  kind = "scan"
  proves = "the dependency scan of a build, with its run id and the blocking rule"
  period = "every build"
  refresh_days = 7
  refreshed = "every build"
```

- `[[control.evidence]]` starts a new item in the list of tables named `control.evidence`.
- `file` is set to the text `"C5-scan-report.json"`: the file.
- `kind` is set to the text `"scan"`: the kind.
- `proves` is set to the text `"the dependency scan of a build, with its run id and the blocking rul…`: what it proves.
- `period` is set to the text `"every build"`: how long the evidence covers.
- `refresh_days` is set to the number `7`: days before it is stale.
- `refreshed` is set to the text `"every build"`: how often it is refreshed.

`controls/controls.toml` lines 93 to 99:

```toml
[[control]]
id = "C6"
name = "Access review"
requires = "access is checked regularly and removed when no longer needed"
where = "people"
iso27001 = ["A.5.18", "A.8.2"]
soc2 = ["CC6.2", "CC6.3"]
```

- `[[control]]` starts a new item in the list of tables named `control`.
- `id` is set to the text `"C6"`: the identifier.
- `name` is set to the text `"Access review"`: the project's or item's name.
- `requires` is set to the text `"access is checked regularly and removed when no longer needed"`: what must be installed first (for a control: what it demands).
- `where` is set to the text `"people"`: the folder to search for packages.
- `iso27001` is set to a list `["A.5.18", "A.8.2"]`: ISO 27001 clauses it answers.
- `soc2` is set to a list `["CC6.2", "CC6.3"]`: SOC 2 criteria it answers.

`controls/controls.toml` lines 101 to 107:

```toml
  [[control.evidence]]
  file = "C6-access-review.md"
  kind = "review"
  proves = "a reviewer decided every access; the removed access is gone on a re-run"
  period = "quarterly point in time"
  refresh_days = 95
  refreshed = "quarterly"
```

- `[[control.evidence]]` starts a new item in the list of tables named `control.evidence`.
- `file` is set to the text `"C6-access-review.md"`: the file.
- `kind` is set to the text `"review"`: the kind.
- `proves` is set to the text `"a reviewer decided every access; the removed access is gone on a re-…`: what it proves.
- `period` is set to the text `"quarterly point in time"`: how long the evidence covers.
- `refresh_days` is set to the number `95`: days before it is stale.
- `refreshed` is set to the text `"quarterly"`: how often it is refreshed.

`controls/controls.toml` lines 109 to 116:

```toml
# A control that fails on purpose: it has no evidence, and the gap is tracked in gaps.toml.
[[control]]
id = "C7"
name = "Backup encryption"
requires = "backups are encrypted at rest"
where = "backup storage"
iso27001 = ["A.8.24"]
soc2 = ["CC6.1"]
```

- `[[control]]` starts a new item in the list of tables named `control`.
- `id` is set to the text `"C7"`: the identifier.
- `name` is set to the text `"Backup encryption"`: the project's or item's name.
- `requires` is set to the text `"backups are encrypted at rest"`: what must be installed first (for a control: what it demands).
- `where` is set to the text `"backup storage"`: the folder to search for packages.
- `iso27001` is set to a list `["A.8.24"]`: ISO 27001 clauses it answers.
- `soc2` is set to a list `["CC6.1"]`: SOC 2 criteria it answers.

### The complete file `controls/exceptions.toml`, line by line

`controls/exceptions.toml` lines 1 to 1:

```toml
# Known deviations from a control, each with how it was handled. `verify` fails when a deviation in the evidence is not listed here.
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- These lines are comments written by the author; they are quoted above.

`controls/exceptions.toml` lines 3 to 8:

```toml
[[exception]]
id = "EXC-1"
control = "C2"
change = 43
description = "Pull request 43 was a hotfix merged without an approver."
followup = "SEC-16: a retroactive review by bruno and chen was recorded the next morning."
```

- `[[exception]]` starts a new item in the list of tables named `exception`.
- `id` is set to the text `"EXC-1"`: the identifier.
- `control` is set to the text `"C2"`: the control id.
- `change` is set to the number `43`: the related change.
- `description` is set to the text `"Pull request 43 was a hotfix merged without an approver."`: a description.
- `followup` is set to the text `"SEC-16: a retroactive review by bruno and chen was recorded the next…`: what happens next.

### The complete file `controls/gaps.toml`, line by line

`controls/gaps.toml` lines 1 to 1:

```toml
# Controls with no evidence yet, tracked on purpose. An untracked missing control fails `verify`; a tracked one is reported.
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- These lines are comments written by the author; they are quoted above.

`controls/gaps.toml` lines 3 to 7:

```toml
[[gap]]
control = "C7"
reason = "Backups are written unencrypted to the scratch volume; encryption at rest is a storage setting that is planned, not yet enabled."
ticket = "SEC-21"
due = 2026-12-01
```

- `[[gap]]` starts a new item in the list of tables named `gap`.
- `control` is set to the text `"C7"`: the control id.
- `reason` is set to the text `"Backups are written unencrypted to the scratch volume; encryption at…`: why.
- `ticket` is set to the text `"SEC-21"`: the ticket.
- `due` is set to the date `2026-12-01`: the due date.

### The complete file `controls/people.toml`, line by line

`controls/people.toml` lines 1 to 1:

```toml
# Who may hold access. All names are made up. A person with left_on set must not keep any access (ARV003).
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- These lines are comments written by the author; they are quoted above.

`controls/people.toml` lines 3 to 5:

```toml
[[person]]
name = "ada"
title = "Developer"
```

- `[[person]]` starts a new item in the list of tables named `person`.
- `name` is set to the text `"ada"`: the project's or item's name.
- `title` is set to the text `"Developer"`: the title.

`controls/people.toml` lines 7 to 9:

```toml
[[person]]
name = "bruno"
title = "Developer"
```

- `[[person]]` starts a new item in the list of tables named `person`.
- `name` is set to the text `"bruno"`: the project's or item's name.
- `title` is set to the text `"Developer"`: the title.

`controls/people.toml` lines 11 to 13:

```toml
[[person]]
name = "chen"
title = "Developer"
```

- `[[person]]` starts a new item in the list of tables named `person`.
- `name` is set to the text `"chen"`: the project's or item's name.
- `title` is set to the text `"Developer"`: the title.

`controls/people.toml` lines 15 to 17:

```toml
[[person]]
name = "dana"
title = "Operations engineer"
```

- `[[person]]` starts a new item in the list of tables named `person`.
- `name` is set to the text `"dana"`: the project's or item's name.
- `title` is set to the text `"Operations engineer"`: the title.

`controls/people.toml` lines 19 to 21:

```toml
[[person]]
name = "eli"
title = "Manager"
```

- `[[person]]` starts a new item in the list of tables named `person`.
- `name` is set to the text `"eli"`: the project's or item's name.
- `title` is set to the text `"Manager"`: the title.

`controls/people.toml` lines 23 to 26:

```toml
[[person]]
name = "contractor-lee"
title = "Contractor"
left_on = 2026-09-18
```

- `[[person]]` starts a new item in the list of tables named `person`.
- `name` is set to the text `"contractor-lee"`: the project's or item's name.
- `title` is set to the text `"Contractor"`: the title.
- `left_on` is set to the date `2026-09-18`: the date the person left.

### The complete file `pyproject.toml`, line by line

`pyproject.toml` lines 1 to 3:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- `[build-system]` starts the table `build-system`; the lines below belong to it.
- `requires` is set to a list `["setuptools>=75"]`: what must be installed first (for a control: what it demands).
- `build-backend` is set to the text `"setuptools.build_meta"`: the program that builds the project.

`pyproject.toml` lines 5 to 13:

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

- `[project]` starts the table `project`; the lines below belong to it.
- `name` is set to the text `"compliance-controls-and-evidence"`: the project's or item's name.
- `version` is set to the text `"0.1.0"`: the version number.
- `description` is set to the text `"A small notes service and the evidence pack that proves six security…`: a description.
- `readme` is set to the text `"README.md"`: the file used as the long description.
- `requires-python` is set to the text `">=3.12"`: the oldest Python version allowed.
- `license` is set to a small table `{ text = "MIT" }`: the license.
- `authors` is set to a list `[{ name = "Sumit Srivastava" }]`: the authors.
- `dependencies` is set to a list `["flask>=3.1,<4", "gunicorn>=23", "psycopg[binary]>=3.2,<4"]`: the packages needed to run.

`pyproject.toml` lines 15 to 23:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<10",
    "pytest-cov>=5",
    "ruff>=0.6",
    "mypy>=1.11",
    "import-linter>=2.0",
    "pip-audit>=2.7",
]
```

- `[project.optional-dependencies]` starts the table `project.optional-dependencies`; the lines below belong to it.
- `dev` is set to a list `[ "pytest>=8,<10", "pytest-cov>=5", "ruff>=0.6", "mypy>=1.11", "import-linter>=…`.

`pyproject.toml` lines 25 to 27:

```toml
[project.scripts]
controls-evidence = "notes_evidence.interfaces.cli:main"
notes-api-health = "notes_evidence.interfaces.health:main"
```

- `[project.scripts]` starts the table `project.scripts`; the lines below belong to it.
- `controls-evidence` is set to the text `"notes_evidence.interfaces.cli:main"`.
- `notes-api-health` is set to the text `"notes_evidence.interfaces.health:main"`.

`pyproject.toml` lines 29 to 30:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

- `[tool.setuptools.packages.find]` starts the table `tool.setuptools.packages.find`; the lines below belong to it.
- `where` is set to a list `["src"]`: the folder to search for packages.

`pyproject.toml` lines 32 to 36:

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
src = ["src", "tests"]
extend-exclude = ["tech"]  # tech/ quotes fragments of code inside Markdown; ruff 0.17 would try to format them
```

- `[tool.ruff]` starts the table `tool.ruff`; the lines below belong to it.
- `line-length` is set to the number `120`: the longest allowed line, in characters.
- `target-version` is set to the text `"py312"`: the Python version to write for.
- `src` is set to a list `["src", "tests"]`: where first-party code lives.
- `extend-exclude` is set to a list `["tech"]`: extra folders the tool skips.

`pyproject.toml` lines 38 to 39:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103", "D104"]
```

- `[tool.ruff.lint]` starts the table `tool.ruff.lint`; the lines below belong to it.
- `select` is set to a list `["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103…`: the rule groups switched on.

`pyproject.toml` lines 41 to 42:

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D"]
```

- `[tool.ruff.lint.per-file-ignores]` starts the table `tool.ruff.lint.per-file-ignores`; the lines below belong to it.
- `"tests/**"` is set to a list `["D"]`.

`pyproject.toml` lines 44 to 47:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["src", "tests"]
```

- `[tool.mypy]` starts the table `tool.mypy`; the lines below belong to it.
- `python_version` is set to the text `"3.12"`: the Python version to check as.
- `strict` is set to `true`: switch on all the strict checks.
- `files` is set to a list `["src", "tests"]`: the files or folders to check.

`pyproject.toml` lines 49 to 53:

```toml
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false
```

- `[[tool.mypy.overrides]]` starts a new item in the list of tables named `tool.mypy.overrides`.
- `module` is set to a list `["tests.*"]`.
- `disallow_untyped_defs` is set to `false`.
- `disallow_incomplete_defs` is set to `false`.
- `disallow_untyped_calls` is set to `false`.

`pyproject.toml` lines 55 to 61:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
markers = [
    "integration: needs PostgreSQL from docker-compose.yml (make up)",
    "e2e: runs the lesson's scenario end to end against PostgreSQL (make up first)",
]
```

- `[tool.pytest.ini_options]` starts the table `tool.pytest.ini_options`; the lines below belong to it.
- `testpaths` is set to a list `["tests"]`: where to look for tests.
- `addopts` is set to the text `"-ra --strict-markers"`: options always added to a run.
- `markers` is set to a list `[ "integration: needs PostgreSQL from docker-compose.yml (make up)", "e2e: runs…`: the registered test markers.

`pyproject.toml` lines 63 to 65:

```toml
[tool.coverage.run]
source = ["notes_evidence"]
branch = true
```

- `[tool.coverage.run]` starts the table `tool.coverage.run`; the lines below belong to it.
- `source` is set to a list `["notes_evidence"]`: the package to measure.
- `branch` is set to `true`: also measure each branch of an if.

`pyproject.toml` lines 67 to 69:

```toml
[tool.coverage.report]
show_missing = true
skip_covered = false
```

- `[tool.coverage.report]` starts the table `tool.coverage.report`; the lines below belong to it.
- `show_missing` is set to `true`: list the missed line numbers.
- `skip_covered` is set to `false`: leave fully covered files out of the table.

`pyproject.toml` lines 71 to 73:

```toml
[tool.importlinter]
root_package = "notes_evidence"
include_external_packages = true
```

- `[tool.importlinter]` starts the table `tool.importlinter`; the lines below belong to it.
- `root_package` is set to the text `"notes_evidence"`: the package to analyse.
- `include_external_packages` is set to `true`: let contracts name installed packages.

`pyproject.toml` lines 75 to 83:

```toml
[[tool.importlinter.contracts]]
name = "Layers: interfaces -> infrastructure -> application -> domain, never upward"
type = "layers"
layers = [
    "notes_evidence.interfaces",
    "notes_evidence.infrastructure",
    "notes_evidence.application",
    "notes_evidence.domain",
]
```

- `[[tool.importlinter.contracts]]` starts a new item in the list of tables named `tool.importlinter.contracts`.
- `name` is set to the text `"Layers: interfaces -> infrastructure -> application -> domain, never…`: the project's or item's name.
- `type` is set to the text `"layers"`: the kind of contract.
- `layers` is set to a list `[ "notes_evidence.interfaces", "notes_evidence.infrastructure", "notes_evidence…`: the modules from highest to lowest.

`pyproject.toml` lines 85 to 89:

```toml
[[tool.importlinter.contracts]]
name = "Domain and application know nothing about Flask or PostgreSQL"
type = "forbidden"
source_modules = ["notes_evidence.domain", "notes_evidence.application"]
forbidden_modules = ["notes_evidence.infrastructure", "notes_evidence.interfaces", "flask", "psycopg"]
```

- `[[tool.importlinter.contracts]]` starts a new item in the list of tables named `tool.importlinter.contracts`.
- `name` is set to the text `"Domain and application know nothing about Flask or PostgreSQL"`: the project's or item's name.
- `type` is set to the text `"forbidden"`: the kind of contract.
- `source_modules` is set to a list `["notes_evidence.domain", "notes_evidence.application"]`: the modules the rule applies to.
- `forbidden_modules` is set to a list `["notes_evidence.infrastructure", "notes_evidence.interfaces", "flask", "psycop…`: the modules they must not import.

## Try it yourself

```bash
.venv/bin/python -c "import tomllib, pprint; pprint.pprint(tomllib.load(open('pyproject.toml','rb'))['project'])"
```
Prints the `[project]` table as a Python dictionary (name, version, `requires-python`, ...).

```bash
.venv/bin/python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(list(d['tool']))"
```
Prints `['ruff', 'mypy', 'pytest', 'coverage', 'importlinter', 'setuptools']` (the tables under `tool`).

```bash
.venv/bin/python -c "import tomllib; print(tomllib.loads('a = [1, 2]\nb = {c = true}'))"
```
Prints `{'a': [1, 2], 'b': {'c': True}}`.


```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('controls/controls.toml','rb')); print(len(d['control']), 'controls;', [c['id'] for c in d['control']])"
```
Prints `7 controls; ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']`: six controls with evidence and `C7`, backup encryption, which `gaps.toml` tracks as a gap with a ticket and a due date.

## Mistakes people make

- **Quoting numbers** (`"120"`) so the value is text, not a number.
- **Mixing up `[table]` and `[[list of tables]]`.**
- **Forgetting commas** between list items.
- **Expecting comments to be kept** when a program rewrites the file.

## Check yourself

1. What does `[tool.ruff]` define?
   **Answer:** A table named `ruff` inside the table `tool`, holding ruff's settings.
2. What is the difference between `[x]` and `[[x]]`?
   **Answer:** `[x]` is one table; `[[x]]` adds an item to a list of tables.
3. How do you write a list?
   **Answer:** In square brackets, separated by commas.
4. Which Python module reads TOML?
   **Answer:** `tomllib`, in the standard library since 3.11.
5. What does `pytest>=8,<10` accept?
   **Answer:** Versions 8.x and 9.x.

## Further reading

- TOML 1.0.0 specification: <https://toml.io/en/v1.0.0>
- `pyproject.toml` specification: <https://packaging.python.org/en/latest/specifications/pyproject-toml/>
- Python `tomllib` (3.12): <https://docs.python.org/3.12/library/tomllib.html>
