-- The queries the controls run, each with a line on what it shows. Run with: make queries

-- C1: database roles that can log in, with their level (the database part of the access list).
SELECT rolname, CASE WHEN rolsuper THEN 'superuser' WHEN rolcreatedb THEN 'createdb' ELSE 'standard' END AS level
FROM pg_roles WHERE rolname NOT LIKE 'pg\_%' AND rolcanlogin ORDER BY 1;

-- C1: what each application role may do on each table (least privilege made visible).
SELECT grantee, table_name, string_agg(privilege_type, ', ' ORDER BY privilege_type) AS privileges
FROM information_schema.role_table_grants
WHERE table_schema = 'public' AND grantee IN ('app_rw', 'audit_retention', 'migrator')
GROUP BY grantee, table_name ORDER BY grantee, table_name;

-- C3: the audit trail, newest first, with the fields the log line carries (and no note content).
SELECT ts, username, action, note_id, outcome FROM audit_log ORDER BY id DESC LIMIT 20;

-- C3: the failed-login alert rule in SQL: accounts with 5 or more failures inside any 2-minute window.
SELECT username, count(*) AS failures, min(ts) AS first_failure, max(ts) AS last_failure
FROM audit_log a
WHERE action = 'login_failed'
  AND EXISTS (
      SELECT 1 FROM audit_log b
      WHERE b.username = a.username AND b.action = 'login_failed' AND b.ts BETWEEN a.ts AND a.ts + interval '2 minutes'
      GROUP BY b.username HAVING count(*) >= 5)
GROUP BY username;

-- C3: every admin role grant, who made it, to whom.
SELECT ts, username AS granted_by, detail ->> 'target' AS granted_to, detail ->> 'role' AS role
FROM audit_log WHERE action = 'role_granted' ORDER BY ts;

-- Retention: how many audit rows are old enough to delete, and the oldest row.
SELECT count(*) FILTER (WHERE ts < now() - make_interval(days => (SELECT days FROM audit_retention))) AS deletable,
       count(*) AS total, min(ts) AS oldest
FROM audit_log;

-- Retention job (run as audit_retention): delete only rows past the retention period; the trigger would refuse younger ones.
-- DELETE FROM audit_log WHERE ts < now() - make_interval(days => (SELECT days FROM audit_retention));

-- C4: the row count the restore test compares.
SELECT count(*) AS notes FROM notes;
