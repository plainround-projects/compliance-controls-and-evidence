# Environment variables and .env files

## What it is

An **environment variable** is a named text value that every program started from a shell can read. A **`.env` file** is a plain
file of `NAME=value` lines that tools load into the environment. Here three different readers use the same file: Make, Docker
Compose and the Python program.

## Why this repository uses it

Twelve-factor configuration: settings live in the environment, validated once at start-up, and secrets never live in code.
`.env.example` documents every setting. **The passwords in it are throwaway development values for a database that exists only
while the container runs** (the file says so); nothing in it is a real secret.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `.env.example` | Committed. Every setting, with a comment. |
| `.env` | Local copy created by `make env`; ignored by git. |
| `Makefile` | `-include .env` and `export`. |
| `docker-compose.yml` | `${POSTGRES_PASSWORD:?set it in .env}` and friends. |
| `src/notes_evidence/infrastructure/settings.py` | Reads and validates the environment. |

## How it works underneath

- Make reads `.env` as variable assignments and, because of `export`, copies them into the environment of every command it
  starts. A value in `.env` takes priority over a variable of the same name already in your shell (unless you use `make -e`).
- Docker Compose reads `.env` itself to fill `${...}` placeholders in the compose file.
- The program receives its environment at start-up; `os.environ` is a dictionary of strings.
- A missing or unusable value stops the program at once with exit code 2 and a message that names the variable.

## Walkthrough of this repository's use

`.env.example`:

```ini
# PostgreSQL superuser and the throwaway passwords of a database that lives only on this machine
# while the container runs. Change them if you share the machine. Nothing here is a real secret.
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev-only-superuser-password
POSTGRES_DB=notes
POSTGRES_PORT=55440
APP_RW_PASSWORD=dev-only-app-password
MIGRATOR_PASSWORD=dev-only-migrator-password
RETENTION_PASSWORD=dev-only-retention-password
# The notes API connects as app_rw (least privilege); the evidence collectors connect as the superuser.
DATABASE_URL=postgresql://app_rw:dev-only-app-password@localhost:55440/notes
ADMIN_DATABASE_URL=postgresql://postgres:dev-only-superuser-password@localhost:55440/notes
```

The first group configures PostgreSQL: the superuser, the throwaway passwords of the three roles, the database name and the host
port (55440, chosen to avoid clashing with a PostgreSQL already on the laptop).

`.env.example`:

```ini
# The notes API connects as app_rw (least privilege); the evidence collectors connect as the superuser.
DATABASE_URL=postgresql://app_rw:dev-only-app-password@localhost:55440/notes
ADMIN_DATABASE_URL=postgresql://postgres:dev-only-superuser-password@localhost:55440/notes
```

`DATABASE_URL` is what the **API** uses: it logs in as `app_rw`, the least-privilege role. `ADMIN_DATABASE_URL` is used only by the
evidence collectors that need to read roles and run `pg_dump`. A URL has the form `postgresql://user:password@host:port/database`.

`.env.example`:

```ini
# Signs session tokens. Set a long random value anywhere real.
NOTES_SECRET=dev-only-signing-secret-change-me-before-sharing
TOKEN_TTL_SECONDS=900
AUDIT_RETENTION_DAYS=365
```

`NOTES_SECRET` signs session tokens and must be at least 32 characters (the loader refuses anything shorter). The other lines set the
token lifetime, the audit retention and the statement timeout.

`.env.example`:

```ini
# Where the evidence pack is written and the controls are described.
EVIDENCE_DIR=evidence
CONTROLS_FILE=controls/controls.toml
# fixture reads the made-up repository, deploy and cloud data under fixtures/; live runs gh and aws.
EVIDENCE_SOURCE=fixture
# Who runs the collectors, for the "run by" column of the index.
EVIDENCE_RUN_BY=ada
STATE_DIR=state
```

Where the pack goes, which controls file to use, `EVIDENCE_SOURCE=fixture` (made-up data; `live` would run `gh` and `aws`), who ran the
collectors, the log level and the API port.

`src/notes_evidence/infrastructure/settings.py`:

```python
def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value:
        raise SettingsError(f"{name} is required")
    return value
```

`src/notes_evidence/infrastructure/settings.py`:

```python
def load_settings(env: Mapping[str, str]) -> Settings:
    """Validate and collect the settings. A signing secret shorter than 32 characters is refused."""
    secret = _required(env, "NOTES_SECRET")
    if len(secret) < 32:
        raise SettingsError("NOTES_SECRET must be at least 32 characters")
    source = env.get("EVIDENCE_SOURCE", "fixture")
    if source not in ("fixture", "live"):
        raise SettingsError(f"EVIDENCE_SOURCE must be fixture or live, got {source!r}")
```

`_required` fails with `NAME is required` when a value is empty. `load_settings` receives the environment as a mapping (so tests can
pass a plain dictionary), checks the secret length and the allowed values of `EVIDENCE_SOURCE` and `LOG_LEVEL`, and converts the numbers
with `_positive_int`.

### The complete file `.env.example`, line by line

`.env.example` lines 1 to 16:

```ini
# PostgreSQL superuser and the throwaway passwords of a database that lives only on this machine
# while the container runs. Change them if you share the machine. Nothing here is a real secret.
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev-only-superuser-password
POSTGRES_DB=notes
POSTGRES_PORT=55440
APP_RW_PASSWORD=dev-only-app-password
MIGRATOR_PASSWORD=dev-only-migrator-password
RETENTION_PASSWORD=dev-only-retention-password
# The notes API connects as app_rw (least privilege); the evidence collectors connect as the superuser.
DATABASE_URL=postgresql://app_rw:dev-only-app-password@localhost:55440/notes
ADMIN_DATABASE_URL=postgresql://postgres:dev-only-superuser-password@localhost:55440/notes
# Signs session tokens. Set a long random value anywhere real.
NOTES_SECRET=dev-only-signing-secret-change-me-before-sharing
TOKEN_TTL_SECONDS=900
AUDIT_RETENTION_DAYS=365
```

> **In plain words.** A `.env` file is a list of `NAME=value` lines that become settings (environment variables) for the programs; a line starting with `#` is a comment.

- `POSTGRES_USER` is set to `postgres`. The author's comment: PostgreSQL superuser and the throwaway passwords of a database that lives only on this machine while the container runs. Change them if you share the machine. Nothing here is a real secret.
- `POSTGRES_PASSWORD` is set to `dev-only-superuser-password`.
- `POSTGRES_DB` is set to `notes`.
- `POSTGRES_PORT` is set to `55440`.
- `APP_RW_PASSWORD` is set to `dev-only-app-password`.
- `MIGRATOR_PASSWORD` is set to `dev-only-migrator-password`.
- `RETENTION_PASSWORD` is set to `dev-only-retention-password`.
- `DATABASE_URL` is set to `postgresql://app_rw:dev-only-app-password@localhost:55440/notes`. The author's comment: The notes API connects as app_rw (least privilege); the evidence collectors connect as the superuser.
- `ADMIN_DATABASE_URL` is set to `postgresql://postgres:dev-only-superuser-password@localhost:55440/notes`.
- `NOTES_SECRET` is set to `dev-only-signing-secret-change-me-before-sharing`. The author's comment: Signs session tokens. Set a long random value anywhere real.
- `TOKEN_TTL_SECONDS` is set to `900`.
- `AUDIT_RETENTION_DAYS` is set to `365`.

`.env.example` lines 17 to 28:

```ini
# A statement running longer than this is cancelled by the database. Generous, so a busy machine does not fail a test.
DB_STATEMENT_TIMEOUT_MS=30000
# Where the evidence pack is written and the controls are described.
EVIDENCE_DIR=evidence
CONTROLS_FILE=controls/controls.toml
# fixture reads the made-up repository, deploy and cloud data under fixtures/; live runs gh and aws.
EVIDENCE_SOURCE=fixture
# Who runs the collectors, for the "run by" column of the index.
EVIDENCE_RUN_BY=ada
STATE_DIR=state
LOG_LEVEL=INFO
HTTP_PORT=8080
```

- `DB_STATEMENT_TIMEOUT_MS` is set to `30000`. The author's comment: A statement running longer than this is cancelled by the database. Generous, so a busy machine does not fail a test.
- `EVIDENCE_DIR` is set to `evidence`. The author's comment: Where the evidence pack is written and the controls are described.
- `CONTROLS_FILE` is set to `controls/controls.toml`.
- `EVIDENCE_SOURCE` is set to `fixture`. The author's comment: fixture reads the made-up repository, deploy and cloud data under fixtures/; live runs gh and aws.
- `EVIDENCE_RUN_BY` is set to `ada`. The author's comment: Who runs the collectors, for the "run by" column of the index.
- `STATE_DIR` is set to `state`.
- `LOG_LEVEL` is set to `INFO`.
- `HTTP_PORT` is set to `8080`.

## Try it yourself

```bash
cat .env.example | head -12
```
Prints the first settings.

```bash
NOTES_SECRET=short .venv/bin/controls-evidence verify; echo "exit: $?"
```
Prints `configuration error: ...` and `exit: 2` (the first missing or bad setting is named; load the others with
`set -a; . ./.env; set +a` to see the secret check).

```bash
git check-ignore -v .env
```
Prints the `.gitignore` line that ignores `.env`.

```bash
grep -n "required\|at least" src/notes_evidence/infrastructure/settings.py | head -5
```
Shows where settings are required and checked.

```bash
make verify
```
Loads `.env` through Make and verifies the pack.

## Mistakes people make

- **Committing `.env`.** It is in `.gitignore`. The values in `.env.example` are throwaway development values, and real secrets must
  never be committed.
- **Using the superuser URL for the API.** The API uses `app_rw`.
- **Expecting the shell to override `.env` inside `make`.** The value in `.env` wins unless you use `make -e`.
- **A short signing secret.** The loader refuses under 32 characters.
- **Forgetting that Compose reads `.env` too**, so a typo affects both.

## Check yourself

1. Which three programs read `.env`?
   **Answer:** Make, Docker Compose and the Python program (through the environment Make passes on).
2. Why does the API connect as `app_rw`?
   **Answer:** Least privilege: that role cannot create accounts or alter the audit log.
3. What does `EVIDENCE_SOURCE=fixture` do?
   **Answer:** Uses made-up data under `fixtures/` instead of running `gh` and `aws`.
4. What stops a short `NOTES_SECRET`?
   **Answer:** `load_settings` raises `SettingsError`; the program exits with code 2.
5. Why is `.env.example` committed and `.env` not?
   **Answer:** The example documents settings; `.env` is local.

## Further reading

- The Twelve-Factor App, III. Config: <https://12factor.net/config>
- Docker Compose, environment variables: <https://docs.docker.com/compose/how-tos/environment-variables/>
- GNU Make, `include` and `export`: <https://www.gnu.org/software/make/manual/make.html#Include>
