#!/usr/bin/env python
"""
Custom test runner for VS Code Test Explorer compatibility.
This script sets up Django environment and runs tests that VS Code can discover.
"""

import os
import sys
import django


def setup_django():
    """Set up Django environment for testing."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
    django.setup()


def run_tests():
    """Run Django tests in a way that's compatible with VS Code."""
    setup_django()

    # Import after Django setup
    from django.test.runner import DiscoverRunner

    # Create test runner
    test_runner = DiscoverRunner(verbosity=2, interactive=False)

    # Run tests for specific apps
    failures = test_runner.run_tests(["gchub_db.apps.workflow.tests"])

    return failures


if __name__ == "__main__":
    # If specific test module is provided as argument, run just that
    if len(sys.argv) > 1:
        test_module = sys.argv[1]
        setup_django()
        from django.test.runner import DiscoverRunner

        test_runner = DiscoverRunner(verbosity=2, interactive=False)
        failures = test_runner.run_tests([test_module])
    else:
        failures = run_tests()

    sys.exit(failures)
