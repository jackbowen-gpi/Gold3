"""
Shim to expose the repo-level `includes/` directory as
`gchub_db.includes` so legacy imports work without moving files.
"""

import os

__path__ = [os.path.dirname(__file__)]
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INCLUDES_DIR = os.path.join(REPO_ROOT, "includes")
if os.path.isdir(INCLUDES_DIR):
    __path__.insert(0, INCLUDES_DIR)
