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

### The complete file `sql/001_schema.sql`, line by line

`sql/001_schema.sql` lines 1 to 4:

```sql
-- DDL for notes-api: roles, tables, constraints, indexes, the append-only audit log, and least-privilege grants.
-- Run as the database superuser with the role passwords as psql variables (make db does this):
--   psql -v app_rw_password=... -v migrator_password=... -v retention_password=... -f sql/001_schema.sql
-- It can be run again: every statement is guarded.
```

> **In plain words.** SQL statements end with a semicolon; `--` starts a comment. A **table** is a grid of rows and columns. A **constraint** (`NOT NULL`, `UNIQUE`, `CHECK`, `REFERENCES`) makes the database refuse bad data. An **index** speeds up lookups. A **query** (`SELECT`) reads rows.

- These lines are comments written by the author (`--` starts a comment); they are quoted above.

`sql/001_schema.sql` lines 6 to 12:

```sql
-- Roles: one per duty, none shared. LOGIN roles show up in the C1 access list.
SELECT 'CREATE ROLE app_rw LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') \gexec
SELECT 'CREATE ROLE migrator LOGIN CREATEDB' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'migrator') \gexec
SELECT 'CREATE ROLE audit_retention LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'audit_retention') \gexec
ALTER ROLE app_rw PASSWORD :'app_rw_password';
ALTER ROLE migrator PASSWORD :'migrator_password';
ALTER ROLE audit_retention PASSWORD :'retention_password';
```

- A **query**: it reads data and returns rows. `SELECT 'CREATE ROLE app_rw LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') \gexec SELECT 'CREATE ROLE migrator LOGI…`.
- Creates or changes a database login (role): `ALTER ROLE migrator PASSWORD :'migrator_password'`.
- Creates or changes a database login (role): `ALTER ROLE audit_retention PASSWORD :'retention_password'`.

`sql/001_schema.sql` lines 14 to 22:

```sql
CREATE TABLE IF NOT EXISTS users (
    id            integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      text        NOT NULL UNIQUE CHECK (username ~ '^[a-z][a-z0-9_-]{1,31}$'),
    role          text        NOT NULL CHECK (role IN ('admin', 'member', 'readonly')),
    password_hash text        NOT NULL,
    active        boolean     NOT NULL DEFAULT TRUE,
    created_at    timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE users IS 'Accounts. password_hash is scrypt$salt$hash; the value ! can never match (a seeded account with no password).';
```

- Creates the table `users` if it does not exist yet. Its columns:
  - `id` of type `integer`: the primary key (unique row identity), numbered automatically.
  - `username` of type `text`: required, never repeated, must satisfy `username ~ '^[a-z][a-z0-9_-]{1,31}$'`.
  - `role` of type `text`: required, must satisfy `role IN ('admin', 'member', 'readonly')`.
  - `password_hash` of type `text`: required.
  - `active` of type `boolean`: required, defaults to `TRUE`.
  - `created_at` of type `timestamptz`: required, defaults to `now()`.
- Stores a description in the database itself: `COMMENT ON TABLE users IS 'Accounts. password_hash is scrypt$salt$hash; the value ! can never match (a seeded…`.

`sql/001_schema.sql` lines 24 to 33:

```sql
CREATE TABLE IF NOT EXISTS notes (
    id         integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id   integer     NOT NULL REFERENCES users (id),
    title      text        NOT NULL CHECK (length(title) BETWEEN 1 AND 120),
    body       text        NOT NULL CHECK (length(body) <= 10000),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_owner_idx ON notes (owner_id, id DESC);
COMMENT ON TABLE notes IS 'Customer notes. They hold personal data, so the audit log never copies their text.';
```

- Creates the table `notes` if it does not exist yet. Its columns:
  - `id` of type `integer`: the primary key (unique row identity), numbered automatically.
  - `owner_id` of type `integer`: required, must match a row in `users (id)` (a foreign key).
  - `title` of type `text`: required, must satisfy `length(title) BETWEEN 1 AND 120`.
  - `body` of type `text`: required, must satisfy `length(body) <= 10000`.
  - `created_at` of type `timestamptz`: required.
  - `updated_at` of type `timestamptz`: required.
- Builds an **index**, a sorted lookup structure that lets the database find rows without reading the whole table: `CREATE INDEX IF NOT EXISTS notes_owner_idx ON notes (owner_id, id DESC)`.
- Stores a description in the database itself: `COMMENT ON TABLE notes IS 'Customer notes. They hold personal data, so the audit log never copies their text.'`.

`sql/001_schema.sql` lines 35 to 40:

```sql
CREATE TABLE IF NOT EXISTS audit_retention (
    only_row boolean PRIMARY KEY DEFAULT TRUE CHECK (only_row),
    days     integer NOT NULL CHECK (days >= 90)
);
INSERT INTO audit_retention (days) VALUES (365) ON CONFLICT DO NOTHING;
COMMENT ON TABLE audit_retention IS 'The one row that says how many days an audit row must be kept before the retention role may delete it.';
```

- Creates the table `audit_retention` if it does not exist yet. Its columns:
  - `only_row` of type `boolean`: the primary key (unique row identity), defaults to `TRUE`, must satisfy `only_row`.
  - `days` of type `integer`: required, must satisfy `days >= 90`.
- Adds rows to `audit_retention` with 1 row(s): `INSERT INTO audit_retention (days) VALUES (365) ON CONFLICT DO NOTHING`.
- Stores a description in the database itself: `COMMENT ON TABLE audit_retention IS 'The one row that says how many days an audit row must be kept before the…`.

`sql/001_schema.sql` lines 42 to 55:

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

- Creates the table `audit_log` if it does not exist yet. Its columns:
  - `id` of type `bigint`: the primary key (unique row identity), numbered automatically.
  - `ts` of type `timestamptz`: required, defaults to `now()`.
  - `user_id` of type `integer`.
  - `username` of type `text`: required.
  - `action` of type `text`: required, must satisfy `action IN ( 'login_ok', 'login_failed', 'note_created', 'note_read', 'note_updated', 'note_deleted'…`.
  - `note_id` of type `integer`.
  - `outcome` of type `text`: required, must satisfy `outcome IN ('ok', 'denied', 'failed')`.
  - `detail` of type `jsonb`: required, defaults to `'{}'`.
- Builds an **index**, a sorted lookup structure that lets the database find rows without reading the whole table: `CREATE INDEX IF NOT EXISTS audit_log_ts_idx ON audit_log (ts)`.
- Builds an **index**, a sorted lookup structure that lets the database find rows without reading the whole table: `CREATE INDEX IF NOT EXISTS audit_log_user_action_idx ON audit_log (username, action, ts)`.
- Stores a description in the database itself: `COMMENT ON TABLE audit_log IS 'Append-only: who did what, to which note, when. No note content. Updates and t…`.

`sql/001_schema.sql` lines 57 to 68:

```sql
-- Append-only, enforced by the database and not by the application's good behavior.
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
```

- Defines a function the database can run (written in PL/pgSQL, PostgreSQL's procedural language): `CREATE OR REPLACE FUNCTION audit_log_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF TG_OP …`. The `$$ ... $$` marks the start and end of its body.

`sql/001_schema.sql` lines 70 to 75:

```sql
DROP TRIGGER IF EXISTS audit_log_no_update ON audit_log;
CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard();
DROP TRIGGER IF EXISTS audit_log_retention_only ON audit_log;
CREATE TRIGGER audit_log_retention_only BEFORE DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard();
DROP TRIGGER IF EXISTS audit_log_no_truncate ON audit_log;
CREATE TRIGGER audit_log_no_truncate BEFORE TRUNCATE ON audit_log FOR EACH STATEMENT EXECUTE FUNCTION audit_log_guard();
```

- Removes the trigger if it exists, so it can be created again: `DROP TRIGGER IF EXISTS audit_log_no_update ON audit_log`.
- Attaches the function to a table so the database runs it automatically on each matching change: `CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard()`.
- Removes the trigger if it exists, so it can be created again: `DROP TRIGGER IF EXISTS audit_log_retention_only ON audit_log`.
- Attaches the function to a table so the database runs it automatically on each matching change: `CREATE TRIGGER audit_log_retention_only BEFORE DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard()`.
- Removes the trigger if it exists, so it can be created again: `DROP TRIGGER IF EXISTS audit_log_no_truncate ON audit_log`.
- Attaches the function to a table so the database runs it automatically on each matching change: `CREATE TRIGGER audit_log_no_truncate BEFORE TRUNCATE ON audit_log FOR EACH STATEMENT EXECUTE FUNCTION audit_log_guard()`.

`sql/001_schema.sql` lines 77 to 85:

```sql
-- Least privilege: nothing for PUBLIC, then exactly what each role needs.
REVOKE ALL ON users, notes, audit_log, audit_retention FROM PUBLIC;
GRANT SELECT ON users TO app_rw;
GRANT UPDATE (role) ON users TO app_rw;                 -- role grants; creating or disabling accounts is an administrator's act
GRANT SELECT, INSERT, UPDATE, DELETE ON notes TO app_rw;
GRANT SELECT, INSERT ON audit_log TO app_rw;            -- no UPDATE, no DELETE
GRANT SELECT ON audit_retention TO app_rw, audit_retention;
GRANT SELECT, DELETE ON audit_log TO audit_retention;   -- the trigger still refuses rows younger than the retention period
GRANT CREATE, USAGE ON SCHEMA public TO migrator;
```

- Removes permissions: `REVOKE ALL ON users, notes, audit_log, audit_retention FROM PUBLIC`.
- Gives permissions: `GRANT SELECT ON users TO app_rw`.
- Gives permissions: `GRANT UPDATE (role) ON users TO app_rw`.
- Gives permissions: `GRANT SELECT, INSERT, UPDATE, DELETE ON notes TO app_rw`.
- Gives permissions: `GRANT SELECT, INSERT ON audit_log TO app_rw`.
- Gives permissions: `GRANT SELECT ON audit_retention TO app_rw, audit_retention`.
- Gives permissions: `GRANT SELECT, DELETE ON audit_log TO audit_retention`.
- Gives permissions: `GRANT CREATE, USAGE ON SCHEMA public TO migrator`.

### The complete file `sql/002_seed.sql`, line by line

`sql/002_seed.sql` lines 1 to 3:

```sql
-- DML: the made-up accounts and 12,400 synthetic notes (a size where a restore takes a measurable moment).
-- Accounts are seeded with the hash '!', which can never match a password; `make run` gives them throwaway passwords in memory.
-- Nothing here is real personal data. Run again safely: it inserts only when the tables are empty.
```

> **In plain words.** SQL statements end with a semicolon; `--` starts a comment. A **table** is a grid of rows and columns. A **constraint** (`NOT NULL`, `UNIQUE`, `CHECK`, `REFERENCES`) makes the database refuse bad data. An **index** speeds up lookups. A **query** (`SELECT`) reads rows.

- These lines are comments written by the author (`--` starts a comment); they are quoted above.

`sql/002_seed.sql` lines 5 to 10:

```sql
INSERT INTO users (username, role, password_hash) VALUES
    ('ada', 'admin', '!'),
    ('bruno', 'member', '!'),
    ('chen', 'member', '!'),
    ('dana', 'readonly', '!')
ON CONFLICT (username) DO NOTHING;
```

- Adds rows to `users` with 5 row(s): `INSERT INTO users (username, role, password_hash) VALUES ('ada', 'admin', '!'), ('bruno', 'member', '!'), ('c…`.

`sql/002_seed.sql` lines 12 to 20:

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

- Adds rows to `notes` from a query: `INSERT INTO notes (owner_id, title, body, created_at, updated_at) SELECT (SELECT id FROM users WHERE username…`.

### The complete file `sql/003_queries.sql`, line by line

`sql/003_queries.sql` lines 1 to 1:

```sql
-- The queries the controls run, each with a line on what it shows. Run with: make queries
```

> **In plain words.** SQL statements end with a semicolon; `--` starts a comment. A **table** is a grid of rows and columns. A **constraint** (`NOT NULL`, `UNIQUE`, `CHECK`, `REFERENCES`) makes the database refuse bad data. An **index** speeds up lookups. A **query** (`SELECT`) reads rows.

- These lines are comments written by the author (`--` starts a comment); they are quoted above.

`sql/003_queries.sql` lines 3 to 5:

```sql
-- C1: database roles that can log in, with their level (the database part of the access list).
SELECT rolname, CASE WHEN rolsuper THEN 'superuser' WHEN rolcreatedb THEN 'createdb' ELSE 'standard' END AS level
FROM pg_roles WHERE rolname NOT LIKE 'pg\_%' AND rolcanlogin ORDER BY 1;
```

- A **query**: it reads data and returns rows. `SELECT rolname, CASE WHEN rolsuper THEN 'superuser' WHEN rolcreatedb THEN 'createdb' ELSE 'standard' END AS level FROM pg_roles WHERE rolna…`.

`sql/003_queries.sql` lines 7 to 11:

```sql
-- C1: what each application role may do on each table (least privilege made visible).
SELECT grantee, table_name, string_agg(privilege_type, ', ' ORDER BY privilege_type) AS privileges
FROM information_schema.role_table_grants
WHERE table_schema = 'public' AND grantee IN ('app_rw', 'audit_retention', 'migrator')
GROUP BY grantee, table_name ORDER BY grantee, table_name;
```

- A **query**: it reads data and returns rows. `SELECT grantee, table_name, string_agg(privilege_type, ', ' ORDER BY privilege_type) AS privileges FROM information_schema.role_table_grant…`.

`sql/003_queries.sql` lines 13 to 14:

```sql
-- C3: the audit trail, newest first, with the fields the log line carries (and no note content).
SELECT ts, username, action, note_id, outcome FROM audit_log ORDER BY id DESC LIMIT 20;
```

- A **query**: it reads data and returns rows. `SELECT ts, username, action, note_id, outcome FROM audit_log ORDER BY id DESC LIMIT 20`.

`sql/003_queries.sql` lines 16 to 24:

```sql
-- C3: the failed-login alert rule in SQL: accounts with 5 or more failures inside any 2-minute window.
SELECT username, count(*) AS failures, min(ts) AS first_failure, max(ts) AS last_failure
FROM audit_log a
WHERE action = 'login_failed'
  AND EXISTS (
      SELECT 1 FROM audit_log b
      WHERE b.username = a.username AND b.action = 'login_failed' AND b.ts BETWEEN a.ts AND a.ts + interval '2 minutes'
      GROUP BY b.username HAVING count(*) >= 5)
GROUP BY username;
```

- A **query**: it reads data and returns rows. `SELECT username, count(*) AS failures, min(ts) AS first_failure, max(ts) AS last_failure FROM audit_log a WHERE action = 'login_failed' AND…`.

`sql/003_queries.sql` lines 26 to 28:

```sql
-- C3: every admin role grant, who made it, to whom.
SELECT ts, username AS granted_by, detail ->> 'target' AS granted_to, detail ->> 'role' AS role
FROM audit_log WHERE action = 'role_granted' ORDER BY ts;
```

- A **query**: it reads data and returns rows. `SELECT ts, username AS granted_by, detail ->> 'target' AS granted_to, detail ->> 'role' AS role FROM audit_log WHERE action = 'role_granted…`.

`sql/003_queries.sql` lines 30 to 33:

```sql
-- Retention: how many audit rows are old enough to delete, and the oldest row.
SELECT count(*) FILTER (WHERE ts < now() - make_interval(days => (SELECT days FROM audit_retention))) AS deletable,
       count(*) AS total, min(ts) AS oldest
FROM audit_log;
```

- A **query**: it reads data and returns rows. `SELECT count(*) FILTER (WHERE ts < now() - make_interval(days => (SELECT days FROM audit_retention))) AS deletable, count(*) AS total, min(…`.

`sql/003_queries.sql` lines 35 to 36:

```sql
-- Retention job (run as audit_retention): delete only rows past the retention period; the trigger would refuse younger ones.
-- DELETE FROM audit_log WHERE ts < now() - make_interval(days => (SELECT days FROM audit_retention));
```

- These lines are comments written by the author (`--` starts a comment); they are quoted above.

`sql/003_queries.sql` lines 38 to 39:

```sql
-- C4: the row count the restore test compares.
SELECT count(*) AS notes FROM notes;
```

- A **query**: it reads data and returns rows. `SELECT count(*) AS notes FROM notes`.

### The complete file `sql/reset.sql`, line by line

`sql/reset.sql` lines 1 to 4:

```sql
-- Drop everything in the public schema so `make db` starts clean. Run as the superuser. Roles are kept (the schema script re-creates them if missing).
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT USAGE ON SCHEMA public TO PUBLIC;
```

> **In plain words.** SQL statements end with a semicolon; `--` starts a comment. A **table** is a grid of rows and columns. A **constraint** (`NOT NULL`, `UNIQUE`, `CHECK`, `REFERENCES`) makes the database refuse bad data. An **index** speeds up lookups. A **query** (`SELECT`) reads rows.

- Drops or creates a schema (a named group of tables): `DROP SCHEMA public CASCADE`.
- Drops or creates a schema (a named group of tables): `CREATE SCHEMA public`.
- Gives permissions: `GRANT USAGE ON SCHEMA public TO PUBLIC`.

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
