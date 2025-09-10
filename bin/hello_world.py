# bin/hello_world.py
from celery_app import app  # project Celery app module used in this repo


@app.task
def hello_world():
    print("Hello, world!")


if __name__ == "__main__":
    # fire-and-forget when run directly (calls the task asynchronously)
    hello_world.delay()
