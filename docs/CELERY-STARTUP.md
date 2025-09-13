Celery startup and celery-beat notes

This document explains the startup wrappers used in the repository and the
`ENABLE_CELERY_BEAT` environment variable that controls whether
`django_celery_beat` stays enabled in `INSTALLED_APPS` for worker/beat
processes.

Why wrappers?
- Some third-party packages (notably `django_celery_beat`) import Django model
  classes at module import time. If that happens before `django.setup()` is
  called the process will raise `AppRegistryNotReady` and exit.
- To avoid calling `django.setup()` at module import time (which causes
  side-effects during linting/static analysis), the project moves Django
  initialization into container startup wrappers. Those scripts wait until the
  `web` service has completed migrations and created the readiness marker
  `/app/.web_ready`, then they call `django.setup()` and start Celery in the
  same Python process. This ensures the app registry is populated when the
  scheduler imports models.

Files
- `scripts/start-celery-worker.sh` — waits for `/app/.web_ready`, calls
  `django.setup()`, then starts the Celery worker in-process.
- `scripts/wait-and-start-celery-beat.sh` — waits for `/app/.web_ready`, calls
  `django.setup()`, configures `app.conf.beat_scheduler` to `src.lazy_beat_scheduler:LazyDatabaseScheduler`
  and starts celery-beat in-process. The lazy scheduler delays importing
  `django_celery_beat` objects until after the registry is ready.
- `src/lazy_beat_scheduler.py` — a small proxy that instantiates
  `django_celery_beat.schedulers.DatabaseScheduler` only when the scheduler
  is created (reduces the surface of early imports).
- `gchub_db/worker_settings.py` — a settings shim used by worker processes.
  It reads the environment variable `ENABLE_CELERY_BEAT`. If that variable is
  not set to a truthy string ("1", "true", "yes", "on"), the shim removes
  `django_celery_beat` from `INSTALLED_APPS` so workers don't import its
  models at process startup.

ENABLE_CELERY_BEAT
- Purpose: provide a simple opt-in mechanism to allow the DB-backed scheduler
  to be present for the `celery-beat` service while leaving workers' runtime
  environment free from import-time model loading.
- Usage in docker-compose (dev):
  - `celery` service sets `ENABLE_CELERY_BEAT: "0"` (workers do not enable)
  - `celery-beat` service sets `ENABLE_CELERY_BEAT: "1"` (beat enables)

Is Flower supposed to be running?
- The compose setup includes a `flower` service. Flower is optional but useful
  for monitoring and inspecting Celery workers. It does not affect the
  scheduler or workers other than reading the broker. If you don't need it,
  you can remove or comment out the `flower` service in `docker-compose.yml`.

Notes and gotchas
- This startup mechanism is intended for local development. For production
  deployments you should ensure your process manager or container startup
  correctly initializes Django before importing apps that rely on the app
  registry.
 - The `wait-and-start-celery-beat.sh` script accepts two optional environment
   variables to control waiting behavior:
   - `WAIT_TIMEOUT` — maximum seconds to wait for the readiness marker
     `/app/.web_ready`. If unset or `0` the script waits indefinitely.
   - `WAIT_INTERVAL` — seconds between checks when waiting (default `1`).
   These can be set from `docker-compose.yml` or the container environment.

 - The script now appends `/app` to `PYTHONPATH` (instead of overwriting it)
   so any existing paths are preserved. You can still set `PYTHONPATH` in
   `docker-compose.yml` if needed; the script will ensure `/app` is present.
- If you need both worker and beat to have `django_celery_beat` enabled, set
  `ENABLE_CELERY_BEAT=1` for both services and ensure your startup ordering
  guarantees migrations and web readiness.

Contact
- If something breaks during startup, check the container logs for
  `AppRegistryNotReady` and verify `/app/.web_ready` exists on the web side.
