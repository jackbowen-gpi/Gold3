#!/usr/bin/env python3
"""Simple smoke test for workflow search UI and autocomplete endpoints."""

import time
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
ENDPOINTS = [
    ("root", "/"),
    ("job_search_legacy", "/workflow/job/search/"),
    ("job_search_modern", "/workflow/job/search/?legacy=0"),
    ("item_search_legacy", "/workflow/item/search/"),
    ("item_search_modern", "/workflow/item/search/?legacy=0"),
    ("job_autocomplete", "/workflow/api/job_autocomplete/?term=12"),
    ("item_autocomplete", "/workflow/api/item_autocomplete/?term=12"),
]


def fetch(path, timeout=10):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "smoke-test"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="ignore")
            return r.getcode(), body
    except urllib.error.HTTPError as e:
        return e.code, getattr(e, "reason", str(e))
    except Exception as e:
        return None, str(e)


def wait_for_server(timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        code, _ = fetch("/")
        if code == 200:
            return True
        time.sleep(0.5)
    return False


def main():
    print("Waiting for server to respond on http://127.0.0.1:8000 ...")
    if not wait_for_server(30):
        print("Server did not respond in time.")
        return 2

    ok = True
    for name, path in ENDPOINTS:
        code, body = fetch(path)
        print(f"{name}: status={code}")
        if code != 200:
            print(f"  ERROR: {name} returned {code} / {body}")
            ok = False
            continue
        # Basic content checks for templates
        if name.endswith("modern") or name.endswith("legacy"):
            if "Legacy Search Interface" in body:
                print("  contains: Legacy Search Interface")
            elif "Universal Search" in body or "Search All Fields" in body:
                print("  contains: Modern search UI markers")
            else:
                print("  WARNING: search page did not contain expected markers")
        if name.endswith("autocomplete"):
            if body.strip().startswith("["):
                print("  autocomplete returned JSON array")
            else:
                print("  WARNING: autocomplete did not return JSON array")

    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
