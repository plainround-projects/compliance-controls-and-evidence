"""Signed, expiring session tokens: `user_id.expires.signature`, HMAC-SHA256 over the first two parts."""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta

from notes_evidence.domain.notes import User


class HmacTokens:
    """Issue and verify tokens with a secret that comes from the environment."""

    def __init__(self, secret: str, ttl: timedelta) -> None:
        self._key = secret.encode()
        self._ttl = ttl

    def issue(self, user: User, now: datetime) -> str:
        """A token for the user that expires after the configured time."""
        body = f"{user.id}.{int((now + self._ttl).timestamp())}"
        return f"{body}.{self._sign(body)}"

    def verify(self, token: str, now: datetime) -> int | None:
        """The user id in a genuine, unexpired token; None for anything else."""
        parts = token.split(".")
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            return None
        if not hmac.compare_digest(parts[2], self._sign(f"{parts[0]}.{parts[1]}")):
            return None
        return int(parts[0]) if int(parts[1]) > now.timestamp() else None

    def _sign(self, body: str) -> str:
        return hmac.new(self._key, body.encode(), hashlib.sha256).hexdigest()
