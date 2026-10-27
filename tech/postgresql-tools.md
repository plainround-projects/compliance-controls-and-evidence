# psql, pg_dump, pg_restore and pg_isready

## What it is

PostgreSQL ships small programs next to the server. `psql` is an interactive terminal and script runner. `pg_dump` writes a
**backup** of a database to a file. `pg_restore` reads a backup made in the custom format back into a database. `pg_isready` asks a
server whether it accepts connections (exit 0 if yes).

## Why this repository uses it

Control C4 says a backup must be **restored** to count, and the restore time must be shown. The tools run inside the database
container, so the laptop needs no PostgreSQL client.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` `PSQL`, `db`, `queries`, `reset-db` | Run SQL files with `psql` through `docker compose exec`. |
| `src/notes_evidence/infrastructure/backup.py` | `pg_dump`, `pg_restore` and `psql` for the restore test. |
| `docker-compose.yml` | `pg_isready` in the health check. |
| `evidence/C4-restore-test.txt` | The artifact. |

## How it works underneath

`docker compose exec -T db <command>` runs a command inside the running `db` container (`-T` disables the terminal, which
a script has no use for). `pg_dump --format=custom` writes a compressed archive to stdout; Python captures those bytes. `pg_restore`
reads the archive from stdin into an existing database. A restore into a **scratch database** proves the backup works without
touching the real one.

## Walkthrough of this repository's use

`Makefile`:

```make
PSQL := docker compose exec -T db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 -q
```

`docker compose exec -T db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 -q`: `-U` is the login role, `-d` the database,
`-v ON_ERROR_STOP=1` stops on the first error, `-q` is quiet.

`Makefile`:

```make
db: ## apply the schema (roles, tables, append-only audit log, grants) and the seed
	$(PSQL) -v app_rw_password='$(APP_RW_PASSWORD)' -v migrator_password='$(MIGRATOR_PASSWORD)' \
	  -v retention_password='$(RETENTION_PASSWORD)' < sql/001_schema.sql
	$(PSQL) < sql/002_seed.sql
```

Files are fed through **stdin** with `< sql/001_schema.sql` (the Makefile's shell redirect). Three `-v name=value` options pass the
role passwords as `psql` variables, which the SQL reads as `:'app_rw_password'`.

`src/notes_evidence/infrastructure/backup.py`:

```python
    def backup(self) -> datetime:
        """pg_dump in custom format; remember the row count at the same moment."""
        taken = datetime.now(UTC)
        self._count_at_backup = self._count(self._database, "notes")
        self._dump = self._execute(
            [*self._prefix, "pg_dump", "-U", self._user, "-d", self._database, "--format=custom"], None
        )
        return taken
```

`pg_dump -U <user> -d <database> --format=custom`: the **custom** format is a compressed archive that `pg_restore` can read, and its
bytes come back through stdout. The row count is taken at the same moment.

`src/notes_evidence/infrastructure/backup.py`:

```python
    def restore_and_count(self, table: str) -> tuple[int, int]:
        """Restore the dump into a fresh scratch database and count the rows there."""
        self._psql("postgres", f"DROP DATABASE IF EXISTS {SCRATCH}")
        self._psql("postgres", f"CREATE DATABASE {SCRATCH}")
        try:
            self._execute(
                [*self._prefix, "pg_restore", "-U", self._user, "-d", SCRATCH, "--no-owner", "--no-privileges"],
                self._dump,
            )
            return self._count_at_backup, self._count(SCRATCH, table)
        finally:
            self._psql("postgres", f"DROP DATABASE IF EXISTS {SCRATCH}")
```

- `DROP DATABASE IF EXISTS notes_restore_test` and `CREATE DATABASE` make an empty scratch database.
- `pg_restore -U ... -d notes_restore_test --no-owner --no-privileges` restores into it. `--no-owner` and `--no-privileges` skip
  ownership and grants, because the scratch database has none of the roles' setup.
- The rows in the scratch database are counted and compared with the count at backup time; the scratch database is dropped in the
  `finally` block.

`src/notes_evidence/infrastructure/backup.py`:

```python
    def _psql(self, database: str, sql: str) -> str:
        out = self._execute(
            [*self._prefix, "psql", "-U", self._user, "-d", database, "-At", "-v", "ON_ERROR_STOP=1", "-c", sql], None
        )
        return out.decode().strip()
```

`psql ... -At -v ON_ERROR_STOP=1 -c "<sql>"`: `-A` unaligned output, `-t` tuples only (no header), `-c` runs one command.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
make up && docker compose exec -T db pg_isready -h 127.0.0.1 -U postgres -d notes
```
Prints `127.0.0.1:5432 - accepting connections`.

```bash
docker compose exec -T db pg_dump -U postgres -d notes --format=custom | wc -c
```
Prints the size in bytes of the backup archive (a few hundred kilobytes).

```bash
make restore-test 2>/dev/null || .venv/bin/controls-evidence restore-test
```
Runs the C4 collector: prints `== restore-test: 12,402 of 12,402 rows restored in N s`.

```bash
cat evidence/C4-restore-test.txt
```
Shows the artifact (this one needs no database).

## Mistakes people make

- **A backup that was never restored.** C4 restores into a scratch database and counts rows.
- **Restoring over the real database** to test. The scratch database is separate and dropped afterwards.
- **Forgetting `-T`** in a script: Docker then tries to allocate a terminal and may fail.
- **Passing passwords on the command line** of a shared machine. These are throwaway development values for a local container.

## Check yourself

1. What does the `custom` format of `pg_dump` give you?
   **Answer:** A compressed archive that `pg_restore` can read.
2. Why restore into a scratch database?
   **Answer:** To prove the backup works without touching the real data.
3. What does `-v ON_ERROR_STOP=1` do?
   **Answer:** Makes `psql` stop at the first error.
4. What does `docker compose exec -T` do?
   **Answer:** Runs a command in a running container without a terminal.
5. What does `pg_isready` return?
   **Answer:** Exit code 0 when the server accepts connections.

## Further reading

- `psql`: <https://www.postgresql.org/docs/18/app-psql.html>
- `pg_dump`: <https://www.postgresql.org/docs/18/app-pgdump.html>
- `pg_restore`: <https://www.postgresql.org/docs/18/app-pgrestore.html>
- `pg_isready`: <https://www.postgresql.org/docs/18/app-pg-isready.html>
