#!/usr/bin/env python
"""Entry point for Django management commands for the gchub_db project."""
import os
import sys

if __name__ == "__main__":
    # Ensure project package import precedence during manage.py runs.
    # Historically the repo root was inserted first which allowed a legacy
    # top-level apps tree (e.g. apps_top_backup_disabled) to shadow the
    # canonical package imports (gchub_db.apps.*) during test discovery.
    # To avoid unittest discovery importing tests from the legacy tree,
    # skip inserting the repo root while running tests. For other commands
    # (runserver, shell, etc.) keep the previous behavior for compatibility.
    repo_root = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(repo_root)
    if "test" in sys.argv:
        # For test runs, insert the repository root and its parent so
        # `import gchub_db` resolves to the `gchub_db` package directory
        # located at <repo_root>/gchub_db. We neutralized legacy shims
        # that previously created nested import paths.
        sys.path.insert(0, repo_root)
        sys.path.insert(1, parent)
    # For test runs we prefer explicit repo_root precedence. Debug
    # logging removed now that discovery is stable.
    else:
        # Preserve original behavior for non-test commands.
        sys.path.insert(0, repo_root)
        sys.path.insert(1, parent)

    # Use the top-level settings.py during local development for compatibility
    # with the repo layout where settings.py lives at the repository root.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        raise
    execute_from_command_line(sys.argv)
