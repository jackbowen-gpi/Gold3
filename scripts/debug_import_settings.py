"""
Quick helper to verify importing `gchub_db.settings` from the repo.

Useful during local setup when Python path issues occur.
"""

import os
import sys
import traceback

repo_root = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), "manage.py")))
sys.path.insert(0, repo_root)
try:
    import gchub_db.settings as s

    print("Imported gchub_db.settings OK from", s.__file__)
except Exception:
    traceback.print_exc()
    print("sys.path:", sys.path[:3])
    sys.exit(1)
