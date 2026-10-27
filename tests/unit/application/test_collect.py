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


class Repo:
    def collaborators(self):
        return [AccessEntry(REPOSITORY, "ada", "admin"), AccessEntry(REPOSITORY, "bruno", "write")]


class Db:
    def roles(self):
        return [AccessEntry(DATABASE, "app_rw", "standard"), AccessEntry(DATABASE, "postgres", "superuser")]


class Cloud:
    def __init__(self):
        self.names = ["ada", "contractor-lee"]

    def users(self):
        return [AccessEntry(CLOUD, name) for name in self.names]

    def remove_user(self, name):
        self.names.remove(name)


class Changes:
    def merged_changes(self):
        at = datetime(2026, 10, 21, 9, tzinfo=UTC)
        return [
            MergedChange(41, "bruno", at, "a41c9de" + "0" * 33, ("ada",), "deploy-41"),
            MergedChange(43, "ada", at, "c7d1e55" + "0" * 33, (), "deploy-43"),
        ]


class Backup:
    def backup(self):
        return T0 - timedelta(hours=6)

    def restore_and_count(self, table):
        return 12408, 12408


class Scanner:
    def scan(self):
        return ScanReport("run-77", "pip-audit", "2.10", T0, "requirements.lock", 12, ())


class Sink:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


class Catalog:
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

    def exceptions(self):
        return [RecordedException("EXC-1", "C2", 43, "hotfix", "SEC-16")]

    def gaps(self):
        return []

    def people(self):
        return {"contractor-lee": Person("contractor-lee", "Contractor", date(2026, 9, 18))}

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


def verify(pack, **changes):
    _, store, catalog, *_ = pack
    return collect.verify(
        store,
        catalog.controls(),
        changes.get("exceptions", catalog.exceptions()),
        changes.get("gaps", []),
        date(2026, 10, 23),
    )


def test_the_whole_pack_verifies(pack):
    report = verify(pack)
    assert report.ok, report.findings
    assert report.findings == ()


def test_access_is_collected_from_the_three_systems_and_the_leaver_is_removed(pack):
    _, store, _, cloud, outcome, _ = pack
    assert outcome.findings == ()
    assert outcome.before is not None
    assert outcome.after is not None
    assert len(outcome.before.entries) - len(outcome.after.entries) == 1
    assert cloud.names == ["ada"]
    assert "contractor-lee" not in store.read(collect.ACCESS_FILE)
    assert "Removed: cloud account users contractor-lee." in store.read(collect.REVIEW_FILE)


def test_the_alert_test_keeps_the_alert_beside_the_time_of_the_action(pack):
    _, store, _, _, _, sink = pack
    text = store.read(collect.ALERT_FILE)
    assert "test action at 2026-10-22T09:01:00Z" in text
    assert "ALERT [failed-logins] 2026-10-22T09:01:00Z 5 failed logins for account bruno within 2 minutes" in text
    assert "ALERT [admin-granted]" in text
    assert len(sink.sent) == 2


def test_the_log_sample_has_log_lines_and_no_note_text(pack):
    _, store, *_ = pack
    sample = store.read(collect.LOG_FILE)
    assert "action=login_failed" in sample
    assert "Call back" not in sample


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


def test_the_index_lists_each_file_who_ran_it_the_exceptions_and_the_gaps(pack):
    _, store, *_ = pack
    index = store.read("INDEX.md")
    assert "| C1-access-list.txt | C1 Access control | proves access_list | ada | 2026-10-22 |" in index
    assert "EXC-1 (C2): hotfix Follow-up: SEC-16." in index
    assert "## Tracked gaps\n\nNone." in index
    assert "| framework table |" in index


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


def test_a_missing_file_is_an_error(pack):
    _, store, *_ = pack
    del store.files[collect.SCAN_FILE]
    assert "EVD002" in {f.code for f in verify(pack).errors}


def test_an_empty_file_is_worse_than_a_missing_one(pack):
    _, store, *_ = pack
    store.files[collect.SCAN_FILE] = " \n"
    assert "EVD002" in {f.code for f in verify(pack).errors}


def test_a_hand_edited_file_fails_its_hash(pack):
    _, store, *_ = pack
    store.files[collect.CHANGES_FILE] += '999,"x","2026-10-22T00:00:00Z","abc","ada","d"\n'
    assert "EVD003" in {f.code for f in verify(pack).errors}


def test_a_file_with_no_manifest_entry_is_unaccounted_for(pack):
    _, store, *_ = pack
    del store.entries[collect.SCAN_FILE]
    assert "EVD003" in {f.code for f in verify(pack).errors}


def test_an_unclaimed_file_is_reported(pack):
    _, store, *_ = pack
    store.files["notes.txt"] = "stray"
    assert "EVD004" in {f.code for f in verify(pack).errors}


def test_a_stale_artifact_is_a_warning_not_an_error(pack):
    _, store, catalog, *_ = pack
    report = collect.verify(store, catalog.controls(), catalog.exceptions(), [], date(2027, 1, 1))
    assert report.ok
    assert {f.code for f in report.warnings} == {"EVD005"}


def test_an_unlisted_exception_in_the_data_fails(pack):
    assert "EVD006" in {f.code for f in verify(pack, exceptions=[]).errors}
    assert "EVD006" in {
        f.code for f in verify(pack, exceptions=[RecordedException("EXC-1", "C2", 43, "hotfix", "")]).errors
    }


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


def test_a_control_needs_two_framework_references(pack):
    _, store, catalog, *_ = pack
    thin = Control(
        "C1", "Access control", "r", "w", {"iso27001": ("A.5.15",), "soc2": ()}, catalog.controls()[0].evidence
    )
    report = collect.verify(store, [thin, *catalog.controls()[1:]], catalog.exceptions(), [], date(2026, 10, 23))
    assert "EVD009" in {f.code for f in report.errors}


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


def test_a_missing_index_is_reported(pack):
    _, store, *_ = pack
    del store.files["INDEX.md"]
    assert any(f.subject == "INDEX.md" for f in verify(pack).errors)


def test_the_exercise_uses_the_service_as_four_roles_and_refuses_two_requests():
    rig = Rig()
    summary = exercise_service(rig.users, rig.hasher, rig.service, new_password=lambda: "throwaway-password-1")
    assert set(summary.users) == {"ada", "bruno", "chen", "dana"}
    assert (summary.notes_created, summary.refusals) == (3, 2)
    assert len(rig.notes.rows) == 2
    assert [e.action for e in rig.audit.events if e.outcome == "denied"] == [AuditAction.ACCESS_DENIED] * 2
    assert not any(isinstance(e, AuditEvent) and "throwaway" in repr(e) for e in rig.audit.events)
