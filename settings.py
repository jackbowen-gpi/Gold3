try:
    # Prefer package settings (gchub_db/settings.py)
    from gchub_db.settings import DEBUG  # noqa: F401
except ImportError:
    # Fallback: try loading legacy common settings if package import fails
    pass
