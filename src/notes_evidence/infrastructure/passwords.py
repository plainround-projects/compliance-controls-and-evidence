"""Password hashing with scrypt from the standard library: salted, slow, compared in constant time."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_N, _R, _P = 2**14, 8, 1
_SCHEME = "scrypt"


class ScryptHasher:
    """`scrypt$<salt>$<hash>`, both base64. The cost parameters are fixed so a stored hash can always be verified."""

    def hash(self, password: str) -> str:
        """Hash a password with a fresh 16-byte salt."""
        salt = secrets.token_bytes(16)
        return f"{_SCHEME}${base64.b64encode(salt).decode()}${base64.b64encode(self._derive(password, salt)).decode()}"

    def verify(self, password: str, stored: str) -> bool:
        """True when the password matches. An unusable or malformed stored value never matches."""
        parts = stored.split("$")
        if len(parts) != 3 or parts[0] != _SCHEME:
            return False
        try:
            salt, expected = base64.b64decode(parts[1]), base64.b64decode(parts[2])
        except ValueError:
            return False
        return hmac.compare_digest(self._derive(password, salt), expected)

    @staticmethod
    def _derive(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
