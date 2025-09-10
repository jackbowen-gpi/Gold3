from celery.schedules import crontab  # type: ignore[import-not-found]

CELERY_BEAT_SCHEDULE = {
    "run-example-task-every-minute": {
        "task": "tasks.example_task",
        "schedule": crontab(),  # every minute
    },
}
