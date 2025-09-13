"""
Shim to expose the repo-level `templatetags/` directory as
`gchub_db.templatetags` for legacy template library imports.
"""

import os

__path__ = [os.path.dirname(__file__)]
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATETAGS_DIR = os.path.join(REPO_ROOT, "templatetags")
if os.path.isdir(TEMPLATETAGS_DIR):
    __path__.insert(0, TEMPLATETAGS_DIR)
