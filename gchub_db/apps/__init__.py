"""Package initializer for gchub_db.apps.

This file extends the package search path to include the repository's
top-level `apps_top` directory (legacy 'apps' location). That lets
`import gchub_db.apps.workflow` resolve modules stored in `apps_top/`.

This is a reversible, low-risk shim to avoid moving many files on disk.
"""

import os

__path__ = [os.path.dirname(__file__)]
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
APPS_TOP = os.path.join(REPO_ROOT, "apps_top")
if os.path.isdir(APPS_TOP):
    # Prepend so package-internal modules prefer the apps_top copy.
    __path__.insert(0, APPS_TOP)
