# SHA-256, HMAC, scrypt, secrets and base64

## What it is

A **hash** (SHA-256) turns any text into a fixed 64-character fingerprint; the same input always gives the same fingerprint and
you cannot go back. An **HMAC** mixes a secret key into the hash, so only the key's holder can produce it. A **password hash**
such as **scrypt** is deliberately slow and uses a random **salt**, so guessing passwords is expensive and two equal passwords
give different hashes. `secrets` gives random bytes safe for security; `base64` writes bytes as text.

## Why this repository uses it

Three controls depend on it. **Evidence integrity:** the manifest holds a SHA-256 of each file, so an edited file is noticed.
**Authentication:** session tokens are HMAC-signed and expire. **Password storage:** the database never holds a password, only a
scrypt hash.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/domain/evidence.py` | `digest(text)`: the SHA-256 of an evidence file. |
| `src/notes_evidence/infrastructure/evidence_store.py` | Records the digest in the manifest. |
| `src/notes_evidence/infrastructure/tokens.py` | `HmacTokens`: issue and verify session tokens. |
| `src/notes_evidence/infrastructure/passwords.py` | `ScryptHasher`: hash and verify passwords. |

## How it works underneath

`hashlib.sha256(data).hexdigest()` computes the fingerprint. `hmac.new(key, message, hashlib.sha256)` computes the keyed version.
To verify a token the server recomputes the signature and compares; `hmac.compare_digest` compares in constant time, so timing
leaks nothing. `hashlib.scrypt(password, salt=..., n=2**14, r=8, p=1, dklen=32)` makes a 32-byte key from a password; `n`, `r` and
`p` set how much memory and time it takes, which is what makes guessing slow.

## Walkthrough of this repository's use

`src/notes_evidence/domain/evidence.py`:

```python
def digest(text: str) -> str:
    """The SHA-256 of a file's text, as the manifest records it."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
```

The SHA-256 of the file's text (as UTF-8 bytes). The verifier calls it again on each file and compares with the manifest.

`src/notes_evidence/infrastructure/tokens.py`:

```python
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
```

- A token is `user_id.expires.signature`. `int((now + self._ttl).timestamp())` is the expiry in seconds since 1970.
- `verify` splits on dots, insists on three parts with digits in the first two, and compares signatures with
  `hmac.compare_digest`. It returns the user id only if the token is genuine **and** `int(parts[1]) > now.timestamp()` (not
  expired). Anything else returns `None`: the same answer for every kind of failure.

`src/notes_evidence/infrastructure/passwords.py`:

```python
_N, _R, _P = 2**14, 8, 1
_SCHEME = "scrypt"
```

`src/notes_evidence/infrastructure/passwords.py`:

```python
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
```

- `_N, _R, _P = 2**14, 8, 1` are the scrypt cost settings (`2**14` is 16,384). They are fixed, so a stored hash can always be
  verified.
- `secrets.token_bytes(16)` makes a fresh 16-byte salt for each password.
- The stored text is `scrypt$<salt>$<hash>`, with the salt and the hash in base64.
- `verify` returns `False` for a malformed or unusable value (the seed's `!` never matches).

`src/notes_evidence/infrastructure/passwords.py`:

```python
    def _derive(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
```

`hashlib.scrypt(...)` is in the standard library (it needs OpenSSL 1.1 or newer, which Python 3.12 builds have).

## Try it yourself

```bash
.venv/bin/python -c "import hashlib; print(hashlib.sha256(open('evidence/C1-access-list.txt','rb').read()).hexdigest())"
```
Prints 64 hex characters; it equals the `sha256` of `C1-access-list.txt` in `evidence/manifest.json` (`ba099eb7...` in the committed pack).

```bash
.venv/bin/python - <<'EOF'
from datetime import UTC, datetime, timedelta
from notes_evidence.domain.notes import User
from notes_evidence.domain.roles import Role
from notes_evidence.infrastructure.tokens import HmacTokens
tokens = HmacTokens("x" * 32, timedelta(minutes=15))
now = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)
token = tokens.issue(User(7, "ada", Role.ADMIN, True), now)
print(token.rsplit(".", 1)[0], tokens.verify(token, now), tokens.verify(token, now + timedelta(hours=1)), tokens.verify(token + "0", now))
EOF
```
Prints `7.1793092500 7 None None`: valid now, expired an hour later, rejected when the signature is changed.

```bash
.venv/bin/python - <<'EOF'
from notes_evidence.infrastructure.passwords import ScryptHasher
h = ScryptHasher()
a, b = h.hash("correct horse"), h.hash("correct horse")
print(a.split("$")[0], a != b, h.verify("correct horse", a), h.verify("wrong", a), h.verify("x", "!"))
EOF
```
Prints `scrypt True True False False`: the same password gives different stored values (different salts), and only the right one verifies.

```bash
.venv/bin/python -c "import secrets; print(len(secrets.token_bytes(16)))"
```
Prints `16`.

## Mistakes people make

- **Storing passwords in plain text or with a fast hash** (SHA-256 alone). Use a slow, salted hash.
- **One shared salt**, or none. Each password gets its own random salt.
- **Comparing secrets with `==`.** Use `hmac.compare_digest`.
- **Changing the scrypt settings** without a plan: old hashes would no longer verify.
- **A short signing secret.** The settings loader refuses a `NOTES_SECRET` under 32 characters.

## Check yourself

1. Why is the manifest hash useful as evidence?
   **Answer:** An edited file no longer matches its recorded SHA-256, so tampering is caught.
2. What is a salt for?
   **Answer:** It makes equal passwords hash differently and defeats pre-computed tables.
3. Why is scrypt slow on purpose?
   **Answer:** Slow hashing makes guessing passwords expensive.
4. What does `hmac.compare_digest` avoid?
   **Answer:** Timing differences that could reveal how much of a secret matched.
5. What does `verify` return for an expired token?
   **Answer:** `None`.

## Further reading

- `hashlib` (Python 3.12): <https://docs.python.org/3.12/library/hashlib.html>; `hmac`: <https://docs.python.org/3.12/library/hmac.html>; `secrets`: <https://docs.python.org/3.12/library/secrets.html>
- scrypt (RFC 7914): <https://www.rfc-editor.org/rfc/rfc7914>; HMAC (RFC 2104): <https://www.rfc-editor.org/rfc/rfc2104>
