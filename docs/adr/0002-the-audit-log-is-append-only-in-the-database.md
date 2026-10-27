# 2. The audit log is append-only in the database

Status: accepted, 2026-10-26

## Context

C3 says actions are logged. A log the application can rewrite proves little. The service runs as a database role, so what that role may do is what an attacker who owns the application may do.

## Decision

`audit_log` is a table the application role may only `SELECT` and `INSERT` into. A trigger also refuses `UPDATE` and `TRUNCATE` for every role, including the superuser, and refuses `DELETE` of any row younger than the retention period (`audit_retention.days`, 365, never below 90). A separate `audit_retention` role holds `DELETE` and runs the retention query.

## Alternatives considered

- **Application discipline only.** Nothing stops a bug or an intruder from editing history.
- **Ship logs to an external store.** The right production answer and an extra system here; the table plus the log stream on standard output is the teaching build.
- **A hash chain over rows.** Detects tampering after the fact; the database already prevents it, and the chain would need its own verification job.

## Consequences

- Integration tests prove the refusals against a real PostgreSQL (`tests/integration/test_postgres.py`).
- Fixing a wrong row means appending a correcting row, never editing; a superuser can still drop the trigger, so production keeps a copy elsewhere.
- `sql/003_queries.sql` holds the retention query; the delete is commented out so a reader chooses to run it.
