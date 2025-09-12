# pytest configuration specific for VS Code Test Explorer
"""
Module conftest_vscode.py
"""

import os
import django


def pytest_configure():
    """Configure Django settings for pytest."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.test_settings")
    django.setup()


# Ignore problematic modules during collection
collect_ignore_glob = ["gchub_db/conftest.py", "*/conftest.py.bak"]
