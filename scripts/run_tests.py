"""Helper script to run tests; prefers pytest and falls back to Django test runner."""

import os
import sys

try:
    from rich.console import Console

    console = Console()
    console.print("[bold green]Using rich for test output if available[/]")
except Exception:
    console = None


def main():
    # Prefer pytest if available
    try:
        import pytest

        if console:
            console.print("Running pytest...")
        rc = pytest.main([])
        sys.exit(rc)
    except Exception:
        # Fallback to Django's manage.py test
        if console:
            console.print("pytest not available; running manage.py test")
        os.execv(sys.executable, [sys.executable, "manage.py", "test"])


if __name__ == "__main__":
    main()
