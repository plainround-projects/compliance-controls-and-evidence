# pytest

## What it is

A **test** is a small function that runs part of the program and states what must be true afterwards, with the
word `assert`. **pytest** is a tool that finds the test functions in a folder, runs them, and reports which passed
and which failed. A **fixture** is a helper function that prepares something a test needs (a temporary folder, a
sample object) and is handed to the test by name.

## Why this repository uses it

The evidence is only credible if the service really behaves as claimed. The unit tests cover every rule with fakes (no
network, no database). The integration tests talk to a real PostgreSQL and check that the database itself refuses what it must
(an update or delete of the audit log, a missing grant). One end-to-end test runs the whole scenario and also proves that
tampering with an evidence file is caught.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/**` | 166 tests per layer; no services needed. |
| `tests/integration/` | 11 tests against PostgreSQL (`make up` first). |
| `tests/e2e/test_scenario.py` | The whole scenario, marked `e2e`. |
| `tests/conftest.py`, `tests/integration/conftest.py` | Shared fakes and the database fixtures. |
| `pyproject.toml` `[tool.pytest.ini_options]` | Where to look, the options to always use, the markers. |

## How it works underneath

1. pytest starts, reads `pyproject.toml`, and walks the folders in `testpaths`.
2. It imports each file named `test_*.py`. Each function whose name starts with `test_` is one test.
3. For each test it looks at the function's parameter names. A parameter named `tmp_path` or `capsys` is a built-in
   fixture; a name defined with `@pytest.fixture` in the file or in `conftest.py` is a custom one. pytest builds
   those values and passes them in.
4. It runs the function. If every `assert` holds and nothing is raised, the test passes. pytest rewrites `assert`
   lines when it imports a test file, so a failure shows both sides of the comparison.
5. After the run it prints one dot per passing test, then a summary line.

## Walkthrough of this repository's use

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
```

- `testpaths = ["tests"]`: when run with no arguments, look only in `tests/`.
- `addopts = "-ra --strict-markers"`: options added to every run. `-ra` prints a short reason line for every
  test that is not a plain pass (skipped, failed, error). `--strict-markers` turns an unknown `@pytest.mark.xyz`
  into an error instead of a silent typo.

`tests/conftest.py`:

```python
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
```

`__file__` is the path of this file. `.resolve()` makes it absolute. `.parents[1]` is two levels up (the folder
holding `tests/`), which is the repository root. Tests use it to find the real `docs/` folder.

`tests/conftest.py`:

```python
class FixedClock:
    """A clock the test moves by hand."""

    def __init__(self, moment: datetime = T0) -> None:
        self.moment = moment

    def now(self) -> datetime:
        return self.moment

    def advance(self, **delta: float) -> None:
        self.moment += timedelta(**delta)
```

Shared test helpers: small in-memory stand-ins for the real adapters, so most tests touch neither a network nor a database.

`tests/unit/domain/test_roles_notes_audit_alerts.py`:

```python
def test_each_role_holds_exactly_its_permissions(role, granted):
    assert {p for p in Permission if allowed(role, p)} == granted


def test_a_valid_username_and_password_pass_through():
```

The simplest kind of test: call a function, compare the result with the expected value using `assert`.

`tests/e2e/test_scenario.py`:

```python
@pytest.fixture
def scenario(tmp_path, monkeypatch):
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not set: run `make up` and use `make test-e2e`")
    for name, value in (
        ("EVIDENCE_DIR", tmp_path / "evidence"),
        ("STATE_DIR", tmp_path / "state"),
        ("REPORT_DIR", tmp_path / "build"),
    ):
        monkeypatch.setenv(name, str(value))
    return tmp_path
```

`@pytest.fixture` marks a function as a fixture: a test that has a parameter named `scenario` receives its return value. `monkeypatch.setenv` sets an environment variable for this test only and undoes it afterwards; `tmp_path` is a fresh empty folder per test. `tmp_path` is a fresh empty folder per test, deleted afterwards. `monkeypatch.setenv` changes an
environment variable for this test only and undoes it at the end. The type hints (`Path`, `pytest.MonkeyPatch`)
are optional for pytest, but help the reader.

`tests/unit/interfaces/test_http_app.py`:

```python
def test_health_reports_the_database(client):
    response = client.get("/healthz")
    assert (response.status_code, response.get_json()) == (200, {"status": "ok"})
    client.healthy["up"] = False
    assert client.get("/healthz").status_code == 503


def test_login_returns_a_token_and_a_wrong_password_is_401(client):
```

This test damages one copied document, runs the real command, and checks the exit code (`== 1`) and the output
with `capsys`, the fixture that captures what the program prints. The tests prove each rule fails when the document
is damaged, not only that the good document passes.

`tests/unit/infrastructure/test_adapters.py`:

```python
@pytest.mark.parametrize("stored", ["!", "", "scrypt$only", "md5$a$b", "scrypt$abc$abc"])
def test_an_unusable_or_malformed_hash_never_matches(stored):
    assert not ScryptHasher().verify("anything", stored)
```

`@pytest.mark.parametrize` runs the same test body once per row of data. A failure names the row that broke.

### Integration and end-to-end tests

`tests/integration/conftest.py`:

```python
@pytest.fixture(scope="session")
def settings() -> Settings:
    if not os.environ.get("DATABASE_URL") or not os.environ.get("ADMIN_DATABASE_URL"):
        pytest.skip("DATABASE_URL and ADMIN_DATABASE_URL are not set: run `make up` and use `make test-integration`")
    return load_settings(os.environ)
```

- `scope="session"` builds the fixture once for the whole run, not once per test.
- `pytest.skip(...)` stops the test with a **skipped** result and a reason. Without a database the integration tests skip,
  saying why (`run make up`), instead of failing.
`pyproject.toml`:

```toml
markers = [
    "integration: needs PostgreSQL from docker-compose.yml (make up)",
    "e2e: runs the lesson's scenario end to end against PostgreSQL (make up first)",
]
```

The two markers `integration` and `e2e` are registered, so `--strict-markers` accepts them. `make test-integration` runs
`-m integration` and `make test-e2e` runs `-m e2e`. They need PostgreSQL; the 166 unit tests do not.

## Try it yourself

```bash
.venv/bin/pytest -q
```
Prints rows of dots (`s` marks a skipped test) and a summary like `166 passed, 12 skipped`. The 11 integration tests and the end-to-end test need PostgreSQL; without it they skip and say why (`DATABASE_URL is not set: run make up ...`).

```bash
.venv/bin/pytest --collect-only -q tests/unit/domain/test_roles_notes_audit_alerts.py
```
Lists the test names without running them, one `path::test_name` per line.

```bash
.venv/bin/pytest -q -k audit
```
Runs only tests whose name contains `audit`: the tests about the audit trail.

```bash
.venv/bin/pytest -q tests/unit/domain/test_roles_notes_audit_alerts.py -x -vv
```
`-x` stops at the first failure; `-vv` shows each test name and result.

```bash
.venv/bin/pytest --fixtures -q | grep -E "tmp_path|capsys|monkeypatch" | head
```
Shows the built-in fixtures this repository uses.

## Mistakes people make

- **Tests that depend on each other's order.** Each test here builds its own data (a fresh `tmp_path`).
- **Asserting only the happy path.** The tests here also break a document on purpose and check the rule code.
- **Forgetting `test_` in a name**, so the test never runs. Check the count in the summary.
- **Editing the real `docs/` from a test.** The CLI tests copy `docs/` to a temporary folder first.

## Check yourself

1. How does pytest know which functions are tests?
   **Answer:** Files named `test_*.py`, functions named `test_*`.
2. What does `tmp_path` give a test?
   **Answer:** A fresh, empty temporary folder that is removed afterwards.
3. What does `-ra` print?
   **Answer:** A short summary line for every test that is not a plain pass.
4. Why does the CLI test copy `docs/` first?
   **Answer:** So the test can damage a document without changing the real repository.
5. What does `parametrize` do?
   **Answer:** It runs one test function several times with different data.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- Configuration (`pyproject.toml`): <https://docs.pytest.org/en/stable/reference/customize.html>
