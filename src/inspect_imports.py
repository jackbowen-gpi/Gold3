r"""
Module src\inspect_imports.py
"""

import importlib
import os
import sys

print("initial sys.path head")
for p in sys.path[:5]:
    print(" ", p)
print("\ntrying import gchub_db")
try:
    m = importlib.import_module("gchub_db")
    print("gchub_db ->", getattr(m, "__file__", getattr(m, "__path__", None)))
except Exception as e:
    print("gchub_db import failed", type(e).__name__, e)
print("\ntrying import gchub_db.apps.legacy_support")
try:
    m = importlib.import_module("gchub_db.apps.legacy_support")
    print("legacy_support ->", getattr(m, "__file__", getattr(m, "__path__", None)))
except Exception as e:
    print("legacy_support import failed", type(e).__name__, e)
print("\ninsert repo_root at index 0 (C:\\Dev\\Gold\\gchub_db)")
repo_root = os.path.abspath(".")
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
for p in sys.path[:5]:
    print(" ", p)
print("\nretry imports")
try:
    m = importlib.import_module("gchub_db")
    print("gchub_db ->", getattr(m, "__file__", getattr(m, "__path__", None)))
except Exception as e:
    print("gchub_db import failed", type(e).__name__, e)
try:
    m = importlib.import_module("gchub_db.apps.legacy_support")
    print("legacy_support ->", getattr(m, "__file__", getattr(m, "__path__", None)))
except Exception as e:
    print("legacy_support import failed", type(e).__name__, e)
