# psycopg 3

## What it is

A **database driver** is a library that lets a program talk to a specific database. **psycopg** (version 3) is the PostgreSQL
driver for Python: it opens a **connection**, sends SQL, and returns rows as Python tuples. `psycopg[binary]` installs a ready-built
copy of the C library it needs, so nothing has to be compiled.

## Why this repository uses it

The API and the evidence collectors use a real PostgreSQL because the controls are about database features: roles, grants and an
append-only audit log. psycopg is the way to run those statements and to check what the database refuses.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/infrastructure/postgres.py` | `Database`, `PostgresUsers`, `PostgresNotes`, `PostgresAuditLog`, `PostgresRoles`. |
| `pyproject.toml` | `psycopg[binary]>=3.2,<4`. |
| `requirements.lock` | `psycopg==3.3.6`, `psycopg-binary==3.3.6`. |
| `tests/integration/` | Real queries against the container. |

## How it works underneath

`psycopg.connect(url)` opens a TCP connection to the server and logs in. `connection.execute(sql, params)` sends the statement
with the parameters **separately**: the server never builds SQL from text pasted together, which stops SQL injection. The driver
starts a **transaction** automatically; nothing is saved until `commit()`, and `rollback()` undoes it. `fetchone()` and
`fetchall()` read the result. Python values are converted both ways (`datetime`, `str`, `int`; `Jsonb(...)` marks a value to be
stored as `jsonb`).

## Walkthrough of this repository's use

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

- `psycopg.connect(self._url, connect_timeout=5, options=f"-c statement_timeout=...")` opens the connection. `connect_timeout=5`
  gives up after 5 seconds. `options="-c statement_timeout=30000"` tells the server to cancel any statement that runs longer
  than 30,000 ms.
- `except psycopg.OperationalError` catches connection problems; the loop retries with back-off, up to five times.

`src/notes_evidence/infrastructure/postgres.py`:

```python
    def find_by_username(self, username: str) -> tuple[User, str] | None:
        """The user and the stored hash, or None."""
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT id, username, role, active, password_hash FROM users WHERE username = %s", (username,)
            ).fetchone()
        return (_user(row), row[4]) if row else None
```

- `%s` is psycopg's placeholder (not `?`). The values go in the tuple `(username,)`.
- `.fetchone()` returns one row (a tuple) or `None`.

`src/notes_evidence/infrastructure/postgres.py`:

```python
    def provision(self, username: str, role: Role, password_hash: str) -> User:
        """Insert the user, or update its role and password hash when the name exists."""
        with self._db.connection() as connection:
            row = connection.execute(
                "INSERT INTO users (username, role, password_hash) VALUES (%s, %s, %s) "
                "ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role, "
                "password_hash = EXCLUDED.password_hash, active = TRUE "
                "RETURNING id, username, role, active",
                (username, role.value, password_hash),
            ).fetchone()
        assert row is not None
        return _user(row)
```

`INSERT ... ON CONFLICT (username) DO UPDATE ... RETURNING ...` inserts or updates in one statement and returns the row. See
`sql.md`.

`src/notes_evidence/infrastructure/postgres.py`:

```python
    def append(self, event: AuditEvent) -> None:
        """Insert one event."""
        with self._db.connection() as connection:
            connection.execute(
                "INSERT INTO audit_log (ts, user_id, username, action, note_id, outcome, detail) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    event.at,
                    event.user_id,
                    event.username,
                    event.action.value,
                    event.note_id,
                    event.outcome,
                    Jsonb(event.detail),
                ),
```

`Jsonb(event.detail)` stores a Python dictionary as `jsonb`. The app role may only insert and read this table.

`src/notes_evidence/infrastructure/postgres.py`:

```python
    def ping(self) -> bool:
        """True when a trivial query works."""
        try:
            with self.connection() as connection:
                connection.execute("SELECT 1")
        except psycopg.Error:
            return False
```

`SELECT 1` is the cheapest query that proves the database answers.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
.venv/bin/python -c "import psycopg; print(psycopg.__version__)"
```
Prints `3.3.6` (this one needs no database).

```bash
make up
set -a; . ./.env; set +a
.venv/bin/python -c "import os, psycopg; c = psycopg.connect(os.environ['DATABASE_URL']); print(c.execute('SELECT current_user, 1 + 1').fetchone())"
```
Prints `('app_rw', 2)`: connected as the least-privilege role.

```bash
.venv/bin/python -c "import os, psycopg; c = psycopg.connect(os.environ['DATABASE_URL']); c.execute('DELETE FROM audit_log')" 2>&1 | tail -1
```
Prints a `psycopg.errors.InsufficientPrivilege` error: `permission denied for table audit_log`.

```bash
make test-integration
```
Runs the 11 integration tests.

## Mistakes people make

- **Using `?` or `%d` placeholders.** psycopg uses `%s` for every type.
- **Building SQL with f-strings.** Pass values separately.
- **Forgetting the transaction**: without `commit()` nothing is saved. The `Database.connection()` context manager commits or rolls back.
- **A connection per query.** That opened thousands of connections in a collector run; the class keeps one long-lived connection.
- **No statement timeout**, so a stuck query hangs a worker.

## Check yourself

1. Why are values passed as a separate tuple?
   **Answer:** The server never builds SQL from pasted text, which stops SQL injection.
2. What does `statement_timeout` do?
   **Answer:** The server cancels any statement that runs longer than the limit.
3. What does `Jsonb(x)` do?
   **Answer:** Marks a Python value to be stored as PostgreSQL `jsonb`.
4. What happens if the block under `with self._db.connection()` raises?
   **Answer:** The transaction is rolled back and the error is re-raised.
5. What is `psycopg[binary]`?
   **Answer:** psycopg plus a pre-built copy of its C library, so nothing is compiled.

## Further reading

- psycopg 3.3 documentation: <https://www.psycopg.org/psycopg3/docs/>
- Passing parameters: <https://www.psycopg.org/psycopg3/docs/basic/params.html>
- Transactions: <https://www.psycopg.org/psycopg3/docs/basic/transactions.html>
