# The tests (application)

## What it is

The pytest tests in `tests/unit/application`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/application/test_collect.py` | 339 lines.  |
| `tests/unit/application/test_notes_service.py` | 138 lines.  |
| `tests/unit/application/test_reporting_and_edges.py` | 78 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/unit/application/test_collect.py`

`tests/unit/application/test_collect.py` lines 1 to 15:

```python
import json
from datetime import UTC, date, datetime, timedelta

import pytest

from notes_evidence.application import evidence_collect as collect
from notes_evidence.application.exercise import exercise_service
from notes_evidence.domain.access import CLOUD, DATABASE, REPOSITORY, AccessEntry
from notes_evidence.domain.audit import AuditAction, AuditEvent
from notes_evidence.domain.changes import MergedChange
from notes_evidence.domain.controls import Control, EvidenceSpec, Gap, RecordedException
from notes_evidence.domain.review import Decision, Person, ReviewRequest
from notes_evidence.domain.roles import Role
from notes_evidence.domain.scan import ScanReport
from tests.conftest import T0, MemoryEvidenceStore, Rig
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `json`.
- From `datetime` it takes `UTC, date, datetime, timedelta`.
- It imports module `pytest`.
- From `notes_evidence.application` it takes `evidence_collect as collect`.
- From `notes_evidence.application.exercise` it takes `exercise_service`.
- From `notes_evidence.domain.access` it takes `CLOUD, DATABASE, REPOSITORY, AccessEntry`.
- From `notes_evidence.domain.audit` it takes `AuditAction, AuditEvent`.
- From `notes_evidence.domain.changes` it takes `MergedChange`.
- From `notes_evidence.domain.controls` it takes `Control, EvidenceSpec, Gap, RecordedException`.
- From `notes_evidence.domain.review` it takes `Decision, Person, ReviewRequest`.
- From `notes_evidence.domain.roles` it takes `Role`.
- From `notes_evidence.domain.scan` it takes `ScanReport`.
- From `tests.conftest` it takes `T0, MemoryEvidenceStore, Rig`.

`tests/unit/application/test_collect.py` lines 18 to 20:

```python
class Repo:
    def collaborators(self):
        return [AccessEntry(REPOSITORY, "ada", "admin"), AccessEntry(REPOSITORY, "bruno", "write")]
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Class `Repo`**.

Its methods, in order:

**Method `collaborators` of class `Repo`.**

Step by step:

- Gives back the list `[AccessEntry(REPOSITORY, 'ada', 'admin'), AccessEntry(REPOSITORY, 'br…`.

`tests/unit/application/test_collect.py` lines 23 to 25:

```python
class Db:
    def roles(self):
        return [AccessEntry(DATABASE, "app_rw", "standard"), AccessEntry(DATABASE, "postgres", "superuser")]
```

**Class `Db`**.

Its methods, in order:

**Method `roles` of class `Db`.**

Step by step:

- Gives back the list `[AccessEntry(DATABASE, 'app_rw', 'standard'), AccessEntry(DATABASE, '…`.

`tests/unit/application/test_collect.py` lines 28 to 36:

```python
class Cloud:
    def __init__(self):
        self.names = ["ada", "contractor-lee"]

    def users(self):
        return [AccessEntry(CLOUD, name) for name in self.names]

    def remove_user(self, name):
        self.names.remove(name)
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Class `Cloud`**.

Its methods, in order:

**Method `__init__` of class `Cloud`.**

Step by step:

- Stores the list `['ada', 'contractor-lee']` in `self.names`.

**Method `users` of class `Cloud`.**

Step by step:

- Gives back a new list made by a loop (`[AccessEntry(CLOUD, name) for name in self.names]`).

**Method `remove_user` of class `Cloud`.**

It takes: `name`.

Step by step:

- Calls `self.names.remove(name)`.

`tests/unit/application/test_collect.py` lines 39 to 45:

```python
class Changes:
    def merged_changes(self):
        at = datetime(2026, 10, 21, 9, tzinfo=UTC)
        return [
            MergedChange(41, "bruno", at, "a41c9de" + "0" * 33, ("ada",), "deploy-41"),
            MergedChange(43, "ada", at, "c7d1e55" + "0" * 33, (), "deploy-43"),
        ]
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Class `Changes`**.

Its methods, in order:

**Method `merged_changes` of class `Changes`.**

Step by step:

- Stores the result of calling `datetime(2026, 10, 21, 9, tzinfo=UTC)` in `at`.
- Gives back the list `[MergedChange(41, 'bruno', at, 'a41c9de' + '0' * 33, ('ada',), 'deplo…`.

`tests/unit/application/test_collect.py` lines 48 to 53:

```python
class Backup:
    def backup(self):
        return T0 - timedelta(hours=6)

    def restore_and_count(self, table):
        return 12408, 12408
```

**Class `Backup`**.

Its methods, in order:

**Method `backup` of class `Backup`.**

Step by step:

- Gives back `T0 - timedelta(hours=6)`.

**Method `restore_and_count` of class `Backup`.**

It takes: `table`.

Step by step:

- Gives back the tuple `(12408, 12408)`.

`tests/unit/application/test_collect.py` lines 56 to 58:

```python
class Scanner:
    def scan(self):
        return ScanReport("run-77", "pip-audit", "2.10", T0, "requirements.lock", 12, ())
```

**Class `Scanner`**.

Its methods, in order:

**Method `scan` of class `Scanner`.**

Step by step:

- Gives back the result of calling `ScanReport('run-77', 'pip-audit', '2.10', T0, 'requirements.lock', 12, ())`.

`tests/unit/application/test_collect.py` lines 61 to 66:

```python
class Sink:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)
```

**Class `Sink`**.

Its methods, in order:

**Method `__init__` of class `Sink`.**

Step by step:

- Stores the list `[]` in `self.sent`.

**Method `send` of class `Sink`.**

It takes: `message`.

Step by step:

- Calls `self.sent.append(message)`.

`tests/unit/application/test_collect.py` lines 69 to 69:

```python
class Catalog:
```

**Class `Catalog`**.

`tests/unit/application/test_collect.py` lines 70 to 123:

```python
    def controls(self):
        def spec(file, kind):
            return EvidenceSpec(file, kind, f"proves {kind}", "point in time", 30, "monthly")

        return [
            Control(
                "C1",
                "Access control",
                "r",
                "w",
                {"iso27001": ("A.5.15",), "soc2": ("CC6.1",)},
                (spec(collect.ACCESS_FILE, "access_list"),),
            ),
            Control(
                "C2",
                "Change management",
                "r",
                "w",
                {"iso27001": ("A.8.32",), "soc2": ("CC8.1",)},
                (spec(collect.CHANGES_FILE, "changes"),),
            ),
            Control(
                "C3",
                "Logging",
                "r",
                "w",
                {"iso27001": ("A.8.15",), "soc2": ("CC7.2",)},
                (spec(collect.LOG_FILE, "log_sample"), spec(collect.ALERT_FILE, "alert_test")),
            ),
            Control(
                "C4",
                "Backup",
                "r",
                "w",
                {"iso27001": ("A.8.13",), "soc2": ("A1.2",)},
                (spec(collect.RESTORE_FILE, "restore"),),
            ),
            Control(
                "C5",
                "Vulnerabilities",
                "r",
                "w",
                {"iso27001": ("A.8.8",), "soc2": ("CC7.1",)},
                (spec(collect.SCAN_FILE, "scan"),),
            ),
            Control(
                "C6",
                "Access review",
                "r",
                "w",
                {"iso27001": ("A.5.18",), "soc2": ("CC6.2",)},
                (spec(collect.REVIEW_FILE, "review"),),
            ),
        ]
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Method `controls` of class `Catalog`.**

Step by step:

- Defines a helper function `spec(file, kind)`.
  - Gives back the result of calling `EvidenceSpec(file, kind, f'proves {kind}', 'point in time', 30, 'monthly')`.
- Gives back the list `[Control('C1', 'Access control', 'r', 'w', {'iso27001': ('A.5.15',), …`.

`tests/unit/application/test_collect.py` lines 125 to 126:

```python
    def exceptions(self):
        return [RecordedException("EXC-1", "C2", 43, "hotfix", "SEC-16")]
```

**Method `exceptions` of class `Catalog`.**

Step by step:

- Gives back the list `[RecordedException('EXC-1', 'C2', 43, 'hotfix', 'SEC-16')]`.

`tests/unit/application/test_collect.py` lines 128 to 129:

```python
    def gaps(self):
        return []
```

**Method `gaps` of class `Catalog`.**

Step by step:

- Gives back the list `[]`.

`tests/unit/application/test_collect.py` lines 131 to 132:

```python
    def people(self):
        return {"contractor-lee": Person("contractor-lee", "Contractor", date(2026, 9, 18))}
```

**Method `people` of class `Catalog`.**

Step by step:

- Gives back the dictionary `{'contractor-lee': Person('contractor-lee', 'Contractor', date(2026, …`.

`tests/unit/application/test_collect.py` lines 134 to 143:

```python
    def review_request(self):
        keep = [
            Decision(REPOSITORY, "ada", True, "needed"),
            Decision(REPOSITORY, "bruno", True, "needed"),
            Decision(DATABASE, "app_rw", True, "service account"),
            Decision(DATABASE, "postgres", True, "administrative"),
            Decision(CLOUD, "ada", True, "deploys"),
            Decision(CLOUD, "contractor-lee", False, "left on 2026-09-18"),
        ]
        return ReviewRequest("eli", date(2026, 10, 22), "SEC-17", tuple(keep))
```

**Method `review_request` of class `Catalog`.**

Step by step:

- Stores the list `[Decision(REPOSITORY, 'ada', True, 'needed'), Decision(REPOSITORY, 'b…` in `keep`.
- Gives back the result of calling `ReviewRequest('eli', date(2026, 10, 22), 'SEC-17', tuple(keep))`.

`tests/unit/application/test_collect.py` lines 146 to 168:

```python
@pytest.fixture
def pack():
    rig = Rig()
    store = MemoryEvidenceStore()
    collector = collect.Collector(store, rig.clock, "ada", "fixture")
    cloud = Cloud()
    catalog = Catalog()
    exercise_service(rig.users, rig.hasher, rig.service)
    rig.clock.advance(minutes=1)
    found = rig.users.find_by_username("ada")
    assert found is not None
    ada = found[0]
    sink = Sink()
    collect.run_alert_test(
        collector, rig.service, rig.audit, sink, lambda: rig.service.grant_role(ada, "chen", Role.ADMIN), "bruno"
    )
    collect.collect_log_sample(collector, rig.audit)
    collect.collect_changes(collector, Changes())
    collect.run_restore_test(collector, Backup())
    collect.collect_scan(collector, Scanner())
    outcome = collect.review_access(collector, Repo(), Db(), cloud, catalog)
    collect.build_index(collector, catalog, "| framework table |")
    return collector, store, catalog, cloud, outcome, sink
```

> **In plain words.** A **fixture** is a helper function marked `@pytest.fixture`. A test that names it as a parameter receives its return value, prepared fresh for that test.
> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Function `pack`.**

Decorators: `@pytest.fixture`.

Step by step:

- Stores the result of calling `Rig()` in `rig`.
- Stores the result of calling `MemoryEvidenceStore()` in `store`.
- Stores the result of calling `collect.Collector(store, rig.clock, 'ada', 'fixture')` in `collector`.
- Stores the result of calling `Cloud()` in `cloud`.
- Stores the result of calling `Catalog()` in `catalog`.
- Calls `exercise_service(rig.users, rig.hasher, rig.service)`.
- Calls `rig.clock.advance(minutes=1)`.
- Stores the result of calling `rig.users.find_by_username('ada')` in `found`.
- Checks that `found` is not the same object as `None`; if not, the test fails.
- Stores `found[0]` in `ada`.
- Stores the result of calling `Sink()` in `sink`.
- Calls `collect.run_alert_test(collector, rig.service, rig.audit, sink, lambda: rig.service.grant_role(ada, 'chen', R…`.
- Calls `collect.collect_log_sample(collector, rig.audit)`.
- Calls `collect.collect_changes(collector, Changes())`.
- Calls `collect.run_restore_test(collector, Backup())`.
- Calls `collect.collect_scan(collector, Scanner())`.
- Stores the result of calling `collect.review_access(collector, Repo(), Db(), cloud, catalog)` in `outcome`.
- Calls `collect.build_index(collector, catalog, '| framework table |')`.
- Gives back the tuple `(collector, store, catalog, cloud, outcome, sink)`.

`tests/unit/application/test_collect.py` lines 171 to 179:

```python
def verify(pack, **changes):
    _, store, catalog, *_ = pack
    return collect.verify(
        store,
        catalog.controls(),
        changes.get("exceptions", catalog.exceptions()),
        changes.get("gaps", []),
        date(2026, 10, 23),
    )
```

> **In plain words.** `*items` **unpacks** a sequence into separate values; `**options` does the same for a dictionary's keys and values.

**Function `verify`.**

It takes: `pack`; `**changes` (any extra named values).

Step by step:

- Unpacks `pack` into `(_, store, catalog, *_)`.
- Gives back the result of calling `collect.verify(store, catalog.controls(), changes.get('exceptions', catalog.exceptions())…`.

`tests/unit/application/test_collect.py` lines 182 to 185:

```python
def test_the_whole_pack_verifies(pack):
    report = verify(pack)
    assert report.ok, report.findings
    assert report.findings == ()
```

> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_the_whole_pack_verifies`** checks: the whole pack verifies.

It takes: `pack`.

Step by step:

- Stores the result of calling `verify(pack)` in `report`.
- Checks that `report.ok` with the message `report.findings`; if not, the test fails.
- Checks that `report.findings` equals `()`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 188 to 196:

```python
def test_access_is_collected_from_the_three_systems_and_the_leaver_is_removed(pack):
    _, store, _, cloud, outcome, _ = pack
    assert outcome.findings == ()
    assert outcome.before is not None
    assert outcome.after is not None
    assert len(outcome.before.entries) - len(outcome.after.entries) == 1
    assert cloud.names == ["ada"]
    assert "contractor-lee" not in store.read(collect.ACCESS_FILE)
    assert "Removed: cloud account users contractor-lee." in store.read(collect.REVIEW_FILE)
```

**Test `test_access_is_collected_from_the_three_systems_and_the_leaver_is_removed`** checks: access is collected from the three systems and the leaver is removed.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, _, cloud, outcome, _)`.
- Checks that `outcome.findings` equals `()`; if not, the test fails.
- Checks that `outcome.before` is not the same object as `None`; if not, the test fails.
- Checks that `outcome.after` is not the same object as `None`; if not, the test fails.
- Checks that `len(outcome.before.entries) - len(outcome.after.e…` equals `1`; if not, the test fails.
- Checks that `cloud.names` equals `['ada']`; if not, the test fails.
- Checks that `'contractor-lee'` is not in `store.read(collect.ACCESS_FILE)`; if not, the test fails.
- Checks that `'Removed: cloud account users contractor-lee.'` is in `store.read(collect.REVIEW_FILE)`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 199 to 205:

```python
def test_the_alert_test_keeps_the_alert_beside_the_time_of_the_action(pack):
    _, store, _, _, _, sink = pack
    text = store.read(collect.ALERT_FILE)
    assert "test action at 2026-10-22T09:01:00Z" in text
    assert "ALERT [failed-logins] 2026-10-22T09:01:00Z 5 failed logins for account bruno within 2 minutes" in text
    assert "ALERT [admin-granted]" in text
    assert len(sink.sent) == 2
```

**Test `test_the_alert_test_keeps_the_alert_beside_the_time_of_the_action`** checks: the alert test keeps the alert beside the time of the action.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, _, _, _, sink)`.
- Stores the result of calling `store.read(collect.ALERT_FILE)` in `text`.
- Checks that `'test action at 2026-10-22T09:01:00Z'` is in `text`; if not, the test fails.
- Checks that `'ALERT [failed-logins] 2026-10-22T09:01:00Z 5 fai…` is in `text`; if not, the test fails.
- Checks that `'ALERT [admin-granted]'` is in `text`; if not, the test fails.
- Checks that `len(sink.sent)` equals `2`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 208 to 212:

```python
def test_the_log_sample_has_log_lines_and_no_note_text(pack):
    _, store, *_ = pack
    sample = store.read(collect.LOG_FILE)
    assert "action=login_failed" in sample
    assert "Call back" not in sample
```

**Test `test_the_log_sample_has_log_lines_and_no_note_text`** checks: the log sample has log lines and no note text.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Stores the result of calling `store.read(collect.LOG_FILE)` in `sample`.
- Checks that `'action=login_failed'` is in `sample`; if not, the test fails.
- Checks that `'Call back'` is not in `sample`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 215 to 229:

```python
def test_changes_restore_and_scan_are_written_with_manifest_entries(pack):
    _, store, *_ = pack
    assert store.read(collect.CHANGES_FILE).splitlines()[0].startswith('"number"')
    assert "result: verified" in store.read(collect.RESTORE_FILE)
    assert json.loads(store.read(collect.SCAN_FILE))["run_id"] == "run-77"
    assert set(store.manifest()) >= {
        collect.ACCESS_FILE,
        collect.CHANGES_FILE,
        collect.LOG_FILE,
        collect.ALERT_FILE,
        collect.RESTORE_FILE,
        collect.SCAN_FILE,
        collect.REVIEW_FILE,
        "INDEX.md",
    }
```

> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.

**Test `test_changes_restore_and_scan_are_written_with_manifest_entries`** checks: changes restore and scan are written with manifest entries.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Checks that `store.read(collect.CHANGES_FILE).splitlines()[0].startswith('"number"…`; if not, the test fails.
- Checks that `'result: verified'` is in `store.read(collect.RESTORE_FILE)`; if not, the test fails.
- Checks that `json.loads(store.read(collect.SCAN_FILE))['run_id…` equals `'run-77'`; if not, the test fails.
- Checks that `set(store.manifest())` is at least `{collect.ACCESS_FILE, collect.CHANGES_FILE, colle…`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 232 to 238:

```python
def test_the_index_lists_each_file_who_ran_it_the_exceptions_and_the_gaps(pack):
    _, store, *_ = pack
    index = store.read("INDEX.md")
    assert "| C1-access-list.txt | C1 Access control | proves access_list | ada | 2026-10-22 |" in index
    assert "EXC-1 (C2): hotfix Follow-up: SEC-16." in index
    assert "## Tracked gaps\n\nNone." in index
    assert "| framework table |" in index
```

**Test `test_the_index_lists_each_file_who_ran_it_the_exceptions_and_the_gaps`** checks: the index lists each file who ran it the exceptions and the gaps.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Stores the result of calling `store.read('INDEX.md')` in `index`.
- Checks that `'| C1-access-list.txt | C1 Access control | prove…` is in `index`; if not, the test fails.
- Checks that `'EXC-1 (C2): hotfix Follow-up: SEC-16.'` is in `index`; if not, the test fails.
- Checks that `'## Tracked gaps\n\nNone.'` is in `index`; if not, the test fails.
- Checks that `'| framework table |'` is in `index`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 241 to 252:

```python
def test_an_incomplete_review_changes_nothing(pack):
    collector, _, _, cloud, *_ = pack

    class Short(Catalog):
        def review_request(self):
            request = super().review_request()
            return ReviewRequest(request.reviewer, request.reviewed_on, request.ticket, request.decisions[:-1])

    cloud.names.append("contractor-lee")
    outcome = collect.review_access(collector, Repo(), Db(), cloud, Short())
    assert [f.code for f in outcome.findings] == ["ARV001"]
    assert "contractor-lee" in cloud.names
```

> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Test `test_an_incomplete_review_changes_nothing`** checks: an incomplete review changes nothing.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(collector, _, _, cloud, *_)`.
- Defines a class `Short`.
- Calls `cloud.names.append('contractor-lee')`.
- Stores the result of calling `collect.review_access(collector, Repo(), Db(), cloud, Short())` in `outcome`.
- Checks that `[f.code for f in outcome.findings]` equals `['ARV001']`; if not, the test fails.
- Checks that `'contractor-lee'` is in `cloud.names`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 255 to 268:

```python
def test_removing_from_a_system_this_build_does_not_manage_is_refused(pack):
    collector, *_ = pack

    class Wants(Catalog):
        def review_request(self):
            request = super().review_request()
            flipped = tuple(
                Decision(REPOSITORY, "bruno", False, "left") if (d.system, d.principal) == (REPOSITORY, "bruno") else d
                for d in request.decisions
            )
            return ReviewRequest("eli", request.reviewed_on, "SEC-17", flipped)

    with pytest.raises(NotImplementedError):
        collect.review_access(collector, Repo(), Db(), Cloud(), Wants())
```

> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Test `test_removing_from_a_system_this_build_does_not_manage_is_refused`** checks: removing from a system this build does not manage is refused.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(collector, *_)`.
- Defines a class `Wants`.
- Expects the steps inside to raise the error in `pytest.raises(NotImplementedError)`:
  - Calls `collect.review_access(collector, Repo(), Db(), Cloud(), Wants())`.

`tests/unit/application/test_collect.py` lines 271 to 274:

```python
def test_a_missing_file_is_an_error(pack):
    _, store, *_ = pack
    del store.files[collect.SCAN_FILE]
    assert "EVD002" in {f.code for f in verify(pack).errors}
```

> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.

**Test `test_a_missing_file_is_an_error`** checks: a missing file is an error.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Removes `store.files[collect.SCAN_FILE]`.
- Checks that `'EVD002'` is in `{f.code for f in verify(pack).errors}`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 277 to 280:

```python
def test_an_empty_file_is_worse_than_a_missing_one(pack):
    _, store, *_ = pack
    store.files[collect.SCAN_FILE] = " \n"
    assert "EVD002" in {f.code for f in verify(pack).errors}
```

**Test `test_an_empty_file_is_worse_than_a_missing_one`** checks: an empty file is worse than a missing one.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Stores the text `' \n'` in `store.files[collect.SCAN_FILE]`.
- Checks that `'EVD002'` is in `{f.code for f in verify(pack).errors}`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 283 to 286:

```python
def test_a_hand_edited_file_fails_its_hash(pack):
    _, store, *_ = pack
    store.files[collect.CHANGES_FILE] += '999,"x","2026-10-22T00:00:00Z","abc","ada","d"\n'
    assert "EVD003" in {f.code for f in verify(pack).errors}
```

**Test `test_a_hand_edited_file_fails_its_hash`** checks: a hand edited file fails its hash.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Adds the text `'999,"x","2026-10-22T00:00:00Z","abc","ada","d"\n'` to `store.files[collect.CHANGES_FILE]`.
- Checks that `'EVD003'` is in `{f.code for f in verify(pack).errors}`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 289 to 292:

```python
def test_a_file_with_no_manifest_entry_is_unaccounted_for(pack):
    _, store, *_ = pack
    del store.entries[collect.SCAN_FILE]
    assert "EVD003" in {f.code for f in verify(pack).errors}
```

**Test `test_a_file_with_no_manifest_entry_is_unaccounted_for`** checks: a file with no manifest entry is unaccounted for.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Removes `store.entries[collect.SCAN_FILE]`.
- Checks that `'EVD003'` is in `{f.code for f in verify(pack).errors}`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 295 to 298:

```python
def test_an_unclaimed_file_is_reported(pack):
    _, store, *_ = pack
    store.files["notes.txt"] = "stray"
    assert "EVD004" in {f.code for f in verify(pack).errors}
```

**Test `test_an_unclaimed_file_is_reported`** checks: an unclaimed file is reported.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Stores the text `'stray'` in `store.files['notes.txt']`.
- Checks that `'EVD004'` is in `{f.code for f in verify(pack).errors}`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 301 to 305:

```python
def test_a_stale_artifact_is_a_warning_not_an_error(pack):
    _, store, catalog, *_ = pack
    report = collect.verify(store, catalog.controls(), catalog.exceptions(), [], date(2027, 1, 1))
    assert report.ok
    assert {f.code for f in report.warnings} == {"EVD005"}
```

**Test `test_a_stale_artifact_is_a_warning_not_an_error`** checks: a stale artifact is a warning not an error.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, catalog, *_)`.
- Stores the result of calling `collect.verify(store, catalog.controls(), catalog.exceptions(), [], date(2027, 1, 1))` in `report`.
- Checks that `report.ok`; if not, the test fails.
- Checks that `{f.code for f in report.warnings}` equals `{'EVD005'}`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 308 to 312:

```python
def test_an_unlisted_exception_in_the_data_fails(pack):
    assert "EVD006" in {f.code for f in verify(pack, exceptions=[]).errors}
    assert "EVD006" in {
        f.code for f in verify(pack, exceptions=[RecordedException("EXC-1", "C2", 43, "hotfix", "")]).errors
    }
```

**Test `test_an_unlisted_exception_in_the_data_fails`** checks: an unlisted exception in the data fails.

It takes: `pack`.

Step by step:

- Checks that `'EVD006'` is in `{f.code for f in verify(pack, exceptions=[]).erro…`; if not, the test fails.
- Checks that `'EVD006'` is in `{f.code for f in verify(pack, exceptions=[Recorde…`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 315 to 326:

```python
def test_a_control_with_no_evidence_needs_a_tracked_gap(pack):
    _, store, catalog, *_ = pack
    controls = [
        *catalog.controls(),
        Control("C7", "Backup encryption", "r", "w", {"iso27001": ("A.8.24",), "soc2": ("CC6.1",)}, ()),
    ]
    untracked = collect.verify(store, controls, catalog.exceptions(), [], date(2026, 10, 23))
    assert "EVD001" in {f.code for f in untracked.errors}
    tracked = collect.verify(
        store, controls, catalog.exceptions(), [Gap("C7", "planned", "SEC-21", date(2026, 12, 1))], date(2026, 10, 23)
    )
    assert tracked.ok
```

**Test `test_a_control_with_no_evidence_needs_a_tracked_gap`** checks: a control with no evidence needs a tracked gap.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, catalog, *_)`.
- Stores the list `[*catalog.controls(), Control('C7', 'Backup encryption', 'r', 'w', {'…` in `controls`.
- Stores the result of calling `collect.verify(store, controls, catalog.exceptions(), [], date(2026, 10, 23))` in `untracked`.
- Checks that `'EVD001'` is in `{f.code for f in untracked.errors}`; if not, the test fails.
- Stores the result of calling `collect.verify(store, controls, catalog.exceptions(), [Gap('C7', 'planned', 'SEC-21', dat…` in `tracked`.
- Checks that `tracked.ok`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 329 to 343:

```python
def test_a_gap_record_must_be_complete_and_real(pack):
    _, store, catalog, *_ = pack
    controls = [*catalog.controls(), Control("C7", "x", "r", "w", {"iso27001": ("A.8.24",), "soc2": ("CC6.1",)}, ())]
    incomplete = collect.verify(
        store, controls, catalog.exceptions(), [Gap("C7", "", "SEC-21", None)], date(2026, 10, 23)
    )
    assert "EVD008" in {f.code for f in incomplete.errors}
    stale = collect.verify(
        store,
        catalog.controls(),
        catalog.exceptions(),
        [Gap("C1", "x", "SEC-1", date(2026, 12, 1)), Gap("C9", "x", "SEC-2", date(2026, 12, 1))],
        date(2026, 10, 23),
    )
    assert [f.code for f in stale.errors].count("EVD008") == 2
```

**Test `test_a_gap_record_must_be_complete_and_real`** checks: a gap record must be complete and real.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, catalog, *_)`.
- Stores the list `[*catalog.controls(), Control('C7', 'x', 'r', 'w', {'iso27001': ('A.8…` in `controls`.
- Stores the result of calling `collect.verify(store, controls, catalog.exceptions(), [Gap('C7', '', 'SEC-21', None)], da…` in `incomplete`.
- Checks that `'EVD008'` is in `{f.code for f in incomplete.errors}`; if not, the test fails.
- Stores the result of calling `collect.verify(store, catalog.controls(), catalog.exceptions(), [Gap('C1', 'x', 'SEC-1', …` in `stale`.
- Checks that `[f.code for f in stale.errors].count('EVD008')` equals `2`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 346 to 352:

```python
def test_a_control_needs_two_framework_references(pack):
    _, store, catalog, *_ = pack
    thin = Control(
        "C1", "Access control", "r", "w", {"iso27001": ("A.5.15",), "soc2": ()}, catalog.controls()[0].evidence
    )
    report = collect.verify(store, [thin, *catalog.controls()[1:]], catalog.exceptions(), [], date(2026, 10, 23))
    assert "EVD009" in {f.code for f in report.errors}
```

**Test `test_a_control_needs_two_framework_references`** checks: a control needs two framework references.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, catalog, *_)`.
- Stores the result of calling `Control('C1', 'Access control', 'r', 'w', {'iso27001': ('A.5.15',), 'soc2': ()}, catalog.…` in `thin`.
- Stores the result of calling `collect.verify(store, [thin, *catalog.controls()[1:]], catalog.exceptions(), [], date(202…` in `report`.
- Checks that `'EVD009'` is in `{f.code for f in report.errors}`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 355 to 391:

```python
@pytest.mark.parametrize(
    ("file", "mutation"),
    [
        (collect.ACCESS_FILE, lambda text: text.replace("## database roles\n", "")),
        (collect.CHANGES_FILE, lambda text: "wrong,header\n1,2\n"),
        (collect.CHANGES_FILE, lambda text: text.splitlines()[0] + "\n"),
        (collect.LOG_FILE, lambda text: "this is not a log line\n"),
        (collect.ALERT_FILE, lambda text: text.replace("ALERT [", "note [")),
        (collect.ALERT_FILE, lambda text: text.replace("test action at", "action at")),
        (
            collect.ALERT_FILE,
            lambda text: text.replace("test action at 2026-10-22T09:01:00Z", "test action at 2026-10-22T09:59:00Z"),
        ),
        (collect.RESTORE_FILE, lambda text: text.replace("result: verified", "result: MISMATCH")),
        (collect.RESTORE_FILE, lambda text: "nothing\n"),
        (collect.SCAN_FILE, lambda text: "not json"),
        (collect.SCAN_FILE, lambda text: text.replace('"run_id": "run-77"', '"run_id": ""')),
        (collect.SCAN_FILE, lambda text: text.replace('"verdict": "pass"', '"verdict": "fail"')),
        (
            collect.REVIEW_FILE,
            lambda text: text.replace("Removed: cloud account users contractor-lee.", "Removed: nothing."),
        ),
        (collect.REVIEW_FILE, lambda text: text.replace("Proof:", "Check:")),
        (collect.REVIEW_FILE, lambda text: text + "still listed\n"),
    ],
)
def test_each_artifact_is_checked_for_what_it_must_say(pack, file, mutation):
    from notes_evidence.domain.evidence import ManifestEntry, digest

    _, store, *_ = pack
    new = mutation(store.files[file])
    store.files[file] = new
    entry = store.entries[file]
    store.entries[file] = ManifestEntry(
        entry.file, entry.control, entry.produced_at, entry.run_by, entry.source, digest(new)
    )
    assert "EVD007" in {f.code for f in verify(pack).errors}
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.

**Test `test_each_artifact_is_checked_for_what_it_must_say`** checks: each artifact is checked for what it must say.

It takes: `pack`; `file`; `mutation`.

Decorators: `@pytest.mark.parametrize(('file', 'mutation'), [(collect.ACCESS_FILE, …`.

Step by step:

- Imports `from notes_evidence.domain.evidence import ManifestEntry, digest`.
- Unpacks `pack` into `(_, store, *_)`.
- Stores the result of calling `mutation(store.files[file])` in `new`.
- Stores `new` in `store.files[file]`.
- Stores `store.entries[file]` in `entry`.
- Stores the result of calling `ManifestEntry(entry.file, entry.control, entry.produced_at, entry.run_by, entry.source, d…` in `store.entries[file]`.
- Checks that `'EVD007'` is in `{f.code for f in verify(pack).errors}`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 394 to 404:

```python
def test_a_removed_principal_still_in_the_access_list_is_caught(pack):
    from notes_evidence.domain.evidence import ManifestEntry, digest

    _, store, *_ = pack
    new = store.files[collect.ACCESS_FILE].replace("ada\n", "ada\ncontractor-lee\n")
    store.files[collect.ACCESS_FILE] = new
    entry = store.entries[collect.ACCESS_FILE]
    store.entries[collect.ACCESS_FILE] = ManifestEntry(
        entry.file, entry.control, entry.produced_at, entry.run_by, entry.source, digest(new)
    )
    assert any("still in" in f.message for f in verify(pack).errors)
```

**Test `test_a_removed_principal_still_in_the_access_list_is_caught`** checks: a removed principal still in the access list is caught.

It takes: `pack`.

Step by step:

- Imports `from notes_evidence.domain.evidence import ManifestEntry, digest`.
- Unpacks `pack` into `(_, store, *_)`.
- Stores the result of calling `store.files[collect.ACCESS_FILE].replace('ada\n', 'ada\ncontractor-lee\n')` in `new`.
- Stores `new` in `store.files[collect.ACCESS_FILE]`.
- Stores `store.entries[collect.ACCESS_FILE]` in `entry`.
- Stores the result of calling `ManifestEntry(entry.file, entry.control, entry.produced_at, entry.run_by, entry.source, d…` in `store.entries[collect.ACCESS_FILE]`.
- Checks that `any(('still in' in f.message for f in verify(pack).errors))`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 407 to 410:

```python
def test_a_missing_index_is_reported(pack):
    _, store, *_ = pack
    del store.files["INDEX.md"]
    assert any(f.subject == "INDEX.md" for f in verify(pack).errors)
```

**Test `test_a_missing_index_is_reported`** checks: a missing index is reported.

It takes: `pack`.

Step by step:

- Unpacks `pack` into `(_, store, *_)`.
- Removes `store.files['INDEX.md']`.
- Checks that `any((f.subject == 'INDEX.md' for f in verify(pack).errors))`; if not, the test fails.

`tests/unit/application/test_collect.py` lines 413 to 420:

```python
def test_the_exercise_uses_the_service_as_four_roles_and_refuses_two_requests():
    rig = Rig()
    summary = exercise_service(rig.users, rig.hasher, rig.service, new_password=lambda: "throwaway-password-1")
    assert set(summary.users) == {"ada", "bruno", "chen", "dana"}
    assert (summary.notes_created, summary.refusals) == (3, 2)
    assert len(rig.notes.rows) == 2
    assert [e.action for e in rig.audit.events if e.outcome == "denied"] == [AuditAction.ACCESS_DENIED] * 2
    assert not any(isinstance(e, AuditEvent) and "throwaway" in repr(e) for e in rig.audit.events)
```

**Test `test_the_exercise_uses_the_service_as_four_roles_and_refuses_two_requests`** checks: the exercise uses the service as four roles and refuses two requests.

Step by step:

- Stores the result of calling `Rig()` in `rig`.
- Stores the result of calling `exercise_service(rig.users, rig.hasher, rig.service, new_password=lambda: 'throwaway-pass…` in `summary`.
- Checks that `set(summary.users)` equals `{'ada', 'bruno', 'chen', 'dana'}`; if not, the test fails.
- Checks that `(summary.notes_created, summary.refusals)` equals `(3, 2)`; if not, the test fails.
- Checks that `len(rig.notes.rows)` equals `2`; if not, the test fails.
- Checks that `[e.action for e in rig.audit.events if e.outcome …` equals `[AuditAction.ACCESS_DENIED] * 2`; if not, the test fails.
- Checks that not (`any((isinstance(e, AuditEvent) and 'throwaway' in repr(e) for e in ri…`); if not, the test fails.

### `tests/unit/application/test_notes_service.py`

`tests/unit/application/test_notes_service.py` lines 1 to 12:

```python
import pytest

from notes_evidence.domain.audit import AuditAction
from notes_evidence.domain.errors import (
    InvalidCredentialsError,
    NotAllowedError,
    NotAuthenticatedError,
    NotFoundError,
    ValidationError,
)
from notes_evidence.domain.roles import Role
from tests.conftest import Rig
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `pytest`.
- From `notes_evidence.domain.audit` it takes `AuditAction`.
- From `notes_evidence.domain.errors` it takes `InvalidCredentialsError, NotAllowedError, NotAuthenticatedError, NotFoundError, ValidationError`.
- From `notes_evidence.domain.roles` it takes `Role`.
- From `tests.conftest` it takes `Rig`.

`tests/unit/application/test_notes_service.py` lines 15 to 22:

```python
@pytest.fixture
def rig() -> Rig:
    rig = Rig()
    rig.add_user("ada", Role.ADMIN)
    rig.add_user("bruno", Role.MEMBER)
    rig.add_user("chen", Role.MEMBER)
    rig.add_user("dana", Role.READONLY)
    return rig
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `rig`.**

It gives back a `Rig`.

Decorators: `@pytest.fixture`.

Step by step:

- Stores the result of calling `Rig()` in `rig`.
- Calls `rig.add_user('ada', Role.ADMIN)`.
- Calls `rig.add_user('bruno', Role.MEMBER)`.
- Calls `rig.add_user('chen', Role.MEMBER)`.
- Calls `rig.add_user('dana', Role.READONLY)`.
- Gives back `rig`.

`tests/unit/application/test_notes_service.py` lines 25 to 26:

```python
def actor(rig: Rig, name: str):
    return rig.service.authenticate(rig.service.login(name, "correct-horse-battery"))
```

**Function `actor`.**

It takes: `rig` (a `Rig`); `name` (a `str`).

Step by step:

- Gives back the result of calling `rig.service.authenticate(rig.service.login(name, 'correct-horse-battery'))`.

`tests/unit/application/test_notes_service.py` lines 29 to 30:

```python
def actions(rig: Rig):
    return [(e.action, e.username, e.outcome) for e in rig.audit.events]
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Function `actions`.**

It takes: `rig` (a `Rig`).

Step by step:

- Gives back a new list made by a loop (`[(e.action, e.username, e.outcome) for e in rig.audit.events]`).

`tests/unit/application/test_notes_service.py` lines 33 to 36:

```python
def test_a_good_login_returns_a_token_and_is_recorded(rig):
    token = rig.service.login("bruno", "correct-horse-battery")
    assert rig.service.authenticate(token).username == "bruno"
    assert actions(rig)[0] == (AuditAction.LOGIN_OK, "bruno", "ok")
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_a_good_login_returns_a_token_and_is_recorded`** checks: a good login returns a token and is recorded.

It takes: `rig`.

Step by step:

- Stores the result of calling `rig.service.login('bruno', 'correct-horse-battery')` in `token`.
- Checks that `rig.service.authenticate(token).username` equals `'bruno'`; if not, the test fails.
- Checks that `actions(rig)[0]` equals `(AuditAction.LOGIN_OK, 'bruno', 'ok')`; if not, the test fails.

`tests/unit/application/test_notes_service.py` lines 39 to 47:

```python
@pytest.mark.parametrize(
    ("name", "password"),
    [("bruno", "wrong-password-here"), ("nobody", "whatever-password"), ("BAD NAME", "x"), (None, "x")],
)
def test_a_failed_login_is_recorded_and_never_says_which_half_was_wrong(rig, name, password):
    with pytest.raises(InvalidCredentialsError, match="invalid username or password"):
        rig.service.login(name, password)
    assert rig.audit.events[-1].action is AuditAction.LOGIN_FAILED
    assert rig.audit.events[-1].outcome == "failed"
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.
> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Test `test_a_failed_login_is_recorded_and_never_says_which_half_was_wrong`** checks: a failed login is recorded and never says which half was wrong.

It takes: `rig`; `name`; `password`.

Decorators: `@pytest.mark.parametrize(('name', 'password'), [('bruno', 'wrong-passw…`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(InvalidCredentialsError, match='invalid username or pas…`:
  - Calls `rig.service.login(name, password)`.
- Checks that `rig.audit.events[-1].action` is the same object as `AuditAction.LOGIN_FAILED`; if not, the test fails.
- Checks that `rig.audit.events[-1].outcome` equals `'failed'`; if not, the test fails.

`tests/unit/application/test_notes_service.py` lines 50 to 53:

```python
def test_a_failed_login_for_a_known_user_carries_the_user_id(rig):
    with pytest.raises(InvalidCredentialsError):
        rig.service.login("bruno", "wrong-password-here")
    assert rig.audit.events[-1].user_id == 2
```

**Test `test_a_failed_login_for_a_known_user_carries_the_user_id`** checks: a failed login for a known user carries the user id.

It takes: `rig`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(InvalidCredentialsError)`:
  - Calls `rig.service.login('bruno', 'wrong-password-here')`.
- Checks that `rig.audit.events[-1].user_id` equals `2`; if not, the test fails.

`tests/unit/application/test_notes_service.py` lines 56 to 62:

```python
def test_a_disabled_account_cannot_log_in_or_use_an_old_token(rig):
    token = rig.service.login("bruno", "correct-horse-battery")
    rig.users.deactivate("bruno")
    with pytest.raises(InvalidCredentialsError):
        rig.service.login("bruno", "correct-horse-battery")
    with pytest.raises(NotAuthenticatedError):
        rig.service.authenticate(token)
```

**Test `test_a_disabled_account_cannot_log_in_or_use_an_old_token`** checks: a disabled account cannot log in or use an old token.

It takes: `rig`.

Step by step:

- Stores the result of calling `rig.service.login('bruno', 'correct-horse-battery')` in `token`.
- Calls `rig.users.deactivate('bruno')`.
- Expects the steps inside to raise the error in `pytest.raises(InvalidCredentialsError)`:
  - Calls `rig.service.login('bruno', 'correct-horse-battery')`.
- Expects the steps inside to raise the error in `pytest.raises(NotAuthenticatedError)`:
  - Calls `rig.service.authenticate(token)`.

`tests/unit/application/test_notes_service.py` lines 65 to 74:

```python
def test_a_forged_or_expired_token_is_refused(rig):
    with pytest.raises(NotAuthenticatedError):
        rig.service.authenticate("garbage")
    token = rig.service.login("bruno", "correct-horse-battery")
    rig.tokens.expired = True
    with pytest.raises(NotAuthenticatedError):
        rig.service.authenticate(token)
    rig.tokens.expired = False
    with pytest.raises(NotAuthenticatedError):
        rig.service.authenticate("token-99")
```

**Test `test_a_forged_or_expired_token_is_refused`** checks: a forged or expired token is refused.

It takes: `rig`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(NotAuthenticatedError)`:
  - Calls `rig.service.authenticate('garbage')`.
- Stores the result of calling `rig.service.login('bruno', 'correct-horse-battery')` in `token`.
- Stores `True` in `rig.tokens.expired`.
- Expects the steps inside to raise the error in `pytest.raises(NotAuthenticatedError)`:
  - Calls `rig.service.authenticate(token)`.
- Stores `False` in `rig.tokens.expired`.
- Expects the steps inside to raise the error in `pytest.raises(NotAuthenticatedError)`:
  - Calls `rig.service.authenticate('token-99')`.

`tests/unit/application/test_notes_service.py` lines 77 to 91:

```python
def test_a_member_creates_reads_updates_and_deletes_their_own_note(rig):
    bruno = actor(rig, "bruno")
    note = rig.service.create_note(bruno, " First ", "text")
    assert rig.service.get_note(bruno, note.id).title == "First"
    assert rig.service.update_note(bruno, note.id, "Second", "more").title == "Second"
    rig.service.delete_note(bruno, note.id)
    with pytest.raises(NotFoundError):
        rig.service.get_note(bruno, note.id)
    assert [a for a, *_ in actions(rig)][-5:] == [
        AuditAction.NOTE_CREATED,
        AuditAction.NOTE_READ,
        AuditAction.NOTE_UPDATED,
        AuditAction.NOTE_DELETED,
        AuditAction.ACCESS_DENIED,
    ]
```

> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.
> **In plain words.** `*items` **unpacks** a sequence into separate values; `**options` does the same for a dictionary's keys and values.

**Test `test_a_member_creates_reads_updates_and_deletes_their_own_note`** checks: a member creates reads updates and deletes their own note.

It takes: `rig`.

Step by step:

- Stores the result of calling `actor(rig, 'bruno')` in `bruno`.
- Stores the result of calling `rig.service.create_note(bruno, ' First ', 'text')` in `note`.
- Checks that `rig.service.get_note(bruno, note.id).title` equals `'First'`; if not, the test fails.
- Checks that `rig.service.update_note(bruno, note.id, 'Second',…` equals `'Second'`; if not, the test fails.
- Calls `rig.service.delete_note(bruno, note.id)`.
- Expects the steps inside to raise the error in `pytest.raises(NotFoundError)`:
  - Calls `rig.service.get_note(bruno, note.id)`.
- Checks that `[a for a, *_ in actions(rig)][-5:]` equals `[AuditAction.NOTE_CREATED, AuditAction.NOTE_READ,…`; if not, the test fails.

`tests/unit/application/test_notes_service.py` lines 94 to 105:

```python
def test_a_member_cannot_see_or_change_another_members_note_and_cannot_tell_it_exists(rig):
    note = rig.service.create_note(actor(rig, "chen"), "Private", "text")
    bruno = actor(rig, "bruno")
    for call in (
        lambda: rig.service.get_note(bruno, note.id),
        lambda: rig.service.update_note(bruno, note.id, "x", "y"),
        lambda: rig.service.delete_note(bruno, note.id),
    ):
        with pytest.raises(NotFoundError, match="note not found"):
            call()
    assert rig.notes.get(note.id) is not None
    assert [e.outcome for e in rig.audit.events if e.action is AuditAction.ACCESS_DENIED] == ["denied"] * 3
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Test `test_a_member_cannot_see_or_change_another_members_note_and_cannot_tell_it_exists`** checks: a member cannot see or change another members note and cannot tell it exists.

It takes: `rig`.

Step by step:

- Stores the result of calling `rig.service.create_note(actor(rig, 'chen'), 'Private', 'text')` in `note`.
- Stores the result of calling `actor(rig, 'bruno')` in `bruno`.
- For each `call` in the tuple `(lambda: rig.service.get_note(bruno, note.id), lambda: rig.service.up…`:
  - Expects the steps inside to raise the error in `pytest.raises(NotFoundError, match='note not found')`:
    - Calls `call()`.
- Checks that `rig.notes.get(note.id)` is not the same object as `None`; if not, the test fails.
- Checks that `[e.outcome for e in rig.audit.events if e.action …` equals `['denied'] * 3`; if not, the test fails.

`tests/unit/application/test_notes_service.py` lines 108 to 113:

```python
def test_listing_shows_own_notes_to_a_member_and_every_note_to_a_reader_and_an_admin(rig):
    rig.service.create_note(actor(rig, "bruno"), "a", "x")
    rig.service.create_note(actor(rig, "chen"), "b", "x")
    assert len(rig.service.list_notes(actor(rig, "bruno"))) == 1
    assert len(rig.service.list_notes(actor(rig, "dana"))) == 2
    assert len(rig.service.list_notes(actor(rig, "ada"))) == 2
```

**Test `test_listing_shows_own_notes_to_a_member_and_every_note_to_a_reader_and_an_admin`** checks: listing shows own notes to a member and every note to a reader and an admin.

It takes: `rig`.

Step by step:

- Calls `rig.service.create_note(actor(rig, 'bruno'), 'a', 'x')`.
- Calls `rig.service.create_note(actor(rig, 'chen'), 'b', 'x')`.
- Checks that `len(rig.service.list_notes(actor(rig, 'bruno')))` equals `1`; if not, the test fails.
- Checks that `len(rig.service.list_notes(actor(rig, 'dana')))` equals `2`; if not, the test fails.
- Checks that `len(rig.service.list_notes(actor(rig, 'ada')))` equals `2`; if not, the test fails.

`tests/unit/application/test_notes_service.py` lines 116 to 126:

```python
def test_a_read_only_role_reads_everything_and_writes_nothing(rig):
    note = rig.service.create_note(actor(rig, "bruno"), "a", "x")
    dana = actor(rig, "dana")
    assert rig.service.get_note(dana, note.id).id == note.id
    with pytest.raises(NotAllowedError):
        rig.service.create_note(dana, "t", "b")
    with pytest.raises(NotAllowedError):
        rig.service.update_note(dana, note.id, "t", "b")
    with pytest.raises(NotAllowedError):
        rig.service.delete_note(dana, note.id)
    assert rig.notes.get(note.id).title == "a"
```

**Test `test_a_read_only_role_reads_everything_and_writes_nothing`** checks: a read only role reads everything and writes nothing.

It takes: `rig`.

Step by step:

- Stores the result of calling `rig.service.create_note(actor(rig, 'bruno'), 'a', 'x')` in `note`.
- Stores the result of calling `actor(rig, 'dana')` in `dana`.
- Checks that `rig.service.get_note(dana, note.id).id` equals `note.id`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(NotAllowedError)`:
  - Calls `rig.service.create_note(dana, 't', 'b')`.
- Expects the steps inside to raise the error in `pytest.raises(NotAllowedError)`:
  - Calls `rig.service.update_note(dana, note.id, 't', 'b')`.
- Expects the steps inside to raise the error in `pytest.raises(NotAllowedError)`:
  - Calls `rig.service.delete_note(dana, note.id)`.
- Checks that `rig.notes.get(note.id).title` equals `'a'`; if not, the test fails.

`tests/unit/application/test_notes_service.py` lines 129 to 134:

```python
def test_an_admin_may_change_any_note(rig):
    note = rig.service.create_note(actor(rig, "bruno"), "a", "x")
    ada = actor(rig, "ada")
    assert rig.service.update_note(ada, note.id, "edited", "y").title == "edited"
    rig.service.delete_note(ada, note.id)
    assert rig.notes.get(note.id) is None
```

**Test `test_an_admin_may_change_any_note`** checks: an admin may change any note.

It takes: `rig`.

Step by step:

- Stores the result of calling `rig.service.create_note(actor(rig, 'bruno'), 'a', 'x')` in `note`.
- Stores the result of calling `actor(rig, 'ada')` in `ada`.
- Checks that `rig.service.update_note(ada, note.id, 'edited', '…` equals `'edited'`; if not, the test fails.
- Calls `rig.service.delete_note(ada, note.id)`.
- Checks that `rig.notes.get(note.id)` is the same object as `None`; if not, the test fails.

`tests/unit/application/test_notes_service.py` lines 137 to 144:

```python
def test_invalid_input_is_refused_before_anything_is_stored(rig):
    bruno = actor(rig, "bruno")
    with pytest.raises(ValidationError):
        rig.service.create_note(bruno, "", "x")
    assert rig.notes.rows == {}
    note = rig.service.create_note(bruno, "ok", "x")
    with pytest.raises(ValidationError):
        rig.service.update_note(bruno, note.id, "t" * 500, "x")
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Test `test_invalid_input_is_refused_before_anything_is_stored`** checks: invalid input is refused before anything is stored.

It takes: `rig`.

Step by step:

- Stores the result of calling `actor(rig, 'bruno')` in `bruno`.
- Expects the steps inside to raise the error in `pytest.raises(ValidationError)`:
  - Calls `rig.service.create_note(bruno, '', 'x')`.
- Checks that `rig.notes.rows` equals `{}`; if not, the test fails.
- Stores the result of calling `rig.service.create_note(bruno, 'ok', 'x')` in `note`.
- Expects the steps inside to raise the error in `pytest.raises(ValidationError)`:
  - Calls `rig.service.update_note(bruno, note.id, 't' * 500, 'x')`.

`tests/unit/application/test_notes_service.py` lines 147 to 149:

```python
def test_updating_a_missing_note_is_not_found(rig):
    with pytest.raises(NotFoundError):
        rig.service.update_note(actor(rig, "ada"), 999, "t", "b")
```

**Test `test_updating_a_missing_note_is_not_found`** checks: updating a missing note is not found.

It takes: `rig`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(NotFoundError)`:
  - Calls `rig.service.update_note(actor(rig, 'ada'), 999, 't', 'b')`.

`tests/unit/application/test_notes_service.py` lines 152 to 164:

```python
def test_only_an_admin_grants_roles_and_the_grant_is_recorded_with_its_target(rig):
    with pytest.raises(NotAllowedError):
        rig.service.grant_role(actor(rig, "bruno"), "chen", Role.ADMIN)
    granted = rig.service.grant_role(actor(rig, "ada"), "chen", Role.ADMIN)
    assert granted.role is Role.ADMIN
    event = rig.audit.events[-1]
    assert (event.action, event.username, event.detail) == (
        AuditAction.ROLE_GRANTED,
        "ada",
        {"role": "admin", "target": "chen"},
    )
    with pytest.raises(NotFoundError):
        rig.service.grant_role(actor(rig, "ada"), "nobody", Role.MEMBER)
```

**Test `test_only_an_admin_grants_roles_and_the_grant_is_recorded_with_its_target`** checks: only an admin grants roles and the grant is recorded with its target.

It takes: `rig`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(NotAllowedError)`:
  - Calls `rig.service.grant_role(actor(rig, 'bruno'), 'chen', Role.ADMIN)`.
- Stores the result of calling `rig.service.grant_role(actor(rig, 'ada'), 'chen', Role.ADMIN)` in `granted`.
- Checks that `granted.role` is the same object as `Role.ADMIN`; if not, the test fails.
- Stores `rig.audit.events[-1]` in `event`.
- Checks that `(event.action, event.username, event.detail)` equals `(AuditAction.ROLE_GRANTED, 'ada', {'role': 'admin…`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(NotFoundError)`:
  - Calls `rig.service.grant_role(actor(rig, 'ada'), 'nobody', Role.MEMBER)`.

`tests/unit/application/test_notes_service.py` lines 167 to 173:

```python
def test_the_audit_trail_never_holds_note_text(rig):
    bruno = actor(rig, "bruno")
    note = rig.service.create_note(bruno, "Secret title", "Secret body text")
    rig.service.get_note(bruno, note.id)
    rig.service.update_note(bruno, note.id, "Other title", "Other body text")
    dump = " ".join(repr(e) for e in rig.audit.events)
    assert not any(text in dump for text in ("Secret", "Other title", "body text"))
```

> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Test `test_the_audit_trail_never_holds_note_text`** checks: the audit trail never holds note text.

It takes: `rig`.

Step by step:

- Stores the result of calling `actor(rig, 'bruno')` in `bruno`.
- Stores the result of calling `rig.service.create_note(bruno, 'Secret title', 'Secret body text')` in `note`.
- Calls `rig.service.get_note(bruno, note.id)`.
- Calls `rig.service.update_note(bruno, note.id, 'Other title', 'Other body text')`.
- Stores the result of calling `' '.join((repr(e) for e in rig.audit.events))` in `dump`.
- Checks that not (`any((text in dump for text in ('Secret', 'Other title', 'body text')))`); if not, the test fails.

### `tests/unit/application/test_reporting_and_edges.py`

`tests/unit/application/test_reporting_and_edges.py` lines 1 to 14:

```python
from datetime import date

import pytest

from notes_evidence.application.exercise import _refused
from notes_evidence.application.notes_service import NotesService
from notes_evidence.application.reporting import render_report, render_text
from notes_evidence.domain.changes import exceptions_in_csv
from notes_evidence.domain.controls import Control, EvidenceSpec, overlap
from notes_evidence.domain.errors import NotFoundError
from notes_evidence.domain.evidence import ManifestEntry, digest, framework_table, verify_pack
from notes_evidence.domain.findings import Report, error, warning
from notes_evidence.domain.roles import Role
from tests.conftest import T0, MemoryNotes, Rig
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- From `datetime` it takes `date`.
- It imports module `pytest`.
- From `notes_evidence.application.exercise` it takes `_refused`.
- From `notes_evidence.application.notes_service` it takes `NotesService`.
- From `notes_evidence.application.reporting` it takes `render_report, render_text`.
- From `notes_evidence.domain.changes` it takes `exceptions_in_csv`.
- From `notes_evidence.domain.controls` it takes `Control, EvidenceSpec, overlap`.
- From `notes_evidence.domain.errors` it takes `NotFoundError`.
- From `notes_evidence.domain.evidence` it takes `ManifestEntry, digest, framework_table, verify_pack`.
- From `notes_evidence.domain.findings` it takes `Report, error, warning`.
- From `notes_evidence.domain.roles` it takes `Role`.
- From `tests.conftest` it takes `T0, MemoryNotes, Rig`.

`tests/unit/application/test_reporting_and_edges.py` lines 16 to 18:

```python
SPEC = EvidenceSpec("C1-access-list.txt", "access_list", "proves", "point in time", 7, "weekly")
C1 = Control("C1", "Access control", "r", "w", {"iso27001": ("A.5.15", "A.5.18"), "soc2": ("CC6.1",)}, (SPEC,))
C6 = Control("C6", "Access review", "r", "w", {"iso27001": ("A.5.18",), "soc2": ("CC6.2",)}, ())
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `EvidenceSpec('C1-access-list.txt', 'access_list', 'proves', 'point in time', 7, 'weekly')` in `SPEC`.
- Stores the result of calling `Control('C1', 'Access control', 'r', 'w', {'iso27001': ('A.5.15', 'A.5.18'), 'soc2': ('CC…` in `C1`.
- Stores the result of calling `Control('C6', 'Access review', 'r', 'w', {'iso27001': ('A.5.18',), 'soc2': ('CC6.2',)}, (…` in `C6`.

`tests/unit/application/test_reporting_and_edges.py` lines 21 to 27:

```python
def test_text_report_lists_findings_and_the_verdict():
    report = Report(("a", "b"), (error("EVD002", "C1 x", "missing"), warning("EVD005", "C2 y", "stale")))
    lines = render_text(report).splitlines()
    assert lines[0] == "ERROR   EVD002 C1 x: missing"
    assert lines[1] == "WARNING EVD005 C2 y: stale"
    assert lines[2] == "FAILED: 2 files checked, 1 errors, 1 warnings"
    assert render_text(Report(("a",), ())) == "OK: 1 files checked, 0 errors, 0 warnings"
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_text_report_lists_findings_and_the_verdict`** checks: text report lists findings and the verdict.

Step by step:

- Stores the result of calling `Report(('a', 'b'), (error('EVD002', 'C1 x', 'missing'), warning('EVD005', 'C2 y', 'stale'…` in `report`.
- Stores the result of calling `render_text(report).splitlines()` in `lines`.
- Checks that `lines[0]` equals `'ERROR EVD002 C1 x: missing'`; if not, the test fails.
- Checks that `lines[1]` equals `'WARNING EVD005 C2 y: stale'`; if not, the test fails.
- Checks that `lines[2]` equals `'FAILED: 2 files checked, 1 errors, 1 warnings'`; if not, the test fails.
- Checks that `render_text(Report(('a',), ()))` equals `'OK: 1 files checked, 0 errors, 0 warnings'`; if not, the test fails.

`tests/unit/application/test_reporting_and_edges.py` lines 30 to 40:

```python
def test_markdown_report_shows_each_control_its_file_and_the_framework_overlap():
    manifest = {SPEC.file: ManifestEntry(SPEC.file, "C1", T0, "ada", "fixture", "a" * 64)}
    text = render_report(Report(("C1-access-list.txt",), ()), [C1, C6], manifest)
    assert "**Verdict:** OK (0 errors, 0 warnings)" in text
    assert "| C1 Access control | C1-access-list.txt | 2026-10-22 | ada | aaaaaaaaaaaa |" in text
    assert "| C6 Access review | none | - | - | - |" in text
    assert "| iso27001 | A.5.18 | C1, C6 (overlap) |" in text
    assert "None." in text
    missing = render_report(Report((), (error("EVD002", "C1", "gone"),)), [C1], {})
    assert "| C1 Access control | C1-access-list.txt | missing | - | - |" in missing
    assert "| error | EVD002 | `C1` | gone |" in missing
```

**Test `test_markdown_report_shows_each_control_its_file_and_the_framework_overlap`** checks: markdown report shows each control its file and the framework overlap.

Step by step:

- Stores the dictionary `{SPEC.file: ManifestEntry(SPEC.file, 'C1', T0, 'ada', 'fixture', 'a' …` in `manifest`.
- Stores the result of calling `render_report(Report(('C1-access-list.txt',), ()), [C1, C6], manifest)` in `text`.
- Checks that `'**Verdict:** OK (0 errors, 0 warnings)'` is in `text`; if not, the test fails.
- Checks that `'| C1 Access control | C1-access-list.txt | 2026-…` is in `text`; if not, the test fails.
- Checks that `'| C6 Access review | none | - | - | - |'` is in `text`; if not, the test fails.
- Checks that `'| iso27001 | A.5.18 | C1, C6 (overlap) |'` is in `text`; if not, the test fails.
- Checks that `'None.'` is in `text`; if not, the test fails.
- Stores the result of calling `render_report(Report((), (error('EVD002', 'C1', 'gone'),)), [C1], {})` in `missing`.
- Checks that `'| C1 Access control | C1-access-list.txt | missi…` is in `missing`; if not, the test fails.
- Checks that `'| error | EVD002 | `C1` | gone |'` is in `missing`; if not, the test fails.

`tests/unit/application/test_reporting_and_edges.py` lines 43 to 47:

```python
def test_overlap_groups_controls_by_reference():
    table = overlap([C1, C6])
    assert table["iso27001"]["A.5.18"] == ["C1", "C6"]
    assert table["soc2"] == {"CC6.1": ["C1"], "CC6.2": ["C6"]}
    assert framework_table([C1, C6]).splitlines()[0] == "| Framework | Reference | Controls |"
```

**Test `test_overlap_groups_controls_by_reference`** checks: overlap groups controls by reference.

Step by step:

- Stores the result of calling `overlap([C1, C6])` in `table`.
- Checks that `table['iso27001']['A.5.18']` equals `['C1', 'C6']`; if not, the test fails.
- Checks that `table['soc2']` equals `{'CC6.1': ['C1'], 'CC6.2': ['C6']}`; if not, the test fails.
- Checks that `framework_table([C1, C6]).splitlines()[0]` equals `'| Framework | Reference | Controls |'`; if not, the test fails.

`tests/unit/application/test_reporting_and_edges.py` lines 50 to 57:

```python
def test_a_manifest_entry_that_names_another_control_is_reported():
    text = (
        "# access list, generated 2026-10-22T09:00:00Z\n## repository (permission per person)\n"
        "## database roles\n## cloud account users\n"
    )
    manifest = {SPEC.file: ManifestEntry(SPEC.file, "C9", T0, "ada", "fixture", digest(text))}
    found = verify_pack([C1], manifest, {SPEC.file: text}, [], [], date(2026, 10, 23))
    assert any("belongs to C9" in f.message for f in found)
```

> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Test `test_a_manifest_entry_that_names_another_control_is_reported`** checks: a manifest entry that names another control is reported.

Step by step:

- Stores the text `'# access list, generated 2026-10-22T09:00:00Z\n## reposito…` in `text`.
- Stores the dictionary `{SPEC.file: ManifestEntry(SPEC.file, 'C9', T0, 'ada', 'fixture', dige…` in `manifest`.
- Stores the result of calling `verify_pack([C1], manifest, {SPEC.file: text}, [], [], date(2026, 10, 23))` in `found`.
- Checks that `any(('belongs to C9' in f.message for f in found))`; if not, the test fails.

`tests/unit/application/test_reporting_and_edges.py` lines 60 to 64:

```python
def test_an_access_list_without_its_dated_header_is_reported():
    text = "## repository (permission per person)\n## database roles\n## cloud account users\n"
    manifest = {SPEC.file: ManifestEntry(SPEC.file, "C1", T0, "ada", "fixture", digest(text))}
    found = verify_pack([C1], manifest, {SPEC.file: text}, [], [], date(2026, 10, 23))
    assert any(f.message == "no dated header" for f in found)
```

**Test `test_an_access_list_without_its_dated_header_is_reported`** checks: an access list without its dated header is reported.

Step by step:

- Stores the text `'## repository (permission per person)\n## database roles\n…` in `text`.
- Stores the dictionary `{SPEC.file: ManifestEntry(SPEC.file, 'C1', T0, 'ada', 'fixture', dige…` in `manifest`.
- Stores the result of calling `verify_pack([C1], manifest, {SPEC.file: text}, [], [], date(2026, 10, 23))` in `found`.
- Checks that `any((f.message == 'no dated header' for f in found))`; if not, the test fails.

`tests/unit/application/test_reporting_and_edges.py` lines 67 to 73:

```python
def test_a_scan_report_without_a_verdict_is_reported():
    spec = EvidenceSpec("C5-scan-report.json", "scan", "p", "x", 7, "weekly")
    control = Control("C5", "Scan", "r", "w", {"iso27001": ("A.8.8",), "soc2": ("CC7.1",)}, (spec,))
    text = '{"run_id": "r1", "verdict": "maybe"}'
    manifest = {spec.file: ManifestEntry(spec.file, "C5", T0, "ada", "fixture", digest(text))}
    found = verify_pack([control], manifest, {spec.file: text}, [], [], date(2026, 10, 23))
    assert any(f.message == "no verdict" for f in found)
```

**Test `test_a_scan_report_without_a_verdict_is_reported`** checks: a scan report without a verdict is reported.

Step by step:

- Stores the result of calling `EvidenceSpec('C5-scan-report.json', 'scan', 'p', 'x', 7, 'weekly')` in `spec`.
- Stores the result of calling `Control('C5', 'Scan', 'r', 'w', {'iso27001': ('A.8.8',), 'soc2': ('CC7.1',)}, (spec,))` in `control`.
- Stores the text `'{"run_id": "r1", "verdict": "maybe"}'` in `text`.
- Stores the dictionary `{spec.file: ManifestEntry(spec.file, 'C5', T0, 'ada', 'fixture', dige…` in `manifest`.
- Stores the result of calling `verify_pack([control], manifest, {spec.file: text}, [], [], date(2026, 10, 23))` in `found`.
- Checks that `any((f.message == 'no verdict' for f in found))`; if not, the test fails.

`tests/unit/application/test_reporting_and_edges.py` lines 76 to 79:

```python
def test_a_change_with_no_deployment_id_is_found_in_the_csv():
    header = '"number","author","merged_at","commit","approvers","deploy_id"'
    text = header + '\n41,"chen","2026-10-21T09:00:00Z","a41c9de","ada",""\n'
    assert [(e.number, e.reason) for e in exceptions_in_csv(text)] == [(41, "no deployment record")]
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Test `test_a_change_with_no_deployment_id_is_found_in_the_csv`** checks: a change with no deployment id is found in the csv.

Step by step:

- Stores the text `'"number","author","merged_at","commit","approvers","deploy…` in `header`.
- Stores `header + '\n41,"chen","2026-10-21T09:00:00Z","a41c9de","ada",""\n'` in `text`.
- Checks that `[(e.number, e.reason) for e in exceptions_in_csv(…` equals `[(41, 'no deployment record')]`; if not, the test fails.

`tests/unit/application/test_reporting_and_edges.py` lines 82 to 88:

```python
def test_refused_counts_a_call_that_goes_through_as_zero():
    assert _refused(lambda: None) == 0

    def refuse():
        raise NotFoundError("x")

    assert _refused(refuse) == 1
```

> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Test `test_refused_counts_a_call_that_goes_through_as_zero`** checks: refused counts a call that goes through as zero.

Step by step:

- Checks that `_refused(lambda: None)` equals `0`; if not, the test fails.
- Defines a helper function `refuse()`.
  - Stops here by raising `NotFoundError('x')`.
- Checks that `_refused(refuse)` equals `1`; if not, the test fails.

`tests/unit/application/test_reporting_and_edges.py` lines 91 to 102:

```python
def test_a_note_that_vanishes_between_the_check_and_the_update_is_not_found():
    class Racing(MemoryNotes):
        def update(self, note_id, title, body, at):
            return None

    rig = Rig()
    notes = Racing()
    service = NotesService(rig.users, notes, rig.audit, rig.hasher, rig.tokens, rig.clock)
    owner = rig.add_user("bruno", Role.MEMBER)
    note = notes.add(owner.id, "t", "b", T0)
    with pytest.raises(NotFoundError, match="note not found"):
        service.update_note(owner, note.id, "x", "y")
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Test `test_a_note_that_vanishes_between_the_check_and_the_update_is_not_found`** checks: a note that vanishes between the check and the update is not found.

Step by step:

- Defines a class `Racing`.
- Stores the result of calling `Rig()` in `rig`.
- Stores the result of calling `Racing()` in `notes`.
- Stores the result of calling `NotesService(rig.users, notes, rig.audit, rig.hasher, rig.tokens, rig.clock)` in `service`.
- Stores the result of calling `rig.add_user('bruno', Role.MEMBER)` in `owner`.
- Stores the result of calling `notes.add(owner.id, 't', 'b', T0)` in `note`.
- Expects the steps inside to raise the error in `pytest.raises(NotFoundError, match='note not found')`:
  - Calls `service.update_note(owner, note.id, 'x', 'y')`.

## Try it yourself

```bash
.venv/bin/pytest -q tests/unit/application
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check tests/unit/application/test_collect.py tests/unit/application/test_notes_service.py tests/unit/application/test_reporting_and_edges.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_the_whole_pack_verifies` check?
   **Answer:** it checks: the whole pack verifies.
2. What does the test `test_access_is_collected_from_the_three_systems_and_the_leaver_is_removed` check?
   **Answer:** it checks: access is collected from the three systems and the leaver is removed.
3. What does the test `test_the_alert_test_keeps_the_alert_beside_the_time_of_the_action` check?
   **Answer:** it checks: the alert test keeps the alert beside the time of the action.
4. What does the test `test_the_log_sample_has_log_lines_and_no_note_text` check?
   **Answer:** it checks: the log sample has log lines and no note text.
5. What does the test `test_changes_restore_and_scan_are_written_with_manifest_entries` check?
   **Answer:** it checks: changes restore and scan are written with manifest entries.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
