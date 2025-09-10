from celery import shared_task  # type: ignore[import-not-found]


@shared_task
def hello_world():
    """Simple test task for Celery autodiscovery."""
    print("Hello, world!")
