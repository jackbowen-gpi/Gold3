# pytest plugin to ensure parent of repo is on sys.path early
r"""
Module data\pytest_local_path.py
"""

import os
import sys

root = os.path.abspath(os.path.dirname(__file__))
# Repo root (where settings_common.py lives)
repo_root = root
# Parent directory (so inner package gchub_db/gchub_db
# can be imported as gchub_db.gchub_db)
parent = os.path.dirname(root)
for p in (repo_root, parent):
    if p not in sys.path:
        sys.path.insert(0, p)
