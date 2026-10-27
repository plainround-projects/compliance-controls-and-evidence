-- DDL for notes-api: roles, tables, constraints, indexes, the append-only audit log, and least-privilege grants.
-- Run as the database superuser with the role passwords as psql variables (make db does this):
--   psql -v app_rw_password=... -v migrator_password=... -v retention_password=... -f sql/001_schema.sql
-- It can be run again: every statement is guarded.

-- Roles: one per duty, none shared. LOGIN roles show up in the C1 access list.
SELECT 'CREATE ROLE app_rw LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') \gexec
SELECT 'CREATE ROLE migrator LOGIN CREATEDB' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'migrator') \gexec
SELECT 'CREATE ROLE audit_retention LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'audit_retention') \gexec
ALTER ROLE app_rw PASSWORD :'app_rw_password';
ALTER ROLE migrator PASSWORD :'migrator_password';
ALTER ROLE audit_retention PASSWORD :'retention_password';

CREATE TABLE IF NOT EXISTS users (
    id            integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      text        NOT NULL UNIQUE CHECK (username ~ '^[a-z][a-z0-9_-]{1,31}$'),
    role          text        NOT NULL CHECK (role IN ('admin', 'member', 'readonly')),
    password_hash text        NOT NULL,
    active        boolean     NOT NULL DEFAULT TRUE,
    created_at    timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE users IS 'Accounts. password_hash is scrypt$salt$hash; the value ! can never match (a seeded account with no password).';

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

CREATE TABLE IF NOT EXISTS audit_retention (
    only_row boolean PRIMARY KEY DEFAULT TRUE CHECK (only_row),
    days     integer NOT NULL CHECK (days >= 90)
);
INSERT INTO audit_retention (days) VALUES (365) ON CONFLICT DO NOTHING;
COMMENT ON TABLE audit_retention IS 'The one row that says how many days an audit row must be kept before the retention role may delete it.';

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

DROP TRIGGER IF EXISTS audit_log_no_update ON audit_log;
CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard();
DROP TRIGGER IF EXISTS audit_log_retention_only ON audit_log;
CREATE TRIGGER audit_log_retention_only BEFORE DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_log_guard();
DROP TRIGGER IF EXISTS audit_log_no_truncate ON audit_log;
CREATE TRIGGER audit_log_no_truncate BEFORE TRUNCATE ON audit_log FOR EACH STATEMENT EXECUTE FUNCTION audit_log_guard();

-- Least privilege: nothing for PUBLIC, then exactly what each role needs.
REVOKE ALL ON users, notes, audit_log, audit_retention FROM PUBLIC;
GRANT SELECT ON users TO app_rw;
GRANT UPDATE (role) ON users TO app_rw;                 -- role grants; creating or disabling accounts is an administrator's act
GRANT SELECT, INSERT, UPDATE, DELETE ON notes TO app_rw;
GRANT SELECT, INSERT ON audit_log TO app_rw;            -- no UPDATE, no DELETE
GRANT SELECT ON audit_retention TO app_rw, audit_retention;
GRANT SELECT, DELETE ON audit_log TO audit_retention;   -- the trigger still refuses rows younger than the retention period
GRANT CREATE, USAGE ON SCHEMA public TO migrator;
