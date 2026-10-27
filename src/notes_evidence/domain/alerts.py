"""Alert rules over the audit stream: the events that need a person."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from notes_evidence.domain.audit import AuditAction, AuditEvent, format_timestamp


@dataclass(frozen=True)
class Alert:
    """An alert message with the time of the event that triggered it."""

    rule: str
    subject: str
    at: datetime
    message: str

    def render(self) -> str:
        """One line a person can read in a chat channel."""
        return f"ALERT [{self.rule}] {format_timestamp(self.at)} {self.message}"


@dataclass(frozen=True)
class AlertRules:
    """Five failed logins for one account in two minutes, or an admin role granted."""

    failed_logins: int = 5
    window: timedelta = timedelta(minutes=2)


def detect_alerts(events: Iterable[AuditEvent], rules: AlertRules | None = None) -> list[Alert]:
    """Walk the events in time order and return the alerts they raise.

    A burst of failed logins raises one alert when the count reaches the threshold inside the window; that account's
    count then starts again, so a long attack raises an alert for each further burst and not for each attempt.
    """
    rules = rules or AlertRules()
    ordered: Sequence[AuditEvent] = sorted(events, key=lambda event: event.at)
    recent: dict[str, deque[datetime]] = defaultdict(deque)
    alerts: list[Alert] = []
    for event in ordered:
        if event.action is AuditAction.LOGIN_FAILED:
            window = recent[event.username]
            window.append(event.at)
            while window and event.at - window[0] > rules.window:
                window.popleft()
            if len(window) >= rules.failed_logins:
                minutes = int(rules.window.total_seconds() // 60)
                alerts.append(
                    Alert(
                        "failed-logins",
                        event.username,
                        event.at,
                        f"{len(window)} failed logins for account {event.username} within {minutes} minutes",
                    )
                )
                window.clear()
        elif event.action is AuditAction.ROLE_GRANTED and event.detail.get("role") == "admin":
            alerts.append(
                Alert(
                    "admin-granted",
                    event.username,
                    event.at,
                    f"admin role granted to {event.detail.get('target', '?')} by {event.username}",
                )
            )
    return alerts
