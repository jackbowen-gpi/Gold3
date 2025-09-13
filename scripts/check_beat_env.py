#!/usr/bin/env python3
import os
import sys
import traceback

print("ENV DJANGO_SETTINGS_MODULE=", os.environ.get("DJANGO_SETTINGS_MODULE"))
try:
    import django
    from django.apps import apps

    print("django imported; apps.ready before setup =", getattr(apps, "ready", None))
except Exception:
    print("failed to import django:")
    traceback.print_exc()

try:
    django.setup()
    print("django.setup() succeeded; apps.ready =", apps.ready)
except Exception:
    print("django.setup() failed:")
    traceback.print_exc()

try:
    from importlib import import_module

    import_module("django_celery_beat.models")
    print("import django_celery_beat.models succeeded")
except Exception:
    print("import django_celery_beat.models failed:")
    traceback.print_exc()

sys.exit(0)
