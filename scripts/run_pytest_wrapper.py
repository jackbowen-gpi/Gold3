"""
Run pytest with repo root prepended to sys.path to avoid import-order races
that prevent Django settings and apps from being imported during pytest startup.

Usage: python scripts/run_pytest_wrapper.py [pytest-args]
"""

import os
import sys

# repo_root is the repository folder (.../gchub_db). The project also contains
# an inner package directory named `gchub_db` at repo_root/gchub_db. To avoid
# import ambiguity we insert the inner package directory first, then the
# repository root, then the parent directory.
repo_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
inner_pkg_dir = os.path.join(repo_root, "gchub_db")
parent = os.path.dirname(repo_root)

# Remove any existing occurrences before inserting our preferred order.
for p in (inner_pkg_dir, repo_root, parent):
    while p in sys.path:
        sys.path.remove(p)

# Insert in reverse order so inner_pkg_dir becomes sys.path[0].
sys.path.insert(0, parent)
sys.path.insert(0, repo_root)
sys.path.insert(0, inner_pkg_dir)
# Ensure pytest-django sees the test settings module explicitly to avoid
# import-order races in this repository layout.
# Point to the minimal test settings inside the inner `gchub_db` package.
# The repo layout places the inner package on sys.path as `gchub_db`, so the
# correct module path is `gchub_db.test_settings`.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.test_settings")


def main():
    # Verify test settings import early; avoid printing diagnostics in normal runs.
    import importlib

    importlib.import_module("gchub_db.test_settings")
    import pytest

    # forward command-line args to pytest; if none, run tests under apps/workflow
    args = sys.argv[1:] or ["gchub_db/gchub_db/apps/workflow"]
    # Ensure pytest-django is told which settings module to use. Allow callers to
    # override via --ds; otherwise append our test settings so the plugin doesn't
    # try to auto-discover or fail during its initial import phase.
    if not any(a.startswith("--ds=") for a in args):
        args = ["--ds=gchub_db.test_settings"] + args
    raise SystemExit(pytest.main(args))


if __name__ == "__main__":
    main()
