# gunicorn 26

## What it is

gunicorn ("Green Unicorn") is a **WSGI HTTP server**: a program that listens on a port, receives HTTP requests, and hands each to
a Python web application (here Flask) through the WSGI interface. Flask's own development server is for development only;
gunicorn is built to run real services, with several worker processes and graceful shutdown.

## Why this repository uses it

The API is shipped as a container image whose process must handle several requests, restart cleanly, and stop gracefully on a
signal. gunicorn does that with a few flags.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Dockerfile` | `CMD ["gunicorn", ...]`. |
| `Makefile` `serve` | Runs gunicorn on localhost. |
| `pyproject.toml` | `gunicorn>=23`. |
| `requirements.lock` | `gunicorn==26.2.0`. |

## How it works underneath

gunicorn starts a **master** process that starts **worker** processes (here 2). Each synchronous worker takes one request at a
time. The master restarts a worker that dies and, on `SIGTERM` (what Docker sends to stop a container), tells workers to finish
current requests within `--graceful-timeout` and exit. `module:name` (`notes_evidence.interfaces.wsgi:app`) says where to find the
WSGI application object. A worker is a separate process, so each opens its own database connection.

## Walkthrough of this repository's use

`Makefile`:

```make
serve: $(STAMP) ## run the notes API with gunicorn on localhost (needs make up)
	$(VENV)/bin/gunicorn --bind 127.0.0.1:$(HTTP_PORT) --workers 2 notes_evidence.interfaces.wsgi:app
```

- `--bind 127.0.0.1:$(HTTP_PORT)`: listen only on the local machine, on the port from `.env` (8080).
- `--workers 2`: two worker processes.
- `notes_evidence.interfaces.wsgi:app`: import the module and use the object `app` (see `flask.md`).

`Dockerfile`:

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "--graceful-timeout", "20", "--no-control-socket", "notes_evidence.interfaces.wsgi:app"]
```

In the container the same command is written as a JSON list (the **exec form**, so gunicorn is process 1 and receives signals
directly):
- `--bind 0.0.0.0:8080`: listen on all interfaces **inside the container**; the compose file publishes the port on the host's
  `127.0.0.1` only.
- `--timeout 30`: kill and restart a worker that is silent for 30 seconds.
- `--graceful-timeout 20`: on a stop signal, give workers 20 seconds to finish.
- `--no-control-socket`: do not create gunicorn's control socket file. The container's file system is read-only, so the file
  could not be created (a fix found during verification).

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
make up && make serve
```
Starts gunicorn on `127.0.0.1:8080`; the log shows `Listening at: http://127.0.0.1:8080` and two `Booting worker` lines.

```bash
curl -s http://127.0.0.1:8080/healthz; echo
```
In another terminal. Prints `{"status":"ok"}`.

```bash
.venv/bin/gunicorn --version
```
Prints `gunicorn (version 26.2.0)`.

```bash
.venv/bin/gunicorn --help | grep -A1 -- "--no-control-socket"
```
Shows the option for the pinned version.

## Mistakes people make

- **Using the Flask development server in production.**
- **Binding to `0.0.0.0` on a laptop**, which exposes the port. `make serve` binds to `127.0.0.1`.
- **Too few or too many workers.** Two is a small default; a rule of thumb is 2 to 4 per CPU core.
- **Forgetting the timeout.** A stuck request would hold a worker forever.
- **Shell-form `CMD`**, where a shell becomes process 1 and signals do not reach gunicorn.

## Check yourself

1. What is a WSGI server?
   **Answer:** A program that receives HTTP requests and passes them to a Python web app through the WSGI interface.
2. What does `notes_evidence.interfaces.wsgi:app` mean?
   **Answer:** Import that module and use the object named `app`.
3. What does `--graceful-timeout` control?
   **Answer:** How long workers get to finish current requests after a stop signal.
4. Why is `--no-control-socket` used?
   **Answer:** The read-only container file system cannot hold the socket file.
5. Why is the exec form of `CMD` better?
   **Answer:** gunicorn receives stop signals directly.

## Further reading

- gunicorn 26 documentation: <https://docs.gunicorn.org/en/stable/>
- Settings: <https://docs.gunicorn.org/en/stable/settings.html>
- Deploying Flask with gunicorn: <https://flask.palletsprojects.com/en/stable/deploying/gunicorn/>
