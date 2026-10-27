import pytest

from notes_evidence.interfaces.cli import build_parser, main


def test_the_parser_knows_every_step():
    names = build_parser().parse_args(["collect"]).command
    assert names == "collect"
    for step in (
        "exercise",
        "alert-test",
        "log-sample",
        "access",
        "changes",
        "restore-test",
        "scan",
        "review",
        "index",
        "verify",
        "report",
    ):
        assert build_parser().parse_args([step]).command == step


def test_an_unknown_command_is_a_usage_error():
    with pytest.raises(SystemExit) as stop:
        build_parser().parse_args(["delete-everything"])
    assert stop.value.code == 2


def test_missing_settings_exit_2(monkeypatch, capsys):
    monkeypatch.delenv("NOTES_SECRET", raising=False)
    assert main(["verify"]) == 2
    assert "NOTES_SECRET is required" in capsys.readouterr().err


def test_a_missing_controls_file_exits_2(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("NOTES_SECRET", "s" * 32)
    monkeypatch.setenv("CONTROLS_FILE", str(tmp_path / "controls.toml"))
    monkeypatch.setenv("EVIDENCE_DIR", str(tmp_path / "evidence"))
    assert main(["verify"]) == 2
    assert "does not exist" in capsys.readouterr().err
