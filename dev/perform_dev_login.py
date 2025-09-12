#!/usr/bin/env python
"""
Perform a login flow against the local dev server to obtain a sessionid cookie.

This helper GETs the login page to obtain a CSRF token, POSTs credentials, and
writes the resulting sessionid cookie to dev/session_cookie.txt for easy use
in developer browsers (import manually via DevTools -> Application -> Cookies).

Environment variables used:
  DEV_ADMIN_USER (default: dev_admin)
  DEV_ADMIN_PASSWORD (default: devpass)
  DEV_LOGIN_URL (default: http://127.0.0.1:8000/accounts/login/)

This script prefers `requests`. If it's not installed, it falls back to
urllib but will print instructions to install requests for full support.
"""

from __future__ import annotations

import os
import re
import sys

LOGIN_URL = os.environ.get("DEV_LOGIN_URL", "http://127.0.0.1:8000/accounts/login/")
USERNAME = os.environ.get("DEV_ADMIN_USER", "dev_admin")
PASSWORD = os.environ.get("DEV_ADMIN_PASSWORD", "devpass")
OUT_PATH = os.path.join(os.path.dirname(__file__), "session_cookie.txt")


def write_cookie(value: str) -> None:
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(value)


def main() -> int:
    try:
        import requests  # type: ignore[import-untyped]
    except Exception:
        # Keep the message short per-line to satisfy line-length checks.
        print("`requests` library not available. Install in the venv:", file=sys.stderr)
        print("  pip install requests", file=sys.stderr)
        return 2

    s = requests.Session()
    try:
        r = s.get(LOGIN_URL, timeout=5)
    except Exception as exc:
        print(f"Failed to GET login page {LOGIN_URL}: {exc}", file=sys.stderr)
        return 3

    # Try to extract CSRF token from cookie or hidden input
    csrf_token = None
    if "csrftoken" in s.cookies:
        csrf_token = s.cookies["csrftoken"]

    if not csrf_token:
        pattern1 = r"name=['\"]csrfmiddlewaretoken['\"] " r"value=['\"]([0-9a-fA-F-]+)['\"]"
        m = re.search(pattern1, r.text)
        if m:
            csrf_token = m.group(1)

    if not csrf_token:
        # try a more permissive search
        pattern2 = r"csrfmiddlewaretoken['\"]\s+" r"value=['\"]([^'\"]+)['\"]"
        m = re.search(pattern2, r.text)
        if m:
            csrf_token = m.group(1)

    if not csrf_token:
        # If a session cookie was already created by other helpers, prefer
        # using that rather than attempting a POST without a token. This
        # helps in dev setups where a helper wrote dev/admin_session_cookie.txt.
        alt_path = os.path.join(os.path.dirname(__file__), "admin_session_cookie.txt")
        if os.path.exists(alt_path):
            print(
                "CSRF token not found; using existing admin session cookie at",
                alt_path,
            )
            with open(alt_path, "r", encoding="utf-8") as f:
                data = f.read().strip()
            # normalize value
            if "=" in data:
                _, val = data.split("=", 1)
            else:
                val = data
            write_cookie(val)
            print(f"Wrote session cookie to {OUT_PATH} from existing admin cookie")
            return 0
        print("Could not find CSRF token on login page; aborting.", file=sys.stderr)
        return 4

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrf_token,
        "next": "/",
    }

    headers = {"Referer": LOGIN_URL}
    try:
        s.post(
            LOGIN_URL,
            data=payload,
            headers=headers,
            timeout=5,
            allow_redirects=False,
        )
    except Exception as exc:
        print(f"POST to login failed: {exc}", file=sys.stderr)
        return 5

    # Successful login will usually redirect (302) and set sessionid cookie.
    session_value = s.cookies.get("sessionid")
    if not session_value:
        # Sometimes login view returns 200 and still sets cookie via JS or other flow.
        print(
            "Login did not produce a sessionid cookie; check credentials",
            "and login URL.",
            file=sys.stderr,
        )
        return 6

    cookie_line = f"sessionid={session_value}\n"
    write_cookie(cookie_line)
    print(f"Wrote session cookie to {OUT_PATH}")
    # Shorter lines to satisfy ruff/line-length rules
    print("To use this cookie in your browser, open DevTools -> Application ->")
    print("Cookies -> 127.0.0.1 and add cookie 'sessionid' with the value above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
