"""
Run pytest with a controlled import environment.

This script inserts the repository parent on sys.path and sets the
DJANGO_SETTINGS_MODULE to the repo-root `settings` shim before importing
pytest. It helps avoid import-order problems where pytest plugins try to
import Django settings before the path is configured.
"""

import os
import sys

THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
PARENT = os.path.abspath(os.path.join(REPO_ROOT, ".."))

# Ensure the repository parent is first on sys.path so the repo-root
# `settings.py` and `gchub_db` package resolve as intended during test
# collection.
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")


def main():
    try:
        import pytest
    except Exception as e:
        print("pytest not available in venv:", e)
        return 2

    args = ["-q", "--ignore=bin"]
    return pytest.main(args)


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
