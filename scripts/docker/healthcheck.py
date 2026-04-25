#!/usr/bin/env python3
"""Container health check for honeypot-med."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import URLError
from urllib.request import urlopen


def main() -> int:
    url = os.getenv("HONEYPOT_MED_HEALTHCHECK_URL", "http://127.0.0.1:8899/health")
    try:
        with urlopen(url, timeout=3) as response:  # noqa: S310
            if response.status != 200:
                return 1
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return 1

    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())

