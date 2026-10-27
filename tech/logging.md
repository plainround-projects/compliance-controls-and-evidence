# logging

## What it is

`logging` is Python's standard way to record what a program does. Code asks for a **logger** by name, calls `logger.info(...)` or
`logger.warning(...)`, and **handlers** send each **record** somewhere (the screen, a file). A **formatter** decides what the line
looks like. The level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) decides which records are kept.

## Why this repository uses it

Control C3 needs a log sample and an alert. The API writes one structured line per request and the audit trail records who did
what; the alert stand-in logs a `WARNING`. Logs are JSON so tools (and the verifier) can read them, and they never contain secrets
or note text.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/infrastructure/logging_setup.py` | `JsonFormatter` and `configure_logging`. |
| `src/notes_evidence/interfaces/http_app.py` | `logger.info("request", extra={...})` after every request. |
| `src/notes_evidence/infrastructure/alerting.py` | `logger.warning("%s", message)` for each alert. |
| `src/notes_evidence/interfaces/wsgi.py` | Calls `configure_logging(settings.log_level)` at start-up. |
| `.env.example` | `LOG_LEVEL=INFO`. |

## How it works underneath

`logging.getLogger("notes.http")` returns the logger of that name (the dots make a tree). A record travels from the logger to the
handlers of the **root** logger. `extra={...}` adds fields to the record as attributes. `record.getMessage()` fills the `%s`
placeholders. `StreamHandler(sys.stdout)` writes lines to standard output, which Docker collects as the container's log.

## Walkthrough of this repository's use

`src/notes_evidence/infrastructure/logging_setup.py`:

```python
_SAFE_FIELDS = ("method", "path", "status", "user_id", "duration_ms")
```

`src/notes_evidence/infrastructure/logging_setup.py`:

```python
class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a record; only the whitelisted extra fields are included."""
        document = {
            "time": datetime.fromtimestamp(record.created, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})
        return json.dumps(document)
```

- `format` receives the record and returns the line. The time comes from `record.created` (seconds since 1970), turned into UTC.
- `document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})` copies a field only if it
  is on the whitelist and the record has it. `getattr` and `hasattr` read an attribute by name.

`src/notes_evidence/infrastructure/logging_setup.py`:

```python
def configure_logging(level: str) -> None:
    """Send JSON logs to stdout at the given level."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
```

`root.handlers[:] = [handler]` replaces all handlers with this one; `root.setLevel(level)` sets the threshold.

`src/notes_evidence/interfaces/http_app.py`:

```python
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

After every request one line is logged with the method, path, status and duration. No header, body or token is logged.

`src/notes_evidence/infrastructure/alerting.py`:

```python
    def send(self, message: str) -> None:
        """Deliver one alert."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(message + "\n")
```

The alert is written to a file and logged at `WARNING`. In a real system this is where a chat message or a page would be sent.

## Try it yourself

```bash
.venv/bin/python - <<'EOF'
import logging
from notes_evidence.infrastructure.logging_setup import configure_logging
configure_logging("INFO")
logging.getLogger("notes.http").info("request", extra={"method": "GET", "path": "/notes", "status": 200, "password": "hidden"})
EOF
```
Prints one JSON line with `time`, `level`, `logger`, `message`, `method`, `path`, `status`. The extra `password` field is **not** printed.

```bash
.venv/bin/python -c "import logging; print(logging.getLevelName(30), logging.WARNING)"
```
Prints `WARNING 30`.

```bash
head -3 evidence/C3-alert-test.txt
```
Shows the alert artifact.

```bash
.venv/bin/pytest -q -k "log" tests/unit
```
Runs the tests about log formatting and the whitelist.

## Mistakes people make

- **Logging secrets, tokens or personal data.** The whitelist prevents it.
- **Building the message with an f-string** instead of `%s` placeholders; the logger can skip the work when the level is off.
- **Configuring logging in a library.** Only the entry point (`wsgi.py`, `cli.py`) configures it.
- **Forgetting the level**: `INFO` lines vanish when the level is `WARNING`.

## Check yourself

1. What is a handler and what is a formatter?
   **Answer:** A handler sends records somewhere; a formatter decides how a record looks.
2. Why are only some `extra` fields printed?
   **Answer:** A whitelist stops anything else from leaking into the log.
3. Where do the container's logs go?
   **Answer:** To standard output, which Docker collects.
4. What does `extra={...}` do?
   **Answer:** It adds fields to the record as attributes.
5. What level is an alert logged at?
   **Answer:** `WARNING`.

## Further reading

- `logging` (Python 3.12): <https://docs.python.org/3.12/library/logging.html>
- Logging HOWTO: <https://docs.python.org/3.12/howto/logging.html>
