# GitHub Actions

## What it is

**Continuous integration (CI)** means a server runs your checks each time you push, so a break is found in minutes. **GitHub
Actions** is GitHub's CI service. A **workflow** is a YAML file in `.github/workflows/`. It names the events that start it and
the **jobs** to run. A **job** is a list of **steps** that run on a fresh virtual machine (a **runner**). Jobs run in parallel
unless one waits for another.

## Why this repository uses it

Two controls are about the build itself: the dependency scan (C5) must be an **artifact of the build** with the run's id, and the
evidence pack should be rebuilt on a schedule instead of in a rush before an audit. Actions does both.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| .github/workflows/ci.yml | Jobs `check` and `integration`. |
| .github/workflows/evidence.yml | Job `weekly-pack` on a schedule. |
| `Makefile` | The workflows only call `make` targets. |

## How it works underneath

1. You push a commit (or open a pull request), or the clock reaches a `schedule`, or someone starts a `workflow_dispatch`.
2. GitHub starts a runner for each job: a clean Ubuntu machine with Docker.
3. The steps run in order: `uses:` runs a packaged action pinned by a tag like `@v4`, `run:` runs a shell command. A failing step
   fails the job.
4. An **artifact** is a file a job saves so you can download it later (`actions/upload-artifact`).
5. `${{ github.run_id }}` is an expression that GitHub replaces with the run's id; the scanner stores it in the report.

## Walkthrough of this repository's use

`.github/workflows/ci.yml`:

```yaml
name: ci

on: [push, pull_request]

jobs:
  check:
    name: Format, lint, types, import rules, unit tests with coverage, dependency audit, the scan as a build artifact (C5)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: make check
      - run: make audit
      - name: C5 evidence — the dependency scan of this build, with this run's id
        run: make scan EVIDENCE_DIR=build/evidence
      - uses: actions/upload-artifact@v4
        with:
          name: scan-report
```

- Job `check` has no database. `make check` is lint and unit tests; `make audit` the audit; `make scan EVIDENCE_DIR=build/evidence`
  writes **C5** into a folder under `build/`. Because the scan runs in CI, its `run_id` is the real `GITHUB_RUN_ID`.
- `actions/upload-artifact@v4` saves `build/evidence/C5-scan-report.json` as the artifact `scan-report`.

`.github/workflows/ci.yml`:

```yaml
  integration:
    name: Integration and end-to-end tests (PostgreSQL 18 from docker-compose.yml)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: make up
      - run: make test-integration test-e2e
      - name: The evidence pack of this run
        run: make evidence EVIDENCE_DIR=build/evidence STATE_DIR=build/state
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: evidence
          path: build/evidence/
```

- Job `integration` runs `make up` (PostgreSQL 18 from `docker-compose.yml`), then `make test-integration test-e2e` (two targets in one
  `make` call), then `make evidence EVIDENCE_DIR=build/evidence STATE_DIR=build/state`, and uploads the whole pack.
- `if: always()` uploads the pack even when an earlier step failed, so the failure can be inspected.

`.github/workflows/evidence.yml`:

```yaml
on:
  schedule:
    - cron: "17 5 * * 1"
  workflow_dispatch:
```

`.github/workflows/evidence.yml`:

```yaml
      - run: make up
      - run: make evidence EVIDENCE_DIR=build/evidence STATE_DIR=build/state
      - run: make verify EVIDENCE_DIR=build/evidence
      - run: make report EVIDENCE_DIR=build/evidence
      - uses: actions/upload-artifact@v4
        with:
          name: evidence-${{ github.run_id }}
          path: |
            build/evidence/
            build/report.md
```

- `on: schedule: - cron: "17 5 * * 1"` runs at 05:17 UTC every Monday. A cron expression has five fields: minute, hour, day of
  month, month, day of week.
- `workflow_dispatch:` adds a "Run workflow" button.
- The job brings up the database, collects, **verifies** (`make verify`), reports, and uploads `evidence-<run id>` containing the pack
  and `build/report.md`. It runs in fixture mode, so it needs no credentials.

## Try it yourself

```bash
sed -n 1,20p .github/workflows/ci.yml
```
Prints the first job.

```bash
grep -nE "^  [a-z-]+:$|uses:|run:" .github/workflows/*.yml
```
Lists the jobs, actions and commands of both workflows.

```bash
make check && make audit && make scan EVIDENCE_DIR=build/evidence
```
What the `check` job does after setting up Python (the scan and audit need network access). The last command prints `== scan: verdict pass`.

```bash
ls .github/workflows
```
Prints `ci.yml` and `evidence.yml`.

## Mistakes people make

- **Different commands in CI and locally.** The workflows only call `make` targets.
- **Unquoted version numbers** like `3.10` in YAML, which become `3.1`.
- **Forgetting `if: always()`** on an artifact upload, so a failed run leaves nothing to inspect.
- **Putting real credentials in the scheduled workflow.** It runs on fixtures; live mode would use repository secrets and read-only roles.
- **Cron in local time.** Actions uses UTC.

## Check yourself

1. Why does the scan run in CI?
   **Answer:** So the report carries the real run id and is an artifact of the build.
2. What does `if: always()` do?
   **Answer:** Runs the step even if an earlier step failed.
3. What does `cron: "17 5 * * 1"` mean?
   **Answer:** 05:17 UTC every Monday.
4. What does `workflow_dispatch` add?
   **Answer:** A manual "Run workflow" button.
5. Why is `make up` run in the integration job?
   **Answer:** The tests need PostgreSQL, which Compose starts and waits for.

## Further reading

- GitHub Actions documentation: <https://docs.github.com/en/actions>
- Workflow syntax: <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions>
- Events that trigger workflows: <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows>
