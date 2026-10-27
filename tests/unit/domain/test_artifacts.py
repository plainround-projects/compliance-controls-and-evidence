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

ENTRIES = (
    AccessEntry(REPOSITORY, "ada", "admin"),
    AccessEntry(REPOSITORY, "bruno", "write"),
    AccessEntry(DATABASE, "app_rw", "standard"),
    AccessEntry(DATABASE, "postgres", "superuser"),
    AccessEntry(CLOUD, "ada"),
    AccessEntry(CLOUD, "contractor-lee"),
)
ACCESS = AccessList(T0, ENTRIES)


def test_the_access_list_renders_one_block_per_system_and_parses_back():
    text = render_access_list(ACCESS)
    assert text.startswith(
        "# access list, generated 2026-10-22T09:00:00Z\n## repository (permission per person)\nada\tadmin\n"
    )
    assert "## cloud account users\nada\ncontractor-lee\n" in text
    assert parse_access_list(text)[CLOUD] == ["ada", "contractor-lee"]
    assert ACCESS.counts() == {REPOSITORY: 2, DATABASE: 2, CLOUD: 2}


def test_removing_one_principal_from_one_system_leaves_the_others():
    after = ACCESS.without(CLOUD, "contractor-lee")
    assert [e.principal for e in after.in_system(CLOUD)] == ["ada"]
    assert len(after.entries) == 5


PEOPLE = {
    "ada": Person("ada", "Developer"),
    "contractor-lee": Person("contractor-lee", "Contractor", date(2026, 9, 18)),
}


def decisions(overrides=None):
    base = {(e.system, e.principal): Decision(e.system, e.principal, True, "needed for the job") for e in ENTRIES}
    base[(CLOUD, "contractor-lee")] = Decision(CLOUD, "contractor-lee", False, "left on 2026-09-18")
    base.update(overrides or {})
    return tuple(base.values())


def request(items=None, ticket="SEC-17"):
    return ReviewRequest("eli", date(2026, 10, 22), ticket, items if items is not None else decisions())


def codes(req):
    return {f.code for f in check_review(ACCESS, req, PEOPLE)}


def test_a_complete_justified_review_has_no_findings():
    assert check_review(ACCESS, request(), PEOPLE) == []


def test_every_principal_needs_a_decision():
    assert "ARV001" in codes(request(decisions()[:-1]))


def test_every_decision_needs_a_reason_and_the_review_a_ticket():
    assert "ARV002" in codes(request(decisions({(REPOSITORY, "ada"): Decision(REPOSITORY, "ada", True, " ")})))
    assert "ARV002" in codes(request(ticket=""))


def test_a_leaver_cannot_be_kept():
    kept = decisions({(CLOUD, "contractor-lee"): Decision(CLOUD, "contractor-lee", True, "still useful")})
    assert "ARV003" in codes(request(kept))


def test_the_review_record_shows_before_removed_after_and_the_proof():
    after = ACCESS.without(CLOUD, "contractor-lee")
    text = render_review(ACCESS, after, request())
    assert text.splitlines()[0] == "Reviewer: eli. Date: 2026-10-22. Ticket: SEC-17."
    assert "Before: 2 repository, 2 database roles, 2 cloud account users." in text
    assert "Removed: cloud account users contractor-lee." in text
    assert "After: 2 repository, 2 database roles, 1 cloud account users." in text
    assert "none of the removed principals is listed" in text


def test_the_review_record_admits_a_removal_that_did_not_happen():
    assert "contractor-lee is still listed" in render_review(ACCESS, ACCESS, request())


def test_a_review_that_removes_nothing_says_so():
    keep_all = request(tuple(Decision(e.system, e.principal, True, "needed") for e in ENTRIES))
    assert "Removed: nothing." in render_review(ACCESS, ACCESS, keep_all)


def change(number, author="chen", approvers=("ada",), deploy="deploy-1", hour=9):
    return MergedChange(
        number, author, datetime(2026, 10, 21, hour, 0, tzinfo=UTC), "a41c9de" + "0" * 33, approvers, deploy
    )


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


def test_the_changes_csv_quotes_strings_not_numbers_and_rederives_the_exceptions():
    text = render_changes([change(43, approvers=()), change(41, approvers=("ada", "bruno"))])
    lines = text.splitlines()
    assert lines[0] == '"number","author","merged_at","commit","approvers","deploy_id"'
    assert lines[1] == '41,"chen","2026-10-21T09:00:00Z","a41c9de","ada+bruno","deploy-1"'
    assert [e.number for e in exceptions_in_csv(text)] == [43]


def test_restore_artifact_has_the_lessons_three_lines_and_a_verdict():
    result = RestoreResult(
        T0, T0 + timedelta(hours=6), T0 + timedelta(hours=6, minutes=4, seconds=41), "notes", 12408, 12408
    )
    text = render_restore(result)
    assert text.splitlines()[0] == "restore started 2026-10-22T15:00:00Z from backup 2026-10-22T09:00:00Z"
    assert "restore finished 2026-10-22T15:04:41Z (4 min 41 s)" in text
    assert "check: notes table has 12,408 rows; source had 12,408 rows at backup time" in text
    assert text.endswith("result: verified\n")


def test_a_restore_with_fewer_rows_is_a_mismatch():
    result = RestoreResult(T0, T0, T0 + timedelta(seconds=9), "notes", 100, 99)
    assert not result.verified
    assert render_restore(result).endswith("result: MISMATCH\n")
    assert format_duration(9) == "9 s"


def test_the_scan_verdict_follows_the_blocking_rule():
    clean = ScanReport("run-1", "pip-audit", "2.10", T0, "requirements.lock", 12, ())
    unfixed = ScanReport("run-1", "pip-audit", "2.10", T0, "x", 12, (ScanFinding("a", "1", "CVE-1", ()),))
    fixable = ScanReport("run-1", "pip-audit", "2.10", T0, "x", 12, (ScanFinding("a", "1", "CVE-1", ("1.1",)),))
    assert (clean.verdict, unfixed.verdict, fixable.verdict) == ("pass", "pass", "fail")
    document = json.loads(fixable.to_json())
    assert document["blocking_rule"] == BLOCKING_RULE
    assert document["findings"][0]["fix_versions"] == ["1.1"]
    assert document["run_id"] == "run-1"


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


@pytest.mark.parametrize("raw", ["not json", "{}"])
def test_unusable_pip_audit_output_raises(raw):
    with pytest.raises((ValueError, KeyError)):
        parse_pip_audit(raw)
