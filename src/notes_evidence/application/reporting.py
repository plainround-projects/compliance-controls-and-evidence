"""Format the verification as text for the terminal and as Markdown for the build artifact."""

from __future__ import annotations

from collections.abc import Mapping

from notes_evidence.domain.controls import Control
from notes_evidence.domain.evidence import ManifestEntry, framework_table
from notes_evidence.domain.findings import Report


def render_text(report: Report) -> str:
    """One line per finding, then the verdict."""
    lines = [
        f"{finding.severity.value.upper():7} {finding.code} {finding.subject}: {finding.message}"
        for finding in report.findings
    ]
    counts = f"{len(report.subjects)} files checked, {len(report.errors)} errors, {len(report.warnings)} warnings"
    lines.append(f"{'OK' if report.ok else 'FAILED'}: {counts}")
    return "\n".join(lines)


def render_report(report: Report, controls: list[Control], manifest: Mapping[str, ManifestEntry]) -> str:
    """The control-to-evidence report: one row per control and file, the findings, the framework overlap."""
    verdict = "OK" if report.ok else "FAILED"
    lines = [
        "# Evidence report",
        "",
        f"**Verdict:** {verdict} ({len(report.errors)} errors, {len(report.warnings)} warnings)",
        "",
        "## Controls and their evidence",
        "",
        "| Control | Evidence file | Produced | Run by | Hash recorded |",
        "| --- | --- | --- | --- | --- |",
    ]
    for control in controls:
        if not control.evidence:
            lines.append(f"| {control.id} {control.name} | none | - | - | - |")
        for spec in control.evidence:
            entry = manifest.get(spec.file)
            if entry is None:
                lines.append(f"| {control.id} {control.name} | {spec.file} | missing | - | - |")
            else:
                produced = entry.produced_at.strftime("%Y-%m-%d")
                lines.append(
                    f"| {control.id} {control.name} | {spec.file} | {produced} | {entry.run_by} | {entry.sha256[:12]} |"
                )
    lines += ["", "## Findings", ""]
    if report.findings:
        lines += ["| Severity | Code | Subject | Message |", "| --- | --- | --- | --- |"]
        lines += [f"| {f.severity.value} | {f.code} | `{f.subject}` | {f.message} |" for f in report.findings]
    else:
        lines.append("None.")
    lines += ["", "## Framework mapping", "", framework_table(controls), ""]
    return "\n".join(lines)
