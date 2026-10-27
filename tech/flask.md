# Flask 3.1

## What it is

Flask is a small Python **web framework**: it receives HTTP requests, finds the function registered for the path (a **route**),
calls it, and turns the return value into an HTTP response. It follows the **WSGI** standard, so any WSGI server (here gunicorn) can
run it.

## Why this repository uses it

The notes API needs about eight routes, a JSON error mapping and request logging. Flask does that with very little code, and the
repository keeps Flask out of the rules: `http_app.py` only translates between HTTP and the service.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/interfaces/http_app.py` | `create_app` builds the `Flask` object and registers routes and handlers. |
| `src/notes_evidence/interfaces/wsgi.py` | Creates the app for gunicorn. |
| `pyproject.toml` | `flask>=3.1,<4`. |
| `requirements.lock` | `flask==3.1.3`. |
| `tests/unit/interfaces/test_http_app.py` | Uses Flask's test client. |

## How it works underneath

`Flask(__name__)` makes an application object. A decorator such as `@app.get("/notes")` registers the function under that path
and method. For each request Flask builds a `request` object (available as a global that is safe per request), runs the
`before_request` hooks, the route function, and the `after_request` hooks, then sends the response. If the route raises an
exception, Flask looks for a registered **error handler** for that exception class. `g` is a per-request scratch space.
`jsonify(...)` builds a JSON response. A function can return `(response, status)`.

## Walkthrough of this repository's use

`src/notes_evidence/interfaces/http_app.py`:

```python
def create_app(service: NotesService, ping: Callable[[], bool]) -> Flask:
    """Build the Flask app around a service and a database ping."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES
```

`create_app` is an **application factory**: a function that builds the app from its parts (`service`, `ping`), so tests can build one
with fakes. `app.config["MAX_CONTENT_LENGTH"]` makes Flask refuse bodies over 64 KiB with `413`.

`src/notes_evidence/interfaces/http_app.py`:

```python
    @app.before_request
    def start_timer() -> None:
        g.started = time.monotonic()

    @app.after_request
    def finish(response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": int((time.monotonic() - g.get("started", time.monotonic())) * 1000),
            },
        )
        return response
```

- `@app.before_request` and `@app.after_request` are hooks that run around every request.
- `g.started = time.monotonic()` stores the start time for this request only.
- The after hook adds two safe headers (`X-Content-Type-Options: nosniff`, `Cache-Control: no-store`) and logs one line.

`src/notes_evidence/interfaces/http_app.py`:

```python
    @app.get("/healthz")
    def healthz() -> tuple[Response, int]:
        healthy = ping()
        return jsonify(status="ok" if healthy else "database unavailable"), 200 if healthy else 503
```

A route returns `(jsonify(...), 200 or 503)`: the health check answers 503 when the database ping fails.

`src/notes_evidence/interfaces/http_app.py`:

```python
    @app.post("/notes")
    def create_note() -> tuple[Response, int]:
        data = _payload()
        return jsonify(_note_json(service.create_note(actor(), data.get("title"), data.get("body")))), 201
```

`@app.post("/notes")` handles `POST /notes`; the tuple's second element, `201`, is the status.

`src/notes_evidence/interfaces/http_app.py`:

```python
    @app.errorhandler(Exception)
    def unexpected(problem: Exception) -> tuple[Response, int]:
        logger.error("unhandled %s", type(problem).__name__)
        return answer(500, "internal error")
```

The catch-all error handler logs only the **class name** of an unexpected error (`type(problem).__name__`), never its message, and
answers `500 internal error`.

`src/notes_evidence/interfaces/wsgi.py`:

```python
app = create()
```

The module-level name `app` is what gunicorn imports (`notes_evidence.interfaces.wsgi:app`).

## Try it yourself

```bash
.venv/bin/python - <<'EOF'
from notes_evidence.interfaces.http_app import create_app
app = create_app(None, lambda: True)   # the health route needs no service
client = app.test_client()
r = client.get("/healthz")
print(r.status_code, r.get_json(), r.headers["Cache-Control"])
print(client.get("/nothing").status_code, client.get("/nothing").get_json())
EOF
```
Prints `200 {'status': 'ok'} no-store` and `404 {'error': 'not found'}`.

```bash
.venv/bin/python -c "from importlib import metadata; print(metadata.version('flask'))"
```
Prints `3.1.3`.

```bash
.venv/bin/python -c "from notes_evidence.interfaces.http_app import create_app; a = create_app(None, lambda: True); print(sorted(str(r) for r in a.url_map.iter_rules())[:4])"
```
Lists some registered routes.

```bash
.venv/bin/pytest -q tests/unit/interfaces/test_http_app.py
```
Runs the tests that drive the app through Flask's test client (no network, no database).

## Mistakes people make

- **Putting rules in the route functions.** Here they only call the service.
- **Returning error details from a catch-all handler.** The handler logs the class name and answers a fixed message.
- **Running `flask run` in production.** Use a WSGI server (gunicorn).
- **Debug mode in production.** It exposes an interactive console; this repository never enables it.
- **Reading `request` outside a request.** It only exists while a request is being handled.

## Check yourself

1. What is an application factory?
   **Answer:** A function that builds the app from its parts, so tests can pass fakes.
2. What does `@app.errorhandler(NotFoundError)` do?
   **Answer:** Registers a function that turns that exception into a response.
3. What is `g`?
   **Answer:** A per-request scratch space.
4. What does `MAX_CONTENT_LENGTH` do?
   **Answer:** Makes Flask refuse larger request bodies with `413`.
5. What is WSGI?
   **Answer:** The standard interface between Python web apps and servers like gunicorn.

## Further reading

- Flask 3.1 documentation: <https://flask.palletsprojects.com/en/stable/>
- Application factories: <https://flask.palletsprojects.com/en/stable/patterns/appfactories/>
- Testing: <https://flask.palletsprojects.com/en/stable/testing/>
