# Celery Beat (scheduler)

Celery Beat schedules periodic tasks and (in this repo) uses the Django database scheduler provided by `django-celery-beat`.

## Purpose
- Runs scheduled tasks (PeriodicTask) and writes scheduling metadata to the database.

## Service name (docker-compose)
- `celery-beat` — runs the scheduler (configured to use DjangoDatabaseScheduler in settings via `django_celery_beat`).

## Key repo specifics
- `django_celery_beat` is installed and included in `INSTALLED_APPS`.
- Readiness coordination: `celery-beat` waits for the web readiness marker (`/app/.web_ready`) to ensure migrations and DB are ready.

## Managing schedules via UI
- Use the Django Admin (`/admin/`) → Django-Celery-Beat → Periodic tasks / Interval schedules / Crontab schedules.

## Programmatic creation
- Example using Django shell to create an IntervalSchedule + PeriodicTask:
```py
from django_celery_beat.models import IntervalSchedule, PeriodicTask
sched, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)
PeriodicTask.objects.create(interval=sched, name='bin_test_every_min', task='bin.tasks.bin_test', enabled=True)
```

## Common commands
```pwsh
docker-compose -f ../../config/docker-compose.yml up -d celery-beat
docker-compose -f ../../config/docker-compose.yml logs -f celery-beat
```

## Troubleshooting
- If beat fails early: confirm migrations for `django_celery_beat` were run and the DB is available.
- If scheduled tasks don't run: verify tasks exist in admin and the worker is running and has the task registered.

## Links
- django-celery-beat: https://github.com/celery/django-celery-beat
