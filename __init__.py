# NOTE: during local modernization we temporarily rename the top-level
# `apps/` package on disk to avoid being importable as `apps.*` while the
# canonical project package remains `gchub_db.apps`. This file is left

# Import the Celery application instance for use with Django and task discovery.
from .celery_app import app as celery_app

__all__ = ("celery_app",)
