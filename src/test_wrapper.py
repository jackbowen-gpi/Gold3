#!/usr/bin/env python
"""
Test wrapper for VS Code Test Explorer integration with Django.
This script allows VS Code to discover and run Django tests individually.
"""

import os
import sys
import django


def setup_django():
    """Set up Django for testing."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.test_settings")
    django.setup()


def main():
    """Main entry point for running tests."""
    # Set up Django
    setup_django()

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: test_wrapper.py <test_module_or_class>")
        sys.exit(1)

    test_target = sys.argv[1]

    # Convert test path for Django test runner
    # e.g., "gchub_db.apps.workflow.tests.
    # test_item_model_basic.ItemModelBasicTests.
    # test_item_creation_basic"

    # Run the test using Django's test runner
    os.environ["DJANGO_SETTINGS_MODULE"] = "gchub_db.test_settings"
    sys.argv = ["manage.py", "test", test_target, "--verbosity=2"]

    try:
        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
    except SystemExit as e:
        sys.exit(e.code)


if __name__ == "__main__":
    main()
