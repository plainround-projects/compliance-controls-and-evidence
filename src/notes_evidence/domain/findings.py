"""The result of a rule: a finding with a code, a severity and the document it is about."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """ERROR fails the check; WARNING is reported and does not."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    """One rule violation. The code names the rule so a test and a reader can point at it."""

    code: str
    severity: Severity
    subject: str
    message: str


def error(code: str, subject: str, message: str) -> Finding:
    """Build an ERROR finding."""
    return Finding(code, Severity.ERROR, subject, message)


@dataclass(frozen=True)
class Report:
    """Every finding from one run, plus the subjects that were checked."""

    subjects: tuple[str, ...]
    findings: tuple[Finding, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        """The findings that fail the check."""
        return tuple(f for f in self.findings if f.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        """The findings that are reported without failing the check."""
        return tuple(f for f in self.findings if f.severity is Severity.WARNING)

    @property
    def ok(self) -> bool:
        """True when no finding is an error."""
        return not self.errors


def warning(code: str, subject: str, message: str) -> Finding:
    """Build a WARNING finding."""
    return Finding(code, Severity.WARNING, subject, message)
