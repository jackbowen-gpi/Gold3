"""Attempt to import `gchub_db.settings` and print traceback on failure."""

import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
try:
    import importlib

    importlib.import_module("gchub_db.settings")
    print("settings imported")
except Exception:
    traceback.print_exc()
