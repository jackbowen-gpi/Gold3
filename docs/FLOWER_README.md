# Flower (Celery monitoring web UI)

Flower provides a web UI to inspect Celery workers, tasks, and events.

## Purpose
- Monitor worker status, active tasks, scheduled tasks, and broker information.

## Service name (docker-compose)
- `flower` — exposed on port 5555 in the compose file.

## Running
```pwsh
docker-compose up -d flower
```

## UI
- Open http://127.0.0.1:5555 to access Flower.

## Troubleshooting
- If Flower doesn't show workers: confirm `CELERY_BROKER_URL` is set correctly and the worker is connected to the same broker.

## Links
- Flower docs: https://flower.readthedocs.io/
