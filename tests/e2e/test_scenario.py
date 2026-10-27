"""The lesson's scenario end to end: use the service, collect the artifacts, review access, verify, catch tampering.

Runs from the repository root against the PostgreSQL of `make up` and writes into a temporary folder.
"""

from __future__ import annotations

import os

import pytest

from notes_evidence.interfaces.cli import main

pytestmark = pytest.mark.e2e


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


def test_collect_produces_a_pack_that_verifies_and_tampering_is_caught(scenario, capsys):
    assert main(["collect"]) == 0
    out = capsys.readouterr().out
    assert "== exercise: 4 accounts used the service, 3 notes written, 2 requests refused" in out
    assert "== alert-test: 2 alert(s) delivered: failed-logins; admin-granted" in out
    assert "== review: 1 access removed" in out
    assert out.splitlines()[-1].startswith("OK:")

    pack = scenario / "evidence"
    names = {path.name for path in pack.iterdir()}
    assert names == {
        "C1-access-list.txt", "C2-changes.csv", "C3-log-sample.txt", "C3-alert-test.txt",
        "C4-restore-test.txt", "C5-scan-report.json", "C6-access-review.md", "INDEX.md", "manifest.json",
    }  # fmt: skip
    assert "contractor-lee" not in (pack / "C1-access-list.txt").read_text()
    assert "Removed: cloud account users contractor-lee." in (pack / "C6-access-review.md").read_text()
    assert "result: verified" in (pack / "C4-restore-test.txt").read_text()
    assert "ALERT [failed-logins]" in (pack / "C3-alert-test.txt").read_text()
    assert "EXC-1 (C2)" in (pack / "INDEX.md").read_text()
    assert (scenario / "state" / "alerts.log").read_text().count("ALERT") == 2

    assert main(["verify"]) == 0
    assert main(["report"]) == 0
    assert "| iso27001 | A.5.18 | C1, C6 (overlap) |" in (scenario / "build" / "report.md").read_text()

    capsys.readouterr()
    (pack / "C2-changes.csv").write_text(
        (pack / "C2-changes.csv").read_text() + '99,"ada","2026-10-22T00:00:00Z","abc1234","ada","d"\n'
    )
    assert main(["verify"]) == 1
    assert "EVD003" in capsys.readouterr().out
