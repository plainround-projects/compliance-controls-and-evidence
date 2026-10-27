# PostgreSQL 18

## What it is

PostgreSQL ("Postgres") is a relational database **server**: a program that stores tables on disk, accepts connections over the
network, and answers SQL. It checks permissions per **role** (a login or a group), enforces constraints, can run code in
**triggers**, and keeps data safe with transactions.

## Why this repository uses it

The controls under test are database controls: least-privilege roles, an audit log that the database itself refuses to alter, a
backup that is restored and counted. Those need a real server, not a stand-in. The server runs in a container, so nothing is
installed on the laptop.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `docker-compose.yml` | The `db` service: image `postgres:18`, a health check, a localhost port. |
| `sql/001_schema.sql` | Roles, tables, constraints, the audit trigger, grants. |
| `sql/002_seed.sql` | Four accounts and 12,400 synthetic notes. |
| `sql/003_queries.sql` | The queries behind the evidence. |
| `src/notes_evidence/infrastructure/postgres.py` | The client side (see `psycopg.md`). |
| `src/notes_evidence/infrastructure/backup.py` | `pg_dump` and `pg_restore` (see `postgresql-tools.md`). |

## How it works underneath

- The server process (`postgres`) listens on port 5432 inside the container. Compose publishes it on the host's
  `127.0.0.1:55440` only.
- A **cluster** holds **databases**; a database holds **schemas** (`public`) which hold **tables**. Each connection logs in as one
  **role**; every statement is checked against that role's **grants**.
- A **transaction** makes a group of statements atomic. The write-ahead log makes committed data survive a crash.
- A **trigger** is a function the server runs automatically before or after a change. This repository's trigger refuses updates
  and truncates of the audit log.
- Data lives in the container's volume. `docker compose down -v` removes the volume, which is why `make down` deletes the data.

## Walkthrough of this repository's use

`docker-compose.yml`:

```yaml
  db:
    image: postgres:18
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?set it in .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set it in .env}
      POSTGRES_DB: ${POSTGRES_DB:-notes}
    ports:
      - "127.0.0.1:${POSTGRES_PORT:-55440}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 10s
      retries: 60
      start_period: 30s
```

Key by key:
- `image: postgres:18`: the official image, major version 18.
- `environment:` sets `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB`. `${POSTGRES_USER:?set it in .env}` is Compose
  interpolation: use the variable, and **stop with that message** if it is not set. `${POSTGRES_DB:-notes}` uses the variable or
  the default `notes`.
- `ports: "127.0.0.1:${POSTGRES_PORT:-55440}:5432"`: host address and port, then the container's port. Binding to `127.0.0.1`
  keeps the database off the network.
- `healthcheck` runs `pg_isready` every 5 s (timeout 10 s) up to 60 times, after a 30 s start period; Compose marks the service
  **healthy** when it passes. `$${POSTGRES_USER}` (double dollar) stops Compose from replacing the variable, so the shell inside the
  container does.

`Makefile`:

```make
up: env $(STAMP) ## start PostgreSQL and apply sql/001_schema.sql and sql/002_seed.sql
	docker compose up -d --wait --wait-timeout 900 db
	$(MAKE) --no-print-directory db
```

`docker compose up -d --wait --wait-timeout 900 db`: start the service in the background (`-d`), and **wait** (`--wait`) until it is
healthy, for at most 900 seconds (a patient limit chosen after a loaded machine timed out). Then `make db` applies the SQL files
(see `sql.md`).

`Makefile`:

```make
reset-db: ## drop the public schema and rebuild it from the SQL scripts
	$(PSQL) < sql/reset.sql
	$(MAKE) --no-print-directory db
```

`reset-db` drops the whole `public` schema and rebuilds it from the SQL files, which is how `make run` starts clean.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
make up
```
Starts the database, waits until it is healthy, and applies the schema and seed.

```bash
docker compose exec -T db psql -U postgres -d notes -c "SELECT count(*) FROM notes;"
```
Prints a table with `12400`.

```bash
docker compose exec -T db psql -U postgres -d notes -c "\du"
```
Lists the roles: `app_rw`, `audit_retention`, `migrator` and the superuser `postgres`.

```bash
docker compose exec -T db psql -U postgres -d notes -c "UPDATE audit_log SET outcome = 'ok';"
```
Prints `ERROR:  audit_log is append-only: UPDATE is not allowed`, even for the superuser: the trigger refuses it.

```bash
make down
```
Stops the container and removes its volume.

## Mistakes people make

- **Publishing the database port on all interfaces.** It is bound to `127.0.0.1`.
- **Using the superuser for the application.** The API connects as `app_rw`.
- **Putting real passwords in `.env.example`.** The values there are throwaway development passwords for a database that lives only
  while the container runs.
- **Starting tests before the server is ready.** `--wait` waits for the health check.
- **Forgetting the data is in a volume.** `down -v` deletes it.

## Check yourself

1. What is a role in PostgreSQL?
   **Answer:** A login or a group that has grants on database objects.
2. What does `--wait` do in `docker compose up -d --wait`?
   **Answer:** Waits until the service's health check passes.
3. What is a trigger?
   **Answer:** A function the server runs automatically before or after a change.
4. Why `127.0.0.1:55440:5432`?
   **Answer:** The host port is reachable only from this machine, and maps to the container's 5432.
5. What does `down -v` remove that `down` alone keeps?
   **Answer:** The data volume.

## Further reading

- PostgreSQL 18 documentation: <https://www.postgresql.org/docs/18/>
- Database roles: <https://www.postgresql.org/docs/18/user-manag.html>
- Triggers: <https://www.postgresql.org/docs/18/triggers.html>
- Official Docker image: <https://hub.docker.com/_/postgres>
