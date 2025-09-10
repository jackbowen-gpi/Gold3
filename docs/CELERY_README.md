# Celery (worker)

This document explains how Celery is used in this repository, how to run and manage the worker, and troubleshooting tips.

## Purpose
- Executes asynchronous tasks from the Django app.
- In this repo the Celery worker is configured to autodiscover tasks from Django apps and the top-level `bin` package.

## Service name (docker-compose)
- `celery` — the worker container; defined in `docker-compose.yml`.

## Key files in this repo
- `celery_app.py` — canonical Celery application object for the project (use `-A celery_app`).
- `bin/tasks.py` — example repo-level tasks (autodiscovered).

## Environment
- `CELERY_BROKER_URL` — broker URL (e.g. `redis://redis:6379/0`). Ensure this is set in the `web`, `celery`, and `celery-beat` services.
- `DJANGO_SETTINGS_MODULE` — should point to `gchub_db.settings` per repo setup.

## Common operations (PowerShell / pwsh)
- Start worker (already in compose):
```pwsh
docker-compose up -d celery
```
- Force recreate worker (so it re-autodiscovers tasks):
```pwsh
docker-compose up -d --no-deps --force-recreate celery
```
- See worker logs (follow):
```pwsh
docker-compose logs -f celery
```

## Verifying tasks
- From web container, publish a task:
```pwsh
docker-compose exec web python manage.py shell -c "from bin.tasks import bin_test; bin_test.delay()"
```
- In the worker logs you should see the task received and executed.

## Best practices
- Use a single broker (Redis) and keep `CELERY_BROKER_URL` consistent across containers.
- Restart the worker whenever you add new modules at the repo root (like `bin`) so autodiscovery picks them up.
- Run workers as a non-root user in production (the container currently warns when run as root).

## Troubleshooting
- Worker not connecting to broker: check `CELERY_BROKER_URL` inside the container and connectivity to the `redis` service.
- Task not found: ensure the dotted task path is correct and the worker was restarted so it autodiscovered newly added modules.

## Links
- Celery docs: https://docs.celeryq.dev/
