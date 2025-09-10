# package marker for gchub_db project package
# This package contains the application subpackages under gchub_db/apps

# Import Celery app for Flower compatibility
from celery_app import app as celery

__all__ = ["celery"]
