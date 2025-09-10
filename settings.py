try:
    # Prefer package settings (gchub_db/settings.py)
    from gchub_db.settings import *  # noqa: F401,F403
except ImportError:
    # Fallback: try loading legacy common settings if package import fails
    pass
