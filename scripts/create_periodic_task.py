#!/usr/bin/env python
"""
Create a sample PeriodicTask (django-celery-beat) for `bin.tasks.bin_test`
and trigger it once.

Usage (inside project):
  python scripts/create_periodic_task.py

This script:
- ensures an IntervalSchedule (1 minute) exists
- creates or updates a PeriodicTask named 'bin_test_every_min'
- triggers the task immediately via the task `.delay()` so the worker processes it now
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gchub_db.settings")
import django

django.setup()

from django_celery_beat.models import IntervalSchedule, PeriodicTask


def main():
    print("Creating interval schedule (1 minute) if missing...")
    sched, created = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)
    print(f"IntervalSchedule id={sched.id} created={created}")

    name = "bin_test_every_min"
    task = "bin.tasks.bin_test"

    pt, created = PeriodicTask.objects.get_or_create(
        name=name,
        defaults={
            "interval": sched,
            "task": task,
            "enabled": True,
            "args": "[]",
        },
    )

    if not created:
        # ensure it's enabled and points to the right schedule/task
        pt.interval = sched
        pt.task = task
        pt.enabled = True
        pt.args = "[]"
        pt.save()
        print(f"Updated existing PeriodicTask '{name}' (id={pt.id})")
    else:
        print(f"Created PeriodicTask '{name}' (id={pt.id})")

    # Trigger the task once immediately to verify worker processing
    print("Triggering the task immediately (bin.tasks.bin_test.delay())...")
    try:
        # import the task and call delay
        from bin.tasks import bin_test

        res = bin_test.delay()
        print("Task sent, task id:", res.id)
    except Exception as exc:
        print("Failed to send task:", exc)


if __name__ == "__main__":
    main()
