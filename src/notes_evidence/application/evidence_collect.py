"""The evidence collectors: each reads a real system through a port and writes one artifact and its manifest entry."""

from __future__ import annotations

import contextlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from notes_evidence.application.ports import (
    AlertSink,
    AuditLog,
    BackupRunner,
    ChangeSource,
    Clock,
    CloudDirectory,
    ControlCatalog,
    DatabaseAccess,
    EvidenceStore,
    Notes,
    RepositoryAccess,
    ScanRunner,
)
from notes_evidence.domain.access import AccessEntry, AccessList, render_access_list
from notes_evidence.domain.alerts import Alert, detect_alerts
from notes_evidence.domain.audit import format_timestamp, render_line
from notes_evidence.domain.changes import find_exceptions, render_changes
from notes_evidence.domain.controls import Control, Gap, RecordedException
from notes_evidence.domain.errors import InvalidCredentialsError
from notes_evidence.domain.evidence import verify_pack
from notes_evidence.domain.findings import Finding, Report, error
from notes_evidence.domain.restore import RestoreResult, render_restore
from notes_evidence.domain.review import ReviewRequest, check_review, render_review

ACCESS_FILE = "C1-access-list.txt"
CHANGES_FILE = "C2-changes.csv"
LOG_FILE = "C3-log-sample.txt"
ALERT_FILE = "C3-alert-test.txt"
RESTORE_FILE = "C4-restore-test.txt"
SCAN_FILE = "C5-scan-report.json"
REVIEW_FILE = "C6-access-review.md"


@dataclass(frozen=True)
class Collector:
    """What every collector shares: where to write, what time it is, who runs it, and which sources it reads."""

    store: EvidenceStore
    clock: Clock
    run_by: str
    source: str


def collect_access(
    collector: Collector, repository: RepositoryAccess, database: DatabaseAccess, cloud: CloudDirectory
) -> AccessList:
    """C1: ask each system who can reach it, and write the list."""
    entries: list[AccessEntry] = [*repository.collaborators(), *database.roles(), *cloud.users()]
    access = AccessList(collector.clock.now(), tuple(entries))
    collector.store.write(
        ACCESS_FILE, render_access_list(access), "C1", access.generated_at, collector.run_by, collector.source
    )
    return access


def collect_changes(collector: Collector, changes: ChangeSource) -> int:
    """C2: write every merged change with its approvers and its deployment; return how many have exceptions."""
    merged = changes.merged_changes()
    collector.store.write(
        CHANGES_FILE, render_changes(merged), "C2", collector.clock.now(), collector.run_by, collector.source
    )
    return len(find_exceptions(merged))


def collect_log_sample(collector: Collector, audit: AuditLog, limit: int = 20) -> int:
    """C3: the most recent audit events, rendered as the log lines the service writes."""
    events = audit.latest(limit)
    text = "\n".join(render_line(event) for event in events) + "\n"
    collector.store.write(LOG_FILE, text, "C3", collector.clock.now(), collector.run_by, collector.source)
    return len(events)


def run_alert_test(
    collector: Collector,
    notes: Notes,
    audit: AuditLog,
    sink: AlertSink,
    grant_admin: Callable[[], object],
    username: str,
    attempts: int = 5,
) -> list[Alert]:
    """C3: do what the alert is for, read the trail back, and keep the alert message beside the time of the action.

    Five wrong passwords for one account, then an admin grant. Each is a real call into the service, so the alert fires
    on what the log really holds and not on the rule's configuration.
    """
    started = collector.clock.now()
    for _ in range(attempts):
        with contextlib.suppress(InvalidCredentialsError):
            notes.login(username, secrets.token_urlsafe(16))
    grant_admin()
    alerts = detect_alerts(audit.since(started))
    for alert in alerts:
        sink.send(alert.render())
    lines = [
        f"alert test: {attempts} wrong passwords for account {username}, then an admin role grant",
        f"test action at {format_timestamp(started)}",
        f"{len(alerts)} alert(s) delivered:",
        *[alert.render() for alert in alerts],
    ]
    collector.store.write(
        ALERT_FILE, "\n".join(lines) + "\n", "C3", collector.clock.now(), collector.run_by, collector.source
    )
    return alerts


def run_restore_test(collector: Collector, runner: BackupRunner, table: str = "notes") -> RestoreResult:
    """C4: back up, restore into a scratch database, count the rows, and time the restore."""
    backup_taken_at = runner.backup()
    started = collector.clock.now()
    source_rows, restored_rows = runner.restore_and_count(table)
    result = RestoreResult(backup_taken_at, started, collector.clock.now(), table, source_rows, restored_rows)
    collector.store.write(
        RESTORE_FILE, render_restore(result), "C4", result.finished_at, collector.run_by, collector.source
    )
    return result


def collect_scan(collector: Collector, scanner: ScanRunner) -> str:
    """C5: run the dependency scan and keep the report; return its verdict."""
    report = scanner.scan()
    collector.store.write(SCAN_FILE, report.to_json(), "C5", report.scanned_at, collector.run_by, collector.source)
    return report.verdict


@dataclass(frozen=True)
class ReviewOutcome:
    """The access review: the problems with the reviewer's answers, or the lists before and after."""

    findings: tuple[Finding, ...]
    before: AccessList | None
    after: AccessList | None


def review_access(
    collector: Collector,
    repository: RepositoryAccess,
    database: DatabaseAccess,
    cloud: CloudDirectory,
    catalog: ControlCatalog,
) -> ReviewOutcome:
    """C6: take the C1 list, check every access was decided, remove what was refused, prove it by running C1 again."""
    before = collect_access(collector, repository, database, cloud)
    request: ReviewRequest = catalog.review_request()
    problems = check_review(before, request, catalog.people())
    if problems:
        return ReviewOutcome(tuple(problems), before, None)
    for decision in request.decisions:
        if not decision.keep:
            _remove(decision.system, decision.principal, cloud)
    after = collect_access(collector, repository, database, cloud)
    collector.store.write(
        REVIEW_FILE,
        render_review(before, after, request),
        "C6",
        collector.clock.now(),
        collector.run_by,
        collector.source,
    )
    return ReviewOutcome((), before, after)


def _remove(system: str, principal: str, cloud: CloudDirectory) -> None:
    if system.startswith("cloud"):
        cloud.remove_user(principal)
        return
    raise NotImplementedError(f"removal from {system} is done by its owner; this build removes cloud users")


def build_index(collector: Collector, catalog: ControlCatalog, framework_markdown: str) -> str:
    """INDEX.md: one line per artifact (file, control, what it proves, who ran it, date), the exceptions, the gaps."""
    manifest = collector.store.manifest()
    controls, exceptions, gaps = catalog.controls(), catalog.exceptions(), catalog.gaps()
    lines = [
        "# Evidence pack index",
        "",
        f"Pack date: {format_timestamp(collector.clock.now())}. Each file below was produced by a command in this"
        " repository (`make evidence`); `manifest.json` records its hash, so a hand edit fails `make verify`.",
        "",
        "| File | Control | Proves | Run by | Date | Period | Refreshed |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for control in controls:
        for spec in control.evidence:
            entry = manifest.get(spec.file)
            ran = f"{entry.run_by} | {entry.produced_at.date().isoformat()}" if entry else "not produced | -"
            lines.append(
                f"| {spec.file} | {control.id} {control.name} | {spec.proves} | {ran} "
                f"| {spec.period} | {spec.refreshed} |"
            )
    lines += ["", "## Exceptions", ""]
    lines += [
        f"- {item.id} ({item.control}): {item.description} Follow-up: {item.followup.rstrip('.')}." for item in exceptions
    ] or ["None."]
    lines += ["", "## Tracked gaps", ""]
    lines += [f"- {gap.control}: {gap.reason} Ticket {gap.ticket}, due {gap.due}." for gap in gaps] or ["None."]
    lines += ["", "## Framework mapping", "", framework_markdown, ""]
    text = "\n".join(lines)
    collector.store.write("INDEX.md", text, "-", collector.clock.now(), collector.run_by, collector.source)
    return text


def verify(
    store: EvidenceStore, controls: list[Control], exceptions: list[RecordedException], gaps: list[Gap], today: date
) -> Report:
    """Every control maps to evidence, every file exists and says what it should, nothing was edited by hand."""
    files = store.read_all()
    manifest = store.manifest()
    findings = verify_pack(controls, manifest, files, exceptions, gaps, today)
    if "INDEX.md" not in files:
        findings.append(error("EVD002", "INDEX.md", "the index is missing: run `make evidence`"))
    subjects = tuple(sorted(files))
    return Report(subjects, tuple(findings))
