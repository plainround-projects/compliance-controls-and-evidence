"""C6: the access review. Every principal gets a decision, leavers go, and the record shows before and after."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from notes_evidence.domain.access import AccessList
from notes_evidence.domain.findings import Finding, error


@dataclass(frozen=True)
class Person:
    """Someone who may hold access. `left_on` is set for a leaver."""

    name: str
    title: str
    left_on: date | None = None


@dataclass(frozen=True)
class Decision:
    """The reviewer's answer for one principal in one system."""

    system: str
    principal: str
    keep: bool
    reason: str


@dataclass(frozen=True)
class ReviewRequest:
    """The review as the reviewer filed it."""

    reviewer: str
    reviewed_on: date
    ticket: str
    decisions: tuple[Decision, ...]


def check_review(before: AccessList, request: ReviewRequest, people: dict[str, Person]) -> list[Finding]:
    """ARV001 to ARV003: complete, justified, and no leaver kept."""
    found: list[Finding] = []
    decided = {(d.system, d.principal): d for d in request.decisions}
    for entry in before.entries:
        decision = decided.get((entry.system, entry.principal))
        if decision is None:
            found.append(
                error(
                    "ARV001",
                    f"{entry.system}: {entry.principal}",
                    "no decision: an access review decides every principal",
                )
            )
            continue
        if not decision.reason.strip():
            found.append(error("ARV002", f"{entry.system}: {entry.principal}", "a decision needs its reason"))
        person = people.get(entry.principal)
        if person is not None and person.left_on is not None and decision.keep:
            found.append(error("ARV003", f"{entry.system}: {entry.principal}", f"left on {person.left_on}, yet kept"))
    if not request.ticket.strip():
        found.append(error("ARV002", "review", "the review needs a ticket the removals are recorded in"))
    return found


def render_review(before: AccessList, after: AccessList, request: ReviewRequest) -> str:
    """The artifact: reviewer, date, before counts, what was removed and why, and the re-run proof."""
    removed = [d for d in request.decisions if not d.keep]
    names = ", ".join(f"{d.system.split(' (')[0]} {d.principal}" for d in removed) or "nothing"
    reasons = "\n".join(f"  - {d.principal} ({d.system.split(' (')[0]}): {d.reason}" for d in removed)
    before_counts = ", ".join(f"{count} {system.split(' (')[0]}" for system, count in before.counts().items())
    after_counts = ", ".join(f"{count} {system.split(' (')[0]}" for system, count in after.counts().items())
    still = [
        d.principal for d in removed if any(e.principal == d.principal and e.system == d.system for e in after.entries)
    ]
    proof = "re-ran the C1 command; " + (
        ", ".join(still) + " is still listed" if still else "none of the removed principals is listed"
    )
    lines = [
        f"Reviewer: {request.reviewer}. Date: {request.reviewed_on.isoformat()}. Ticket: {request.ticket}.",
        f"Before: {before_counts}.",
        f"Removed: {names}.",
    ]
    if reasons:
        lines.append(reasons)
    lines += [f"After: {after_counts}.", f"Proof: {proof}."]
    return "\n".join(lines) + "\n"
