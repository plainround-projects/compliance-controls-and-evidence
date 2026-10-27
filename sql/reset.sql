-- Drop everything in the public schema so `make db` starts clean. Run as the superuser. Roles are kept (the schema script re-creates them if missing).
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT USAGE ON SCHEMA public TO PUBLIC;
