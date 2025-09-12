# Celery configuration
"""
Module settings.py
"""

import os

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
try:
    # Prefer package settings (gchub_db/settings.py)
    from gchub_db.settings import *  # noqa: F401,F403
except ImportError:
    # Fallback: try loading legacy common settings if package import fails
    pass
