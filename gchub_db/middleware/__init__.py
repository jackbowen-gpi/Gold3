"""
Shim to expose repo-level middleware/ as gchub_db.middleware
for legacy imports.
"""

import os

__path__ = [os.path.dirname(__file__)]
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MIDDLEWARE_DIR = os.path.join(REPO_ROOT, "middleware")
if os.path.isdir(MIDDLEWARE_DIR):
    __path__.insert(0, MIDDLEWARE_DIR)
