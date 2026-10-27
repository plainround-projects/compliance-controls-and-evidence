"""The control matrix: each control, the frameworks it answers to, and the evidence that proves it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

KINDS = ("access_list", "changes", "log_sample", "alert_test", "restore", "scan", "review")
FRAMEWORKS = ("iso27001", "soc2")


@dataclass(frozen=True)
class EvidenceSpec:
    """One artifact a control is shown by."""

    file: str
    kind: str
    proves: str
    period: str
    refresh_days: int
    refreshed: str


@dataclass(frozen=True)
class Control:
    """A control: what it requires, where it lives, the framework references it satisfies, its evidence."""

    id: str
    name: str
    requires: str
    where: str
    references: dict[str, tuple[str, ...]]
    evidence: tuple[EvidenceSpec, ...]


@dataclass(frozen=True)
class RecordedException:
    """A known deviation, with how it was handled. Hiding exceptions is the mistake the lesson names."""

    id: str
    control: str
    change: int | None
    description: str
    followup: str


@dataclass(frozen=True)
class Gap:
    """A control with no evidence yet, tracked on purpose."""

    control: str
    reason: str
    ticket: str
    due: date | None


def overlap(controls: list[Control]) -> dict[str, dict[str, list[str]]]:
    """For each framework, each reference and its controls. A reference with two controls is an overlap."""
    table: dict[str, dict[str, list[str]]] = {name: {} for name in FRAMEWORKS}
    for control in controls:
        for framework, refs in control.references.items():
            for ref in refs:
                table.setdefault(framework, {}).setdefault(ref, []).append(control.id)
    return {framework: dict(sorted(refs.items())) for framework, refs in table.items()}
