r"""
Module src\celery_app.py
"""

import os
import logging

# Ensure a default settings module is available; actual django.setup()
# is performed by the container startup wrappers so importing this module
# doesn't trigger Django app population during package import.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

from celery import Celery  # type: ignore[import-not-found]

# Explicitly import tasks from bin package since it's not a Django app.
# Do this after Django is set up in the container entrypoint to avoid
# import-time side-effects.
try:
    import bin.tasks  # noqa: F401
except Exception:
    # Import may fail during static analysis or before Django is configured;
    # defer failures to runtime when startup wrappers call django.setup().
    pass

app = Celery("Gold3")
# Load configuration from Django settings (CELERY_ prefixed settings)
app.config_from_object("django.conf:settings", namespace="CELERY")

# If the Django settings module didn't set a broker URL, allow an explicit
# environment variable to override so processes started in Docker (web)
# can publish tasks to the same broker as workers.
env_broker = os.environ.get("CELERY_BROKER_URL")
if env_broker and not getattr(app.conf, "broker_url", None):
    app.conf.broker_url = env_broker


app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    logger = logging.getLogger(__name__)
    logger.info(f"Request: {self.request!r}")
    print(f"Request: {self.request!r}")
