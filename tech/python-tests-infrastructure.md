# The tests (infrastructure)

## What it is

The pytest tests in `tests/unit/infrastructure`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/infrastructure/test_adapters.py` | 271 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/unit/infrastructure/test_adapters.py`

`tests/unit/infrastructure/test_adapters.py` lines 1 to 31:

```python
import json
import logging
from datetime import UTC, datetime, timedelta

import pytest

from notes_evidence.domain.access import CLOUD, REPOSITORY
from notes_evidence.domain.notes import User
from notes_evidence.domain.roles import Role
from notes_evidence.infrastructure.alerting import FileAlertSink
from notes_evidence.infrastructure.backup import SCRATCH, BackupError, DockerBackupRunner, run_in_container
from notes_evidence.infrastructure.catalog import CatalogError, TomlCatalog
from notes_evidence.infrastructure.clock import SystemClock
from notes_evidence.infrastructure.evidence_store import FileEvidenceStore
from notes_evidence.infrastructure.logging_setup import JsonFormatter, configure_logging
from notes_evidence.infrastructure.passwords import ScryptHasher
from notes_evidence.infrastructure.scanner import PipAuditScanner, ScanError, run_pip_audit
from notes_evidence.infrastructure.settings import SettingsError, load_settings
from notes_evidence.infrastructure.sources import (
    AwsCloudDirectory,
    GithubChanges,
    GithubRepositoryAccess,
    SourceError,
    StateCloudDirectory,
    command_json,
    file_json,
    parse_merged_prs,
    run_command,
)
from notes_evidence.infrastructure.tokens import HmacTokens
from tests.conftest import REPOSITORY_ROOT, T0
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `json`.
- It imports module `logging`.
- From `datetime` it takes `UTC, datetime, timedelta`.
- It imports module `pytest`.
- From `notes_evidence.domain.access` it takes `CLOUD, REPOSITORY`.
- From `notes_evidence.domain.notes` it takes `User`.
- From `notes_evidence.domain.roles` it takes `Role`.
- From `notes_evidence.infrastructure.alerting` it takes `FileAlertSink`.
- From `notes_evidence.infrastructure.backup` it takes `SCRATCH, BackupError, DockerBackupRunner, run_in_container`.
- From `notes_evidence.infrastructure.catalog` it takes `CatalogError, TomlCatalog`.
- From `notes_evidence.infrastructure.clock` it takes `SystemClock`.
- From `notes_evidence.infrastructure.evidence_store` it takes `FileEvidenceStore`.
- From `notes_evidence.infrastructure.logging_setup` it takes `JsonFormatter, configure_logging`.
- From `notes_evidence.infrastructure.passwords` it takes `ScryptHasher`.
- From `notes_evidence.infrastructure.scanner` it takes `PipAuditScanner, ScanError, run_pip_audit`.
- From `notes_evidence.infrastructure.settings` it takes `SettingsError, load_settings`.
- From `notes_evidence.infrastructure.sources` it takes `AwsCloudDirectory, GithubChanges, GithubRepositoryAccess, SourceError, StateCloudDirectory, command_json, file_json, parse_merged_prs, run_command`.
- From `notes_evidence.infrastructure.tokens` it takes `HmacTokens`.
- From `tests.conftest` it takes `REPOSITORY_ROOT, T0`.

`tests/unit/infrastructure/test_adapters.py` lines 33 to 33:

```python
FIXTURES = REPOSITORY_ROOT / "fixtures"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores `REPOSITORY_ROOT / 'fixtures'` in `FIXTURES`.

`tests/unit/infrastructure/test_adapters.py` lines 36 to 42:

```python
def test_scrypt_hashes_are_salted_and_verified():
    hasher = ScryptHasher()
    first, second = hasher.hash("correct horse"), hasher.hash("correct horse")
    assert first != second
    assert first.startswith("scrypt$")
    assert hasher.verify("correct horse", first)
    assert not hasher.verify("wrong horse", first)
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_scrypt_hashes_are_salted_and_verified`** checks: scrypt hashes are salted and verified.

Step by step:

- Stores the result of calling `ScryptHasher()` in `hasher`.
- Unpacks the tuple `(hasher.hash('correct horse'), hasher.hash('correct horse'))` into `(first, second)`.
- Checks that `first` is different from `second`; if not, the test fails.
- Checks that `first.startswith('scrypt$')`; if not, the test fails.
- Checks that `hasher.verify('correct horse', first)`; if not, the test fails.
- Checks that not (`hasher.verify('wrong horse', first)`); if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 45 to 47:

```python
@pytest.mark.parametrize("stored", ["!", "", "scrypt$only", "md5$a$b", "scrypt$abc$abc"])
def test_an_unusable_or_malformed_hash_never_matches(stored):
    assert not ScryptHasher().verify("anything", stored)
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.

**Test `test_an_unusable_or_malformed_hash_never_matches`** checks: an unusable or malformed hash never matches.

It takes: `stored`.

Decorators: `@pytest.mark.parametrize('stored', ['!', '', 'scrypt$only', 'md5$a$b',…`.

Step by step:

- Checks that not (`ScryptHasher().verify('anything', stored)`); if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 50 to 50:

```python
USER = User(7, "ada", Role.ADMIN, True)
```

These module-level lines:

- Stores the result of calling `User(7, 'ada', Role.ADMIN, True)` in `USER`.

`tests/unit/infrastructure/test_adapters.py` lines 53 to 57:

```python
def test_tokens_verify_until_they_expire():
    tokens = HmacTokens("s" * 32, timedelta(minutes=15))
    token = tokens.issue(USER, T0)
    assert tokens.verify(token, T0 + timedelta(minutes=14)) == 7
    assert tokens.verify(token, T0 + timedelta(minutes=16)) is None
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Test `test_tokens_verify_until_they_expire`** checks: tokens verify until they expire.

Step by step:

- Stores the result of calling `HmacTokens('s' * 32, timedelta(minutes=15))` in `tokens`.
- Stores the result of calling `tokens.issue(USER, T0)` in `token`.
- Checks that `tokens.verify(token, T0 + timedelta(minutes=14))` equals `7`; if not, the test fails.
- Checks that `tokens.verify(token, T0 + timedelta(minutes=16))` is the same object as `None`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 60 to 72:

```python
@pytest.mark.parametrize(
    "mutate",
    [
        lambda t: t[:-1] + ("0" if t[-1] != "0" else "1"),
        lambda t: "8" + t[1:],
        lambda t: t + ".x",
        lambda t: "a.b.c",
        lambda t: "",
    ],
)
def test_forged_tokens_are_refused(mutate):
    tokens = HmacTokens("s" * 32, timedelta(minutes=15))
    assert tokens.verify(mutate(tokens.issue(USER, T0)), T0) is None
```

> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Test `test_forged_tokens_are_refused`** checks: forged tokens are refused.

It takes: `mutate`.

Decorators: `@pytest.mark.parametrize('mutate', [lambda t: t[:-1] + ('0' if t[-1] !…`.

Step by step:

- Stores the result of calling `HmacTokens('s' * 32, timedelta(minutes=15))` in `tokens`.
- Checks that `tokens.verify(mutate(tokens.issue(USER, T0)), T0)` is the same object as `None`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 75 to 77:

```python
def test_a_token_signed_with_another_secret_is_refused():
    token = HmacTokens("a" * 32, timedelta(minutes=15)).issue(USER, T0)
    assert HmacTokens("b" * 32, timedelta(minutes=15)).verify(token, T0) is None
```

**Test `test_a_token_signed_with_another_secret_is_refused`** checks: a token signed with another secret is refused.

Step by step:

- Stores the result of calling `HmacTokens('a' * 32, timedelta(minutes=15)).issue(USER, T0)` in `token`.
- Checks that `HmacTokens('b' * 32, timedelta(minutes=15)).verif…` is the same object as `None`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 80 to 80:

```python
ENV = {"DATABASE_URL": "postgresql://x", "NOTES_SECRET": "s" * 32}
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

These module-level lines:

- Stores the dictionary `{'DATABASE_URL': 'postgresql://x', 'NOTES_SECRET': 's' * 32}` in `ENV`.

`tests/unit/infrastructure/test_adapters.py` lines 83 to 93:

```python
def test_settings_defaults():
    settings = load_settings(ENV)
    assert (settings.token_ttl_seconds, settings.retention_days, settings.evidence_source, settings.http_port) == (
        900,
        365,
        "fixture",
        8080,
    )
    assert settings.statement_timeout_ms == 30_000
    assert load_settings({**ENV, "DB_STATEMENT_TIMEOUT_MS": "1000"}).statement_timeout_ms == 1000
    assert settings.db_exec_prefix == ("docker", "compose", "exec", "-T", "db")
```

**Test `test_settings_defaults`** checks: settings defaults.

Step by step:

- Stores the result of calling `load_settings(ENV)` in `settings`.
- Checks that `(settings.token_ttl_seconds, settings.retention_d…` equals `(900, 365, 'fixture', 8080)`; if not, the test fails.
- Checks that `settings.statement_timeout_ms` equals `30000`; if not, the test fails.
- Checks that `load_settings({**ENV, 'DB_STATEMENT_TIMEOUT_MS': …` equals `1000`; if not, the test fails.
- Checks that `settings.db_exec_prefix` equals `('docker', 'compose', 'exec', '-T', 'db')`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 96 to 111:

```python
@pytest.mark.parametrize(
    "env",
    [
        {},
        {"DATABASE_URL": "x"},
        {**ENV, "NOTES_SECRET": "short"},
        {**ENV, "EVIDENCE_SOURCE": "cloud"},
        {**ENV, "LOG_LEVEL": "LOUD"},
        {**ENV, "TOKEN_TTL_SECONDS": "soon"},
        {**ENV, "HTTP_PORT": "0"},
        {**ENV, "DB_STATEMENT_TIMEOUT_MS": "never"},
    ],
)
def test_bad_settings_are_rejected(env):
    with pytest.raises(SettingsError):
        load_settings(env)
```

> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.

**Test `test_bad_settings_are_rejected`** checks: bad settings are rejected.

It takes: `env`.

Decorators: `@pytest.mark.parametrize('env', [{}, {'DATABASE_URL': 'x'}, {**ENV, 'N…`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(SettingsError)`:
  - Calls `load_settings(env)`.

`tests/unit/infrastructure/test_adapters.py` lines 114 to 125:

```python
def test_the_evidence_store_writes_files_and_a_manifest_with_hashes(tmp_path):
    store = FileEvidenceStore(tmp_path / "evidence")
    store.write("a.txt", "hello\n", "C1", T0, "ada", "fixture")
    store.write("b.txt", "world\n", "C2", T0, "bruno", "live")
    assert store.read("a.txt") == "hello\n"
    assert store.read("missing.txt") is None
    assert set(store.read_all()) == {"a.txt", "b.txt", "manifest.json"}
    entry = store.manifest()["b.txt"]
    assert (entry.control, entry.run_by, entry.source, entry.produced_at) == ("C2", "bruno", "live", T0)
    assert len(entry.sha256) == 64
    assert FileEvidenceStore(tmp_path / "nothing").read_all() == {}
    assert FileEvidenceStore(tmp_path / "nothing").manifest() == {}
```

> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** `tmp_path` is a built-in pytest fixture: a fresh, empty temporary folder (a `Path`) that is removed after the test.

**Test `test_the_evidence_store_writes_files_and_a_manifest_with_hashes`** checks: the evidence store writes files and a manifest with hashes.

It takes: `tmp_path`.

Step by step:

- Stores the result of calling `FileEvidenceStore(tmp_path / 'evidence')` in `store`.
- Calls `store.write('a.txt', 'hello\n', 'C1', T0, 'ada', 'fixture')`.
- Calls `store.write('b.txt', 'world\n', 'C2', T0, 'bruno', 'live')`.
- Checks that `store.read('a.txt')` equals `'hello\n'`; if not, the test fails.
- Checks that `store.read('missing.txt')` is the same object as `None`; if not, the test fails.
- Checks that `set(store.read_all())` equals `{'a.txt', 'b.txt', 'manifest.json'}`; if not, the test fails.
- Stores `store.manifest()['b.txt']` in `entry`.
- Checks that `(entry.control, entry.run_by, entry.source, entry…` equals `('C2', 'bruno', 'live', T0)`; if not, the test fails.
- Checks that `len(entry.sha256)` equals `64`; if not, the test fails.
- Checks that `FileEvidenceStore(tmp_path / 'nothing').read_all()` equals `{}`; if not, the test fails.
- Checks that `FileEvidenceStore(tmp_path / 'nothing').manifest()` equals `{}`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 128 to 130:

```python
def test_the_evidence_store_refuses_names_outside_its_folder(tmp_path):
    with pytest.raises(ValueError, match="directly in"):
        FileEvidenceStore(tmp_path).write("../x.txt", "x", "C1", T0, "ada", "fixture")
```

**Test `test_the_evidence_store_refuses_names_outside_its_folder`** checks: the evidence store refuses names outside its folder.

It takes: `tmp_path`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(ValueError, match='directly in')`:
  - Calls `FileEvidenceStore(tmp_path).write('../x.txt', 'x', 'C1', T0, 'ada', 'fixture')`.

`tests/unit/infrastructure/test_adapters.py` lines 133 to 145:

```python
def test_the_catalog_reads_the_repositorys_own_control_files():
    catalog = TomlCatalog(REPOSITORY_ROOT / "controls" / "controls.toml")
    controls = catalog.controls()
    assert [c.id for c in controls] == ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    assert controls[2].evidence[1].kind == "alert_test"
    assert controls[0].references["iso27001"] == ("A.5.15", "A.5.18", "A.8.2")
    assert controls[6].evidence == ()
    assert catalog.exceptions()[0].change == 43
    assert catalog.gaps()[0].control == "C7"
    assert catalog.people()["contractor-lee"].left_on is not None
    request = catalog.review_request()
    assert request.ticket == "SEC-17"
    assert sum(1 for d in request.decisions if not d.keep) == 1
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Test `test_the_catalog_reads_the_repositorys_own_control_files`** checks: the catalog reads the repositorys own control files.

Step by step:

- Stores the result of calling `TomlCatalog(REPOSITORY_ROOT / 'controls' / 'controls.toml')` in `catalog`.
- Stores the result of calling `catalog.controls()` in `controls`.
- Checks that `[c.id for c in controls]` equals `['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']`; if not, the test fails.
- Checks that `controls[2].evidence[1].kind` equals `'alert_test'`; if not, the test fails.
- Checks that `controls[0].references['iso27001']` equals `('A.5.15', 'A.5.18', 'A.8.2')`; if not, the test fails.
- Checks that `controls[6].evidence` equals `()`; if not, the test fails.
- Checks that `catalog.exceptions()[0].change` equals `43`; if not, the test fails.
- Checks that `catalog.gaps()[0].control` equals `'C7'`; if not, the test fails.
- Checks that `catalog.people()['contractor-lee'].left_on` is not the same object as `None`; if not, the test fails.
- Stores the result of calling `catalog.review_request()` in `request`.
- Checks that `request.ticket` equals `'SEC-17'`; if not, the test fails.
- Checks that `sum((1 for d in request.decisions if not d.keep))` equals `1`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 148 to 164:

```python
def test_a_bad_control_file_is_reported_with_its_name(tmp_path):
    (tmp_path / "controls.toml").write_text('[[control]]\nid = "C1"\n')
    with pytest.raises(CatalogError, match="missing"):
        TomlCatalog(tmp_path / "controls.toml").controls()
    (tmp_path / "controls.toml").write_text("not toml [")
    with pytest.raises(CatalogError, match="not valid TOML"):
        TomlCatalog(tmp_path / "controls.toml").controls()
    with pytest.raises(CatalogError, match="does not exist"):
        TomlCatalog(tmp_path / "controls.toml").people()
    (tmp_path / "controls.toml").write_text(
        '[[control]]\nid="C1"\nname="n"\nrequires="r"\nwhere="w"\n[[control.evidence]]\nfile="f"\nkind="mystery"\nproves="p"\nperiod="x"\nrefresh_days=1\nrefreshed="x"\n'
    )
    with pytest.raises(CatalogError, match="unknown evidence kind"):
        TomlCatalog(tmp_path / "controls.toml").controls()
    (tmp_path / "access-review.toml").write_text("[review]\nreviewer='x'\n")
    with pytest.raises(CatalogError, match="missing"):
        TomlCatalog(tmp_path / "controls.toml").review_request()
```

**Test `test_a_bad_control_file_is_reported_with_its_name`** checks: a bad control file is reported with its name.

It takes: `tmp_path`.

Step by step:

- Calls `(tmp_path / 'controls.toml').write_text('[[control]]\nid = "C1"\n')`.
- Expects the steps inside to raise the error in `pytest.raises(CatalogError, match='missing')`:
  - Calls `TomlCatalog(tmp_path / 'controls.toml').controls()`.
- Calls `(tmp_path / 'controls.toml').write_text('not toml [')`.
- Expects the steps inside to raise the error in `pytest.raises(CatalogError, match='not valid TOML')`:
  - Calls `TomlCatalog(tmp_path / 'controls.toml').controls()`.
- Expects the steps inside to raise the error in `pytest.raises(CatalogError, match='does not exist')`:
  - Calls `TomlCatalog(tmp_path / 'controls.toml').people()`.
- Calls `(tmp_path / 'controls.toml').write_text('[[control]]\nid="C1"\nname="n"\nrequires="r"\nwhere="w"\n[[control.e…`.
- Expects the steps inside to raise the error in `pytest.raises(CatalogError, match='unknown evidence kind')`:
  - Calls `TomlCatalog(tmp_path / 'controls.toml').controls()`.
- Calls `(tmp_path / 'access-review.toml').write_text("[review]\nreviewer='x'\n")`.
- Expects the steps inside to raise the error in `pytest.raises(CatalogError, match='missing')`:
  - Calls `TomlCatalog(tmp_path / 'controls.toml').review_request()`.

`tests/unit/infrastructure/test_adapters.py` lines 167 to 182:

```python
def test_the_fixture_sources_parse_the_shapes_of_gh_and_aws():
    access = GithubRepositoryAccess(file_json(FIXTURES / "github-collaborators.json")).collaborators()
    assert [(e.principal, e.level) for e in access] == [
        ("ada", "admin"),
        ("bruno", "write"),
        ("chen", "write"),
        ("dana", "read"),
    ]
    assert all(e.system == REPOSITORY for e in access)
    changes = GithubChanges(
        file_json(FIXTURES / "github-merged-prs.json"), file_json(FIXTURES / "deploy-log.json")
    ).merged_changes()
    assert [c.number for c in changes] == [38, 39, 40, 41, 42, 43]
    assert changes[1].approvers == ("ada", "bruno")
    assert changes[5].approvers == ()
    assert all(c.deploy_id for c in changes)
```

**Test `test_the_fixture_sources_parse_the_shapes_of_gh_and_aws`** checks: the fixture sources parse the shapes of gh and aws.

Step by step:

- Stores the result of calling `GithubRepositoryAccess(file_json(FIXTURES / 'github-collaborators.json')).collaborators()` in `access`.
- Checks that `[(e.principal, e.level) for e in access]` equals `[('ada', 'admin'), ('bruno', 'write'), ('chen', '…`; if not, the test fails.
- Checks that `all((e.system == REPOSITORY for e in access))`; if not, the test fails.
- Stores the result of calling `GithubChanges(file_json(FIXTURES / 'github-merged-prs.json'), file_json(FIXTURES / 'deplo…` in `changes`.
- Checks that `[c.number for c in changes]` equals `[38, 39, 40, 41, 42, 43]`; if not, the test fails.
- Checks that `changes[1].approvers` equals `('ada', 'bruno')`; if not, the test fails.
- Checks that `changes[5].approvers` equals `()`; if not, the test fails.
- Checks that `all((c.deploy_id for c in changes))`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 185 to 187:

```python
def test_a_commit_missing_from_the_deploy_log_has_no_deploy_id():
    prs = json.loads((FIXTURES / "github-merged-prs.json").read_text())
    assert parse_merged_prs(prs[:1], [])[0].deploy_id == ""
```

**Test `test_a_commit_missing_from_the_deploy_log_has_no_deploy_id`** checks: a commit missing from the deploy log has no deploy id.

Step by step:

- Stores the result of calling `json.loads((FIXTURES / 'github-merged-prs.json').read_text())` in `prs`.
- Checks that `parse_merged_prs(prs[:1], [])[0].deploy_id` equals `''`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 190 to 198:

```python
def test_the_state_cloud_directory_seeds_itself_and_removes_a_user(tmp_path):
    cloud = StateCloudDirectory(tmp_path / "state" / "cloud.json", FIXTURES / "aws-iam-users.json")
    assert [(e.system, e.principal) for e in cloud.users()] == [(CLOUD, "ada"), (CLOUD, "contractor-lee")]
    cloud.remove_user("contractor-lee")
    assert [e.principal for e in cloud.users()] == ["ada"]
    assert [
        e.principal
        for e in StateCloudDirectory(tmp_path / "state" / "cloud.json", FIXTURES / "aws-iam-users.json").users()
    ] == ["ada"]
```

**Test `test_the_state_cloud_directory_seeds_itself_and_removes_a_user`** checks: the state cloud directory seeds itself and removes a user.

It takes: `tmp_path`.

Step by step:

- Stores the result of calling `StateCloudDirectory(tmp_path / 'state' / 'cloud.json', FIXTURES / 'aws-iam-users.json')` in `cloud`.
- Checks that `[(e.system, e.principal) for e in cloud.users()]` equals `[(CLOUD, 'ada'), (CLOUD, 'contractor-lee')]`; if not, the test fails.
- Calls `cloud.remove_user('contractor-lee')`.
- Checks that `[e.principal for e in cloud.users()]` equals `['ada']`; if not, the test fails.
- Checks that `[e.principal for e in StateCloudDirectory(tmp_pat…` equals `['ada']`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 201 to 212:

```python
def test_the_aws_directory_runs_the_aws_commands():
    calls: list[list[str]] = []

    def runner(argv: list[str]) -> str:
        calls.append(argv)
        return (FIXTURES / "aws-iam-users.json").read_text()

    cloud = AwsCloudDirectory(runner)
    assert [e.principal for e in cloud.users()] == ["ada", "contractor-lee"]
    cloud.remove_user("contractor-lee")
    assert calls[0][:3] == ["aws", "iam", "list-users"]
    assert calls[1] == ["aws", "iam", "delete-user", "--user-name", "contractor-lee"]
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Test `test_the_aws_directory_runs_the_aws_commands`** checks: the aws directory runs the aws commands.

Step by step:

- Declares `calls` as a `list[list[str]]` and stores the list `[]` in it.
- Defines a helper function `runner(argv)`.
  - Calls `calls.append(argv)`.
  - Gives back the result of calling `(FIXTURES / 'aws-iam-users.json').read_text()`.
- Stores the result of calling `AwsCloudDirectory(runner)` in `cloud`.
- Checks that `[e.principal for e in cloud.users()]` equals `['ada', 'contractor-lee']`; if not, the test fails.
- Calls `cloud.remove_user('contractor-lee')`.
- Checks that `calls[0][:3]` equals `['aws', 'iam', 'list-users']`; if not, the test fails.
- Checks that `calls[1]` equals `['aws', 'iam', 'delete-user', '--user-name', 'con…`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 215 to 216:

```python
def test_command_json_runs_the_command_and_parses_its_output():
    assert command_json(lambda argv: '{"a": 1}', ["x"])() == {"a": 1}
```

**Test `test_command_json_runs_the_command_and_parses_its_output`** checks: command json runs the command and parses its output.

Step by step:

- Checks that `command_json(lambda argv: '{"a": 1}', ['x'])()` equals `{'a': 1}`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 219 to 224:

```python
def test_run_command_returns_output_and_wraps_failures():
    assert run_command(["echo", "hi"]).strip() == "hi"
    with pytest.raises(SourceError, match="exited 1"):
        run_command(["false"])
    with pytest.raises(SourceError):
        run_command(["definitely-not-a-command-xyz"])
```

**Test `test_run_command_returns_output_and_wraps_failures`** checks: run command returns output and wraps failures.

Step by step:

- Checks that `run_command(['echo', 'hi']).strip()` equals `'hi'`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(SourceError, match='exited 1')`:
  - Calls `run_command(['false'])`.
- Expects the steps inside to raise the error in `pytest.raises(SourceError)`:
  - Calls `run_command(['definitely-not-a-command-xyz'])`.

`tests/unit/infrastructure/test_adapters.py` lines 227 to 236:

```python
class Recorder:
    def __init__(self, fail_on: str = "") -> None:
        self.calls: list[tuple[list[str], bytes | None]] = []
        self.fail_on = fail_on

    def __call__(self, argv: list[str], stdin: bytes | None) -> bytes:
        self.calls.append((argv, stdin))
        if self.fail_on and self.fail_on in argv:
            raise BackupError("boom")
        return b""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.

**Class `Recorder`**.

Its methods, in order:

**Method `__init__` of class `Recorder`.**

It takes: `fail_on` (a `str`), default `''`.

It gives back a `None`.

Step by step:

- Declares `self.calls` as a `list[tuple[list[str], bytes | None]]` and stores the list `[]` in it.
- Stores `fail_on` in `self.fail_on`.

**Method `__call__` of class `Recorder`.**

It takes: `argv` (a `list[str]`); `stdin` (a `bytes | None`).

It gives back a `bytes`.

Step by step:

- Calls `self.calls.append((argv, stdin))`.
- If `self.fail_on` and `self.fail_on` is in `argv`:
  - Stops here by raising `BackupError('boom')`.
- Gives back the number `b''`.

`tests/unit/infrastructure/test_adapters.py` lines 239 to 258:

```python
def test_the_backup_runner_dumps_restores_into_a_scratch_database_and_drops_it():
    class Execute(Recorder):
        def __call__(self, argv, stdin):
            super().__call__(argv, stdin)
            if "pg_dump" in argv:
                return b"DUMP"
            if "SELECT count(*) FROM notes" in argv:
                return b"12408\n"
            return b""

    execute = Execute()
    runner = DockerBackupRunner(("docker", "compose", "exec", "-T", "db"), "postgres", "notes", execute)
    assert isinstance(runner.backup(), datetime)
    assert runner.restore_and_count("notes") == (12408, 12408)
    commands = [" ".join(argv) for argv, _ in execute.calls]
    assert any("pg_dump -U postgres -d notes --format=custom" in c for c in commands)
    assert any(f"CREATE DATABASE {SCRATCH}" in c for c in commands)
    assert commands[-1].endswith(f"DROP DATABASE IF EXISTS {SCRATCH}")
    restore = next(call for call in execute.calls if "pg_restore" in call[0])
    assert restore[1] == b"DUMP"
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Test `test_the_backup_runner_dumps_restores_into_a_scratch_database_and_drops_it`** checks: the backup runner dumps restores into a scratch database and drops it.

Step by step:

- Defines a class `Execute`.
- Stores the result of calling `Execute()` in `execute`.
- Stores the result of calling `DockerBackupRunner(('docker', 'compose', 'exec', '-T', 'db'), 'postgres', 'notes', execut…` in `runner`.
- Checks that `isinstance(runner.backup(), datetime)`; if not, the test fails.
- Checks that `runner.restore_and_count('notes')` equals `(12408, 12408)`; if not, the test fails.
- Stores a new list made by a loop (`[' '.join(argv) for argv, _ in execute.calls]`) in `commands`.
- Checks that `any(('pg_dump -U postgres -d notes --format=custom' in c for c in com…`; if not, the test fails.
- Checks that `any((f'CREATE DATABASE {SCRATCH}' in c for c in commands))`; if not, the test fails.
- Checks that `commands[-1].endswith(f'DROP DATABASE IF EXISTS {SCRATCH}')`; if not, the test fails.
- Stores the result of calling `next((call for call in execute.calls if 'pg_restore' in call[0]))` in `restore`.
- Checks that `restore[1]` equals `b'DUMP'`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 261 to 266:

```python
def test_the_scratch_database_is_dropped_even_when_the_restore_fails():
    execute = Recorder(fail_on="pg_restore")
    runner = DockerBackupRunner(("db",), "postgres", "notes", execute)
    with pytest.raises(BackupError):
        runner.restore_and_count("notes")
    assert any(f"DROP DATABASE IF EXISTS {SCRATCH}" in " ".join(argv) for argv, _ in execute.calls[-1:])
```

**Test `test_the_scratch_database_is_dropped_even_when_the_restore_fails`** checks: the scratch database is dropped even when the restore fails.

Step by step:

- Stores the result of calling `Recorder(fail_on='pg_restore')` in `execute`.
- Stores the result of calling `DockerBackupRunner(('db',), 'postgres', 'notes', execute)` in `runner`.
- Expects the steps inside to raise the error in `pytest.raises(BackupError)`:
  - Calls `runner.restore_and_count('notes')`.
- Checks that `any((f'DROP DATABASE IF EXISTS {SCRATCH}' in ' '.join(argv) for argv,…`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 269 to 271:

```python
def test_only_the_notes_table_can_be_counted():
    with pytest.raises(BackupError, match="unsupported"):
        DockerBackupRunner(("db",), "postgres", "notes", Recorder()).restore_and_count("users")
```

**Test `test_only_the_notes_table_can_be_counted`** checks: only the notes table can be counted.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(BackupError, match='unsupported')`:
  - Calls `DockerBackupRunner(('db',), 'postgres', 'notes', Recorder()).restore_and_count('users')`.

`tests/unit/infrastructure/test_adapters.py` lines 274 to 279:

```python
def test_run_in_container_wraps_failures():
    assert run_in_container(["cat"], b"abc") == b"abc"
    with pytest.raises(BackupError, match="exited"):
        run_in_container(["false"], None)
    with pytest.raises(BackupError):
        run_in_container(["definitely-not-a-command-xyz"], None)
```

**Test `test_run_in_container_wraps_failures`** checks: run in container wraps failures.

Step by step:

- Checks that `run_in_container(['cat'], b'abc')` equals `b'abc'`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(BackupError, match='exited')`:
  - Calls `run_in_container(['false'], None)`.
- Expects the steps inside to raise the error in `pytest.raises(BackupError)`:
  - Calls `run_in_container(['definitely-not-a-command-xyz'], None)`.

`tests/unit/infrastructure/test_adapters.py` lines 282 to 289:

```python
AUDIT_JSON = json.dumps(
    {
        "dependencies": [
            {"name": "flask", "version": "3.1.3", "vulns": []},
            {"name": "x", "version": "1", "vulns": [{"id": "V-1", "fix_versions": ["2"]}]},
        ]
    }
)
```

These module-level lines:

- Stores the result of calling `json.dumps({'dependencies': [{'name': 'flask', 'version': '3.1.3', 'vulns': []}, {'name':…` in `AUDIT_JSON`.

`tests/unit/infrastructure/test_adapters.py` lines 292 to 304:

```python
def test_the_scanner_wraps_pip_audit_with_the_run_that_produced_it():
    commands: list[list[str]] = []

    def run(argv: list[str]) -> str:
        commands.append(argv)
        return AUDIT_JSON

    now = datetime(2026, 10, 22, 9, 0, tzinfo=UTC)
    report = PipAuditScanner("requirements.lock", {"GITHUB_RUN_ID": "9001"}, lambda: now, run).scan()
    assert (report.run_id, report.packages_scanned, report.verdict) == ("9001", 2, "fail")
    assert commands[0][-2:] == ["-r", "requirements.lock"]
    local = PipAuditScanner("requirements.lock", {}, lambda: now, run).scan()
    assert local.run_id == "local-20261022T090000Z"
```

**Test `test_the_scanner_wraps_pip_audit_with_the_run_that_produced_it`** checks: the scanner wraps pip audit with the run that produced it.

Step by step:

- Declares `commands` as a `list[list[str]]` and stores the list `[]` in it.
- Defines a helper function `run(argv)`.
  - Calls `commands.append(argv)`.
  - Gives back `AUDIT_JSON`.
- Stores the result of calling `datetime(2026, 10, 22, 9, 0, tzinfo=UTC)` in `now`.
- Stores the result of calling `PipAuditScanner('requirements.lock', {'GITHUB_RUN_ID': '9001'}, lambda: now, run).scan()` in `report`.
- Checks that `(report.run_id, report.packages_scanned, report.v…` equals `('9001', 2, 'fail')`; if not, the test fails.
- Checks that `commands[0][-2:]` equals `['-r', 'requirements.lock']`; if not, the test fails.
- Stores the result of calling `PipAuditScanner('requirements.lock', {}, lambda: now, run).scan()` in `local`.
- Checks that `local.run_id` equals `'local-20261022T090000Z'`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 307 to 313:

```python
def test_run_pip_audit_accepts_exit_0_and_1_and_rejects_the_rest():
    assert run_pip_audit(["python3", "-c", "print('{}')"]).strip() == "{}"
    assert run_pip_audit(["python3", "-c", "import sys; print('{}'); sys.exit(1)"]).strip() == "{}"
    with pytest.raises(ScanError):
        run_pip_audit(["python3", "-c", "import sys; sys.exit(2)"])
    with pytest.raises(ScanError):
        run_pip_audit(["definitely-not-a-command-xyz"])
```

**Test `test_run_pip_audit_accepts_exit_0_and_1_and_rejects_the_rest`** checks: run pip audit accepts exit 0 and 1 and rejects the rest.

Step by step:

- Checks that `run_pip_audit(['python3', '-c', "print('{}')"]).s…` equals `'{}'`; if not, the test fails.
- Checks that `run_pip_audit(['python3', '-c', "import sys; prin…` equals `'{}'`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(ScanError)`:
  - Calls `run_pip_audit(['python3', '-c', 'import sys; sys.exit(2)'])`.
- Expects the steps inside to raise the error in `pytest.raises(ScanError)`:
  - Calls `run_pip_audit(['definitely-not-a-command-xyz'])`.

`tests/unit/infrastructure/test_adapters.py` lines 316 to 320:

```python
def test_the_alert_sink_appends_to_a_file(tmp_path):
    sink = FileAlertSink(tmp_path / "state" / "alerts.log")
    sink.send("ALERT one")
    sink.send("ALERT two")
    assert (tmp_path / "state" / "alerts.log").read_text() == "ALERT one\nALERT two\n"
```

**Test `test_the_alert_sink_appends_to_a_file`** checks: the alert sink appends to a file.

It takes: `tmp_path`.

Step by step:

- Stores the result of calling `FileAlertSink(tmp_path / 'state' / 'alerts.log')` in `sink`.
- Calls `sink.send('ALERT one')`.
- Calls `sink.send('ALERT two')`.
- Checks that `(tmp_path / 'state' / 'alerts.log').read_text()` equals `'ALERT one\nALERT two\n'`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 323 to 330:

```python
def test_the_json_formatter_keeps_only_whitelisted_fields():
    record = logging.LogRecord("notes.http", logging.INFO, "f", 1, "request", (), None)
    record.status = 200
    record.password = "never"
    document = json.loads(JsonFormatter().format(record))
    assert document["status"] == 200
    assert "password" not in document
    assert document["level"] == "INFO"
```

**Test `test_the_json_formatter_keeps_only_whitelisted_fields`** checks: the json formatter keeps only whitelisted fields.

Step by step:

- Stores the result of calling `logging.LogRecord('notes.http', logging.INFO, 'f', 1, 'request', (), None)` in `record`.
- Stores the number `200` in `record.status`.
- Stores the text `'never'` in `record.password`.
- Stores the result of calling `json.loads(JsonFormatter().format(record))` in `document`.
- Checks that `document['status']` equals `200`; if not, the test fails.
- Checks that `'password'` is not in `document`; if not, the test fails.
- Checks that `document['level']` equals `'INFO'`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 333 to 338:

```python
def test_configure_logging_installs_one_json_handler():
    configure_logging("WARNING")
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
    assert root.level == logging.WARNING
```

**Test `test_configure_logging_installs_one_json_handler`** checks: configure logging installs one json handler.

Step by step:

- Calls `configure_logging('WARNING')`.
- Stores the result of calling `logging.getLogger()` in `root`.
- Checks that `len(root.handlers)` equals `1`; if not, the test fails.
- Checks that `isinstance(root.handlers[0].formatter, JsonFormatter)`; if not, the test fails.
- Checks that `root.level` equals `logging.WARNING`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 341 to 342:

```python
def test_the_system_clock_is_timezone_aware():
    assert SystemClock().now().tzinfo is not None
```

**Test `test_the_system_clock_is_timezone_aware`** checks: the system clock is timezone aware.

Step by step:

- Checks that `SystemClock().now().tzinfo` is not the same object as `None`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/unit/infrastructure
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check tests/unit/infrastructure/test_adapters.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_scrypt_hashes_are_salted_and_verified` check?
   **Answer:** it checks: scrypt hashes are salted and verified.
2. What does the test `test_an_unusable_or_malformed_hash_never_matches` check?
   **Answer:** it checks: an unusable or malformed hash never matches.
3. What does the test `test_tokens_verify_until_they_expire` check?
   **Answer:** it checks: tokens verify until they expire.
4. What does the test `test_forged_tokens_are_refused` check?
   **Answer:** it checks: forged tokens are refused.
5. What does the test `test_a_token_signed_with_another_secret_is_refused` check?
   **Answer:** it checks: a token signed with another secret is refused.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
