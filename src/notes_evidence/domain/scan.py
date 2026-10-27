"""C5: the dependency scan, as a report a build produced and a rule that decides whether it blocks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.audit import format_timestamp

BLOCKING_RULE = "any known vulnerability with a fixed version available fails the build"


@dataclass(frozen=True)
class ScanFinding:
    """A vulnerable package version and the versions that fix it."""

    package: str
    version: str
    vulnerability: str
    fix_versions: tuple[str, ...]

    @property
    def blocking(self) -> bool:
        """True when a fix exists: the rule says upgrade, not accept."""
        return bool(self.fix_versions)


@dataclass(frozen=True)
class ScanReport:
    """One scan run: who ran it, on what, when, and what it found."""

    run_id: str
    tool: str
    tool_version: str
    scanned_at: datetime
    target: str
    packages_scanned: int
    findings: tuple[ScanFinding, ...]

    @property
    def verdict(self) -> str:
        """pass or fail under the blocking rule."""
        return "fail" if any(finding.blocking for finding in self.findings) else "pass"

    def to_json(self) -> str:
        """The artifact: stable keys, sorted findings."""
        document = {
            "run_id": self.run_id,
            "tool": self.tool,
            "tool_version": self.tool_version,
            "scanned_at": format_timestamp(self.scanned_at),
            "target": self.target,
            "packages_scanned": self.packages_scanned,
            "blocking_rule": BLOCKING_RULE,
            "verdict": self.verdict,
            "findings": [
                {
                    "package": f.package,
                    "version": f.version,
                    "vulnerability": f.vulnerability,
                    "fix_versions": list(f.fix_versions),
                }
                for f in sorted(self.findings, key=lambda item: (item.package, item.vulnerability))
            ],
        }
        return json.dumps(document, indent=2) + "\n"


def parse_pip_audit(raw: str) -> tuple[int, tuple[ScanFinding, ...]]:
    """Packages scanned and findings from `pip-audit -f json` output."""
    data = json.loads(raw)
    dependencies = data["dependencies"] if isinstance(data, dict) else data
    findings = tuple(
        ScanFinding(dep["name"], dep.get("version", ""), vuln["id"], tuple(vuln.get("fix_versions", [])))
        for dep in dependencies
        for vuln in dep.get("vulns", [])
    )
    return len(dependencies), findings
