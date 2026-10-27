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

FIXTURES = REPOSITORY_ROOT / "fixtures"


def test_scrypt_hashes_are_salted_and_verified():
    hasher = ScryptHasher()
    first, second = hasher.hash("correct horse"), hasher.hash("correct horse")
    assert first != second
    assert first.startswith("scrypt$")
    assert hasher.verify("correct horse", first)
    assert not hasher.verify("wrong horse", first)


@pytest.mark.parametrize("stored", ["!", "", "scrypt$only", "md5$a$b", "scrypt$abc$abc"])
def test_an_unusable_or_malformed_hash_never_matches(stored):
    assert not ScryptHasher().verify("anything", stored)


USER = User(7, "ada", Role.ADMIN, True)


def test_tokens_verify_until_they_expire():
    tokens = HmacTokens("s" * 32, timedelta(minutes=15))
    token = tokens.issue(USER, T0)
    assert tokens.verify(token, T0 + timedelta(minutes=14)) == 7
    assert tokens.verify(token, T0 + timedelta(minutes=16)) is None


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


def test_a_token_signed_with_another_secret_is_refused():
    token = HmacTokens("a" * 32, timedelta(minutes=15)).issue(USER, T0)
    assert HmacTokens("b" * 32, timedelta(minutes=15)).verify(token, T0) is None


ENV = {"DATABASE_URL": "postgresql://x", "NOTES_SECRET": "s" * 32}


def test_settings_defaults():
    settings = load_settings(ENV)
    assert (settings.token_ttl_seconds, settings.retention_days, settings.evidence_source, settings.http_port) == (
        900,
        365,
        "fixture",
        8080,
    )
    assert settings.db_exec_prefix == ("docker", "compose", "exec", "-T", "db")


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
    ],
)
def test_bad_settings_are_rejected(env):
    with pytest.raises(SettingsError):
        load_settings(env)


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


def test_the_evidence_store_refuses_names_outside_its_folder(tmp_path):
    with pytest.raises(ValueError, match="directly in"):
        FileEvidenceStore(tmp_path).write("../x.txt", "x", "C1", T0, "ada", "fixture")


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


def test_a_commit_missing_from_the_deploy_log_has_no_deploy_id():
    prs = json.loads((FIXTURES / "github-merged-prs.json").read_text())
    assert parse_merged_prs(prs[:1], [])[0].deploy_id == ""


def test_the_state_cloud_directory_seeds_itself_and_removes_a_user(tmp_path):
    cloud = StateCloudDirectory(tmp_path / "state" / "cloud.json", FIXTURES / "aws-iam-users.json")
    assert [(e.system, e.principal) for e in cloud.users()] == [(CLOUD, "ada"), (CLOUD, "contractor-lee")]
    cloud.remove_user("contractor-lee")
    assert [e.principal for e in cloud.users()] == ["ada"]
    assert [
        e.principal
        for e in StateCloudDirectory(tmp_path / "state" / "cloud.json", FIXTURES / "aws-iam-users.json").users()
    ] == ["ada"]


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


def test_command_json_runs_the_command_and_parses_its_output():
    assert command_json(lambda argv: '{"a": 1}', ["x"])() == {"a": 1}


def test_run_command_returns_output_and_wraps_failures():
    assert run_command(["echo", "hi"]).strip() == "hi"
    with pytest.raises(SourceError, match="exited 1"):
        run_command(["false"])
    with pytest.raises(SourceError):
        run_command(["definitely-not-a-command-xyz"])


class Recorder:
    def __init__(self, fail_on: str = "") -> None:
        self.calls: list[tuple[list[str], bytes | None]] = []
        self.fail_on = fail_on

    def __call__(self, argv: list[str], stdin: bytes | None) -> bytes:
        self.calls.append((argv, stdin))
        if self.fail_on and self.fail_on in argv:
            raise BackupError("boom")
        return b""


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


def test_the_scratch_database_is_dropped_even_when_the_restore_fails():
    execute = Recorder(fail_on="pg_restore")
    runner = DockerBackupRunner(("db",), "postgres", "notes", execute)
    with pytest.raises(BackupError):
        runner.restore_and_count("notes")
    assert any(f"DROP DATABASE IF EXISTS {SCRATCH}" in " ".join(argv) for argv, _ in execute.calls[-1:])


def test_only_the_notes_table_can_be_counted():
    with pytest.raises(BackupError, match="unsupported"):
        DockerBackupRunner(("db",), "postgres", "notes", Recorder()).restore_and_count("users")


def test_run_in_container_wraps_failures():
    assert run_in_container(["cat"], b"abc") == b"abc"
    with pytest.raises(BackupError, match="exited"):
        run_in_container(["false"], None)
    with pytest.raises(BackupError):
        run_in_container(["definitely-not-a-command-xyz"], None)


AUDIT_JSON = json.dumps(
    {
        "dependencies": [
            {"name": "flask", "version": "3.1.3", "vulns": []},
            {"name": "x", "version": "1", "vulns": [{"id": "V-1", "fix_versions": ["2"]}]},
        ]
    }
)


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


def test_run_pip_audit_accepts_exit_0_and_1_and_rejects_the_rest():
    assert run_pip_audit(["python3", "-c", "print('{}')"]).strip() == "{}"
    assert run_pip_audit(["python3", "-c", "import sys; print('{}'); sys.exit(1)"]).strip() == "{}"
    with pytest.raises(ScanError):
        run_pip_audit(["python3", "-c", "import sys; sys.exit(2)"])
    with pytest.raises(ScanError):
        run_pip_audit(["definitely-not-a-command-xyz"])


def test_the_alert_sink_appends_to_a_file(tmp_path):
    sink = FileAlertSink(tmp_path / "state" / "alerts.log")
    sink.send("ALERT one")
    sink.send("ALERT two")
    assert (tmp_path / "state" / "alerts.log").read_text() == "ALERT one\nALERT two\n"


def test_the_json_formatter_keeps_only_whitelisted_fields():
    record = logging.LogRecord("notes.http", logging.INFO, "f", 1, "request", (), None)
    record.status = 200
    record.password = "never"
    document = json.loads(JsonFormatter().format(record))
    assert document["status"] == 200
    assert "password" not in document
    assert document["level"] == "INFO"


def test_configure_logging_installs_one_json_handler():
    configure_logging("WARNING")
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
    assert root.level == logging.WARNING


def test_the_system_clock_is_timezone_aware():
    assert SystemClock().now().tzinfo is not None
