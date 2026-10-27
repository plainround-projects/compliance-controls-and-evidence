# The tests (domain)

## What it is

The pytest tests in `tests/unit/domain`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/domain/test_artifacts.py` | 143 lines.  |
| `tests/unit/domain/test_roles_notes_audit_alerts.py` | 79 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/unit/domain/test_artifacts.py`

`tests/unit/domain/test_artifacts.py` lines 1 to 25:

```python
import json
from datetime import UTC, date, datetime, timedelta

import pytest

from notes_evidence.domain.access import (
    CLOUD,
    DATABASE,
    REPOSITORY,
    AccessEntry,
    AccessList,
    parse_access_list,
    render_access_list,
)
from notes_evidence.domain.changes import (
    MergedChange,
    exceptions_in_csv,
    find_exceptions,
    independent_approvers,
    render_changes,
)
from notes_evidence.domain.restore import RestoreResult, format_duration, render_restore
from notes_evidence.domain.review import Decision, Person, ReviewRequest, check_review, render_review
from notes_evidence.domain.scan import BLOCKING_RULE, ScanFinding, ScanReport, parse_pip_audit
from tests.conftest import T0
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `json`.
- From `datetime` it takes `UTC, date, datetime, timedelta`.
- It imports module `pytest`.
- From `notes_evidence.domain.access` it takes `CLOUD, DATABASE, REPOSITORY, AccessEntry, AccessList, parse_access_list, render_access_list`.
- From `notes_evidence.domain.changes` it takes `MergedChange, exceptions_in_csv, find_exceptions, independent_approvers, render_changes`.
- From `notes_evidence.domain.restore` it takes `RestoreResult, format_duration, render_restore`.
- From `notes_evidence.domain.review` it takes `Decision, Person, ReviewRequest, check_review, render_review`.
- From `notes_evidence.domain.scan` it takes `BLOCKING_RULE, ScanFinding, ScanReport, parse_pip_audit`.
- From `tests.conftest` it takes `T0`.

`tests/unit/domain/test_artifacts.py` lines 27 to 35:

```python
ENTRIES = (
    AccessEntry(REPOSITORY, "ada", "admin"),
    AccessEntry(REPOSITORY, "bruno", "write"),
    AccessEntry(DATABASE, "app_rw", "standard"),
    AccessEntry(DATABASE, "postgres", "superuser"),
    AccessEntry(CLOUD, "ada"),
    AccessEntry(CLOUD, "contractor-lee"),
)
ACCESS = AccessList(T0, ENTRIES)
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the tuple `(AccessEntry(REPOSITORY, 'ada', 'admin'), AccessEntry(REPOSITORY, 'br…` in `ENTRIES`.
- Stores the result of calling `AccessList(T0, ENTRIES)` in `ACCESS`.

`tests/unit/domain/test_artifacts.py` lines 38 to 45:

```python
def test_the_access_list_renders_one_block_per_system_and_parses_back():
    text = render_access_list(ACCESS)
    assert text.startswith(
        "# access list, generated 2026-10-22T09:00:00Z\n## repository (permission per person)\nada\tadmin\n"
    )
    assert "## cloud account users\nada\ncontractor-lee\n" in text
    assert parse_access_list(text)[CLOUD] == ["ada", "contractor-lee"]
    assert ACCESS.counts() == {REPOSITORY: 2, DATABASE: 2, CLOUD: 2}
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_the_access_list_renders_one_block_per_system_and_parses_back`** checks: the access list renders one block per system and parses back.

Step by step:

- Stores the result of calling `render_access_list(ACCESS)` in `text`.
- Checks that `text.startswith('# access list, generated 2026-10-22T09:00:00Z\n## re…`; if not, the test fails.
- Checks that `'## cloud account users\nada\ncontractor-lee\n'` is in `text`; if not, the test fails.
- Checks that `parse_access_list(text)[CLOUD]` equals `['ada', 'contractor-lee']`; if not, the test fails.
- Checks that `ACCESS.counts()` equals `{REPOSITORY: 2, DATABASE: 2, CLOUD: 2}`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 48 to 51:

```python
def test_removing_one_principal_from_one_system_leaves_the_others():
    after = ACCESS.without(CLOUD, "contractor-lee")
    assert [e.principal for e in after.in_system(CLOUD)] == ["ada"]
    assert len(after.entries) == 5
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Test `test_removing_one_principal_from_one_system_leaves_the_others`** checks: removing one principal from one system leaves the others.

Step by step:

- Stores the result of calling `ACCESS.without(CLOUD, 'contractor-lee')` in `after`.
- Checks that `[e.principal for e in after.in_system(CLOUD)]` equals `['ada']`; if not, the test fails.
- Checks that `len(after.entries)` equals `5`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 54 to 57:

```python
PEOPLE = {
    "ada": Person("ada", "Developer"),
    "contractor-lee": Person("contractor-lee", "Contractor", date(2026, 9, 18)),
}
```

These module-level lines:

- Stores the dictionary `{'ada': Person('ada', 'Developer'), 'contractor-lee': Person('contrac…` in `PEOPLE`.

`tests/unit/domain/test_artifacts.py` lines 60 to 64:

```python
def decisions(overrides=None):
    base = {(e.system, e.principal): Decision(e.system, e.principal, True, "needed for the job") for e in ENTRIES}
    base[(CLOUD, "contractor-lee")] = Decision(CLOUD, "contractor-lee", False, "left on 2026-09-18")
    base.update(overrides or {})
    return tuple(base.values())
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.

**Function `decisions`.**

It takes: `overrides`, default `None`.

Step by step:

- Stores a new dictionary made by a loop (`{(e.system, e.principal): Decision(e.system, e.principal, True, 'need…`) in `base`.
- Stores the result of calling `Decision(CLOUD, 'contractor-lee', False, 'left on 2026-09-18')` in `base[CLOUD, 'contractor-lee']`.
- Calls `base.update(overrides or {})`.
- Gives back the result of calling `tuple(base.values())`.

`tests/unit/domain/test_artifacts.py` lines 67 to 68:

```python
def request(items=None, ticket="SEC-17"):
    return ReviewRequest("eli", date(2026, 10, 22), ticket, items if items is not None else decisions())
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `request`.**

It takes: `items`, default `None`; `ticket`, default `'SEC-17'`.

Step by step:

- Gives back the result of calling `ReviewRequest('eli', date(2026, 10, 22), ticket, items if items is not None else decision…`.

`tests/unit/domain/test_artifacts.py` lines 71 to 72:

```python
def codes(req):
    return {f.code for f in check_review(ACCESS, req, PEOPLE)}
```

> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.

**Function `codes`.**

It takes: `req`.

Step by step:

- Gives back a new set made by a loop (`{f.code for f in check_review(ACCESS, req, PEOPLE)}`).

`tests/unit/domain/test_artifacts.py` lines 75 to 76:

```python
def test_a_complete_justified_review_has_no_findings():
    assert check_review(ACCESS, request(), PEOPLE) == []
```

**Test `test_a_complete_justified_review_has_no_findings`** checks: a complete justified review has no findings.

Step by step:

- Checks that `check_review(ACCESS, request(), PEOPLE)` equals `[]`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 79 to 80:

```python
def test_every_principal_needs_a_decision():
    assert "ARV001" in codes(request(decisions()[:-1]))
```

> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Test `test_every_principal_needs_a_decision`** checks: every principal needs a decision.

Step by step:

- Checks that `'ARV001'` is in `codes(request(decisions()[:-1]))`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 83 to 85:

```python
def test_every_decision_needs_a_reason_and_the_review_a_ticket():
    assert "ARV002" in codes(request(decisions({(REPOSITORY, "ada"): Decision(REPOSITORY, "ada", True, " ")})))
    assert "ARV002" in codes(request(ticket=""))
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Test `test_every_decision_needs_a_reason_and_the_review_a_ticket`** checks: every decision needs a reason and the review a ticket.

Step by step:

- Checks that `'ARV002'` is in `codes(request(decisions({(REPOSITORY, 'ada'): Dec…`; if not, the test fails.
- Checks that `'ARV002'` is in `codes(request(ticket=''))`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 88 to 90:

```python
def test_a_leaver_cannot_be_kept():
    kept = decisions({(CLOUD, "contractor-lee"): Decision(CLOUD, "contractor-lee", True, "still useful")})
    assert "ARV003" in codes(request(kept))
```

**Test `test_a_leaver_cannot_be_kept`** checks: a leaver cannot be kept.

Step by step:

- Stores the result of calling `decisions({(CLOUD, 'contractor-lee'): Decision(CLOUD, 'contractor-lee', True, 'still usef…` in `kept`.
- Checks that `'ARV003'` is in `codes(request(kept))`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 93 to 100:

```python
def test_the_review_record_shows_before_removed_after_and_the_proof():
    after = ACCESS.without(CLOUD, "contractor-lee")
    text = render_review(ACCESS, after, request())
    assert text.splitlines()[0] == "Reviewer: eli. Date: 2026-10-22. Ticket: SEC-17."
    assert "Before: 2 repository, 2 database roles, 2 cloud account users." in text
    assert "Removed: cloud account users contractor-lee." in text
    assert "After: 2 repository, 2 database roles, 1 cloud account users." in text
    assert "none of the removed principals is listed" in text
```

**Test `test_the_review_record_shows_before_removed_after_and_the_proof`** checks: the review record shows before removed after and the proof.

Step by step:

- Stores the result of calling `ACCESS.without(CLOUD, 'contractor-lee')` in `after`.
- Stores the result of calling `render_review(ACCESS, after, request())` in `text`.
- Checks that `text.splitlines()[0]` equals `'Reviewer: eli. Date: 2026-10-22. Ticket: SEC-17.'`; if not, the test fails.
- Checks that `'Before: 2 repository, 2 database roles, 2 cloud …` is in `text`; if not, the test fails.
- Checks that `'Removed: cloud account users contractor-lee.'` is in `text`; if not, the test fails.
- Checks that `'After: 2 repository, 2 database roles, 1 cloud a…` is in `text`; if not, the test fails.
- Checks that `'none of the removed principals is listed'` is in `text`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 103 to 104:

```python
def test_the_review_record_admits_a_removal_that_did_not_happen():
    assert "contractor-lee is still listed" in render_review(ACCESS, ACCESS, request())
```

**Test `test_the_review_record_admits_a_removal_that_did_not_happen`** checks: the review record admits a removal that did not happen.

Step by step:

- Checks that `'contractor-lee is still listed'` is in `render_review(ACCESS, ACCESS, request())`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 107 to 109:

```python
def test_a_review_that_removes_nothing_says_so():
    keep_all = request(tuple(Decision(e.system, e.principal, True, "needed") for e in ENTRIES))
    assert "Removed: nothing." in render_review(ACCESS, ACCESS, keep_all)
```

> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Test `test_a_review_that_removes_nothing_says_so`** checks: a review that removes nothing says so.

Step by step:

- Stores the result of calling `request(tuple((Decision(e.system, e.principal, True, 'needed') for e in ENTRIES)))` in `keep_all`.
- Checks that `'Removed: nothing.'` is in `render_review(ACCESS, ACCESS, keep_all)`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 112 to 115:

```python
def change(number, author="chen", approvers=("ada",), deploy="deploy-1", hour=9):
    return MergedChange(
        number, author, datetime(2026, 10, 21, hour, 0, tzinfo=UTC), "a41c9de" + "0" * 33, approvers, deploy
    )
```

**Function `change`.**

It takes: `number`; `author`, default `'chen'`; `approvers`, default `('ada',)`; `deploy`, default `'deploy-1'`; `hour`, default `9`.

Step by step:

- Gives back the result of calling `MergedChange(number, author, datetime(2026, 10, 21, hour, 0, tzinfo=UTC), 'a41c9de' + '0'…`.

`tests/unit/domain/test_artifacts.py` lines 118 to 130:

```python
def test_a_change_without_an_independent_approver_or_a_deployment_is_an_exception():
    changes = [
        change(41),
        change(42, approvers=()),
        change(43, author="ada", approvers=("ada",)),
        change(44, deploy=""),
    ]
    assert [(e.number, e.reason) for e in find_exceptions(changes)] == [
        (42, "merged with no independent approver"),
        (43, "merged with no independent approver"),
        (44, "no deployment record"),
    ]
    assert independent_approvers(change(1, author="ada", approvers=("ada", "bruno"))) == ("bruno",)
```

**Test `test_a_change_without_an_independent_approver_or_a_deployment_is_an_exception`** checks: a change without an independent approver or a deployment is an exception.

Step by step:

- Stores the list `[change(41), change(42, approvers=()), change(43, author='ada', appro…` in `changes`.
- Checks that `[(e.number, e.reason) for e in find_exceptions(ch…` equals `[(42, 'merged with no independent approver'), (43…`; if not, the test fails.
- Checks that `independent_approvers(change(1, author='ada', app…` equals `('bruno',)`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 133 to 138:

```python
def test_the_changes_csv_quotes_strings_not_numbers_and_rederives_the_exceptions():
    text = render_changes([change(43, approvers=()), change(41, approvers=("ada", "bruno"))])
    lines = text.splitlines()
    assert lines[0] == '"number","author","merged_at","commit","approvers","deploy_id"'
    assert lines[1] == '41,"chen","2026-10-21T09:00:00Z","a41c9de","ada+bruno","deploy-1"'
    assert [e.number for e in exceptions_in_csv(text)] == [43]
```

**Test `test_the_changes_csv_quotes_strings_not_numbers_and_rederives_the_exceptions`** checks: the changes csv quotes strings not numbers and rederives the exceptions.

Step by step:

- Stores the result of calling `render_changes([change(43, approvers=()), change(41, approvers=('ada', 'bruno'))])` in `text`.
- Stores the result of calling `text.splitlines()` in `lines`.
- Checks that `lines[0]` equals `'"number","author","merged_at","commit","approver…`; if not, the test fails.
- Checks that `lines[1]` equals `'41,"chen","2026-10-21T09:00:00Z","a41c9de","ada+…`; if not, the test fails.
- Checks that `[e.number for e in exceptions_in_csv(text)]` equals `[43]`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 141 to 149:

```python
def test_restore_artifact_has_the_lessons_three_lines_and_a_verdict():
    result = RestoreResult(
        T0, T0 + timedelta(hours=6), T0 + timedelta(hours=6, minutes=4, seconds=41), "notes", 12408, 12408
    )
    text = render_restore(result)
    assert text.splitlines()[0] == "restore started 2026-10-22T15:00:00Z from backup 2026-10-22T09:00:00Z"
    assert "restore finished 2026-10-22T15:04:41Z (4 min 41 s)" in text
    assert "check: notes table has 12,408 rows; source had 12,408 rows at backup time" in text
    assert text.endswith("result: verified\n")
```

**Test `test_restore_artifact_has_the_lessons_three_lines_and_a_verdict`** checks: restore artifact has the lessons three lines and a verdict.

Step by step:

- Stores the result of calling `RestoreResult(T0, T0 + timedelta(hours=6), T0 + timedelta(hours=6, minutes=4, seconds=41)…` in `result`.
- Stores the result of calling `render_restore(result)` in `text`.
- Checks that `text.splitlines()[0]` equals `'restore started 2026-10-22T15:00:00Z from backup…`; if not, the test fails.
- Checks that `'restore finished 2026-10-22T15:04:41Z (4 min 41 …` is in `text`; if not, the test fails.
- Checks that `'check: notes table has 12,408 rows; source had 1…` is in `text`; if not, the test fails.
- Checks that `text.endswith('result: verified\n')`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 152 to 156:

```python
def test_a_restore_with_fewer_rows_is_a_mismatch():
    result = RestoreResult(T0, T0, T0 + timedelta(seconds=9), "notes", 100, 99)
    assert not result.verified
    assert render_restore(result).endswith("result: MISMATCH\n")
    assert format_duration(9) == "9 s"
```

**Test `test_a_restore_with_fewer_rows_is_a_mismatch`** checks: a restore with fewer rows is a mismatch.

Step by step:

- Stores the result of calling `RestoreResult(T0, T0, T0 + timedelta(seconds=9), 'notes', 100, 99)` in `result`.
- Checks that not (`result.verified`); if not, the test fails.
- Checks that `render_restore(result).endswith('result: MISMATCH\n')`; if not, the test fails.
- Checks that `format_duration(9)` equals `'9 s'`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 159 to 167:

```python
def test_the_scan_verdict_follows_the_blocking_rule():
    clean = ScanReport("run-1", "pip-audit", "2.10", T0, "requirements.lock", 12, ())
    unfixed = ScanReport("run-1", "pip-audit", "2.10", T0, "x", 12, (ScanFinding("a", "1", "CVE-1", ()),))
    fixable = ScanReport("run-1", "pip-audit", "2.10", T0, "x", 12, (ScanFinding("a", "1", "CVE-1", ("1.1",)),))
    assert (clean.verdict, unfixed.verdict, fixable.verdict) == ("pass", "pass", "fail")
    document = json.loads(fixable.to_json())
    assert document["blocking_rule"] == BLOCKING_RULE
    assert document["findings"][0]["fix_versions"] == ["1.1"]
    assert document["run_id"] == "run-1"
```

**Test `test_the_scan_verdict_follows_the_blocking_rule`** checks: the scan verdict follows the blocking rule.

Step by step:

- Stores the result of calling `ScanReport('run-1', 'pip-audit', '2.10', T0, 'requirements.lock', 12, ())` in `clean`.
- Stores the result of calling `ScanReport('run-1', 'pip-audit', '2.10', T0, 'x', 12, (ScanFinding('a', '1', 'CVE-1', ())…` in `unfixed`.
- Stores the result of calling `ScanReport('run-1', 'pip-audit', '2.10', T0, 'x', 12, (ScanFinding('a', '1', 'CVE-1', ('1…` in `fixable`.
- Checks that `(clean.verdict, unfixed.verdict, fixable.verdict)` equals `('pass', 'pass', 'fail')`; if not, the test fails.
- Stores the result of calling `json.loads(fixable.to_json())` in `document`.
- Checks that `document['blocking_rule']` equals `BLOCKING_RULE`; if not, the test fails.
- Checks that `document['findings'][0]['fix_versions']` equals `['1.1']`; if not, the test fails.
- Checks that `document['run_id']` equals `'run-1'`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 170 to 182:

```python
def test_pip_audit_output_is_parsed_in_both_shapes():
    raw = json.dumps(
        {
            "dependencies": [
                {"name": "a", "version": "1", "vulns": [{"id": "X", "fix_versions": ["2"]}]},
                {"name": "b", "version": "1", "vulns": []},
            ]
        }
    )
    count, findings = parse_pip_audit(raw)
    assert count == 2
    assert findings == (ScanFinding("a", "1", "X", ("2",)),)
    assert parse_pip_audit(json.dumps([{"name": "c", "version": "1", "vulns": []}])) == (1, ())
```

**Test `test_pip_audit_output_is_parsed_in_both_shapes`** checks: pip audit output is parsed in both shapes.

Step by step:

- Stores the result of calling `json.dumps({'dependencies': [{'name': 'a', 'version': '1', 'vulns': [{'id': 'X', 'fix_ver…` in `raw`.
- Unpacks the result of calling `parse_pip_audit(raw)` into `(count, findings)`.
- Checks that `count` equals `2`; if not, the test fails.
- Checks that `findings` equals `(ScanFinding('a', '1', 'X', ('2',)),)`; if not, the test fails.
- Checks that `parse_pip_audit(json.dumps([{'name': 'c', 'versio…` equals `(1, ())`; if not, the test fails.

`tests/unit/domain/test_artifacts.py` lines 185 to 188:

```python
@pytest.mark.parametrize("raw", ["not json", "{}"])
def test_unusable_pip_audit_output_raises(raw):
    with pytest.raises((ValueError, KeyError)):
        parse_pip_audit(raw)
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.
> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.

**Test `test_unusable_pip_audit_output_raises`** checks: unusable pip audit output raises.

It takes: `raw`.

Decorators: `@pytest.mark.parametrize('raw', ['not json', '{}'])`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises((ValueError, KeyError))`:
  - Calls `parse_pip_audit(raw)`.

### `tests/unit/domain/test_roles_notes_audit_alerts.py`

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 1 to 10:

```python
from datetime import timedelta

import pytest

from notes_evidence.domain.alerts import AlertRules, detect_alerts
from notes_evidence.domain.audit import AuditAction, AuditEvent, format_timestamp, render_line
from notes_evidence.domain.errors import ValidationError
from notes_evidence.domain.notes import validate_note, validate_password, validate_username
from notes_evidence.domain.roles import Permission, Role, allowed
from tests.conftest import T0
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- From `datetime` it takes `timedelta`.
- It imports module `pytest`.
- From `notes_evidence.domain.alerts` it takes `AlertRules, detect_alerts`.
- From `notes_evidence.domain.audit` it takes `AuditAction, AuditEvent, format_timestamp, render_line`.
- From `notes_evidence.domain.errors` it takes `ValidationError`.
- From `notes_evidence.domain.notes` it takes `validate_note, validate_password, validate_username`.
- From `notes_evidence.domain.roles` it takes `Permission, Role, allowed`.
- From `tests.conftest` it takes `T0`.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 13 to 22:

```python
@pytest.mark.parametrize(
    ("role", "granted"),
    [
        (Role.ADMIN, set(Permission)),
        (Role.MEMBER, {Permission.READ_OWN, Permission.WRITE_OWN}),
        (Role.READONLY, {Permission.READ_OWN, Permission.READ_ANY}),
    ],
)
def test_each_role_holds_exactly_its_permissions(role, granted):
    assert {p for p in Permission if allowed(role, p)} == granted
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.
> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.
> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_each_role_holds_exactly_its_permissions`** checks: each role holds exactly its permissions.

It takes: `role`; `granted`.

Decorators: `@pytest.mark.parametrize(('role', 'granted'), [(Role.ADMIN, set(Permis…`.

Step by step:

- Checks that `{p for p in Permission if allowed(role, p)}` equals `granted`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 25 to 27:

```python
def test_a_valid_username_and_password_pass_through():
    assert validate_username("ada") == "ada"
    assert validate_password("twelve chars!") == "twelve chars!"
```

**Test `test_a_valid_username_and_password_pass_through`** checks: a valid username and password pass through.

Step by step:

- Checks that `validate_username('ada')` equals `'ada'`; if not, the test fails.
- Checks that `validate_password('twelve chars!')` equals `'twelve chars!'`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 30 to 33:

```python
@pytest.mark.parametrize("bad", ["", "A", "1abc", "has space", "x" * 40, None, 7])
def test_bad_usernames_are_rejected(bad):
    with pytest.raises(ValidationError):
        validate_username(bad)
```

> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.

**Test `test_bad_usernames_are_rejected`** checks: bad usernames are rejected.

It takes: `bad`.

Decorators: `@pytest.mark.parametrize('bad', ['', 'A', '1abc', 'has space', 'x' * 4…`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(ValidationError)`:
  - Calls `validate_username(bad)`.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 36 to 39:

```python
@pytest.mark.parametrize("bad", ["short", "", None])
def test_short_passwords_are_rejected(bad):
    with pytest.raises(ValidationError):
        validate_password(bad)
```

**Test `test_short_passwords_are_rejected`** checks: short passwords are rejected.

It takes: `bad`.

Decorators: `@pytest.mark.parametrize('bad', ['short', '', None])`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(ValidationError)`:
  - Calls `validate_password(bad)`.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 42 to 44:

```python
def test_a_note_is_trimmed_and_validated():
    data = validate_note("  Title  ", "body")
    assert (data.title, data.body) == ("Title", "body")
```

**Test `test_a_note_is_trimmed_and_validated`** checks: a note is trimmed and validated.

Step by step:

- Stores the result of calling `validate_note(' Title ', 'body')` in `data`.
- Checks that `(data.title, data.body)` equals `('Title', 'body')`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 47 to 52:

```python
@pytest.mark.parametrize(
    ("title", "body"), [("", "x"), ("   ", "x"), ("t" * 121, "x"), (5, "x"), ("t", "b" * 10_001), ("t", None)]
)
def test_bad_notes_are_rejected(title, body):
    with pytest.raises(ValidationError):
        validate_note(title, body)
```

**Test `test_bad_notes_are_rejected`** checks: bad notes are rejected.

It takes: `title`; `body`.

Decorators: `@pytest.mark.parametrize(('title', 'body'), [('', 'x'), (' ', 'x'), ('…`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(ValidationError)`:
  - Calls `validate_note(title, body)`.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 55 to 56:

```python
def event(action, seconds=0, user="bruno", outcome="ok", **detail):
    return AuditEvent(T0 + timedelta(seconds=seconds), 1, user, action, None, outcome, detail)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Function `event`.**

It takes: `action`; `seconds`, default `0`; `user`, default `'bruno'`; `outcome`, default `'ok'`; `**detail` (any extra named values).

Step by step:

- Gives back the result of calling `AuditEvent(T0 + timedelta(seconds=seconds), 1, user, action, None, outcome, detail)`.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 59 to 68:

```python
def test_a_log_line_has_fixed_fields_and_no_content():
    line = render_line(AuditEvent(T0, 7, "ada", AuditAction.NOTE_READ, 12, "ok"))
    assert line == "2026-10-22T09:00:00Z user=ada id=7 action=note_read note=12 outcome=ok"
    assert render_line(AuditEvent(T0, None, "unknown", AuditAction.LOGIN_FAILED, None, "failed")).endswith(
        "note=- outcome=failed"
    )
    assert render_line(event(AuditAction.ROLE_GRANTED, role="admin", target="chen")).endswith(
        "outcome=ok role=admin target=chen"
    )
    assert format_timestamp(T0) == "2026-10-22T09:00:00Z"
```

**Test `test_a_log_line_has_fixed_fields_and_no_content`** checks: a log line has fixed fields and no content.

Step by step:

- Stores the result of calling `render_line(AuditEvent(T0, 7, 'ada', AuditAction.NOTE_READ, 12, 'ok'))` in `line`.
- Checks that `line` equals `'2026-10-22T09:00:00Z user=ada id=7 action=note_r…`; if not, the test fails.
- Checks that `render_line(AuditEvent(T0, None, 'unknown', AuditAction.LOGIN_FAILED,…`; if not, the test fails.
- Checks that `render_line(event(AuditAction.ROLE_GRANTED, role='admin', target='che…`; if not, the test fails.
- Checks that `format_timestamp(T0)` equals `'2026-10-22T09:00:00Z'`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 71 to 72:

```python
def failed(seconds, user="bruno"):
    return event(AuditAction.LOGIN_FAILED, seconds, user, "failed")
```

**Function `failed`.**

It takes: `seconds`; `user`, default `'bruno'`.

Step by step:

- Gives back the result of calling `event(AuditAction.LOGIN_FAILED, seconds, user, 'failed')`.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 75 to 83:

```python
def test_five_failed_logins_in_two_minutes_raise_one_alert():
    alerts = detect_alerts([failed(0), failed(10), failed(20), failed(30), failed(40)])
    assert len(alerts) == 1
    assert alerts[0].rule == "failed-logins"
    assert alerts[0].at == T0 + timedelta(seconds=40)
    assert (
        alerts[0].render()
        == "ALERT [failed-logins] 2026-10-22T09:00:40Z 5 failed logins for account bruno within 2 minutes"
    )
```

> **In plain words.** `obj[key]` looks a value up by key or position.

**Test `test_five_failed_logins_in_two_minutes_raise_one_alert`** checks: five failed logins in two minutes raise one alert.

Step by step:

- Stores the result of calling `detect_alerts([failed(0), failed(10), failed(20), failed(30), failed(40)])` in `alerts`.
- Checks that `len(alerts)` equals `1`; if not, the test fails.
- Checks that `alerts[0].rule` equals `'failed-logins'`; if not, the test fails.
- Checks that `alerts[0].at` equals `T0 + timedelta(seconds=40)`; if not, the test fails.
- Checks that `alerts[0].render()` equals `'ALERT [failed-logins] 2026-10-22T09:00:40Z 5 fai…`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 86 to 87:

```python
def test_four_failed_logins_raise_nothing():
    assert detect_alerts([failed(s) for s in (0, 10, 20, 30)]) == []
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Test `test_four_failed_logins_raise_nothing`** checks: four failed logins raise nothing.

Step by step:

- Checks that `detect_alerts([failed(s) for s in (0, 10, 20, 30)…` equals `[]`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 90 to 91:

```python
def test_failures_spread_beyond_the_window_raise_nothing():
    assert detect_alerts([failed(s) for s in (0, 40, 80, 120, 160, 200)]) == []
```

**Test `test_failures_spread_beyond_the_window_raise_nothing`** checks: failures spread beyond the window raise nothing.

Step by step:

- Checks that `detect_alerts([failed(s) for s in (0, 40, 80, 120…` equals `[]`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 94 to 95:

```python
def test_each_account_is_counted_on_its_own():
    assert detect_alerts([failed(s, "bruno") for s in (0, 1, 2)] + [failed(s, "chen") for s in (3, 4)]) == []
```

**Test `test_each_account_is_counted_on_its_own`** checks: each account is counted on its own.

Step by step:

- Checks that `detect_alerts([failed(s, 'bruno') for s in (0, 1,…` equals `[]`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 98 to 99:

```python
def test_a_long_attack_raises_an_alert_per_burst_not_per_attempt():
    assert len(detect_alerts([failed(s) for s in range(0, 12)])) == 2
```

**Test `test_a_long_attack_raises_an_alert_per_burst_not_per_attempt`** checks: a long attack raises an alert per burst not per attempt.

Step by step:

- Checks that `len(detect_alerts([failed(s) for s in range(0, 12…` equals `2`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 102 to 104:

```python
def test_the_rule_is_configurable():
    rules = AlertRules(failed_logins=2, window=timedelta(minutes=1))
    assert len(detect_alerts([failed(0), failed(30)], rules)) == 1
```

**Test `test_the_rule_is_configurable`** checks: the rule is configurable.

Step by step:

- Stores the result of calling `AlertRules(failed_logins=2, window=timedelta(minutes=1))` in `rules`.
- Checks that `len(detect_alerts([failed(0), failed(30)], rules))` equals `1`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 107 to 111:

```python
def test_an_admin_grant_raises_an_alert_and_a_member_grant_does_not():
    assert [
        a.rule for a in detect_alerts([event(AuditAction.ROLE_GRANTED, 0, "ada", role="admin", target="chen")])
    ] == ["admin-granted"]
    assert detect_alerts([event(AuditAction.ROLE_GRANTED, 0, "ada", role="member", target="chen")]) == []
```

**Test `test_an_admin_grant_raises_an_alert_and_a_member_grant_does_not`** checks: an admin grant raises an alert and a member grant does not.

Step by step:

- Checks that `[a.rule for a in detect_alerts([event(AuditAction…` equals `['admin-granted']`; if not, the test fails.
- Checks that `detect_alerts([event(AuditAction.ROLE_GRANTED, 0,…` equals `[]`; if not, the test fails.

`tests/unit/domain/test_roles_notes_audit_alerts.py` lines 114 to 115:

```python
def test_events_out_of_order_are_sorted_first():
    assert len(detect_alerts([failed(40), failed(0), failed(30), failed(10), failed(20)])) == 1
```

**Test `test_events_out_of_order_are_sorted_first`** checks: events out of order are sorted first.

Step by step:

- Checks that `len(detect_alerts([failed(40), failed(0), failed(…` equals `1`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/unit/domain
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 60 source files`.

```bash
.venv/bin/ruff check tests/unit/domain/test_artifacts.py tests/unit/domain/test_roles_notes_audit_alerts.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_the_access_list_renders_one_block_per_system_and_parses_back` check?
   **Answer:** it checks: the access list renders one block per system and parses back.
2. What does the test `test_removing_one_principal_from_one_system_leaves_the_others` check?
   **Answer:** it checks: removing one principal from one system leaves the others.
3. What does the test `test_a_complete_justified_review_has_no_findings` check?
   **Answer:** it checks: a complete justified review has no findings.
4. What does the test `test_every_principal_needs_a_decision` check?
   **Answer:** it checks: every principal needs a decision.
5. What does the test `test_every_decision_needs_a_reason_and_the_review_a_ticket` check?
   **Answer:** it checks: every decision needs a reason and the review a ticket.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
