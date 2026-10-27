# Docker

## What it is

A **container** is a running program that sees its own private file system and network, built from an **image** (a packaged
file system plus a start command). Docker is the tool that builds images and runs containers. Unlike a virtual machine, a container
shares the host's kernel, so it starts in seconds. **Docker Compose** describes several containers in one file (`docker-compose.yml`).

## Why this repository uses it

The lesson needs a real PostgreSQL, and the API should run the way it would in production: a pinned image, a non-root user, a
read-only file system, a health check. Docker gives both without installing a database on the laptop.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `docker-compose.yml` | Two services: `db` (PostgreSQL) and `api` (behind the `api` profile). |
| `Dockerfile` | How the API image is built (see `dockerfile.md`). |
| `.dockerignore` | What is left out of the build context. |
| `Makefile` | `up`, `api-up`, `docker-build`, `down`, `smoke`. |
| .github/workflows/ci.yml | The `integration` job uses Docker on the CI runner. |

## How it works underneath

- An **image** is made of read-only **layers**, one per Dockerfile instruction. Layers are cached, so an unchanged step is not
  rebuilt.
- A **container** adds a thin writable layer on top and runs one main process (**process 1**). When that process exits, the
  container stops.
- A **volume** is storage that outlives the container; the database's data lives in one.
- Docker uses Linux features (namespaces for isolation, cgroups for limits). On a Mac, Docker Desktop runs a small Linux
  virtual machine to host them, which is why its memory and CPU limits matter.
- The **build context** is the folder sent to the builder; `.dockerignore` removes files from it.

## Walkthrough of this repository's use

`.dockerignore`:

```
.git
.venv
.env
state
build
evidence
tests
fixtures
**/__pycache__
.mypy_cache
.ruff_cache
.pytest_cache
.coverage
.omc
```

Everything the image does not need is left out of the build context: git history, the virtualenv, `.env` (so secrets never enter
an image), generated state, the evidence folder, the tests and the fixtures, plus caches. A smaller context builds faster and
cannot leak files.

`Makefile`:

```make
api-up: ## build the image and start the API container beside the database
	docker compose --profile api up -d --build --wait api
```

`Makefile`:

```make
docker-build: ## build the API image
	docker build -t compliance-controls-and-evidence:dev .
```

- `docker compose --profile api up -d --build --wait api`: start the `api` service, which is behind the `api` **profile** (so a plain
  `make up` does not start it), building the image first (`--build`) and waiting for its health check.
- `docker build -t compliance-controls-and-evidence:dev .` builds the image from the `Dockerfile` in this folder and tags it.

`Makefile`:

```make
down: ## stop PostgreSQL and delete its data and the generated state
	docker compose --profile api down -v
	rm -rf state build
```

`docker compose --profile api down -v` stops and removes the containers and the volume (`-v`). Nothing stays running between
verifications.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
docker --version && docker compose version
```
Prints the client versions.

```bash
docker compose ps
```
Lists this project's containers and their state (`healthy` for the database after `make up`).

```bash
docker compose logs db | tail -5
```
Shows the last lines the PostgreSQL container printed.

```bash
docker image ls compliance-controls-and-evidence
```
After `make docker-build`, lists the image `compliance-controls-and-evidence:dev` and its size.

```bash
make down
```
Removes the containers and the data volume.

## Mistakes people make

- **Leaving containers running** on a shared machine. `make down` ends every verification.
- **Putting `.env` or other secrets into an image.** `.dockerignore` excludes them.
- **Running as root inside the container.** The API runs as an unprivileged user.
- **Using `latest` tags.** The base image is pinned by version and digest (see `dockerfile.md`).
- **Forgetting that data in a container is lost** unless it is in a volume.

## Check yourself

1. What is the difference between an image and a container?
   **Answer:** An image is a packaged file system and start command; a container is a running instance of it.
2. What does `.dockerignore` do?
   **Answer:** Removes files from the build context.
3. What is a Compose profile?
   **Answer:** A label that makes a service start only when that profile is requested.
4. What does `down -v` remove?
   **Answer:** The containers and their volumes.
5. Why does a container stop when its main process exits?
   **Answer:** The container exists to run that one process.

## Further reading

- Docker documentation: <https://docs.docker.com/>
- Docker Compose file reference: <https://docs.docker.com/reference/compose-file/>
- `.dockerignore`: <https://docs.docker.com/build/concepts/context/#dockerignore-files>
