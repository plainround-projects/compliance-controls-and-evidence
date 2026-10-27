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

SPEC = EvidenceSpec("C1-access-list.txt", "access_list", "proves", "point in time", 7, "weekly")
C1 = Control("C1", "Access control", "r", "w", {"iso27001": ("A.5.15", "A.5.18"), "soc2": ("CC6.1",)}, (SPEC,))
C6 = Control("C6", "Access review", "r", "w", {"iso27001": ("A.5.18",), "soc2": ("CC6.2",)}, ())


def test_text_report_lists_findings_and_the_verdict():
    report = Report(("a", "b"), (error("EVD002", "C1 x", "missing"), warning("EVD005", "C2 y", "stale")))
    lines = render_text(report).splitlines()
    assert lines[0] == "ERROR   EVD002 C1 x: missing"
    assert lines[1] == "WARNING EVD005 C2 y: stale"
    assert lines[2] == "FAILED: 2 files checked, 1 errors, 1 warnings"
    assert render_text(Report(("a",), ())) == "OK: 1 files checked, 0 errors, 0 warnings"


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


def test_overlap_groups_controls_by_reference():
    table = overlap([C1, C6])
    assert table["iso27001"]["A.5.18"] == ["C1", "C6"]
    assert table["soc2"] == {"CC6.1": ["C1"], "CC6.2": ["C6"]}
    assert framework_table([C1, C6]).splitlines()[0] == "| Framework | Reference | Controls |"


def test_a_manifest_entry_that_names_another_control_is_reported():
    text = (
        "# access list, generated 2026-10-22T09:00:00Z\n## repository (permission per person)\n"
        "## database roles\n## cloud account users\n"
    )
    manifest = {SPEC.file: ManifestEntry(SPEC.file, "C9", T0, "ada", "fixture", digest(text))}
    found = verify_pack([C1], manifest, {SPEC.file: text}, [], [], date(2026, 10, 23))
    assert any("belongs to C9" in f.message for f in found)


def test_an_access_list_without_its_dated_header_is_reported():
    text = "## repository (permission per person)\n## database roles\n## cloud account users\n"
    manifest = {SPEC.file: ManifestEntry(SPEC.file, "C1", T0, "ada", "fixture", digest(text))}
    found = verify_pack([C1], manifest, {SPEC.file: text}, [], [], date(2026, 10, 23))
    assert any(f.message == "no dated header" for f in found)


def test_a_scan_report_without_a_verdict_is_reported():
    spec = EvidenceSpec("C5-scan-report.json", "scan", "p", "x", 7, "weekly")
    control = Control("C5", "Scan", "r", "w", {"iso27001": ("A.8.8",), "soc2": ("CC7.1",)}, (spec,))
    text = '{"run_id": "r1", "verdict": "maybe"}'
    manifest = {spec.file: ManifestEntry(spec.file, "C5", T0, "ada", "fixture", digest(text))}
    found = verify_pack([control], manifest, {spec.file: text}, [], [], date(2026, 10, 23))
    assert any(f.message == "no verdict" for f in found)


def test_a_change_with_no_deployment_id_is_found_in_the_csv():
    header = '"number","author","merged_at","commit","approvers","deploy_id"'
    text = header + '\n41,"chen","2026-10-21T09:00:00Z","a41c9de","ada",""\n'
    assert [(e.number, e.reason) for e in exceptions_in_csv(text)] == [(41, "no deployment record")]


def test_refused_counts_a_call_that_goes_through_as_zero():
    assert _refused(lambda: None) == 0

    def refuse():
        raise NotFoundError("x")

    assert _refused(refuse) == 1


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
