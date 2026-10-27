"""C2: every merged change with its approver and the deployment that shipped it."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.audit import format_timestamp

HEADER = ("number", "author", "merged_at", "commit", "approvers", "deploy_id")


@dataclass(frozen=True)
class MergedChange:
    """One merged pull request, as the hosting platform reports it."""

    number: int
    author: str
    merged_at: datetime
    commit: str
    approvers: tuple[str, ...]
    deploy_id: str


@dataclass(frozen=True)
class ChangeException:
    """A change that broke the rule: no approver, only a self-approval, or no deployment record."""

    number: int
    reason: str


def independent_approvers(change: MergedChange) -> tuple[str, ...]:
    """Approvers other than the author: a change approved only by its author was not reviewed."""
    return tuple(name for name in change.approvers if name != change.author)


def find_exceptions(changes: list[MergedChange]) -> list[ChangeException]:
    """Changes with no independent approver, or with no deployment id."""
    found: list[ChangeException] = []
    for change in changes:
        if not independent_approvers(change):
            found.append(ChangeException(change.number, "merged with no independent approver"))
        if not change.deploy_id:
            found.append(ChangeException(change.number, "no deployment record"))
    return found


def render_changes(changes: list[MergedChange]) -> str:
    """The artifact as CSV: strings quoted, the number bare, approvers joined with '+'."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")
    writer.writerow(HEADER)
    for change in sorted(changes, key=lambda item: item.number):
        writer.writerow(
            [
                change.number,
                change.author,
                format_timestamp(change.merged_at),
                change.commit[:7],
                "+".join(change.approvers),
                change.deploy_id,
            ]
        )
    return buffer.getvalue()


def exceptions_in_csv(text: str) -> list[ChangeException]:
    """Re-derive the exceptions from a rendered artifact, so the check does not trust the collector."""
    rows = list(csv.DictReader(io.StringIO(text)))
    found: list[ChangeException] = []
    for row in rows:
        approvers = [name for name in row["approvers"].split("+") if name and name != row["author"]]
        if not approvers:
            found.append(ChangeException(int(row["number"]), "merged with no independent approver"))
        if not row["deploy_id"]:
            found.append(ChangeException(int(row["number"]), "no deployment record"))
    return found
