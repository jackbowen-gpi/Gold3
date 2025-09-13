try:
    # Prefer package settings (gchub_db/settings.py)
    from gchub_db.settings import *  # noqa: F403
except ImportError:
    # Fallback: try loading legacy common settings if package import fails
    from config.settings_common import *  # noqa: F403
