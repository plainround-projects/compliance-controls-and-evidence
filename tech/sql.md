# SQL (PostgreSQL dialect)

## What it is

SQL (Structured Query Language) is the language for asking a relational database to create tables, store rows and find them. A
**table** is a grid: each **row** is one record, each **column** has a name and a type. Statements end with a semicolon; `--` starts a
comment. PostgreSQL adds its own extras (roles, `jsonb`, triggers written in PL/pgSQL).

## Why this repository uses it

The controls are written in SQL: who can do what (`GRANT`), what cannot be changed (a trigger), what the evidence queries show.
The scripts are the database's whole definition and can be run again safely.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `sql/001_schema.sql` | Roles, tables, constraints, indexes, the audit trigger, grants. |
| `sql/002_seed.sql` | Accounts and 12,400 generated notes. |
| `sql/003_queries.sql` | Queries for the access list, grants, audit trail and alert rule. |
| `sql/reset.sql` | Drops and recreates the `public` schema. |
| `src/notes_evidence/infrastructure/postgres.py` | The statements the app and collectors run. |

## How it works underneath

The server parses a statement, plans it, runs it and returns rows or a count. Constraints (`NOT NULL`, `UNIQUE`, `CHECK`,
`REFERENCES`) are checked on every change. A `GRANT` gives a role a privilege; without one the server answers `permission denied`.
`psql` (see `postgresql-tools.md`) reads a script and sends its statements one by one; a line starting with a backslash, such as
`\gexec`, is a `psql` command, not SQL.

## Walkthrough of this repository's use

`sql/001_schema.sql`:

```sql
SELECT 'CREATE ROLE app_rw LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') \gexec
SELECT 'CREATE ROLE migrator LOGIN CREATEDB' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'migrator') \gexec
SELECT 'CREATE ROLE audit_retention LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'audit_retention') \gexec
ALTER ROLE app_rw PASSWORD :'app_rw_password';
```

- `SELECT 'CREATE ROLE app_rw LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') \gexec`: the query returns
  the text `CREATE ROLE app_rw LOGIN` only if no such role exists, and `\gexec` (a `psql` command) **runs each returned text as a
  statement**. This makes the script safe to run twice, because `CREATE ROLE` has no `IF NOT EXISTS`.
- `ALTER ROLE app_rw PASSWORD :'app_rw_password';` uses a `psql` variable, passed on the command line with `-v` (see the
  Makefile's `db` target); `:'name'` inserts it as a quoted string.

`sql/001_schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS users (
    id            integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      text        NOT NULL UNIQUE CHECK (username ~ '^[a-z][a-z0-9_-]{1,31}$'),
    role          text        NOT NULL CHECK (role IN ('admin', 'member', 'readonly')),
    password_hash text        NOT NULL,
    active        boolean     NOT NULL DEFAULT TRUE,
    created_at    timestamptz NOT NULL DEFAULT now()
);
```

- `integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY`: an automatic row number that cannot be set by hand.
- `CHECK (username ~ '^[a-z][a-z0-9_-]{1,31}$')`: `~` matches a regular expression (see `re.md`).
- `CHECK (role IN ('admin', 'member', 'readonly'))`: only these roles exist.
- `timestamptz NOT NULL DEFAULT now()`: a time with a time zone, filled with the current time.

`sql/001_schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ts       timestamptz NOT NULL DEFAULT now(),
    user_id  integer,
    username text        NOT NULL,
    action   text        NOT NULL CHECK (action IN (
        'login_ok', 'login_failed', 'note_created', 'note_read', 'note_updated', 'note_deleted', 'role_granted', 'access_denied')),
    note_id  integer,
    outcome  text        NOT NULL CHECK (outcome IN ('ok', 'denied', 'failed')),
    detail   jsonb       NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS audit_log_ts_idx ON audit_log (ts);
CREATE INDEX IF NOT EXISTS audit_log_user_action_idx ON audit_log (username, action, ts);
COMMENT ON TABLE audit_log IS 'Append-only: who did what, to which note, when. No note content. Updates and truncates are refused; deletes only after the retention period.';
```

- `bigint ... IDENTITY`: a large automatic number.
- `detail jsonb NOT NULL DEFAULT '{}'`: a JSON document column.
- The `CHECK ... IN (...)` lists restrict `action` and `outcome` to known values.
- `COMMENT ON TABLE` stores a description in the database.

`sql/001_schema.sql`:

```sql
CREATE OR REPLACE FUNCTION audit_log_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.ts > now() - make_interval(days => (SELECT days FROM audit_retention)) THEN
            RAISE EXCEPTION 'audit_log rows are kept for % days', (SELECT days FROM audit_retention);
        END IF;
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'audit_log is append-only: % is not allowed', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS audit_log_no_update ON audit_log;
CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard();
DROP TRIGGER IF EXISTS audit_log_retention_only ON audit_log;
CREATE TRIGGER audit_log_retention_only BEFORE DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard();
DROP TRIGGER IF EXISTS audit_log_no_truncate ON audit_log;
CREATE TRIGGER audit_log_no_truncate BEFORE TRUNCATE ON audit_log FOR EACH STATEMENT EXECUTE FUNCTION audit_log_guard();
```

The **append-only rule lives in the database**:
- `CREATE FUNCTION ... RETURNS trigger LANGUAGE plpgsql AS $$ ... $$` defines a function in PL/pgSQL, PostgreSQL's procedural
  language. `$$ ... $$` is a quoting style for the body.
- `TG_OP` is the operation that fired the trigger. For `DELETE` the function allows rows older than the retention period
  (`make_interval(days => (SELECT days FROM audit_retention))`) and refuses younger ones with `RAISE EXCEPTION`. For any other
  operation (`UPDATE`, `TRUNCATE`) it always refuses.
- `CREATE TRIGGER ... BEFORE UPDATE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard()` attaches it. `BEFORE TRUNCATE ...
  FOR EACH STATEMENT` handles the whole-table case.

`sql/001_schema.sql`:

```sql
REVOKE ALL ON users, notes, audit_log, audit_retention FROM PUBLIC;
GRANT SELECT ON users TO app_rw;
GRANT UPDATE (role) ON users TO app_rw;                 -- role grants; creating or disabling accounts is an administrator's act
GRANT SELECT, INSERT, UPDATE, DELETE ON notes TO app_rw;
GRANT SELECT, INSERT ON audit_log TO app_rw;            -- no UPDATE, no DELETE
GRANT SELECT ON audit_retention TO app_rw, audit_retention;
GRANT SELECT, DELETE ON audit_log TO audit_retention;   -- the trigger still refuses rows younger than the retention period
GRANT CREATE, USAGE ON SCHEMA public TO migrator;
```

**Least privilege**: first `REVOKE ALL ... FROM PUBLIC` removes everything for everyone, then each role gets only what it needs.
`app_rw` may `SELECT` users and update only the `role` column (`GRANT UPDATE (role)`), read and write notes, and only `SELECT` and
`INSERT` into the audit log. `audit_retention` may read and delete audit rows, and the trigger still decides which.

`sql/002_seed.sql`:

```sql
INSERT INTO notes (owner_id, title, body, created_at, updated_at)
SELECT
    (SELECT id FROM users WHERE username = CASE WHEN g % 2 = 0 THEN 'bruno' ELSE 'chen' END),
    'Synthetic note ' || g,
    'Synthetic body for the restore test, row ' || g || '. No personal data.',
    TIMESTAMPTZ '2026-09-01 00:00:00+00' + g * interval '3 minutes',
    TIMESTAMPTZ '2026-09-01 00:00:00+00' + g * interval '3 minutes'
FROM generate_series(1, 12400) AS g
WHERE NOT EXISTS (SELECT 1 FROM notes);
```

`generate_series(1, 12400) AS g` produces the numbers 1 to 12,400; for each, one note is inserted. `WHERE NOT EXISTS (SELECT 1 FROM
notes)` makes the seed a no-op when notes already exist. `||` joins text; `g * interval '3 minutes'` spaces the notes in time.

`sql/003_queries.sql`:

```sql
SELECT grantee, table_name, string_agg(privilege_type, ', ' ORDER BY privilege_type) AS privileges
FROM information_schema.role_table_grants
WHERE table_schema = 'public' AND grantee IN ('app_rw', 'audit_retention', 'migrator')
GROUP BY grantee, table_name ORDER BY grantee, table_name;
```

`information_schema.role_table_grants` lists grants. `string_agg(privilege_type, ', ' ORDER BY privilege_type)` joins the
privileges of a group into one text. `GROUP BY` makes one row per role and table.

`src/notes_evidence/infrastructure/postgres.py`:

```python
                "INSERT INTO users (username, role, password_hash) VALUES (%s, %s, %s) "
                "ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role, "
                "password_hash = EXCLUDED.password_hash, active = TRUE "
                "RETURNING id, username, role, active",
                (username, role.value, password_hash),
```

`ON CONFLICT (username) DO UPDATE SET ... = EXCLUDED....` is an **upsert**: insert, or if the user name exists, update; `EXCLUDED`
is the row that was refused. `RETURNING` gives back the stored row.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
make up && make queries | head -20
```
Applies the scripts and runs `sql/003_queries.sql`; the first result lists the login roles: `app_rw standard`, `audit_retention standard`,
`migrator createdb`, `postgres superuser`.

```bash
docker compose exec -T db psql -U postgres -d notes -c "DELETE FROM audit_log;"
```
Prints `ERROR:  audit_log rows are kept for 365 days`: the retention rule refuses young rows.

```bash
docker compose exec -T db psql -U app_rw -d notes -c "INSERT INTO users (username, role, password_hash) VALUES ('x','member','!');"
```
Prints `ERROR:  permission denied for table users`: the app role cannot create accounts. (Password: `APP_RW_PASSWORD` from `.env`.)

```bash
grep -c "GRANT" sql/001_schema.sql
```
Counts the grants (this one needs no database).

```bash
make reset-db
```
Drops and rebuilds the schema.

## Mistakes people make

- **Granting to `PUBLIC` by accident.** The script revokes first, then grants by role.
- **Relying on application code to keep a log append-only.** A trigger and missing grants enforce it in the database.
- **Running the schema script as the application role.** It needs a superuser.
- **Pasting values into SQL text.** Use parameters (see `psycopg.md`).
- **Forgetting `ON_ERROR_STOP`.** Without it `psql` carries on after an error (the Makefile sets it).

## Check yourself

1. What does `\gexec` do?
   **Answer:** Runs each value returned by the query as a SQL statement.
2. Why is the audit log's rule a trigger and not application code?
   **Answer:** The database enforces it for every client, including the superuser.
3. What does `REVOKE ALL ... FROM PUBLIC` followed by specific grants achieve?
   **Answer:** Least privilege: each role gets only what it needs.
4. What does `ON CONFLICT ... DO UPDATE` do?
   **Answer:** Inserts, or updates the existing row if the key already exists.
5. What does `generate_series(1, 12400)` return?
   **Answer:** The numbers 1 to 12,400, one row each.

## Further reading

- PostgreSQL 18 SQL commands: <https://www.postgresql.org/docs/18/sql-commands.html>
- PL/pgSQL: <https://www.postgresql.org/docs/18/plpgsql.html>
- `GRANT`: <https://www.postgresql.org/docs/18/sql-grant.html>
- `psql`: <https://www.postgresql.org/docs/18/app-psql.html>
