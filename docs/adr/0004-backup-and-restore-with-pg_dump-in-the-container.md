# 4. Back up and restore with pg_dump and pg_restore inside the database container

Status: accepted, 2026-10-26

## Context

C4 wants a restore into a scratch database, with the row count and the time it took. The host has no PostgreSQL client tools, and a client with a different major version than the server refuses to dump.

## Decision

`DockerBackupRunner` runs `pg_dump --format=custom`, `psql` and `pg_restore` through `docker compose exec -T db`, so the tools are always the server's own version. The dump travels through the program's memory (a few megabytes here). The restore goes into `notes_restore_test`, which is dropped afterward even when the restore fails. The row count is taken from the source at backup time and from the scratch database after the restore.

## Alternatives considered

- **COPY the table in Python.** Portable, but it proves a Python round trip and not the backup tool an operator would use.
- **Volume snapshots.** The production answer for large databases; not reproducible on a laptop.

## Consequences

- The restore test needs Docker, like the rest of the integration tests; CI uses the same compose file.
- The dump is held in memory, so this approach stops working at gigabyte sizes (ARCHITECTURE.md, limits).
