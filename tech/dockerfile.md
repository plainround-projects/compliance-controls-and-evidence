# Dockerfile

## What it is

A **Dockerfile** is a text file of instructions that `docker build` follows to make an image. Each instruction (`FROM`, `COPY`,
`RUN`, ...) adds a layer. The last instructions say how the container starts (`CMD`) and how to check that it is healthy
(`HEALTHCHECK`).

## Why this repository uses it

The API image is part of the evidence: it shows how the service is built to run safely. A pinned base image, hash-checked
dependencies, an unprivileged user, a health check and graceful shutdown are all in this one short file.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Dockerfile` | The only one. |
| `docker-compose.yml` | `build: .` builds it for the `api` service. |
| `Makefile` `docker-build` | Builds and tags it. |
| `.dockerignore` | Controls what `COPY` can see. |

## How it works underneath

`docker build` sends the build context to the builder, then runs the instructions in order. Each produces a layer; if the
instruction and the files it uses have not changed, Docker reuses the cached layer. So **order matters**: put what changes
rarely (the dependency list) before what changes often (the source). The result is an image; `docker run` or Compose starts a
container from it.

## Walkthrough of this repository's use

`Dockerfile`:

```dockerfile
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
```

`FROM image@sha256:...` chooses the base: Python 3.12.8 on Debian bookworm, slim variant. The `@sha256:` **digest** pins the exact
image, so a later change to the tag cannot change the build.

`Dockerfile`:

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

`ENV` sets environment variables for the build and the container: `PYTHONDONTWRITEBYTECODE=1` stops Python writing `.pyc`
files (the file system is read-only at run time), `PYTHONUNBUFFERED=1` sends output at once so logs appear immediately, and the
two `PIP_` settings keep pip quiet and its cache out of the image. The `\` joins lines.

`Dockerfile`:

```dockerfile
WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock
```

`WORKDIR /app` sets the working folder. The dependency list is copied **first**, and installed with `--require-hashes`, so the
install layer is rebuilt only when `requirements.lock` changes.

`Dockerfile`:

```dockerfile
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .
```

Then the project: `pyproject.toml`, `README.md` (the packaging reads it) and `src`. `pip install --no-deps .` installs only the project
itself.

`Dockerfile`:

```dockerfile
RUN useradd --system --uid 10001 --no-create-home app
USER app
```

`useradd --system --uid 10001 --no-create-home app` creates an unprivileged user with a fixed id and no home folder. `USER app`
makes every later instruction, and the running container, use it: the process cannot act as root.

`Dockerfile`:

```dockerfile
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["notes-api-health"]
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "--graceful-timeout", "20", "--no-control-socket", "notes_evidence.interfaces.wsgi:app"]
```

- `EXPOSE 8080` documents the port the app listens on.
- `HEALTHCHECK --interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["notes-api-health"]`: Docker runs the check every 30 s,
  waits up to 20 s for it, ignores failures for the first 30 s, and marks the container unhealthy after 3 failures in a row. The command
  is the small Python program in `interfaces/health.py` (see `argparse.md`), so the image needs no `curl`.
- `CMD [...]` is the start command (see `gunicorn.md`), in exec form.

### The complete file `Dockerfile`, line by line

`Dockerfile` lines 1 to 2:

```dockerfile
# The notes API as an image: pinned base, hash-pinned dependencies, a non-root user, a health check, graceful shutdown by gunicorn.
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
```

> **In plain words.** A Dockerfile is a list of instructions that `docker build` runs in order to make an **image**: a packaged file system plus a start command. Each instruction adds a **layer**, and Docker reuses a layer when nothing it depends on changed, so the order matters.

- `FROM` starts the image from this base image (the `@sha256:` part pins the exact version): `python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0`.

`Dockerfile` lines 4 to 7:

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

- `ENV` sets environment variables for the build and for the running container: `PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1`. `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `PIP_NO_CACHE_DIR=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1`.

`Dockerfile` lines 9 to 11:

```dockerfile
WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock
```

- `WORKDIR` sets the folder that later instructions run in: `/app`.
- `COPY` copies files from the build folder into the image: `requirements.lock ./`.
- `RUN` runs a command while the image is built: `pip install --require-hashes -r requirements.lock`. It runs pip, the package installer, subcommand `install` with `--require-hashes` (refuse any package without a pinned hash), `-r requirements.lock` (read the list from the named file).

`Dockerfile` lines 13 to 15:

```dockerfile
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .
```

- `COPY` copies files from the build folder into the image: `pyproject.toml README.md ./`.
- `COPY` copies files from the build folder into the image: `src ./src`.
- `RUN` runs a command while the image is built: `pip install --no-deps .`. It runs pip, the package installer, subcommand `install` with `--no-deps` (do not install or resolve dependencies), `.`.

`Dockerfile` lines 17 to 18:

```dockerfile
RUN useradd --system --uid 10001 --no-create-home app
USER app
```

- `RUN` runs a command while the image is built: `useradd --system --uid 10001 --no-create-home app`. It runs useradd, which creates an operating-system user with `--system` (a system account), `--uid 10001` (numeric user id), `--no-create-home` (do not create a home folder), `app`.
- `USER` makes later instructions and the running container use this user: `app`.

`Dockerfile` lines 20 to 22:

```dockerfile
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["notes-api-health"]
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "--graceful-timeout", "20", "--no-control-socket", "notes_evidence.interfaces.wsgi:app"]
```

- `EXPOSE` documents the port the app listens on: `8080`.
- `HEALTHCHECK` tells Docker how to test that the container works: `--interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["notes-api-health"]`. `--interval` is the time between checks, `--timeout` how long one may take, `--start-period` the grace time after start, `--retries` the failures allowed in a row.
- `CMD` sets the command that runs when a container starts: `["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "--graceful-timeout", "20", "--no-control-socket", "notes_evide…`. The JSON list form (exec form) runs the program directly, with no shell in between.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
make docker-build
```
Builds the image; the last lines show `naming to docker.io/library/compliance-controls-and-evidence:dev`.

```bash
docker run --rm --entrypoint id compliance-controls-and-evidence:dev
```
Prints `uid=10001(app) gid=10001(app) ...`: the image runs as the unprivileged user.

```bash
docker history compliance-controls-and-evidence:dev | head -8
```
Lists the layers, newest first, one per instruction.

```bash
grep -n "^[A-Z]" Dockerfile
```
Lists the instructions (this one needs no Docker).

```bash
make api-up && make smoke && docker compose ps
```
Starts the API beside the database; `smoke` prints `{"status":"ok"}` and `ps` shows `api` as `healthy`.

## Mistakes people make

- **Copying the source before installing dependencies**, which makes every code change reinstall everything.
- **Using a moving tag** (`python:3.12`). A digest pins the exact image.
- **Running as root.** The image creates and switches to a user.
- **Installing build tools or `curl` just for a health check.** A tiny Python program does the check.
- **Shell-form `CMD`.** Exec form makes gunicorn process 1 so it gets the stop signal.

## Check yourself

1. Why is `requirements.lock` copied before `src`?
   **Answer:** So the dependency layer is cached and rebuilt only when the lock file changes.
2. What does the `@sha256:` part of `FROM` do?
   **Answer:** Pins the exact image, whatever the tag points to later.
3. What does `USER app` change?
   **Answer:** Later instructions and the running container use the unprivileged user.
4. What does `HEALTHCHECK` do?
   **Answer:** Runs a command on a schedule and marks the container healthy or unhealthy.
5. Why `--require-hashes` in the image build?
   **Answer:** Only the exact, hash-checked packages of the lock file are installed.

## Further reading

- Dockerfile reference: <https://docs.docker.com/reference/dockerfile/>
- Build best practices: <https://docs.docker.com/build/building/best-practices/>
- Official Python image: <https://hub.docker.com/_/python>
