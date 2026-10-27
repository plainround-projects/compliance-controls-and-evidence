"""Verify the evidence pack: every control maps to evidence, and every file exists, says what it should, is unedited."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime

from notes_evidence.domain.access import SYSTEMS, parse_access_list
from notes_evidence.domain.changes import HEADER, exceptions_in_csv
from notes_evidence.domain.controls import Control, EvidenceSpec, Gap, RecordedException, overlap
from notes_evidence.domain.findings import Finding, error, warning

LOG_LINE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z user=\S+ id=\S+ action=[a-z_]+ note=\S+ outcome=[a-z]+( \w+=\S+)*$"
)
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
SUPPORT_FILES = frozenset({"INDEX.md", "manifest.json"})
MIN_LOG_LINES = 5


@dataclass(frozen=True)
class ManifestEntry:
    """What a collector recorded about the file it wrote."""

    file: str
    control: str
    produced_at: datetime
    run_by: str
    source: str
    sha256: str


def digest(text: str) -> str:
    """The SHA-256 of a file's text, as the manifest records it."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_pack(
    controls: list[Control],
    manifest: Mapping[str, ManifestEntry],
    files: Mapping[str, str],
    exceptions: list[RecordedException],
    gaps: list[Gap],
    today: date,
) -> list[Finding]:
    """EVD001 to EVD009. `files` holds the text of every file in the evidence folder."""
    found: list[Finding] = []
    gap_controls = {gap.control for gap in gaps}
    mapped: set[str] = set()
    for control in controls:
        if not control.evidence:
            if control.id not in gap_controls:
                found.append(error("EVD001", control.id, "the control has no evidence and no tracked gap"))
            continue
        if control.id in gap_controls:
            found.append(error("EVD008", control.id, "listed as a gap but it has evidence: close the gap record"))
        for spec in control.evidence:
            mapped.add(spec.file)
            found.extend(_check_file(control, spec, manifest, files, exceptions, today))
        if len(control.references.get("iso27001", ())) + len(control.references.get("soc2", ())) < 2:
            found.append(error("EVD009", control.id, "the control maps to fewer than two framework references"))
    for gap in gaps:
        if not gap.reason.strip() or not gap.ticket.strip() or gap.due is None:
            found.append(error("EVD008", gap.control, "a tracked gap needs a reason, a ticket and a due date"))
        if gap.control not in {control.id for control in controls}:
            found.append(error("EVD008", gap.control, "the gap names a control that does not exist"))
    for path in sorted(set(files) - mapped - SUPPORT_FILES):
        found.append(error("EVD004", path, "an evidence file that no control claims"))
    found.extend(_cross_checks(controls, files))
    return found


def _check_file(
    control: Control,
    spec: EvidenceSpec,
    manifest: Mapping[str, ManifestEntry],
    files: Mapping[str, str],
    exceptions: list[RecordedException],
    today: date,
) -> list[Finding]:
    subject = f"{control.id} {spec.file}"
    text = files.get(spec.file)
    if text is None or not text.strip():
        return [
            error("EVD002", subject, "the evidence file is missing or empty: an empty file is worse than a missing one")
        ]
    found: list[Finding] = []
    entry = manifest.get(spec.file)
    if entry is None:
        found.append(error("EVD003", subject, "no manifest entry: nobody recorded who produced it or when"))
    else:
        if entry.sha256 != digest(text):
            found.append(
                error("EVD003", subject, "the file differs from the hash its collector recorded: it was edited by hand")
            )
        if entry.control != control.id:
            found.append(error("EVD003", subject, f"the manifest says it belongs to {entry.control}"))
        age = (today - entry.produced_at.date()).days
        if age > spec.refresh_days:
            found.append(
                warning("EVD005", subject, f"produced {age} days ago; the control refreshes every {spec.refresh_days}")
            )
    found.extend(_check_content(control, spec, text, exceptions))
    return found


def _check_content(
    control: Control, spec: EvidenceSpec, text: str, exceptions: list[RecordedException]
) -> list[Finding]:
    subject = f"{control.id} {spec.file}"
    if spec.kind == "changes":
        return [error(code, subject, message) for code, message in _changes(text, control.id, exceptions)]
    checks = {
        "access_list": _access_list,
        "log_sample": _log_sample,
        "alert_test": _alert_test,
        "restore": _restore,
        "scan": _scan,
        "review": _review,
    }
    return [error("EVD007", subject, problem) for problem in checks[spec.kind](text)]


def _access_list(text: str) -> list[str]:
    blocks = parse_access_list(text)
    problems = [f"no '## {system}' block" for system in SYSTEMS if system not in blocks]
    if not text.startswith("# access list, generated "):
        problems.append("no dated header")
    return problems


def _changes(text: str, control_id: str, exceptions: list[RecordedException]) -> list[tuple[str, str]]:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or tuple(rows[0]) != HEADER:
        return [("EVD007", f"the header must be {','.join(HEADER)}")]
    if len(rows) < 2:
        return [("EVD007", "no changes listed")]
    listed = {item.change for item in exceptions if item.control == control_id and item.followup.strip()}
    return [
        ("EVD006", f"change {item.number} ({item.reason}) is not listed in controls/exceptions.toml with a follow-up")
        for item in exceptions_in_csv(text)
        if item.number not in listed
    ]


def _log_sample(text: str) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    bad = [line for line in lines if not LOG_LINE.match(line)]
    problems = [f"not a log line: {line[:60]!r}" for line in bad[:3]]
    if len(lines) < MIN_LOG_LINES:
        problems.append(f"{len(lines)} lines; a sample needs at least {MIN_LOG_LINES}")
    return problems


def _alert_test(text: str) -> list[str]:
    problems: list[str] = []
    action = re.search(r"test action at (" + TIMESTAMP.pattern + ")", text)
    alert = re.search(r"ALERT \[[a-z-]+\] (" + TIMESTAMP.pattern + ")", text)
    if action is None:
        problems.append("no 'test action at <timestamp>' line")
    if alert is None:
        problems.append("no alert message with its timestamp: the alert did not fire")
    if action and alert and alert.group(1) < action.group(1):
        problems.append("the alert is dated before the test action")
    return problems


def _restore(text: str) -> list[str]:
    problems = []
    if "restore started " not in text or "restore finished " not in text:
        problems.append("no start and finish lines")
    if "result: verified" not in text:
        problems.append("the restore was not verified by row counts")
    return problems


def _scan(text: str) -> list[str]:
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        return ["not JSON"]
    problems = []
    if not document.get("run_id"):
        problems.append("no run id: a scan report must name the CI run that produced it")
    if document.get("verdict") not in ("pass", "fail"):
        problems.append("no verdict")
    if document.get("verdict") == "fail":
        problems.append("the scan failed the blocking rule: the build would not have shipped")
    return problems


def _review(text: str) -> list[str]:
    problems = [
        f"no '{label}' line" for label in ("Reviewer:", "Before:", "Removed:", "After:", "Proof:") if label not in text
    ]
    if "Removed: nothing" in text:
        problems.append("the review removed nothing: a review that finds nothing raises questions")
    if "still listed" in text:
        problems.append("a removed principal is still listed after the review")
    return problems


def _cross_checks(controls: list[Control], files: Mapping[str, str]) -> list[Finding]:
    """The review's removed principals must be absent from the current access list."""
    review_files = [spec.file for control in controls for spec in control.evidence if spec.kind == "review"]
    access_files = [spec.file for control in controls for spec in control.evidence if spec.kind == "access_list"]
    found: list[Finding] = []
    for review_file in review_files:
        review = files.get(review_file, "")
        removed = re.findall(r"^Removed: (.+)\.$", review, re.MULTILINE)
        names = (
            {part.strip().split(" ")[-1] for part in removed[0].split(",")}
            if removed and removed[0] != "nothing"
            else set()
        )
        for access_file in access_files:
            present = {
                principal for block in parse_access_list(files.get(access_file, "")).values() for principal in block
            }
            for name in sorted(names & present):
                found.append(
                    error("EVD007", review_file, f"{name} was removed by the review but is still in {access_file}")
                )
    return found


def framework_table(controls: list[Control]) -> str:
    """The overlap of the controls across the two frameworks, as Markdown."""
    lines = ["| Framework | Reference | Controls |", "| --- | --- | --- |"]
    for framework, refs in overlap(controls).items():
        for ref, ids in refs.items():
            lines.append(f"| {framework} | {ref} | {', '.join(ids)}{' (overlap)' if len(ids) > 1 else ''} |")
    return "\n".join(lines)
