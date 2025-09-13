"""
Simple health check for the devserver used by CI.

Usage: run this from the project root with the virtualenv active.
Exits with non-zero code if any checked endpoint fails or returns non-200.
"""

import os
import sys


def add_project_root_to_path():
    # scripts/ is one level below the project root. Ensure the project root is
    # on sys.path so `import settings` works the same way manage.py does.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


if __name__ == "__main__":
    # Make sure Django settings are discoverable when run from repo root.
    add_project_root_to_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    import django

    django.setup()
    from django.test import Client

    client = Client()
    endpoints = ["/", "/acs/pdf_generation_form/"]
    host = os.environ.get("HEALTH_CHECK_HOST", "127.0.0.1")
    failures = []
    for ep in endpoints:
        # Follow redirects so endpoints that redirect to a login or landing
        # page still count as healthy for CI smoke tests.
        resp = client.get(ep, HTTP_HOST=host, follow=True)
        if resp.status_code < 200 or resp.status_code >= 400:
            failures.append((ep, resp.status_code))

    if failures:
        for ep, code in failures:
            print(f"FAIL: {ep} returned {code}")
        sys.exit(2)
    print("OK")
    sys.exit(0)
