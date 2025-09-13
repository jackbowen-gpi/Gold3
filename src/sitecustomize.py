"""
Early sys.path normalizer for developer/test runs.

Place this file at the repository root so when Python starts (and runs
`site`) it will import this module and normalize sys.path to avoid the
ambiguous layout where the repo root and an inner package both are named
`gchub_db`.

Behavior:
- Ensure the repo root is sys.path[0] and its parent is sys.path[1].
- Remove duplicate occurrences of these paths.
- Set an env var `GCHUB_SYSPATH_NORMALIZED=1` so other scripts can detect
  the normalization.

This is intentionally conservative and runs very early; it is a pragmatic
measure to make local test runs and CI less fragile for this legacy layout.
"""

import os
import sys

try:
    repo_root = os.path.abspath(os.path.dirname(__file__))
except Exception:
    # Fallback: if __file__ isn't set for some reason, use cwd
    repo_root = os.path.abspath(os.getcwd())
repo_parent = os.path.dirname(repo_root)


def _ensure_first(path, index=0):
    # Remove all occurrences then insert at requested index
    while path in sys.path:
        sys.path.remove(path)
    sys.path.insert(index, path)


# Make repo_root first, repo_parent second so imports resolve to the inner
# package directory under repo_root (e.g. repo_root/gchub_db) as the
# canonical location for the `gchub_db` package.
try:
    _ensure_first(repo_parent, 1)
    _ensure_first(repo_root, 0)
except Exception:
    pass

os.environ.setdefault("GCHUB_SYSPATH_NORMALIZED", "1")
