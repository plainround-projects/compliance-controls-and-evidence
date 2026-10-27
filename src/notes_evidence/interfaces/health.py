"""`notes-api-health`: the container's health check. Exit 0 when /healthz answers 200."""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    """Ask the local API if it is healthy."""
    port = os.environ.get("HTTP_PORT", "8080")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=3) as response:
            return 0 if response.status == 200 else 1
    except (urllib.error.URLError, OSError):
        print("unhealthy", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
