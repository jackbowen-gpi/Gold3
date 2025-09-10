import os
import logging
from celery import Celery  # type: ignore[import-not-found]

# Explicitly import tasks from bin package since it's not a Django app
import bin.tasks  # noqa: F401

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")

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
