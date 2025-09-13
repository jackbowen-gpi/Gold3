# package marker for gchub_db project package
# This package contains the application subpackages under gchub_db/apps

# Import Celery app for Flower compatibility
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.celery_app import app as celery

__all__ = ["celery"]
