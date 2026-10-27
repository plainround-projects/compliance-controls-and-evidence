# Docker Compose

## What it is

Docker Compose reads one YAML file (`docker-compose.yml`) that lists **services** (containers), their images, ports, environment,
volumes and start order, and starts them together with `docker compose up`. A **profile** makes a service optional.

## Why this repository uses it

The database must be up and healthy before anything else, the API should wait for it, and both should be configured from `.env`.
One file captures all of that and also records the API's hardening settings.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `docker-compose.yml` | Services `db` and `api`. |
| `.env` / `.env.example` | The values Compose substitutes (`POSTGRES_*`, `APP_RW_PASSWORD`, `NOTES_SECRET`, `HTTP_PORT`). |
| `Makefile` | `up`, `api-up`, `down`. |

## How it works underneath

Compose reads `.env` from the project folder to fill `${VARIABLE}` placeholders, then asks the Docker engine to create a network,
a volume if needed, and the containers. `depends_on` with `condition: service_healthy` makes a service wait for another's health
check. Services reach each other by name on the private network (`db:5432`).

## Walkthrough of this repository's use

(The `db` service is explained key by key in `postgresql.md`.)

`docker-compose.yml`:

```yaml
  api:
    profiles: ["api"]
    build: .
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://app_rw:${APP_RW_PASSWORD:?set it in .env}@db:5432/${POSTGRES_DB:-notes}
      NOTES_SECRET: ${NOTES_SECRET:?set it in .env}
      HTTP_PORT: "8080"
    ports:
      - "127.0.0.1:${HTTP_PORT:-8080}:8080"
    read_only: true
    tmpfs: ["/tmp"]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
```

- `profiles: ["api"]`: the service starts only with `--profile api`.
- `build: .`: build the image from the `Dockerfile` in this folder (see `dockerfile.md`).
- `depends_on: db: condition: service_healthy`: start only after the database reports healthy.
- `environment:` passes `DATABASE_URL` (note the host `db`, the service name), `NOTES_SECRET` and `HTTP_PORT`.
  `${APP_RW_PASSWORD:?set it in .env}` stops with that message if the variable is missing.
- `ports: "127.0.0.1:${HTTP_PORT:-8080}:8080"`: reachable only from this machine.
- `read_only: true`: the container's root file system cannot be written to.
- `tmpfs: ["/tmp"]`: but `/tmp` is an in-memory scratch folder, which programs like gunicorn need.
- `cap_drop: [ALL]`: remove every Linux capability (special privileges) from the process.
- `security_opt: ["no-new-privileges:true"]`: the process can never gain privileges, for example through a setuid program.

### The complete file `docker-compose.yml`, line by line

`docker-compose.yml` lines 1 to 31:

```yaml
services:
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
  api:
    profiles: ["api"]
    build: .
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://app_rw:${APP_RW_PASSWORD:?set it in .env}@db:5432/${POSTGRES_DB:-notes}
      NOTES_SECRET: ${NOTES_SECRET:?set it in .env}
      HTTP_PORT: "8080"
    ports:
      - "127.0.0.1:${HTTP_PORT:-8080}:8080"
    read_only: true
    tmpfs: ["/tmp"]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
```

> **In plain words.** YAML is a settings format that uses indentation (spaces, never tabs) to show what belongs to what. `key: value` sets a value, `- item` is one entry of a list, `&name` names a block and `*name` reuses it, and `#` starts a comment.

- A setting `services` (the containers) starts a group; the more indented lines below belong to it.
- A setting `db` starts a group; the more indented lines below belong to it.
- A setting `image` (the image to run) is `postgres:18`.
- A setting `environment` (environment variables) starts a group; the more indented lines below belong to it.
- A setting `POSTGRES_USER` is `${POSTGRES_USER:?set it in .env}`.
- A setting `POSTGRES_PASSWORD` is `${POSTGRES_PASSWORD:?set it in .env}`.
- A setting `POSTGRES_DB` is `${POSTGRES_DB:-notes}`.
- A setting `ports` (ports to publish) starts a group; the more indented lines below belong to it.
- A list item `"127.0.0.1:${POSTGRES_PORT:-55440}:5432"`.
- A setting `healthcheck` (how to test that the container is healthy) starts a group; the more indented lines below belong to it.
- A setting `test` (the health command) is `["CMD-SHELL", "pg_isready -h 127.0.0.1 -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]`.
- A setting `interval` (time between checks) is `5s`.
- A setting `timeout` (time allowed for one check) is `10s`.
- A setting `retries` (failures allowed in a row) is `60`.
- A setting `start_period` (grace time after start) is `30s`.
- A setting `api` starts a group; the more indented lines below belong to it.
- A setting `profiles` (the profiles this service belongs to) is `["api"]`.
- A setting `build` (build the image from this folder) is `.`.
- A setting `depends_on` (start after these services) starts a group; the more indented lines below belong to it.
- A setting `db` starts a group; the more indented lines below belong to it.
- A setting `condition` (what to wait for) is `service_healthy`.
- A setting `environment` (environment variables) starts a group; the more indented lines below belong to it.
- A setting `DATABASE_URL` is `postgresql://app_rw:${APP_RW_PASSWORD:?set it in .env}@db:5432/${POSTGRES_DB:-notes}`.
- A setting `NOTES_SECRET` is `${NOTES_SECRET:?set it in .env}`.
- A setting `HTTP_PORT` is `"8080"`.
- A setting `ports` (ports to publish) starts a group; the more indented lines below belong to it.
- A list item `"127.0.0.1:${HTTP_PORT:-8080}:8080"`.
- A setting `read_only` (make the root file system read-only) is `true`.
- A setting `tmpfs` (in-memory scratch folders) is `["/tmp"]`.
- A setting `cap_drop` (Linux capabilities to remove) is `[ALL]`.
- A setting `security_opt` (extra security options) is `["no-new-privileges:true"]`.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
docker compose config --quiet && echo "compose file is valid"
```
Checks the YAML and the variables (it needs `.env`; run `make env` first).

```bash
docker compose config | sed -n 1,12p
```
Prints the file with every variable replaced.

```bash
docker compose --profile api config --services
```
Prints the two service names, `db` and `api`.

```bash
make api-up && docker compose exec -T api id
```
Prints `uid=10001(app) ...`.

```bash
docker compose exec -T api sh -c 'touch /app/x' ; echo "exit: $?"
```
Prints an error `Read-only file system` and `exit: 1`.

## Mistakes people make

- **Real secrets in `docker-compose.yml`.** Values come from `.env`; missing ones stop the run.
- **Publishing ports on all interfaces.** These bind to `127.0.0.1`.
- **`depends_on` without a health condition**, so the API starts before the database can answer.
- **Forgetting `-v` on `down`**, leaving an old volume with old data.
- **A writable root file system** where it is not needed. `read_only: true` limits what a compromise can change.

## Check yourself

1. What does `condition: service_healthy` do?
   **Answer:** Waits for the other service's health check to pass.
2. What does `${VAR:?message}` do?
   **Answer:** Uses the variable, or stops with the message if it is not set.
3. What does `cap_drop: [ALL]` do?
   **Answer:** Removes all Linux capabilities from the container process.
4. Why `tmpfs: ["/tmp"]` together with `read_only: true`?
   **Answer:** The root file system is read-only, but programs still need a writable scratch folder.
5. How does the API reach the database?
   **Answer:** By the service name: `db:5432` on Compose's private network.

## Further reading

- Compose file reference: <https://docs.docker.com/reference/compose-file/>
- Services: <https://docs.docker.com/reference/compose-file/services/>
- Interpolation: <https://docs.docker.com/reference/compose-file/interpolation/>
