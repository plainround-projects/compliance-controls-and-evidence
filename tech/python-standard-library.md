# The Python standard library modules this repository imports

## What it is

The **standard library** is the set of modules that come with Python itself. You `import` them; nothing is downloaded. This note
covers the smaller modules together. The bigger ones have their own notes: `dataclasses.md`, `re.md`, `argparse.md`,
`pathlib.md`, `json.md`, `csv.md`, `logging.md`, `subprocess.md`, `hashing-and-signing.md` (hashlib, hmac, secrets, scrypt),
`tomllib.md`.

## Why this repository uses it

Most of what the service and the evidence tool need is in the standard library (hashing, JSON, CSV, logging, processes). Three
packages are added only where Python has no equivalent: Flask for HTTP, gunicorn to run it, and psycopg for PostgreSQL.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `enum` | `Role`, `Permission`, `AuditAction`, `Severity`. |
| `typing.Protocol` | The interfaces in `application/ports.py`. |
| `contextlib` | `@contextmanager` in `infrastructure/postgres.py`. |
| `datetime` | Times in UTC everywhere; `timedelta` for the token lifetime. |
| `threading` | An `RLock` around the shared database connection. |
| `time` | `time.sleep` for the reconnect back-off; `time.monotonic` in the HTTP timer. |
| `base64` | Encodes the salt and hash in a password record. |
| `importlib.metadata` | Reads the installed version of pip-audit. |
| `urllib.request` | The container health check asks `/healthz`. |
| `os`, `sys`, `io` | Environment, error stream, in-memory text buffer for CSV. |

## How it works underneath

A standard-library module is a file (or folder) inside Python's own installation. `import enum` finds it the same way as any
module, through `sys.path`. Some are partly written in C for speed. Their behavior is fixed by the Python version, which is why
this repository pins 3.12 as the lowest version.

## Walkthrough of this repository's use

### `enum`

`src/notes_evidence/domain/roles.py`:

```python
class Role(Enum):
    """member writes their own notes; readonly reads every note and writes none; admin does everything."""

    ADMIN = "admin"
    MEMBER = "member"
    READONLY = "readonly"
```

An `Enum` is a fixed set of named values. `Role("admin")` looks a member up by value and raises `ValueError` for an unknown one;
the HTTP layer uses that to answer `400` for a bad role.

### `typing.Protocol`

`src/notes_evidence/application/ports.py`:

```python
class Clock(Protocol):
    """The current time, injected so tests are deterministic."""

    def now(self) -> datetime:
        """The current moment, timezone aware."""
        ...
```

A `Protocol` says "anything with these methods will do". `SystemClock` fits `Clock`, and so does a test's fixed clock, without
inheriting from anything. The `...` body means "no code here, this is only the shape". mypy checks the match.

### `contextlib.contextmanager`, `threading`, `time`

`src/notes_evidence/infrastructure/postgres.py`:

```python
    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection[tuple[Any, ...]]]:
        """The connection inside a transaction: committed on success, rolled back on any error."""
        with self._lock:
            connection = self._ensure()
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()
```

- `@contextmanager` turns a function with one `yield` into something usable after `with`: the code before `yield` runs at the
  start of the block, the block's value is `connection`, and the code after runs at the end.
- `with self._lock:` takes a `threading.RLock`, a lock that only one thread can hold at a time (the same thread may take it again).
  It protects the shared connection if two threads ever use it.
- `except BaseException: connection.rollback(); raise` rolls back on **any** error and re-raises it; `else: connection.commit()`
  runs only when the block ended well.

`src/notes_evidence/infrastructure/postgres.py`:

```python
    def _ensure(self) -> psycopg.Connection[tuple[Any, ...]]:
        if self._connection is not None and not self._connection.closed and not self._connection.broken:
            return self._connection
        delay = 0.5
        for attempt in range(1, CONNECT_ATTEMPTS + 1):
            try:
                self._connection = psycopg.connect(
                    self._url, connect_timeout=5, options=f"-c statement_timeout={self._statement_timeout_ms}"
                )
                return self._connection
            except psycopg.OperationalError:
                if attempt == CONNECT_ATTEMPTS:
                    raise
                self._sleep(delay)
                delay *= 2
        raise AssertionError("unreachable")  # pragma: no cover
```

`time.sleep(delay)` pauses; the code doubles `delay` after each failure (0.5 s, 1 s, 2 s, ...): **exponential back-off**. The
`sleep` function is passed in (`sleep: Callable[[float], None] = time.sleep`) so tests can skip the waiting.

### `urllib`, `os`, `sys`

`src/notes_evidence/interfaces/health.py`:

```python
def main() -> int:
    """Ask the local API if it is healthy."""
    port = os.environ.get("HTTP_PORT", "8080")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=3) as response:
            return 0 if response.status == 200 else 1
    except (urllib.error.URLError, OSError):
        print("unhealthy", file=sys.stderr)
        return 1
```

`urllib.request.urlopen(url, timeout=3)` makes an HTTP GET and returns a response; as a `with` target it is closed afterwards.
`os.environ.get("HTTP_PORT", "8080")` reads the port. A network error (`URLError`, an `OSError`) is caught, and the program prints
to `sys.stderr` and returns 1.

### `base64` and `importlib.metadata`

`src/notes_evidence/infrastructure/passwords.py`:

```python
    def hash(self, password: str) -> str:
        """Hash a password with a fresh 16-byte salt."""
        salt = secrets.token_bytes(16)
```

`base64.b64encode(bytes)` turns raw bytes into text made of letters, digits, `+`, `/` and `=`, so a salt and a hash can live in
one string. `src/notes_evidence/infrastructure/scanner.py`:

```python
        return ScanReport(run_id, "pip-audit", metadata.version("pip-audit"), started, self._lock, count, findings)
```

`metadata.version("pip-audit")` returns the installed version of a package as text.

## Try it yourself

```bash
.venv/bin/python -c "from notes_evidence.domain.roles import Role, Permission, allowed; print(Role('member'), allowed(Role.MEMBER, Permission.READ_ANY), allowed(Role.ADMIN, Permission.GRANT_ROLE))"
```
Prints `Role.MEMBER False True`.

```bash
.venv/bin/python -c "import base64; print(base64.b64encode(b'salt'), base64.b64decode('c2FsdA=='))"
```
Prints `b'c2FsdA=='` and `b'salt'`.

```bash
.venv/bin/python -c "from importlib import metadata; print(metadata.version('pip-audit'))"
```
Prints `2.10.1`.

```bash
.venv/bin/python -c "import time; a = time.monotonic(); time.sleep(0.1); print(round(time.monotonic() - a, 1))"
```
Prints `0.1`: a monotonic clock never goes backward, so it is the right one for measuring durations.

```bash
grep -rhE "^(import|from) [a-z_.]+" src --include='*.py' | grep -v notes_evidence | sort | uniq -c | sort -rn | head -15
```
Lists the imports of the source with counts. Only `flask` and `psycopg` come from outside the standard library.

## Mistakes people make

- **Using `time.time()` to measure a duration.** The clock can be adjusted; use `time.monotonic()`.
- **Retrying forever.** The reconnect loop gives up after five attempts and raises the last error.
- **Naive datetimes.** Everything here is timezone-aware UTC.
- **Sharing a connection between threads without a lock.** `Database` serializes access with an `RLock`.

## Check yourself

1. What does `@contextmanager` do?
   **Answer:** Turns a one-`yield` function into something you can use after `with`.
2. What is exponential back-off?
   **Answer:** Waiting longer after each failed attempt, here doubling the delay.
3. Why pass `time.sleep` in as an argument?
   **Answer:** So tests can replace it and not wait.
4. What does the health check return when the API answers 200?
   **Answer:** Exit code 0.
5. What does `Role('admin')` do for an unknown value?
   **Answer:** Raises `ValueError`.

## Further reading

- Python 3.12 standard library: <https://docs.python.org/3.12/library/index.html>
- `enum`: <https://docs.python.org/3.12/library/enum.html>; `contextlib`: <https://docs.python.org/3.12/library/contextlib.html>; `threading`: <https://docs.python.org/3.12/library/threading.html>; `urllib.request`: <https://docs.python.org/3.12/library/urllib.request.html>; `base64`: <https://docs.python.org/3.12/library/base64.html>; `importlib.metadata`: <https://docs.python.org/3.12/library/importlib.metadata.html>
