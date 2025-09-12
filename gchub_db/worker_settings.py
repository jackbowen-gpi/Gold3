"""
Settings shim for Celery worker/beat processes.

This module imports the normal project settings then conditionally removes
``django_celery_beat`` from ``INSTALLED_APPS`` when the environment variable
``ENABLE_CELERY_BEAT`` is not set to a truthy value. That allows worker
processes (which don't need the DB-backed scheduler) to avoid importing
django-celery-beat model code at import time while keeping a single
configuration entrypoint for the project.

Usage:
- To run the scheduler with the Django database-backed scheduler, set
    ``ENABLE_CELERY_BEAT=1`` in the environment for the process that runs
    ``celery-beat`` (the default dev docker-compose already does this).
- Worker processes can leave ``ENABLE_CELERY_BEAT`` unset or set to ``0`` to
    avoid early model imports.

This shim is intended for developer convenience and should be reviewed if
you change runtime startup behavior or run in production.
"""

import os
from .settings import *  # noqa: F401,F403

# Ensure DJANGO_SETTINGS_MODULE points at this module when used as settings
__name__ = "gchub_db.worker_settings"

# ENABLE_CELERY_BEAT controls whether django_celery_beat remains in INSTALLED_APPS
_enable = os.environ.get("ENABLE_CELERY_BEAT", "").lower()
if _enable not in ("1", "true", "yes", "on"):
    _apps = list(globals().get("INSTALLED_APPS", []))
    if "django_celery_beat" in _apps:
        _apps.remove("django_celery_beat")
        INSTALLED_APPS = _apps
