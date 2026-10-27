"""C5: run pip-audit over the locked dependencies and wrap its JSON with the run that produced it."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import datetime
from importlib import metadata

from notes_evidence.domain.scan import ScanReport, parse_pip_audit

Run = Callable[[list[str]], str]


class ScanError(RuntimeError):
    """pip-audit produced no usable report."""


def run_pip_audit(argv: list[str]) -> str:
    """Run pip-audit; exit code 1 means it found vulnerabilities and still prints the report."""
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as problem:
        raise ScanError(f"pip-audit: {problem}") from None
    if done.returncode not in (0, 1) or not done.stdout.strip():
        raise ScanError(f"pip-audit exited {done.returncode}: {done.stderr.strip()[-300:]}")
    return done.stdout


class PipAuditScanner:
    """Scan one lock file. The run id is the CI run when there is one, else a local stamp."""

    def __init__(
        self, lock_file: str, env: Mapping[str, str], now: Callable[[], datetime], run: Run = run_pip_audit
    ) -> None:
        self._lock = lock_file
        self._env = env
        self._now = now
        self._run = run

    def scan(self) -> ScanReport:
        """Run the scan."""
        started = self._now()
        raw = self._run(
            [sys.executable, "-m", "pip_audit", "-f", "json", "--no-deps", "--disable-pip", "-r", self._lock]
        )
        count, findings = parse_pip_audit(raw)
        run_id = self._env.get("GITHUB_RUN_ID") or f"local-{started.strftime('%Y%m%dT%H%M%SZ')}"
        return ScanReport(run_id, "pip-audit", metadata.version("pip-audit"), started, self._lock, count, findings)
