# Celery & Celery Beat Integration for Gold3

## What is Celery?
Celery is a distributed task queue for Python. It allows you to run background jobs (tasks) asynchronously or on a schedule, outside the main web request/response cycle. Celery is widely used for sending emails, processing files, running periodic jobs, and more.

- [Celery Project Homepage](https://docs.celeryq.dev/en/stable/)
- [Celery Beat (Scheduler)](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)

## What is Celery Beat?
Celery Beat is a scheduler that kicks off tasks at regular intervals, which are then executed by Celery workers. It is similar to cron, but managed in Python and integrated with Celery.

## How It Works in This Project
- **Celery** runs as a separate process (container in Docker) and executes tasks defined in `tasks.py` or any app's `tasks.py`.
- **Celery Beat** runs as a scheduler, sending scheduled tasks to Celery workers.
- **Redis** is used as the message broker for task queueing.

## Running Locally
1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Start Redis (you can use Docker or install locally):
   ```sh
   docker run -p 6379:6379 redis:7
   ```
3. Start a Celery worker:
   ```sh
   celery -A celery_app worker --loglevel=info
   ```
4. (Optional) Start Celery Beat for scheduled tasks:
   ```sh
   celery -A celery_app beat --loglevel=info
   ```

## Running in Docker
All services are defined in `docker-compose.yml`:
- `web`: Django app
- `db`: Postgres database
- `redis`: Redis broker
- `celery`: Celery worker
- `celery-beat`: Celery Beat scheduler

To start everything:
```sh
docker-compose -f config/docker-compose.yml up --build
```

## Adding Tasks
- Add new tasks to `tasks.py` or any app's `tasks.py` using the `@shared_task` decorator.
- To schedule tasks, add them to `celery_beat_schedule.py`.

## Example Task
```
from celery import shared_task

@shared_task
def my_task():
    print("Task is running!")
```

## Important Links
- [Celery Documentation](https://docs.celeryq.dev/en/stable/)
- [Celery Beat Periodic Tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)
- [Django + Celery Guide](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)

## Troubleshooting
- Make sure Redis is running and accessible.
- Check logs for errors in the Celery and Celery Beat containers.
- Use `docker-compose -f config/docker-compose.yml logs celery` and `docker-compose -f config/docker-compose.yml logs celery-beat` for debugging.

---

This setup allows you to run scheduled and background jobs both locally and in Docker, with minimal changes to your workflow.
