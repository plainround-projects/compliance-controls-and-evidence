"""`controls-evidence`: run the collectors, build the index, verify and report. Owns the exit codes."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from notes_evidence.application import evidence_collect as collect
from notes_evidence.application.exercise import exercise_service
from notes_evidence.application.reporting import render_report, render_text
from notes_evidence.domain.controls import Gap, RecordedException
from notes_evidence.domain.evidence import framework_table
from notes_evidence.domain.findings import Report
from notes_evidence.domain.roles import Role
from notes_evidence.infrastructure.alerting import FileAlertSink
from notes_evidence.infrastructure.backup import BackupError, DockerBackupRunner
from notes_evidence.infrastructure.catalog import CatalogError, TomlCatalog
from notes_evidence.infrastructure.evidence_store import FileEvidenceStore
from notes_evidence.infrastructure.logging_setup import configure_logging
from notes_evidence.infrastructure.scanner import PipAuditScanner, ScanError
from notes_evidence.infrastructure.settings import Settings, SettingsError, load_settings
from notes_evidence.infrastructure.sources import SourceError
from notes_evidence.interfaces import wiring

STEPS = ("exercise", "alert-test", "log-sample", "access", "changes", "restore-test", "scan", "review", "index")


def build_parser() -> argparse.ArgumentParser:
    """One subcommand per collector, plus collect, verify and report."""
    parser = argparse.ArgumentParser(prog="controls-evidence", description="Produce and verify the evidence pack.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in (*STEPS, "collect", "verify", "report"):
        commands.add_parser(name)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command and return the exit code: 0 ok, 1 findings or a failed step, 2 bad configuration or input."""
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings(os.environ)
        configure_logging("WARNING")
        return _dispatch(args.command, settings)
    except (SettingsError, CatalogError) as problem:
        print(f"configuration error: {problem}", file=sys.stderr)
        return 2
    except (SourceError, BackupError, ScanError, OSError) as problem:
        print(f"step failed: {problem}", file=sys.stderr)
        return 1


def _dispatch(command: str, settings: Settings) -> int:
    store = FileEvidenceStore(settings.evidence_dir)
    catalog = TomlCatalog(settings.controls_file)
    if command == "verify":
        report = _verify(store, catalog)
        print(render_text(report))
        return 0 if report.ok else 1
    if command == "report":
        report = _verify(store, catalog)
        target = Path(os.environ.get("REPORT_DIR", "build")) / "report.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_report(report, catalog.controls(), store.manifest()), encoding="utf-8")
        print(f"wrote {target}")
        return 0 if report.ok else 1
    runtime = wiring.build_runtime(settings)
    collector = collect.Collector(store, runtime.clock, settings.run_by, settings.evidence_source)
    steps = STEPS if command == "collect" else (command,)
    for step in steps:
        print(f"== {step}: {_run_step(step, settings, runtime, collector, catalog)}")
    if command == "collect":
        report = _verify(store, catalog)
        print(render_text(report))
        return 0 if report.ok else 1
    return 0


def _verify(store: FileEvidenceStore, catalog: TomlCatalog) -> Report:
    exceptions: list[RecordedException] = catalog.exceptions()
    gaps: list[Gap] = catalog.gaps()
    return collect.verify(store, catalog.controls(), exceptions, gaps, datetime.now(UTC).date())


def _run_step(
    step: str, settings: Settings, runtime: wiring.Runtime, collector: collect.Collector, catalog: TomlCatalog
) -> str:
    handlers: dict[str, Callable[[], str]] = {
        "exercise": lambda: _exercise(runtime),
        "alert-test": lambda: _alert_test(runtime, collector, settings),
        "log-sample": lambda: (
            f"{collect.collect_log_sample(collector, runtime.audit)} audit events in {collect.LOG_FILE}"
        ),
        "access": lambda: _access(settings, collector),
        "changes": lambda: (
            f"{collect.collect_changes(collector, wiring.change_source(settings))} change(s) with exceptions, "
            f"written to {collect.CHANGES_FILE}"
        ),
        "restore-test": lambda: _restore(settings, collector),
        "scan": lambda: _scan(settings, collector),
        "review": lambda: _review(settings, collector, catalog),
        "index": lambda: _index(collector, catalog),
    }
    return handlers[step]()


def _exercise(runtime: wiring.Runtime) -> str:
    summary = exercise_service(wiring.provisioner(runtime.settings), runtime.hasher, runtime.service)
    return (
        f"{len(summary.users)} accounts used the service, {summary.notes_created} notes written, "
        f"{summary.refusals} requests refused"
    )


def _alert_test(runtime: wiring.Runtime, collector: collect.Collector, settings: Settings) -> str:
    found = runtime.users.find_by_username("ada")
    if found is None:
        raise SourceError("the alert test needs the account 'ada': run `exercise` first")
    admin = found[0]
    sink = FileAlertSink(settings.state_dir / "alerts.log")
    alerts = collect.run_alert_test(
        collector, runtime.service, runtime.audit, sink, lambda: _grant_and_revert(runtime, admin), "bruno"
    )
    return f"{len(alerts)} alert(s) delivered: " + "; ".join(alert.rule for alert in alerts)


def _grant_and_revert(runtime: wiring.Runtime, admin: object) -> None:
    from notes_evidence.domain.notes import User

    assert isinstance(admin, User)
    runtime.service.grant_role(admin, "chen", Role.ADMIN)
    runtime.service.grant_role(admin, "chen", Role.MEMBER)


def _access(settings: Settings, collector: collect.Collector) -> str:
    access = collect.collect_access(
        collector, wiring.repository_access(settings), wiring.database_roles(settings), wiring.cloud_directory(settings)
    )
    return ", ".join(f"{count} {system.split(' (')[0]}" for system, count in access.counts().items())


def _restore(settings: Settings, collector: collect.Collector) -> str:
    runner = DockerBackupRunner(settings.db_exec_prefix, settings.postgres_user, settings.postgres_db)
    result = collect.run_restore_test(collector, runner)
    return f"{result.restored_rows:,} of {result.source_rows:,} rows restored in {result.seconds} s"


def _scan(settings: Settings, collector: collect.Collector) -> str:
    scanner = PipAuditScanner("requirements.lock", os.environ, collector.clock.now)
    return f"verdict {collect.collect_scan(collector, scanner)}"


def _review(settings: Settings, collector: collect.Collector, catalog: TomlCatalog) -> str:
    outcome = collect.review_access(
        collector,
        wiring.repository_access(settings),
        wiring.database_roles(settings),
        wiring.cloud_directory(settings),
        catalog,
    )
    if outcome.findings:
        raise SourceError("the access review is incomplete: " + "; ".join(f.message for f in outcome.findings))
    assert outcome.before is not None
    assert outcome.after is not None
    gone = len(outcome.before.entries) - len(outcome.after.entries)
    return f"{gone} access removed, recorded in {collect.REVIEW_FILE}"


def _index(collector: collect.Collector, catalog: TomlCatalog) -> str:
    collect.build_index(collector, catalog, framework_table(catalog.controls()))
    return "wrote INDEX.md"


if __name__ == "__main__":
    raise SystemExit(main())
