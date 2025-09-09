"""Bootstrap settings shim.

This file remains at the repo root for tooling that expects to import
`settings` directly. It delegates to the package-level
`gchub_db.settings` we just created.
"""

try:
    # Prefer package settings (gchub_db/settings.py)
    from gchub_db.settings import *  # noqa: F401,F403
except Exception:
    # Fallback: try loading legacy common settings if package import fails
    from settings_common import *  # type: ignore
